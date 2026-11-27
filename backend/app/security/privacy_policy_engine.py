"""Single decision vocabulary for model, document, tool and release boundaries."""

from dataclasses import dataclass
from enum import StrEnum

from app.security.classification import Classification, classify


class SecurityMode(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    UNIVERSITY_SECURE = "UNIVERSITY_SECURE"
    PUBLIC_RESEARCH = "PUBLIC_RESEARCH"
    EXPERIMENTAL_PUBLIC = "EXPERIMENTAL_PUBLIC"
    MODEL_PROVISIONING = "MODEL_PROVISIONING"


class Decision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_AUTHORIZED_APPROVAL = "REQUIRE_AUTHORIZED_APPROVAL"


@dataclass(frozen=True)
class ProcessingContext:
    classification: object = None
    mode: SecurityMode = SecurityMode.DEVELOPMENT
    authorized: bool = False
    local_boundary_verified: bool = False
    target_approved: bool = False
    production_ready: bool = False
    external: bool = True
    action: str = "inference"


class PrivacyPolicyEngine:
    def decide(self, context: ProcessingContext) -> Decision:
        level = classify(context.classification)
        if not context.authorized:
            return Decision.DENY
        # Ordinary approval can never override this rule, including summaries/embeddings.
        if context.external or not context.local_boundary_verified:
            return Decision.DENY
        if context.action not in {"inference", "read", "process", "review", "delete"}:
            return Decision.DENY
        if context.mode not in {SecurityMode.DEVELOPMENT, SecurityMode.UNIVERSITY_SECURE}:
            return Decision.DENY  # Separate isolated executables are not released.
        if level != Classification.PUBLIC:
            if context.mode != SecurityMode.UNIVERSITY_SECURE:
                return Decision.DENY
            if not context.production_ready or not context.target_approved:
                return Decision.REQUIRE_AUTHORIZED_APPROVAL
        if not context.target_approved:
            return Decision.DENY
        return Decision.ALLOW
