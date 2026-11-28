"""Explicit stages; uncertainty alone never triggers extra agents or proves quality."""


def plan_escalation(finding, *, complex_topic=False, resources_available=True):
    reasons = ["L1_LOCAL_STRUCTURE_AND_QUOTE_CHECK", "L2_CRITERION_SEMANTIC_REVIEW"]
    critical = (
        finding.kind in {"WEAKNESS", "SOURCE_ISSUE", "FORMAL_ISSUE"}
        or finding.judgment == "NEGATIVE"
    )
    deficient = finding.evidence_quality in {"INSUFFICIENT", "NOT_ASSESSABLE", "CONTRADICTORY"}
    unresolved_question = finding.kind == "OPEN_QUESTION" and finding.judgment == "MIXED"
    scientific_concern = any(c["issues"] for c in finding.claim_checks)
    verify = (
        critical
        or deficient
        or unresolved_question
        or finding.conflict
        or bool(finding.relationships)
        or scientific_concern
        or "SECURITY_CONTEXT_UNIFORM_POSITIVE_REQUIRES_HUMAN" in finding.open_questions
    )
    specialized = complex_topic and (
        critical or deficient or unresolved_question or finding.claim_type == "ABSENCE"
    )
    if verify:
        reasons.append("CRITICAL_OR_INADEQUATE_EVIDENCE_REQUIRES_INDEPENDENT_CHECK")
    if specialized:
        reasons.append("TOPIC_COMPLEXITY_AND_FINDING_NEED")
    if not resources_available:
        reasons.append("RESOURCE_LIMIT_REQUIRES_HUMAN_CLARIFICATION")
    human = (
        deficient
        or finding.claim_type == "ABSENCE"
        or finding.conflict
        or scientific_concern
        or (verify and not resources_available)
        or any("REQUIRES_HUMAN" in q for q in finding.open_questions)
    )
    return {
        "level": 4 if human else 3 if verify else 2,
        "reasons": reasons,
        "independent_verification_required": verify,
        "specialist_needed": specialized,
        "human_required": human,
        "resources_available": resources_available,
        "confidence_used_as_sole_trigger": False,
    }
