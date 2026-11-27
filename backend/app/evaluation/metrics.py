"""Mechanical metrics and explicit human adjudications; no LLM-as-truth matching."""

import hashlib
import json
import re
from itertools import combinations

from app.schemas.domain import StrictModel
from pydantic import Field, model_validator


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


def fingerprint(finding) -> str:
    value = finding.model_dump() if hasattr(finding, "model_dump") else finding
    return digest(
        {
            k: re.sub(r"\s+", " ", value[k]).strip() if isinstance(value[k], str) else value[k]
            for k in ("criterion_id", "judgment", "kind", "description", "page", "quote")
        }
    )


class Adjudication(StrictModel):
    prediction_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    correct: bool
    matched_reference_ids: list[str] = Field(default_factory=list)
    hallucinated: bool
    source_correct: bool | None = None


class HumanReferenceSet(StrictModel):
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    adjudicated_by: list[str] = Field(min_length=1, max_length=10)
    reference_ids: list[str]
    adjudications: list[Adjudication]

    @model_validator(mode="after")
    def unambiguous(self):
        ids = [a.prediction_fingerprint for a in self.adjudications]
        if len(ids) != len(set(ids)) or len(self.reference_ids) != len(set(self.reference_ids)):
            raise ValueError("Duplicate reference/adjudication")
        if any(
            not set(a.matched_reference_ids) <= set(self.reference_ids) for a in self.adjudications
        ):
            raise ValueError("Unknown reference target")
        if any(a.matched_reference_ids and not a.correct for a in self.adjudications):
            raise ValueError("An incorrect prediction cannot recover a reference finding")
        return self


def quality_metrics(
    findings, reference: HumanReferenceSet | None, dataset_hash, profile_hash
) -> dict:
    empty = dict.fromkeys(
        (
            "precision",
            "recall",
            "false_positive_criticism",
            "false_negatives",
            "hallucination_rate",
            "source_correctness",
        )
    )
    if reference is None:
        return {**empty, "reference_status": "NO_HUMAN_REFERENCES"}
    if (reference.dataset_sha256, reference.profile_sha256) != (dataset_hash, profile_hash):
        raise ValueError("Reference scope does not match this document and catalog")
    annotations = {a.prediction_fingerprint: a for a in reference.adjudications}
    if any(fingerprint(f) not in annotations for f in findings):
        return {**empty, "reference_status": "INCOMPLETE_HUMAN_ADJUDICATION"}
    values = [annotations[fingerprint(f)] for f in findings]
    recovered = set().union(*(set(a.matched_reference_ids) for a in values)) if values else set()
    sources = [a.source_correct for a in values if a.source_correct is not None]
    return {
        "precision": sum(a.correct for a in values) / len(values) if values else None,
        "recall": len(recovered) / len(reference.reference_ids)
        if reference.reference_ids
        else None,
        "false_positive_criticism": sum(
            not a.correct and f.kind in {"WEAKNESS", "FORMAL_ISSUE", "SOURCE_ISSUE"}
            for f, a in zip(findings, values, strict=True)
        ),
        "false_negatives": len(set(reference.reference_ids) - recovered),
        "hallucination_rate": sum(a.hallucinated for a in values) / len(values) if values else None,
        "source_correctness": sum(sources) / len(sources) if sources else None,
        "reference_status": "HUMAN_ADJUDICATED",
    }


def consistency(rows: list[dict]) -> list[dict]:
    results = []
    groups = {
        (
            r["architecture"],
            r["variation"],
            r.get("ablation", "baseline"),
            r.get("dataset_sha256", "UNKNOWN"),
            r.get("profile_sha256", "UNKNOWN"),
        )
        for r in rows
        if r["status"] == "COMPLETED"
    }
    for architecture, variation, ablation, dataset_hash, profile_hash in sorted(groups):
        selected = [
            r
            for r in rows
            if (r["architecture"], r["variation"], r["status"])
            == (architecture, variation, "COMPLETED")
            and r.get("ablation", "baseline") == ablation
            and r.get("dataset_sha256", "UNKNOWN") == dataset_hash
            and r.get("profile_sha256", "UNKNOWN") == profile_hash
        ]
        pairs = []
        for first, second in combinations(selected, 2):
            a, b = set(first["prediction_fingerprints"]), set(second["prediction_fingerprints"])
            judgments_a = {f["criterion_id"]: f["judgment"] for f in first["findings"]}
            judgments_b = {f["criterion_id"]: f["judgment"] for f in second["findings"]}
            keys = set(judgments_a) | set(judgments_b)
            pairs.append(
                {
                    "finding_jaccard": len(a & b) / len(a | b) if a | b else 1.0,
                    "judgment_agreement": sum(
                        judgments_a.get(k) == judgments_b.get(k) for k in keys
                    )
                    / len(keys)
                    if keys
                    else None,
                    "point_deviation": None,
                }
            )
        results.append(
            {
                "architecture": architecture,
                "dataset_sha256": dataset_hash,
                "profile_sha256": profile_hash,
                "variation": variation,
                "ablation": ablation,
                "comparisons": pairs,
                "status": "MEASURED" if pairs else "NEEDS_REPEATS",
            }
        )
    return results


