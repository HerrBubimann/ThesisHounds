import re

from app.assessments.provenance import content_digest
from app.assessments.schemas import AssessmentFinding, CriterionReview
from app.services.context_management import embed

PERSPECTIVE_FIELDS = {
    "strengths",
    "weaknesses",
    "claim_type",
    "required_context",
    "uncertainty",
    "scientific_claims",
    "relationships",
    "supporting_passages",
    "supporting_evidence",
    "contradicting_evidence",
    "sources",
    "verification_status",
    "open_questions",
    "unverifiable_aspects",
    "claim_checks",
    "relationship_checks",
    "debate_summary",
    "evidence_quality",
    "verification_rounds",
}


def compare(human: CriterionReview, ai: AssessmentFinding) -> str:
    # Labels compare coarse judgments, not semantic agreement or truth of the rationale.
    if ai.abstention or human.assessability == "NOT_APPLICABLE":
        return "NOT_ASSESSABLE"
    if ai.evidence_status != "QUOTE_MATCHED" or "NOT_ASSESSABLE" in {human.judgment, ai.judgment}:
        return "INSUFFICIENT_EVIDENCE"
    if human.judgment == ai.judgment:
        return "AGREEMENT"
    if "MIXED" in {human.judgment, ai.judgment}:
        return "PARTIAL_AGREEMENT"
    return "DISAGREEMENT"


def _signature(finding):
    return content_digest(
        finding.model_dump(
            include=PERSPECTIVE_FIELDS
            | {
                "criterion_id",
                "judgment",
                "kind",
                "description",
                "rationale",
                "page",
                "quote",
                "scientific_claims",
                "relationships",
                "supporting_passages",
                "contradicting_evidence",
            }
        )
    )


def finding_groups(document, findings):
    """Conservative same-scope candidates. No finding, perspective or contradiction is deleted."""
    flat = [f for primary in findings for f in [primary, *primary.supplemental]]
    if len(flat) > 100:
        raise ValueError("FINDING_GROUP_LIMIT")
    if any(f.assessment_id != document.analysis_id for f in flat):
        raise ValueError("FINDING_GROUP_SCOPE_DENIED")

    def similar(first, second):
        if (first.criterion_id, first.kind, first.judgment) != (
            second.criterion_id,
            second.kind,
            second.judgment,
        ):
            return False
        if (
            first.conflict
            or second.conflict
            or first.contradicting_evidence != second.contradicting_evidence
        ):
            return False
        if first.evidence_status != "QUOTE_MATCHED" or second.evidence_status != "QUOTE_MATCHED":
            return False
        text = document.pages.get(first.page, "")
        if (
            first.page != second.page
            or not first.quote
            or not second.quote
            or text.count(first.quote) != 1
            or text.count(second.quote) != 1
        ):
            return False
        a, b = text.index(first.quote), text.index(second.quote)
        overlap = max(0, min(a + len(first.quote), b + len(second.quote)) - max(a, b))
        if overlap / min(len(first.quote), len(second.quote)) < 0.8:
            return False

        # Shared category labels do not imply equal claims, relations or evidence.
        if first.model_dump(include=PERSPECTIVE_FIELDS) != second.model_dump(
            include=PERSPECTIVE_FIELDS
        ):
            return False
        if _signature(first) == _signature(second):
            return True
        a = (first.description + " " + first.rationale).casefold()
        b = (second.description + " " + second.rationale).casefold()
        for pattern in (
            r"\b(?:nicht|kein\w*|ohne|nie|not|no|without|never)\b",
            r"\b\d+(?:[.,]\d+)?\b",
        ):
            if set(re.findall(pattern, a)) != set(re.findall(pattern, b)):
                return False
        tokens_a, tokens_b = set(re.findall(r"\w+", a)), set(re.findall(r"\w+", b))
        lexical = len(tokens_a & tokens_b) / max(1, len(tokens_a | tokens_b))
        cosine = sum(x * y for x, y in zip(embed(a), embed(b), strict=True))
        return lexical >= 0.8 and cosine >= 0.9

    grouped = []
    for finding in flat:
        for group in grouped:
            # Complete linkage prevents A~B~C chaining from swallowing distinct perspectives.
            if all(similar(finding, member) for member in group):
                group.append(finding)
                break
        else:
            grouped.append([finding])
    return {
        "method": "LOCAL_FEATURE_HASH_AND_EVIDENCE_OVERLAP.v2",
        "groups": [
            {
                "id": "group-" + content_digest(sorted(f.finding_id for f in group))[:20],
                "finding_ids": [f.finding_id for f in group],
                "criterion_id": group[0].criterion_id,
                "exact_duplicates": len(group) > 1 and len({_signature(f) for f in group}) == 1,
                "human_review_required": True,
            }
            for group in grouped
        ],
        "findings_before": len(flat),
        "candidate_groups_after": len(grouped),
        "redundancy_candidates": len(flat) - len(grouped),
        "deleted_findings": 0,
        "semantic_equivalence_verified": False,
        "automatic_grade_effect": False,
    }


