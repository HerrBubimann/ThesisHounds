from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.llm.errors import LLMError
from app.llm.model_registry import ModelDefinition
from app.security.classification import Classification, classify
from app.security.privacy_policy_engine import (
    Decision,
    PrivacyPolicyEngine,
    ProcessingContext,
    SecurityMode,
)


class PolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mode: Literal["LOCAL_ONLY", "EXPERIMENTAL"] = "LOCAL_ONLY"
    experimental_enabled: bool = False
    allowed_providers: list[str] = Field(default_factory=lambda: ["ollama"])
    allowed_tools: list[str] = Field(default_factory=lambda: ["document.read"])


class PolicyEngine:
    def __init__(self, config: PolicyConfig) -> None:
        self.config = config
        self.engine = PrivacyPolicyEngine()
        self.pilot_endpoint: str | None = None
        self.pilot_models: frozenset[str] = frozenset()
        # EXPERIMENTAL needs an isolated runner without access to this document store.
        if config.mode != "LOCAL_ONLY" or config.experimental_enabled:
            raise ValueError("EXPERIMENTAL requires a separate isolated runner; not enabled here")

    def check(self, model: ModelDefinition, classification: str | None, role: str) -> None:
        level = classify(classification)
        approved = (
            model.local
            and model.provider == "ollama"
            and model.deployment_type == "LOCAL"
            and (
                model.approved_endpoint == "http://ollama:11434"
                or (
                    model.id in self.pilot_models
                    and model.approved_endpoint.rstrip("/") == self.pilot_endpoint
                )
            )
            and model.data_processing_location == "PRIVATE_PROCESSING_ZONE"
            and model.network_access == "APPROVED_INFERENCE_ONLY"
            and not model.telemetry_enabled
            and not model.cloud_features_enabled
            and model.approval_status in {"DEVELOPMENT_ONLY", "APPROVED"}
            and model.security_review_status in {"DEVELOPMENT_ONLY", "APPROVED"}
            and level in model.allowed_classifications
            and (
                model.approval_status != "APPROVED"
                or (
                    model.version
                    and model.expected_digest
                    and model.weights_origin
                    and model.license_status == "APPROVED"
                    and model.security_review_status == "APPROVED"
                )
            )
        )
        context = ProcessingContext(
            classification=level,
            mode=SecurityMode.DEVELOPMENT,
            authorized=model.enabled and role in model.allowed_roles,
            local_boundary_verified=approved,
            target_approved=approved,
            external=not model.local or model.provider != "ollama",
        )
        if (
            model.provider not in self.config.allowed_providers
            or level != Classification.PUBLIC
            or self.engine.decide(context) != Decision.ALLOW
        ):
            raise LLMError(403, "Verarbeitung durch die Datenschutzrichtlinie gesperrt.")
