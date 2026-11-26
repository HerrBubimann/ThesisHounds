from app.llm.errors import LLMError


def validate_tools(requested: list[str], policy_allowlist: list[str]) -> None:
    # This release has no shell, network, Python execution or arbitrary file tools.
    if not set(requested) <= (set(policy_allowlist) & {"document.read"}):
        raise LLMError(403, "Werkzeug ist nicht freigegeben.")
