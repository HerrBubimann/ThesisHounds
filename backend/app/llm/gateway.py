import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.errors import LLMError
from app.llm.model_registry import ModelDefinition, ModelRegistry
from app.llm.providers.base import Completion, LLMProvider
from app.security.policy_engine import PolicyEngine

T = TypeVar("T", bound=BaseModel)


@dataclass
class CallBudget:
    max_calls: int
    max_tokens: int
    calls: int = 0
    reserved_tokens: int = 0
    observed_tokens: int = 0
    unknown_token_calls: int = 0

    def reserve(self, input_bound: int, output_bound: int) -> None:
        # Reserving before awaiting is atomic on this single asyncio event loop.
        if (
            self.calls >= self.max_calls
            or self.reserved_tokens + input_bound + output_bound > self.max_tokens
        ):
            raise LLMError(429, "Modellaufruf- oder Tokenbudget ist ausgeschöpft.")
        self.calls += 1
        self.reserved_tokens += input_bound + output_bound

    def record(self, response: Completion) -> None:
        if response.input_tokens is None or response.output_tokens is None:
            self.unknown_token_calls += 1
        self.observed_tokens += (response.input_tokens or 0) + (response.output_tokens or 0)


class LLMGateway:
    def __init__(
        self,
        registry: ModelRegistry,
        providers: dict[str, LLMProvider],
        policy: PolicyEngine,
        *,
        max_parallel: int = 1,
        sequential_loading: bool = True,
    ) -> None:
        self.registry = registry
        self.providers = providers
        self.policy = policy
        self.sequential_loading = sequential_loading
        self.slots = asyncio.Semaphore(1 if sequential_loading else max_parallel)

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
    ) -> tuple[Completion, T | None]:
        model = self.registry.get(model_id, role)
        self.policy.check(model, classification, role)
        capability = "structured_output" if output_type else "chat"
        if capability not in model.capabilities or model.provider not in self.providers:
            raise LLMError(503, "Provider oder Modellfähigkeit ist nicht verfügbar.")
        # Byte length is a deliberately conservative input-token reservation, including schema.
        schema = output_type.model_json_schema() if output_type else None
        input_bound = (
            sum(len(m["content"].encode("utf-8")) for m in messages)
            + len(str(schema or "").encode())
            + 256
        )
        if input_bound + max_tokens > model.context_length:
            raise LLMError(422, "Anfrage überschreitet das konservative Kontextbudget.")
        async with self.slots:
            self.policy.check(model, classification, role)
            budget.reserve(input_bound, max_tokens)
            if on_call:
                on_call()
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
            budget.record(response)
            if on_result:
                on_result(response)
        if output_type is None:
            return response, None
        try:
            return response, output_type.model_validate_json(response.text)
        except ValidationError:
            raise LLMError(
                502, "Modellantwort entspricht nicht dem freigegebenen Schema."
            ) from None

    def independent_reviewers(self, source: ModelDefinition) -> list[ModelDefinition]:
        return [
            m
            for m in self.registry.enabled()
            if "reviewer" in m.allowed_roles and m.manufacturer != source.manufacturer
        ]
