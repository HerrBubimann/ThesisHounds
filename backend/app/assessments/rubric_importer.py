"""Import structured candidates. File extraction and official promotion remain human tasks."""

import hashlib
import json

import yaml
from app.assessments.profile_registry import AssessmentProfile


def import_candidate(text: str, format: str) -> AssessmentProfile:
    if len(text.encode()) > 65536 or format not in {"json", "yaml"}:
        raise ValueError("Use a bounded structured JSON/YAML rubric")
    data = json.loads(text) if format == "json" else yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Expected a rubric object")
    # Validate without trusting any approval embedded in an imported document.
    data.update(status="CANDIDATE", approved_by="", approved_at="")
    profile = AssessmentProfile.model_validate(data)
    digest = hashlib.sha256(text.encode()).hexdigest()
    profile.source = f"import-sha256:{digest}"
    # Per-criterion source locations remain as supplied for a human to check.
    return profile
