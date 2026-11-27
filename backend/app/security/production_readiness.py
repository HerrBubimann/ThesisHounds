"""An environment switch is not a production authorization."""

from app.security.privacy_policy_engine import SecurityMode

BLOCKERS = (
    "UNIVERSITY_IDENTITY_INTEGRATION",
    "HOST_EGRESS_ACCEPTANCE",
    "TLS_SERVICE_IDENTITY",
    "ENCRYPTED_STORAGE_AND_BACKUPS",
    "PARSER_SANDBOX_ACCEPTANCE",
    "MODEL_ARTIFACT_APPROVAL",
    "RETENTION_AND_DELETION_ACCEPTANCE",
    "SPERRVERMERK_AUTHORIZATION",
    "LEGAL_BASIS_REVIEW",
    "EXAMINATION_RULES_REVIEW",
    "ORGANIZATIONAL_SIGNOFF",
)


def require_supported_mode(mode: SecurityMode) -> None:
    # This release has no validated production identity/parser/storage adapters.
    # Do not add an env-var bypass or treat a self-authored JSON checklist as evidence.
    if mode != SecurityMode.DEVELOPMENT:
        raise ValueError("PRODUCTION_NOT_READY: " + ", ".join(BLOCKERS))


def readiness_status() -> dict:
    return {"ready": False, "blockers": list(BLOCKERS), "real_documents_allowed": False}
