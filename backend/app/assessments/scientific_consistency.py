"""Structured relationship candidates; verified text is not verified inference."""

import re

from app.security.classification import combine
from app.validation.evidence_validator import check_evidence

ASPECTS = {
    "QUESTION": r"forschungsfrage|research question",
    "OBJECTIVE": r"zielsetz|objective",
    "THEORY": r"theori|grundlagen",
    "PRIOR_WORK": r"forschungsstand|literatur|prior work",
    "METHOD": r"method",
    "DATA": r"datenerheb|stichprob|data collection",
    "ANALYSIS": r"analyse|auswert",
    "RESULTS": r"ergebnis|results",
    "DISCUSSION": r"diskussion|discussion",
    "LIMITATIONS": r"limitation|einschr.nk|.bertrag|begrenz",
    "CONCLUSION": r"fazit|schlussfolger|conclusion",
}


def consistency_map(document, structure):
    return {
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
        "classification": document.classification,
        "nodes": [
            {
                "aspect": key,
                "candidates": [
                    {"page": b.page, "start": b.start, "end": b.end, "chapter": b.chapter}
                    for b in structure.blocks
                    if re.search(pattern, (b.chapter or "") + " " + b.text, re.I)
                ][:12],
            }
            for key, pattern in ASPECTS.items()
        ],
        "absence_proven": False,
        "semantic_consistency": "HUMAN_REVIEW_REQUIRED",
    }


def passage(document, page, quote):
    checked = check_evidence(document, page, quote)
    return {
        "page": page,
        "quote": quote,
        "start": checked.start,
        "end": checked.end,
        "status": checked.status,
        "classification": document.classification,
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
    }


def update_evidence(finding, document):
    document = document.model_copy(
        update={"classification": combine(document.classification, finding.data_classification)}
    )
    support = [passage(document, p.page, p.quote) for p in finding.supporting_passages]
    if finding.page and finding.quote:
        support.insert(0, passage(document, finding.page, finding.quote))
    finding.supporting_evidence = list({(p["page"], p["quote"]): p for p in support}.values())
    finding.contradicting_evidence = [
        {**passage(document, r["counter_page"], r["counter_quote"]), "round": r["round"]}
        for r in finding.verification_rounds
        if r.get("counter_page") and r.get("counter_quote")
    ]
    finding.relationship_checks = []
    for relation in finding.relationships:
        checks = [passage(document, p.page, p.quote) for p in relation.passages]
        valid = {
            (p["page"], p["start"], p["end"]) for p in checks if p["status"] == "QUOTE_MATCHED"
        }
        grounded = (
            len(valid) >= 2 and len(valid) == len(checks) and relation.source != relation.target
        )
        finding.relationship_checks.append(
            {
                **relation.model_dump(),
                "criterion_id": finding.criterion_id,
                "classification": document.classification,
                "analysis_id": document.analysis_id,
                "document_id": document.document_id,
                "passage_checks": checks,
                "status": "GROUNDED_PROPOSAL" if grounded else "INSUFFICIENT_EVIDENCE",
                "semantic_status": "HUMAN_REVIEW_REQUIRED",
                "automatic_criticism": False,
            }
        )
    valid_support = [p for p in finding.supporting_evidence if p["status"] == "QUOTE_MATCHED"]
    if finding.conflict and any(
        p["status"] == "QUOTE_MATCHED" for p in finding.contradicting_evidence
    ):
        quality = "CONTRADICTORY"
    elif finding.judgment == "NOT_ASSESSABLE":
        quality = "NOT_ASSESSABLE"
    elif (
        finding.evidence_status != "QUOTE_MATCHED"
        or finding.conflict
        or "UNVERIFIED_COMPLEX_OBJECT_EXTRACTION" in finding.open_questions
        or any(p["status"] != "QUOTE_MATCHED" for p in support)
    ):
        quality = "INSUFFICIENT"
    elif finding.relationship_checks:
        quality = (
            "INFERRED"
            if all(r["status"] == "GROUNDED_PROPOSAL" for r in finding.relationship_checks)
            else "INSUFFICIENT"
        )
    elif len(valid_support) > 1:
        quality = "MULTIPLE_EVIDENCE"
    else:
        quality = "DIRECT_EVIDENCE"
    finding.evidence_quality = quality
    selection = finding.context_trace.get("selection")
    if selection is not None and any(
        not any(
            c["page"] == p["page"]
            and p["start"] is not None
            and c["start"] <= p["start"]
            and c["end"] >= p["end"]
            for c in selection
        )
        for p in valid_support
    ):
        finding.evidence_quality = quality = "INSUFFICIENT"
        finding.open_questions = list(
            dict.fromkeys([*finding.open_questions, "QUOTE_OUTSIDE_SELECTED_CONTEXT"])
        )
    questions = []
    if finding.claim_type == "ABSENCE":
        questions.append("ABSENCE_REQUIRES_EXPANDED_SEARCH_AND_HUMAN_REVIEW")
    if quality in {"CONTRADICTORY", "INSUFFICIENT", "NOT_ASSESSABLE"}:
        questions.append("HUMAN_EVIDENCE_CLARIFICATION_REQUIRED")
    finding.open_questions = list(dict.fromkeys([*finding.open_questions, *questions]))
    finding.unverifiable_aspects = ["SEMANTIC_TRUTH_NOT_ESTABLISHED_BY_QUOTE_OR_MODEL_CONSENSUS"]