def variation_comparisons(rows: list[dict]) -> list[dict]:
    comparisons = []
    for row in rows:
        if row["variation"] == "baseline" or row["status"] != "COMPLETED":
            continue
        baseline = next(
            (
                b
                for b in rows
                if b["architecture"] == row["architecture"]
                and b.get("document_id") == row.get("document_id")
                and b["variation"] == "baseline"
                and b["repeat"] == row["repeat"]
                and b["status"] == "COMPLETED"
                and b.get("ablation", "baseline") == row.get("ablation", "baseline")
            ),
            None,
        )
        if baseline is None:
            continue
        a, b = set(baseline["prediction_fingerprints"]), set(row["prediction_fingerprints"])
        first = {f["criterion_id"]: f["judgment"] for f in baseline["findings"]}
        second = {f["criterion_id"]: f["judgment"] for f in row["findings"]}
        keys = set(first) | set(second)
        comparisons.append(
            {
                "architecture": row["architecture"],
                "variation": row["variation"],
                "repeat": row["repeat"],
                "applied": row["variation_applied"],
                "finding_jaccard": len(a & b) / len(a | b) if a | b else 1.0,
                "judgment_agreement": sum(first.get(k) == second.get(k) for k in keys) / len(keys)
                if keys
                else None,
                "causal_bias_conclusion": "NOT_ESTABLISHED_BY_THIS_PILOT",
                "ablation": row.get("ablation", "baseline"),
                "outcome_change": outcome_change(baseline, row),
            }
        )
    return comparisons


def outcome_summary(row):
    from collections import Counter

    flat = [v for f in row["findings"] for v in [f, *f.get("supplemental", [])]]
    criticism = [f for f in flat if f["kind"] in {"WEAKNESS", "FORMAL_ISSUE", "SOURCE_ISSUE"}]
    return {
        "criticism_count": len(criticism),
        "kinds": dict(Counter(f["kind"] for f in flat)),
        "evidence_quality": dict(Counter(f.get("evidence_quality", "UNKNOWN") for f in flat)),
        "judgments": {f["criterion_id"]: f["judgment"] for f in row["findings"]},
        "optional_points": None,
    }


def outcome_change(first, second):
    a, b = outcome_summary(first), outcome_summary(second)
    return {
        "criticism_count_delta": b["criticism_count"] - a["criticism_count"],
        "kind_distribution_changed": a["kinds"] != b["kinds"],
        "evidence_quality_changed": a["evidence_quality"] != b["evidence_quality"],
        "judgment_consistent": a["judgments"] == b["judgments"],
        "point_deviation": None,
    }


def ablation_comparisons(rows):
    results = []
    for row in rows:
        if row.get("ablation", "baseline") == "baseline" or row["status"] != "COMPLETED":
            continue
        base = next(
            (
                b
                for b in rows
                if (
                    b["architecture"],
                    b["variation"],
                    b["repeat"],
                    b.get("ablation", "baseline"),
                    b["status"],
                )
                == (row["architecture"], row["variation"], row["repeat"], "baseline", "COMPLETED")
                and b.get("document_id") == row.get("document_id")
            ),
            None,
        )
        if not base:
            continue
        results.append(
            {
                "architecture": row["architecture"],
                "variation": row["variation"],
                "repeat": row["repeat"],
                "removed_component": row["ablation"],
                "same_document_and_catalog": (base["dataset_sha256"], base["profile_sha256"])
                == (row["dataset_sha256"], row["profile_sha256"]),
                "changed_flags": [
                    key
                    for key in base["component_flags"]
                    if base["component_flags"][key] != row["component_flags"][key]
                ],
                "model_call_delta": row["model_calls"] - base["model_calls"],
                "outcome_change": outcome_change(base, row),
                "causal_quality_benefit": "NOT_ESTABLISHED_WITHOUT_HUMAN_REFERENCES",
            }
        )
    return results
