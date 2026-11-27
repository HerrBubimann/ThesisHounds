from contextvars import ContextVar

from pydantic import BaseModel, ConfigDict, Field

from app.llm.errors import LLMError
from app.security.access_control import principal
from app.security.classification import combine

current_agent: ContextVar = ContextVar("executing_agent", default=None)


def validate_tools(requested: list[str], policy_allowlist: list[str]) -> None:
    # This release has no shell, network, Python execution or arbitrary file tools.
    if not set(requested) <= (set(policy_allowlist) & {"document.read"}):
        raise LLMError(403, "Werkzeug ist nicht freigegeben.")


class ToolInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    agent_id: str
    analysis_id: str
    document_id: str
    tool_id: str
    purpose: str = Field(min_length=1, max_length=60)
    parameters: dict = Field(default_factory=dict)
    network_target: str | None = None


def authorize_tool_call(call, registry, record, document, budget, limits):
    call = ToolInvocation.model_validate(
        call.model_dump() if isinstance(call, ToolInvocation) else call
    )
    actor = principal()
    if (
        "process" not in actor.permissions
        or "read" not in actor.permissions
        or record.owner_subject != actor.subject
        or registry.records.get(record.agent_id) is not record
        or call.agent_id != record.agent_id
        or call.analysis_id != record.run_id
        or document.analysis_id != call.analysis_id
        or call.document_id != document.document_id
        or call.document_id not in record.allowed_documents
        or combine(record.data_classification, document.classification)
        != record.data_classification
        or call.network_target is not None
        or record.depth > limits.max_delegation_depth
    ):
        raise LLMError(403, "TOOL_FIREWALL_SCOPE_DENIED")
    validate_tools([call.tool_id], list(record.allowed_tools))
    if call.parameters or call.purpose not in {
        "plan",
        "propose",
        "delegate",
        "analyze",
        "review",
        "synthesize",
        "findings",
        "supervise",
        "specialist",
        "synthesis",
    }:
        raise LLMError(403, "TOOL_FIREWALL_PARAMETERS_DENIED")
    if budget.calls >= budget.max_calls or budget.reserved_tokens >= budget.max_tokens:
        raise LLMError(429, "TOOL_FIREWALL_BUDGET_DENIED")


def validate_model_messages(messages):
    # No tools/functions or extra message attributes enter an LLM transport.
    if any(
        set(m) != {"role", "content"}
        or m["role"] not in {"system", "user", "assistant"}
        or not isinstance(m["content"], str)
        for m in messages
    ):
        raise LLMError(403, "MODEL_MESSAGE_FIREWALL_DENIED")


def validate_model_output(value):
    forbidden = {
        "tool_calls",
        "function_call",
        "points",
        "grade",
        "score",
        "shell_command",
        "policy_override",
    }
    stack, count = [value], 0
    while stack:
        item = stack.pop()
        count += 1
        if count > 20000:
            raise LLMError(502, "MODEL_OUTPUT_LIMIT")
        if isinstance(item, dict):
            if forbidden & set(item) or item.get("kind") == "SECURITY_INCIDENT":
                raise LLMError(502, "MODEL_OUTPUT_ACTION_DENIED")
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
