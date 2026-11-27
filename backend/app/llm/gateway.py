import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.errors import LLMError
from app.llm.model_registry import ModelDefinition, ModelRegistry
from app.llm.model_router import ModelRouter, ResourceBudget, RoutingDecision, TaskType
from app.llm.providers.base import Completion, LLMProvider
from app.security.access_control import principal
from app.security.audit_service import AuditEvent, AuditService
from app.security.classification import classify, combine
from app.security.egress_policy import inference_dispatch
from app.security.information_flow import InformationLabel
from app.security.policy_engine import PolicyEngine
from app.security.tool_permissions import (
    current_agent,
    validate_model_messages,
    validate_model_output,
)

T = TypeVar("T", bound=BaseModel)


def _validate_token_bounds(input_bound: int, output_bound: int) -> None:
    if (
        type(input_bound) is not int
        or input_bound < 0
        or type(output_bound) is not int
        or output_bound < 1
    ):
        raise LLMError(422, "Tokenlimits müssen gültige ganzzahlige Grenzen sein.")


def estimate_input_tokens(messages: list[dict[str, str]], schema: dict | None) -> int:
    """Conservative reservation, not a model-specific tokenizer or measured usage.

    Without a verified tokenizer for each model, reserve one token per serialized
    UTF-8 byte rather than divide by an average characters/bytes-per-token ratio.
    Include roles, JSON escaping and the schema, plus token margins for the model's
    chat template and per-message framing. Templates can still exceed these margins;
    reconcile reported usage after inference. No prompt text is persisted here.
    """
    payload = {"messages": messages}
    if schema is not None:
        payload["format"] = schema
    serialized = json.dumps(payload, ensure_ascii=False)
    return len(serialized.encode("utf-8")) + 512 + 32 * len(messages)


@dataclass
class CallBudget:
    max_calls: int
    max_tokens: int
    calls: int = 0
    reserved_tokens: int = 0
    observed_tokens: int = 0
    unknown_token_calls: int = 0

    def reserve(self, input_bound: int, output_bound: int) -> None:
        _validate_token_bounds(input_bound, output_bound)
        # Reserving before awaiting is atomic on this single asyncio event loop.
        if (
            self.calls >= self.max_calls
            or self.reserved_tokens + input_bound + output_bound > self.max_tokens
        ):
            raise LLMError(429, "Modellaufruf- oder Tokenbudget ist ausgeschöpft.")
        self.calls += 1
        self.reserved_tokens += input_bound + output_bound

    def record(self, response: Completion, *, reserved_input: int, reserved_output: int) -> None:
        if response.input_tokens is None or response.output_tokens is None:
            self.unknown_token_calls += 1
        self.observed_tokens += (response.input_tokens or 0) + (response.output_tokens or 0)
        # Never refund a conservative reservation or a failed/unknown call. If the
        # template or provider exceeds it, charge the excess before any further call.
        self.reserved_tokens += max(0, (response.input_tokens or 0) - reserved_input)
        self.reserved_tokens += max(0, (response.output_tokens or 0) - reserved_output)


