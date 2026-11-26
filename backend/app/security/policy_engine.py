from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.llm.errors import LLMError
from app.llm.model_registry import ModelDefinition

Classification = Literal["SYNTHETIC", "PUBLIC", "CONFIDENTIAL"]


class PolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["LOCAL_ONLY", "EXPERIMENTAL"] = "LOCAL_ONLY"
    experimental_enabled: bool = False
    allowed_providers: list[str] = ["ollama"]
    allowed_tools: list[str] = ["document.read"]


class PolicyEngine:
    def __init__(self, config: PolicyConfig) -> None:
        self.config = config
        # EXPERIMENTAL needs an isolated runner without access to this document store.
        if config.mode != "LOCAL_ONLY" or config.experimental_enabled:
            raise ValueError("EXPERIMENTAL requires a separate isolated runner; not enabled here")

    def check(self, model: ModelDefinition, classification: str | None, role: str) -> None:
        classification = (
            classification if classification in {"SYNTHETIC", "PUBLIC"} else "CONFIDENTIAL"
        )
        if not model.local or model.provider != "ollama":
            raise LLMError(403, "Externe Provider sind in dieser Umgebung deaktiviert.")
        if model.provider not in self.config.allowed_providers:
            raise LLMError(403, "Provider ist durch die Datenschutzrichtlinie gesperrt.")
        if role not in model.allowed_roles or not model.enabled:
            raise LLMError(403, "Agentenrolle ist für dieses Modell nicht freigegeben.")
        if classification == "CONFIDENTIAL" and model.privacy != "CONFIDENTIAL":
            raise LLMError(403, "Modell ist nicht für vertrauliche Daten freigegeben.")
