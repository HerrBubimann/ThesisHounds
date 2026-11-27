from app.assessments.schemas import AssessmentFinding, CriterionReview


def compare(human: CriterionReview, ai: AssessmentFinding) -> str:
    # Labels compare coarse judgments, not semantic agreement or truth of the rationale.
    if ai.evidence_status != "QUOTE_MATCHED" or "NOT_ASSESSABLE" in {human.judgment, ai.judgment}:
        return "INSUFFICIENT_EVIDENCE"
    if human.judgment == ai.judgment:
        return "AGREEMENT"
    if "MIXED" in {human.judgment, ai.judgment}:
        return "PARTIAL_AGREEMENT"
    return "DISAGREEMENT"