def reviewer_questions(document, profile, findings, reproducibility, numerical):
    """Bounded deterministic question drafts anchored in existing criteria and evidence."""
    questions = []

    def add(criterion, reason, text, ids=(), passages=()):
        key = content_digest(
            [content_digest(document.pages), criterion, reason, list(ids), list(passages)]
        )[:24]
        if not any(row["id"] == "question-" + key for row in questions):
            questions.append(
                {
                    "id": "question-" + key,
                    "criterion_id": criterion,
                    "reason": reason,
                    "text": text,
                    "finding_ids": list(ids),
                    "passages": list(passages),
                    "origin": "LOCAL_QUESTION_DRAFT",
                    "automatic_exam": False,
                    "human_review_required": True,
                }
            )

    flat = [f for p in findings for f in [p, *p.supplemental]]
    for f in flat:
        passages = (
            [{"page": f.page, "quote": f.quote}]
            if f.quote and f.quote in document.pages.get(f.page, "")
            else []
        )
        if f.conflict:
            add(
                f.criterion_id,
                "CONFLICT",
                "Wie lassen sich unterstützende und widersprechende Evidenz "
                "dieses Befunds vereinbaren?",
                [f.finding_id],
                passages,
            )
        if f.evidence_status != "QUOTE_MATCHED" or f.judgment == "NOT_ASSESSABLE":
            add(
                f.criterion_id,
                "INSUFFICIENT_EVIDENCE",
                "Welche Originalstelle oder zusätzliche Information erlaubt "
                "eine belastbare Einordnung dieses Befunds?",
                [f.finding_id],
                passages,
            )
        elif f.kind in {"OPEN_QUESTION", "METHOD_CONCERN", "UNVERIFIABLE"}:
            add(
                f.criterion_id,
                "METHOD_UNCERTAINTY",
                "Welche fachliche Begründung und welche Evidenz erläutern "
                "die hier angesprochene wissenschaftliche Entscheidung?",
                [f.finding_id],
                passages,
            )
    for method in reproducibility.get("methods", []):
        missing = [
            c["label"]
            for c in method["checks"]
            if c["status"]
            in {"NOT_LOCATED_IN_METHOD_CONTEXT", "DOCUMENTATION_UNCERTAINTY_REQUIRES_HUMAN"}
        ]
        if missing:
            add(
                method["criterion_id"],
                "REPRODUCIBILITY_CONTEXT",
                "Wo sind für diese angewandte Methode folgende Angaben dokumentiert "
                "oder als nicht anwendbar begründet: " + ", ".join(missing) + "?",
                passages=method["evidence"],
            )
    for criterion in profile.criteria:
        if not any(f.criterion_id == criterion.id for f in flat):
            add(
                criterion.id,
                "OPEN_CRITERION",
                "Welche dokumentierte Evidenz ermöglicht die Bearbeitung "
                "dieses offenen Bewertungskriteriums?",
            )
    # Numerical claims are not silently assigned to a content rubric when none exists.
    criteria = [c.id for c in profile.criteria if c.category == "content"]
    if criteria:
        for row in numerical.get("arithmetic", []):
            if row["status"] == "ARITHMETIC_MISMATCH_CANDIDATE":
                add(
                    criteria[0],
                    "NUMERICAL_ARITHMETIC",
                    "Die dokumentierten Zahlen ergeben rechnerisch "
                    + row["calculated_percent"]
                    + " %. Wie erklärt sich die Abweichung zur Originalangabe; "
                    "stimmen Bezugsgröße und Extraktion?",
                    passages=[{"page": row["page"], "quote": row["quote"]}],
                )
        claims = {c["id"]: c for c in numerical.get("claims", [])}
        for comparison in numerical.get("comparisons", []):
            if comparison["status"] == "NUMERIC_CONFLICT_CANDIDATE":
                sides = [claims[comparison[key]] for key in ("first_id", "second_id")]
                add(
                    criteria[0],
                    "NUMERICAL_CONTEXT",
                    "Wie erklärt sich die Zahlenabweichung bei gleichem Experimentkontext; "
                    "stimmen Metrik, Einheit und Bezugsgröße überein?",
                    passages=[{"page": c["page"], "quote": c["quote"]} for c in sides],
                )
    return questions[:40]


def balanced_findings(findings):
    flat = [f for primary in findings for f in [primary, *primary.supplemental]]
    return {
        "items": [
            {
                "finding_id": f.finding_id,
                "criterion_id": f.criterion_id,
                "kind": f.kind,
                "evidence_status": f.evidence_status,
                "evidence_required": True,
                "scientific_error_proven": False,
            }
            for f in flat
        ],
        "forced_balance": False,
        "minimum_criticism_count": 0,
        "positive_evidence_pending": [
            f.finding_id
            for f in flat
            if f.kind == "STRENGTH" and f.evidence_status != "QUOTE_MATCHED"
        ],
    }
