"""Local provenance snapshots. Configuration traceability is not exact reproducibility."""

import copy
import hashlib
import json
import os
import re

from app.schemas.domain import now


def content_digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


def snapshot(record, config):
    sha = os.getenv("THESISHOUNDS_GIT_SHA", "")
    return {
        "schema_version": "assessment-provenance.v1",
        "created_at": now().isoformat(),
        "analysis_id": record.id,
        "document_id": record.document.document_id,
        "document_version_sha256": content_digest(record.document.pages),
        "catalog_id": record.profile.id,
        "catalog_version": record.profile.version,
        "catalog_status": record.profile.status,
        "catalog_sha256": content_digest(record.profile.model_dump()),
        "dhbw_guideline_snapshot": copy.deepcopy(record.institutional_rules),
        "application_version": "0.2.0",
        "git_commit_sha": sha if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha) else None,
        "git_evidence": "OPERATOR_REPORTED_NOT_INDEPENDENTLY_VERIFIED"
        if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", sha)
        else "UNKNOWN",
        "working_tree_state": "UNKNOWN",
        "workflow_version": "adaptive-review.v2",
        "agent_configuration": config.agents.model_dump(),
        "execution_limits": config.limits.model_dump(),
        "exact_reproducibility": "NOT_GUARANTEED",
        "automatic_training": False,
        "retention": "SCOPED_IN_MEMORY_SAME_TTL_AS_ASSESSMENT_NO_RESTART_RECOVERY",
    }
