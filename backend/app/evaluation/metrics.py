"""Mechanical metrics and explicit human adjudications; no LLM-as-truth matching."""

import hashlib
import json
import re
from itertools import combinations
from typing import Literal

from app.schemas.domain import StrictModel
from pydantic import ConfigDict, Field, StrictBool, model_validator


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


class RelianceTrial(StrictModel):
    """Explicit research data, never inferred from agreement or production telemetry."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    condition: Literal["A_EARLY_AI", "B_EVIDENCE", "C_HUMAN_FIRST", "D_DISCUSSION"]
    trial_id: str = Field(min_length=1, max_length=100)
    participant_code: str = Field(min_length=1, max_length=100)
    reference_id: str = Field(min_length=1, max_length=100)
    ai_correct: StrictBool
    adopted_ai: StrictBool
    initial_correct: StrictBool | None = None
    final_correct: StrictBool
    elapsed_seconds: float = Field(ge=0, allow_inf_nan=False)
    usability: int | None = Field(default=None, ge=1, le=7)
    perceived_control: int | None = Field(default=None, ge=1, le=7)
    traceability: int | None = Field(default=None, ge=1, le=7)
    professional_acceptance: int | None = Field(default=None, ge=1, le=7)


def reliance_metrics(trials, *, approved_protocol, dataset_kind, validated_reference_ids):
    """Offline descriptive summaries only; no experimental disclosure API is installed."""
    if (
        not isinstance(approved_protocol, str)
        or not approved_protocol.strip()
        or dataset_kind not in {"SYNTHETIC", "APPROVED_RESEARCH_TEST_DATA"}
        or not validated_reference_ids
    ):
        raise ValueError("APPROVED_PROTOCOL_AND_HUMAN_REFERENCES_REQUIRED")
    rows = [RelianceTrial.model_validate(t) for t in trials]
    if len({r.trial_id for r in rows}) != len(rows):
        raise ValueError("DUPLICATE_TRIAL")
    if any(r.reference_id not in validated_reference_ids for r in rows):
        raise ValueError("HUMAN_VALIDATED_REFERENCE_REQUIRED")
    result = {}
    for condition in sorted({r.condition for r in rows}):
        group = [r for r in rows if r.condition == condition]
        correct = [r for r in group if r.ai_correct]
        incorrect = [r for r in group if not r.ai_correct]
        paired = [r for r in group if r.initial_correct is not None]
        result[condition] = {
            "n": len(group),
            "correct_ai_adoption": sum(r.adopted_ai for r in correct) / len(correct)
            if correct
            else None,
            "incorrect_ai_adoption": sum(r.adopted_ai for r in incorrect) / len(incorrect)
            if incorrect
            else None,
            "unsupported_criticism_rejection": sum(not r.adopted_ai for r in incorrect)
            / len(incorrect)
            if incorrect
            else None,
            "final_reference_accuracy": sum(r.final_correct for r in group) / len(group),
            "paired_initial_final_outcome_changes": sum(
                r.initial_correct != r.final_correct for r in paired
            ),
            "paired_n": len(paired),
            "mean_elapsed_seconds": sum(r.elapsed_seconds for r in group) / len(group),
            "subjective_ratings": {
                field: [getattr(r, field) for r in group if getattr(r, field) is not None]
                for field in (
                    "usability",
                    "perceived_control",
                    "traceability",
                    "professional_acceptance",
                )
            },
        }
    return {
        "conditions": result,
        "protocol": approved_protocol,
        "empirical_effectiveness_established": False,
        "interpretation": "DESCRIPTIVE_ONLY_NO_CAUSAL_OR_INDIVIDUAL_BIAS_DIAGNOSIS",
    }


def feedback_codes(action, reason):
    outcome = {
        "ACCEPT": "ACCEPTED",
        "REJECT": "REJECTED",
        "CORRECT": "CORRECTED",
        "SUPPLEMENT": "SUPPLEMENTED",
        "NOT_RELEVANT": "REJECTED",
        "INSUFFICIENT_EVIDENCE": "INSUFFICIENT_EVIDENCE",
        "MANUAL_REVIEW_REQUIRED": "MANUAL_REVIEW_REQUIRED",
    }[action]
    error = {
        "WRONG_STATEMENT": "FACTUAL_ERROR",
        "WRONG_CRITERION": "INCORRECT_CRITERION",
        "DUPLICATE": "DUPLICATE_FINDING",
    }.get(reason, reason)
    return {"outcome": outcome, "error_category": error}


def feedback_metrics(entries, findings):
    """Latest local human feedback per finding; version counts are reported separately.

    No cross-assessment export, model reconfiguration, gold-label promotion or training.
    """
    from collections import Counter

    catalog = {f.finding_id: f for primary in findings for f in [primary, *primary.supplemental]}
    latest = {e["finding_id"]: e for e in entries}
    groups = {}
    for key, e in latest.items():
        if key not in catalog:
            raise ValueError("Feedback refers to an unknown finding")
        f = catalog[key]
        codes = feedback_codes(e["action"], e["reason"])
        group = (f.model_id, f.agent_id, f.criterion_id, codes["error_category"])
        groups.setdefault(group, Counter())[codes["outcome"]] += 1
    return {
        "groups": [
            {
                "model_id": model,
                "agent_id": agent,
                "criterion_id": criterion,
                "error_category": error,
                "outcomes": dict(counts),
                "findings": sum(counts.values()),
            }
            for (model, agent, criterion, error), counts in groups.items()
        ],
        "feedback_versions": len(entries),
        "adjudicated_findings": len(latest),
        "pending_findings": len(set(catalog) - latest.keys()),
        "classification": "RESTRICTED",
        "origin": "HUMAN_CONFIRMED",
        "scope": "CURRENT_ASSESSMENT_ONLY",
        "automatic_training": False,
        "automatic_model_routing_changes": False,
        "quality_benefit": "NOT_ESTABLISHED_BY_FEEDBACK_COUNTS",
    }


def fingerprint(finding) -> str:
    value = finding.model_dump() if hasattr(finding, "model_dump") else finding
    return digest(
        {
            k: re.sub(r"\s+", " ", value[k]).strip() if isinstance(value[k], str) else value[k]
            for k in (
                "criterion_id",
                "judgment",
                "kind",
                "description",
                "page",
                "quote",
                "scientific_claims",
                "relationships",
                "supporting_passages",
            )
            if k in value
        }
    )


class Adjudication(StrictModel):
    prediction_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    correct: bool
    matched_reference_ids: list[str] = Field(default_factory=list)
    hallucinated: bool
    source_correct: bool | None = None
    claim_correct: bool | None = None
    methodological_weakness_correct: bool | None = None
    propagated_error: bool | None = None
    reviewer_accepted: bool | None = None


class SpecialistAdjudication(StrictModel):
    proposal_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    relevant: bool
    matched_specialist_ids: list[str] = Field(default_factory=list, max_length=20)


class HumanReferenceSet(StrictModel):
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    profile_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    adjudicated_by: list[str] = Field(min_length=1, max_length=10)
    reference_ids: list[str]
    adjudications: list[Adjudication]
    review_tool_adjudications: dict[str, StrictBool] = Field(default_factory=dict, max_length=2000)
    required_specialist_ids: list[str] | None = None
    specialist_adjudications: list[SpecialistAdjudication] = Field(
        default_factory=list, max_length=100
    )

    @model_validator(mode="after")
    def unambiguous(self):
        keys = [a.proposal_sha256 for a in self.specialist_adjudications]
        if len(keys) != len(set(keys)) or (
            self.required_specialist_ids is not None
            and len(set(self.required_specialist_ids)) != len(self.required_specialist_ids)
        ):
            raise ValueError("Duplicate specialist reference/adjudication")
        if any(
            not set(a.matched_specialist_ids) <= set(self.required_specialist_ids or [])
            or (a.matched_specialist_ids and not a.relevant)
            for a in self.specialist_adjudications
        ):
            raise ValueError("Invalid specialist adjudication")
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


def review_tool_metrics(document, profile, findings, reference=None):
    """No expert scores from keyword checks or duplicate counts; explicit labels only."""
    from app.assessments.comparison import finding_groups, reviewer_questions
    from app.assessments.routine_checks import numerical_consistency
    from app.assessments.scientific_consistency import (
        applied_method_candidates,
        reproducibility_report,
    )

    groups = finding_groups(document, findings)
    numerical = numerical_consistency(document)
    reproduction = reproducibility_report(
        document, profile, applied_method_candidates(document, profile, findings)
    )
    questions = reviewer_questions(document, profile, findings, reproduction, numerical)
    flat = [f for primary in findings for f in [primary, *primary.supplemental]]
    catalog = {f.finding_id: fingerprint(f) for f in flat}
    predictions = {
        "deduplication": [],
        "numerical": [],
        "reproducibility": [],
        "questions": [],
        "positive_evidence": [],
        "negative_evidence": [],
    }
    for group in groups["groups"]:
        if len(group["finding_ids"]) > 1:
            predictions["deduplication"].append(
                "dedup-" + digest(sorted(catalog[key] for key in group["finding_ids"]))
            )
    for row in numerical["arithmetic"]:
        if row["status"] == "ARITHMETIC_MISMATCH_CANDIDATE":
            predictions["numerical"].append(
                "numeric-" + digest([row["page"], row["quote"], row["calculated_percent"]])
            )
    for row in numerical["comparisons"]:
        if row["status"] == "NUMERIC_CONFLICT_CANDIDATE":
            predictions["numerical"].append(
                "numeric-" + digest([row["first_id"], row["second_id"]])
            )
    for method in reproduction["methods"]:
        for check in method["checks"]:
            if check["status"] == "NOT_LOCATED_IN_METHOD_CONTEXT":
                predictions["reproducibility"].append(
                    "repro-"
                    + digest(
                        [
                            method["criterion_id"],
                            method["family"],
                            check["aspect"],
                            method["evidence"],
                        ]
                    )
                )
    for q in questions:
        predictions["questions"].append(
            "question-" + digest([q["criterion_id"], q["reason"], q["text"], q["passages"]])
        )
    for f in flat:
        if f.kind in {"STRENGTH", "WEAKNESS", "METHOD_CONCERN"}:
            key = "positive_evidence" if f.kind == "STRENGTH" else "negative_evidence"
            predictions[key].append("finding-" + fingerprint(f))
    result = {
        "findings_before": groups["findings_before"],
        "candidate_groups_after": groups["candidate_groups_after"],
        "redundancy_candidates": groups["redundancy_candidates"],
        "deleted_findings": 0,
        "prediction_ids": predictions,
        "quality": {key: None for key in predictions},
        "reference_status": "NO_EXPERT_REFERENCES",
        "human_time_saved_seconds": None,
        "reviewer_acceptance": None,
        "mechanical_reduction_is_quality_gain": False,
    }
    if reference is None:
        return result
    reference = HumanReferenceSet.model_validate(reference.model_dump())
    if (reference.dataset_sha256, reference.profile_sha256) != (
        digest(document.pages),
        digest(profile.model_dump()),
    ):
        return {**result, "reference_status": "REFERENCE_SCOPE_MISMATCH"}
    labels = reference.review_tool_adjudications
    complete = True
    for key, ids in predictions.items():
        if ids and set(ids) <= labels.keys():
            result["quality"][key] = sum(labels[item] for item in ids) / len(ids)
        elif ids:
            complete = False
    result["reference_status"] = (
        "EXPLICIT_EXPERT_ADJUDICATION" if complete and labels else "INCOMPLETE_EXPERT_ADJUDICATION"
    )
    return result


def planning_metrics(planning, reference):
    proposals = planning.get("proposals", [])
    execution = planning.get("execution", [])
    result = {
        "proposed_specialists": len(proposals),
        "created_specialists": len(execution),
        "completed_specialists": sum(e["status"] == "COMPLETED" for e in execution),
        "specialist_relevance": None,
        "unnecessary_specialists": None,
        "missing_necessary_specialists": None,
        "planning_reference_status": "NO_HUMAN_PLANNING_REFERENCES",
    }
    if reference is None or reference.required_specialist_ids is None:
        return result
    annotations = {a.proposal_sha256: a for a in reference.specialist_adjudications}
    if any(digest(p) not in annotations for p in proposals):
        return {**result, "planning_reference_status": "INCOMPLETE_HUMAN_PLANNING_ADJUDICATION"}
    values = [annotations[digest(p)] for p in proposals]
    matched = {key for a in values if a.relevant for key in a.matched_specialist_ids}
    return {
        **result,
        "planning_reference_status": "HUMAN_ADJUDICATED",
        "specialist_relevance": sum(a.relevant for a in values) / len(values) if values else None,
        "unnecessary_specialists": sum(not a.relevant for a in values),
        "missing_necessary_specialists": len(set(reference.required_specialist_ids) - matched),
    }


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
            "scientific_claim_correctness",
            "methodological_weakness_correctness",
            "error_propagation_rate",
            "reviewer_acceptance",
            "human_time_saved_seconds",
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

    def annotated_rate(field):
        labels = [getattr(a, field) for a in values if getattr(a, field) is not None]
        return sum(labels) / len(labels) if labels else None

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
        "scientific_claim_correctness": annotated_rate("claim_correct"),
        "methodological_weakness_correctness": annotated_rate("methodological_weakness_correct"),
        "error_propagation_rate": annotated_rate("propagated_error"),
        "reviewer_acceptance": annotated_rate("reviewer_accepted"),
        "human_time_saved_seconds": None,
        "annotation_counts": {
            field: sum(getattr(a, field) is not None for a in values)
            for field in (
                "claim_correct",
                "methodological_weakness_correct",
                "propagated_error",
                "reviewer_accepted",
            )
        },
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
            r.get("planning_variant") or "DEFAULT",
        )
        for r in rows
        if r["status"] == "COMPLETED"
    }
    for architecture, variation, ablation, dataset_hash, profile_hash, planning_variant in sorted(
        groups
    ):
        selected = [
            r
            for r in rows
            if (r["architecture"], r["variation"], r["status"])
            == (architecture, variation, "COMPLETED")
            and r.get("ablation", "baseline") == ablation
            and r.get("dataset_sha256", "UNKNOWN") == dataset_hash
            and r.get("profile_sha256", "UNKNOWN") == profile_hash
            and (r.get("planning_variant") or "DEFAULT") == planning_variant
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
                "planning_variant": planning_variant,
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
                and b.get("planning_variant") == row.get("planning_variant")
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
                and b.get("planning_variant") == row.get("planning_variant")
                and b.get("document_id") == row.get("document_id")
                and b["dataset_sha256"] == row["dataset_sha256"]
                and b["profile_sha256"] == row["profile_sha256"]
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
