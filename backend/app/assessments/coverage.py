"""Criterion coverage is structural, never evidence of academic correctness."""

from collections import Counter
from dataclasses import dataclass

from app.assessments.profile_registry import AssessmentProfile
from app.assessments.schemas import AssessmentFinding


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
