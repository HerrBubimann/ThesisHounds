"""Criterion coverage is structural, never evidence of academic correctness."""

from collections import Counter
from dataclasses import dataclass

from app.assessments.profile_registry import AssessmentProfile
from app.assessments.schemas import AssessmentFinding
from app.llm.errors import LLMError


@dataclass(frozen=True)
class CoverageReport:
    complete: bool
    required: tuple[str, ...]
    missing: tuple[str, ...]
    duplicates: tuple[str, ...]
    unexpected: tuple[str, ...]
    not_assessable: tuple[str, ...]


def check_coverage(profile: AssessmentProfile, findings: list[AssessmentFinding]) -> CoverageReport:
    counts = Counter(f.criterion_id for f in findings)
    catalog = {c.id for c in profile.criteria}
    required = {c.id for c in profile.criteria if c.required}
    missing = required - counts.keys()
    duplicates = {key for key, count in counts.items() if count > 1}
    unexpected = counts.keys() - catalog
    return CoverageReport(
        not (missing or duplicates or unexpected),
        tuple(sorted(required)),
        tuple(sorted(missing)),
        tuple(sorted(duplicates)),
        tuple(sorted(unexpected)),
        tuple(sorted(f.criterion_id for f in findings if f.judgment == "NOT_ASSESSABLE")),
    )


def criterion_states(profile, findings, execution_state):
    """Outcome states, for released views only; never infer success from missing output."""
    values = {f.criterion_id: f for f in findings}
    return {
        c.id: ("NOT_ASSESSABLE" if values[c.id].judgment == "NOT_ASSESSABLE" else "REVIEWED")
        if c.id in values
        else (
            "FAILED"
            if execution_state in {"FAILED", "CANCELLED"}
            or (execution_state == "COMPLETED" and c.required)
            else "OPTIONAL_NOT_REVIEWED"
            if execution_state == "COMPLETED"
            else "PENDING"
        )
        for c in profile.criteria
    }


def assessment_coverage(record, citation_report):
    """Deterministic accounting of executed criteria and selected original character spans.

    Input selection is measurable; scientific understanding and extraction completeness are not.
    The report is released through the existing review embargo only.
    """
    profile, document, findings = record.profile, record.document, record.ai
    if (citation_report["analysis_id"], citation_report["document_id"]) != (
        document.analysis_id,
        document.document_id,
    ):
        raise LLMError(403, "COVERAGE_CITATION_SCOPE_DENIED")
    flat = [f for primary in findings for f in [primary, *primary.supplemental]]
    structural = check_coverage(profile, findings)
    states = criterion_states(profile, findings, record.ai_state)
    selected = {p: [] for p in document.pages}
    for f in flat:
        if f.assessment_id != document.analysis_id:
            raise LLMError(403, "COVERAGE_SCOPE_DENIED")
        traces = [f.context_trace, *(r.get("context_trace", {}) for r in f.verification_rounds)]
        for trace in traces:
            if trace and (trace.get("analysis_id"), trace.get("document_id")) != (
                document.analysis_id,
                document.document_id,
            ):
                raise LLMError(403, "COVERAGE_TRACE_SCOPE_DENIED")
            for span in trace.get("selection", []):
                page, start, end = span["page"], span["start"], span["end"]
                if page in selected and 0 <= start < end <= len(document.pages[page]):
                    selected[page].append((start, end))
    gaps, covered = [], 0
    for page, text in sorted(document.pages.items()):
        cursor = 0
        for start, end in sorted(selected[page]):
            if start > cursor:
                gaps.append({"page": page, "start": cursor, "end": start})
            covered += max(0, end - max(cursor, start))
            cursor = max(cursor, end)
        if cursor < len(text):
            gaps.append({"page": page, "start": cursor, "end": len(text)})
    total = sum(len(t) for t in document.pages.values())
    required = [c.id for c in profile.criteria if c.required]
    optional = [c.id for c in profile.criteria if not c.required]
    reviewed = {f.criterion_id for f in findings if f.judgment != "NOT_ASSESSABLE"}
    failed = [
        {"criterion_id": k, "component": "MANDATORY"} for k, v in states.items() if v == "FAILED"
    ]
    limitations = []
    for f in flat:
        for question in f.open_questions:
            if "FAILED" in question or "PLANNING" in question:
                failed.append({"criterion_id": f.criterion_id, "component": question})
        for r in f.verification_rounds:
            if "error_code" in r:
                failed.append(
                    {
                        "criterion_id": f.criterion_id,
                        "component": "VERIFICATION",
                        "error_code": r["error_code"],
                    }
                )
                if r["error_code"] in {422, 429, 504}:
                    limitations.append(
                        {"criterion_id": f.criterion_id, "error_code": r["error_code"]}
                    )
        if f.context_trace.get("empty"):
            limitations.append({"criterion_id": f.criterion_id, "reason": "NO_CONTEXT"})
        if f.escalation.get("resources_available") is False:
            limitations.append({"criterion_id": f.criterion_id, "reason": "RESOURCE_LIMIT"})
    unverified = [
        r["entry"]["id"]
        for r in citation_report["references"]
        if not any(s.startswith("VERIFIED_") for s in r["statuses"])
    ]
    latest = {d["criterion_id"]: d for d in record.decisions}
    feedback = {e["finding_id"]: e for e in record.finding_feedback}
    human = [c.id for c in profile.criteria if c.id not in latest]
    blocked_feedback = [
        key
        for key, e in feedback.items()
        if e["action"] in {"INSUFFICIENT_EVIDENCE", "MANUAL_REVIEW_REQUIRED"}
    ]
    complete = (
        record.ai_state == "COMPLETED"
        and structural.complete
        and not structural.not_assessable
        and set(required + optional) <= reviewed
        and not gaps
        and document.complete
        and not failed
        and not limitations
        and not unverified
        and not human
        and not blocked_feedback
        and not document.extraction_warnings
    )
    return {
        **structural.__dict__,
        "analysis_complete": bool(complete),
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "required_reviewed": sorted(set(required) & reviewed),
        "optional_reviewed": sorted(set(optional) & reviewed),
        "criterion_states": states,
        "required_review_ratio": len(set(required) & reviewed) / len(required)
        if required
        else None,
        "optional_review_ratio": len(set(optional) & reviewed) / len(optional)
        if optional
        else None,
        "selected_original_characters": covered,
        "total_original_characters": total,
        "context_selection_ratio": covered / total if total else None,
        "context_metric_scope": "SELECTED_INPUT_SPANS_NOT_SCIENTIFIC_COMPLETENESS",
        "unprocessed_regions": gaps,
        "extraction_complete": document.complete,
        "extraction_warnings": list(document.extraction_warnings),
        "failed_subanalyses": failed,
        "unverifiable_sources": unverified,
        "resource_limitations": limitations,
        "open_human_decisions": human,
        "open_finding_decisions": blocked_feedback,
        "origin": "DETERMINISTIC_CHECK",
        "classification": record.classification,
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
    }
