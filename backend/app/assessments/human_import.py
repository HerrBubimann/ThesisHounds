"""Human review import adapter over the existing bounded, offline candidate extractor."""

import base64
import binascii
import json

from app.assessments.schemas import CriterionReview
from app.knowledge.importer import ImportRejected, extract_candidate, safe_yaml
from pydantic import ValidationError


def extract_review(payload, profile):
    try:
        data = base64.b64decode(payload.content_base64, validate=True)
    except (ValueError, binascii.Error):
        raise ImportRejected("INVALID_REVIEW_ENCODING") from None
    result = extract_candidate(data, "." + payload.format)
    text = result["text"]
    if len(text) > 100_000:
        raise ImportRejected("REVIEW_TEXT_LIMIT")
    mapped, unknown, ambiguous = [], [], []
    expected = {c.id for c in profile.criteria}
    if payload.format in {"json", "yaml"}:
        value = json.loads(text) if payload.format == "json" else safe_yaml(text)
        rows = value.get("criteria", []) if isinstance(value, dict) else []
        if not isinstance(rows, list) or len(rows) > 50:
            raise ImportRejected("REVIEW_ROWS_DENIED")
        for row in rows:
            if not isinstance(row, dict) or row.get("criterion_id") not in expected:
                unknown.append(row)
                continue
            mapped.append({"criterion_id": row["criterion_id"], "extracted": row})
    else:
        # Exact explicit headers only. Never infer a judgment or invent missing text.
        current, parts = None, []

        def flush():
            if parts:
                entry = {"criterion_id": current, "original_text": "\n".join(parts)}
                (mapped if current else unknown).append(entry)

        for line in text.splitlines():
            header = line.strip().rstrip(":").casefold()
            matches = [
                c.id
                for c in profile.criteria
                if header in {c.id.casefold(), c.description.casefold()}
            ]
            if matches:
                flush()
                parts = []
                current = matches[0] if len(matches) == 1 else None
                if len(matches) > 1:
                    ambiguous.append({"text": line, "candidates": matches})
            elif line.strip():
                parts.append(line)
        flush()
    seen = set()
    valid = set()
    for row in mapped:
        key = row["criterion_id"]
        if key in seen:
            ambiguous.append({"criterion_id": key, "reason": "DUPLICATE_MAPPING"})
        seen.add(key)
        try:
            row["form_values"] = CriterionReview.model_validate(
                row.get("extracted", {})
            ).model_dump()
            valid.add(key)
        except ValidationError:
            row["requires_manual_completion"] = True
    return {
        "source_sha256": result["sha256"],
        "original_text": text,
        "mapped": mapped,
        "unrecognized": unknown,
        "ambiguous": ambiguous,
        "missing_required": [c.id for c in profile.criteria if c.required and c.id not in valid],
        "warnings": result["warnings"],
        "status": "PREVIEW_REQUIRES_HUMAN_CONFIRMATION",
        "model_used": False,
        "classification": "RESTRICTED",
    }