class LLMGateway:
    def __init__(
        self,
        registry: ModelRegistry,
        providers: dict[str, LLMProvider],
        policy: PolicyEngine,
        *,
        max_parallel: int = 1,
        sequential_loading: bool = True,
        capability_records=(),
    ) -> None:
        self.registry = registry
        self.providers = providers
        self.policy = policy
        self.sequential_loading = sequential_loading
        self.slots = asyncio.Semaphore(1 if sequential_loading else max_parallel)
        self.audit: AuditService | None = None
        self.router = ModelRouter(registry, policy, capability_records)

    async def route(
        self,
        task: TaskType,
        role: str,
        classification: str,
        manual_default: str,
        *,
        resources: ResourceBudget | None = None,
        exclude_manufacturers: frozenset[str] = frozenset(),
        available: dict[str, str] | None = None,
        required_tasks: tuple[TaskType, ...] = (),
    ) -> RoutingDecision:
        if available is None:
            provider = self.providers.get("ollama")
            if provider is None:
                raise LLMError(503, "Lokaler Provider fehlt.")
            available = {m.name: m.digest for m in await provider.discover()}
        # The live gateway policy remains mandatory, even if it is replaced/unavailable.
        self.router.policy = self.policy
        return self.router.select(
            task,
            role,
            classification,
            available,
            manual_default,
            resources=resources,
            exclude_manufacturers=exclude_manufacturers,
            required_tasks=required_tasks,
        )

    async def complete(
        self,
        model_id: str,
        role: str,
        classification: str | None,
        messages: list[dict[str, str]],
        budget: CallBudget,
        *,
        output_type: type[T] | None = None,
        max_tokens: int = 2048,
        on_call: Callable[[], None] | None = None,
        on_result: Callable[[Completion], None] | None = None,
        label: InformationLabel | None = None,
    ) -> tuple[Completion, T | None]:
        classification = (
            combine(classification, label.classification) if label else classify(classification)
        )
        model = self.registry.get(model_id, role)
        try:
            self.policy.check(model, classification, role)
        except Exception:
            if self.audit and label:
                self.audit.record(
                    AuditEvent(analysis_id=label.analysis_id, action="DENY", decision="DENY")
                )
            raise
        capability = "structured_output" if output_type else "chat"
        if "process" not in principal().permissions:
            raise LLMError(403, "MODEL_ACTOR_DENIED")
        if label and "read" not in principal().permissions:
            raise LLMError(403, "MODEL_DOCUMENT_READ_DENIED")
        validate_model_messages(messages)
        agent = current_agent.get()
        if agent and (
            agent.owner_subject != principal().subject
            or not label
            or label.analysis_id != agent.run_id
            or not label.document_ids <= agent.allowed_documents
            or model_id != agent.model_id
            or model_id not in agent.allowed_models
            or role != agent.role
        ):
            raise LLMError(403, "MODEL_AGENT_SCOPE_DENIED")
        if label and (not label.analysis_id or not label.document_ids):
            raise LLMError(403, "MODEL_DOCUMENT_SCOPE_REQUIRED")
        if capability not in model.capabilities or model.provider not in self.providers:
            raise LLMError(503, "Provider oder Modellfähigkeit ist nicht verfügbar.")
        schema = output_type.model_json_schema() if output_type else None
        input_bound = estimate_input_tokens(messages, schema)
        _validate_token_bounds(input_bound, max_tokens)
        if input_bound + max_tokens > model.context_length:
            raise LLMError(422, "Anfrage überschreitet das konservative Kontextbudget.")
        async with self.slots:
            self.policy.check(model, classification, role)
            if self.audit and label:
                self.audit.record(
                    AuditEvent(analysis_id=label.analysis_id, action="PROCESS", decision="ALLOW")
                )
            budget.reserve(input_bound, max_tokens)
            if on_call:
                on_call()
            dispatch_token = inference_dispatch.set(model.name)
            try:
                response = await self.providers[model.provider].complete(
                    model,
                    messages,
                    schema,
                    max_tokens,
                    unload=self.sequential_loading,
                )
            except BaseException:
                budget.unknown_token_calls += 1
                raise
            finally:
                inference_dispatch.reset(dispatch_token)
            budget.record(response, reserved_input=input_bound, reserved_output=max_tokens)
            response = response.model_copy(update={"data_classification": classification})
            if on_result:
                on_result(response)
            if budget.reserved_tokens > budget.max_tokens:
                raise LLMError(429, "Gemeldeter Tokenverbrauch überschreitet das Modellbudget.")
        if output_type is None:
            return response, None
        try:
            validate_model_output(json.loads(response.text))
            parsed = output_type.model_validate_json(response.text)
            validate_model_output(parsed.model_dump())
            return response, parsed
        except (ValidationError, json.JSONDecodeError):
            raise LLMError(
                502, "Modellantwort entspricht nicht dem freigegebenen Schema."
            ) from None

    def independent_reviewers(self, source: ModelDefinition) -> list[ModelDefinition]:
        return [
            m
            for m in self.registry.enabled()
            if "reviewer" in m.allowed_roles and m.manufacturer != source.manufacturer
        ]
