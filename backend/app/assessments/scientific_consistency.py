"""Structured relationship candidates; verified text is not verified inference."""

import re
from collections import Counter

from app.assessments.provenance import content_digest
from app.llm.errors import LLMError
from app.research.citations import verify_citations
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
    "HYPOTHESIS": r"hypothes",
    "SOURCE": r"quellen|references",
    "DATASET": r"datensatz|dataset",
    "EXPERIMENT": r"experiment|versuch",
}


def consistency_map(document, structure, findings=()):
    level = combine(
        document.classification,
        *(f.data_classification for primary in findings for f in [primary, *primary.supplemental]),
    )
    return {
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
        "classification": level,
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
        "graph": relationship_graph(document, findings),
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
        "origin": "ORIGINAL_DOCUMENT",
        "verification_origin": "DETERMINISTIC_CHECK",
        "verified_property": "EXACT_TEXT_LOCATION_ONLY",
    }


def interpretation_context(finding, document):
    """Project only scoped proposals and rechecked original references to later reviewers."""
    if finding.assessment_id != document.analysis_id:
        raise LLMError(403, "REVIEW_CONTEXT_SCOPE_DENIED")
    document = document.model_copy(
        update={"classification": combine(document.classification, finding.data_classification)}
    )
    return {
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
        "classification": document.classification,
        "origin": "UNVERIFIED_FINDING_PROPOSAL",
        "interpretation": finding.model_dump(
            include={"description", "rationale", "claim_type", "scientific_claims", "relationships"}
        ),
        "original_reference": passage(document, finding.page, finding.quote),
        "prior_challenges": [
            {
                "origin": "MODEL_INTERPRETATION",
                "semantic_truth_verified": False,
                "round": r["round"],
                "verdict": r.get("verdict", "UNAVAILABLE"),
                "rationale": r.get("rationale", ""),
                "counterargument": r.get("counterargument", ""),
                "counter_reference": passage(
                    document, r.get("counter_page"), r.get("counter_quote", "")
                ),
            }
            for r in finding.verification_rounds
        ],
        "semantic_truth_verified": False,
    }


def check_claims(finding, document, citation_report):
    """Ground model candidates; metadata and exact quotes never establish semantic truth."""
    if (finding.assessment_id, citation_report["analysis_id"], citation_report["document_id"]) != (
        document.analysis_id,
        document.analysis_id,
        document.document_id,
    ):
        raise LLMError(403, "SCIENTIFIC_CLAIM_SCOPE_DENIED")
    references = {r["entry"]["id"]: r for r in citation_report["references"]}
    counts = Counter(r["entry"]["id"] for r in citation_report["references"])
    checks = []
    for claim in finding.scientific_claims:
        original = passage(document, claim.passage.page, claim.passage.quote)
        support = [passage(document, p.page, p.quote) for p in claim.support]
        counter = [passage(document, p.page, p.quote) for p in claim.counterevidence]
        sources = [
            {
                "citation_id": key,
                "statuses": ["AMBIGUOUS_REFERENCE_ID"]
                if counts[key] > 1
                else references[key]["statuses"]
                if key in references
                else ["NOT_FOUND"],
                "checks": references[key]["checks"] if counts[key] == 1 else [],
                "origin": "DETERMINISTIC_CHECK",
                "link_origin": "MODEL_INTERPRETATION",
                "semantic_support": "MANUAL_REVIEW_REQUIRED",
                "not_found_scope": "LOCAL_SNAPSHOT_ONLY",
            }
            for key in claim.citation_ids
        ]
        issues = []
        if original["status"] != "QUOTE_MATCHED":
            issues.append("CLAIM_LOCATION_UNVERIFIED")
        selection = finding.context_trace.get("selection")
        if selection is not None and any(
            p["status"] == "QUOTE_MATCHED"
            and not any(
                s["page"] == p["page"] and s["start"] <= p["start"] and s["end"] >= p["end"]
                for s in selection
            )
            for p in [original, *support, *counter]
        ):
            issues.append("CLAIM_EVIDENCE_OUTSIDE_SELECTED_CONTEXT")
        if any(p["status"] != "QUOTE_MATCHED" for p in [*support, *counter]):
            issues.append("EVIDENCE_LOCATION_UNVERIFIED")
        if not any(p["status"] == "QUOTE_MATCHED" for p in support):
            issues.append("MISSING_SUPPORT_NOT_FACTUAL_ERROR")
        if any(p["status"] == "QUOTE_MATCHED" for p in counter):
            issues.append("POSSIBLE_CONTRADICTION_REQUIRES_HUMAN")
        if claim.category == "LITERATURE_BASED" and not sources:
            issues.append("MISSING_CITATION_LINK")
        if any(not any(s.startswith("VERIFIED_") for s in r["statuses"]) for r in sources):
            issues.append("SOURCE_UNVERIFIABLE_LOCALLY")
        if claim.concern != "NONE":
            issues.append("MODEL_CONCERN_REQUIRES_HUMAN")
        checks.append(
            {
                **claim.model_dump(),
                "claim_id": content_digest(claim.model_dump()),
                "analysis_id": document.analysis_id,
                "document_id": document.document_id,
                "classification": document.classification,
                "criterion_id": finding.criterion_id,
                "origin": "MODEL_INTERPRETATION",
                "status": "CANDIDATE",
                "original": original,
                "support_checks": support,
                "counterevidence_checks": counter,
                "source_checks": sources,
                "issues": issues,
                "factual_error_established": False,
                "argumentation_status": "HUMAN_REVIEW_REQUIRED",
                "context_is_complete": False,
            }
        )
    return checks


def relationship_graph(document, findings):
    """JSON graph of grounded candidates, never an inferred official requirement."""
    nodes, edges = {}, []
    for primary in findings:
        for finding in [primary, *primary.supplemental]:
            if finding.assessment_id != document.analysis_id:
                raise LLMError(403, "SCIENTIFIC_GRAPH_SCOPE_DENIED")
            level = combine(document.classification, finding.data_classification)
            scoped = document.model_copy(update={"classification": level})
            for relation in finding.relationships:
                refs = [passage(scoped, p.page, p.quote) for p in relation.passages]
                ids = []
                for aspect, ref in zip((relation.source, relation.target), refs[:2], strict=False):
                    key = content_digest([aspect, ref])
                    nodes[key] = {
                        "id": key,
                        "aspect": aspect,
                        "reference": ref,
                        "status": "CANDIDATE",
                    }
                    ids.append(key)
                edges.append(
                    {
                        **relation.model_dump(),
                        "source_node": ids[0] if ids else None,
                        "target_node": ids[1] if len(ids) > 1 else None,
                        "finding_id": finding.finding_id,
                        "criterion_id": finding.criterion_id,
                        "references": refs,
                        "classification": level,
                        "status": "CANDIDATE",
                        "origin": "MODEL_INTERPRETATION",
                        "semantic_status": "HUMAN_REVIEW_REQUIRED",
                        "automatic_criticism": False,
                        "evidence_status": "GROUNDED_PROPOSAL"
                        if len({(r["page"], r["start"], r["end"]) for r in refs}) >= 2
                        and all(r["status"] == "QUOTE_MATCHED" for r in refs)
                        and relation.source != relation.target
                        else "INSUFFICIENT_EVIDENCE",
                    }
                )
    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "missing_links": "NOT_INFERRED_FROM_INCOMPLETE_CANDIDATES",
    }


def update_evidence(finding, document, *, citation_report=None):
    if finding.assessment_id != document.analysis_id:
        raise LLMError(403, "SCIENTIFIC_EVIDENCE_SCOPE_DENIED")
    document = document.model_copy(
        update={"classification": combine(document.classification, finding.data_classification)}
    )
    finding.claim_checks = check_claims(
        finding, document, citation_report or verify_citations(document)
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


REPRO_ASPECTS = {
    "dataset_description": ("Datensatzbeschreibung", r"datensatz|dataset|stichprobe|sample"),
    "data_origin": ("Datenherkunft", r"datenherkunft|data source|erhoben|collected|datenquelle"),
    "preprocessing": (
        "Datenvorverarbeitung",
        r"vorverarbeit|preprocess|normalis|standardis|bereinig",
    ),
    "architecture": (
        "Modellarchitektur",
        r"architektur|architecture|random forest|logistische regression|neuronale? netz",
    ),
    "software_versions": (
        "Softwareversionen",
        r"(?:python|pytorch|tensorflow|scikit-learn|r version)\s*(?:version\s*)?\d+\.\d+",
    ),
    "hyperparameters": (
        "Hyperparameter",
        r"hyperparameter|learning.rate|lernrate|batch.size|n_estimators|max_depth",
    ),
    "random_seeds": ("Random Seeds", r"(?:random.seed|zufallsseed|seed)\s*(?:=|:)?\s*\d+"),
    "train_test_split": (
        "Trainings-/Testtrennung",
        r"train.test|testdat|trainingsdat|training.data|cross.validation|kreuzvalid",
    ),
    "evaluation_metrics": (
        "Evaluationsmetriken",
        r"accuracy|precision|recall|f1.score|auc|rmse|mae|evaluationsmetrik",
    ),
    "baselines": ("Baselines", r"baseline|vergleichsmodell|referenzmodell"),
    "hardware": ("Hardwareumgebung", r"gpu|cpu|arbeitsspeicher|ram|hardware"),
    "conditions": (
        "Experimentelle Bedingungen",
        r"versuchsbeding|experimentelle beding|experimental.condition|messbeding|"
        r"interviewleitfaden|kodierleitfaden|coding.protocol",
    ),
    "limitations": ("Limitationen", r"limitation|einschr.nkung|begrenzte|nicht .bertragbar"),
}
REPRO_METHOD_ASPECTS = {
    "MACHINE_LEARNING": tuple(REPRO_ASPECTS),
    "DEEP_LEARNING": tuple(REPRO_ASPECTS),
    "STATISTICS": (
        "dataset_description",
        "data_origin",
        "preprocessing",
        "software_versions",
        "random_seeds",
        "evaluation_metrics",
        "conditions",
        "limitations",
    ),
    "QUALITATIVE": ("dataset_description", "data_origin", "conditions", "limitations"),
    "EXPERT_INTERVIEWS": ("dataset_description", "data_origin", "conditions", "limitations"),
    "LITERATURE_REVIEW": ("data_origin", "conditions", "limitations"),
    "SOFTWARE_ENGINEERING": ("software_versions", "hardware", "conditions", "limitations"),
    "DATA_ENGINEERING": (
        "dataset_description",
        "data_origin",
        "preprocessing",
        "software_versions",
        "conditions",
        "limitations",
    ),
    "ECONOMIC_ANALYSIS": ("dataset_description", "data_origin", "conditions", "limitations"),
}


def reproducibility_report(document, profile, methods=()):
    """Documentation checklist for explicitly evidenced applied methods; no execution."""
    from app.services.document_intelligence import INTERPRETATION_CUES, structure_document

    structure = structure_document(document)
    report = {
        "status": "NOT_ASSESSABLE_METHOD_CONTEXT",
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
        "classification": document.classification,
        "document_sha256": content_digest(document.pages),
        "methods": [],
        "experiment_reproduced": False,
        "documented_reproducibility": "NOT_ESTABLISHED",
        "official_criterion": False,
        "automatic_grade_effect": False,
    }
    if len(methods) > 6:
        raise ValueError("REPRODUCIBILITY_METHOD_LIMIT")
    catalog = {c.id for c in profile.criteria}
    for method in methods:
        if method.get("use") != "APPLIED" or method.get("family") not in REPRO_METHOD_ASPECTS:
            continue
        if method.get("criterion_id") not in catalog or method.get("origin") not in {
            "HUMAN_CONFIRMED",
            "VALIDATED_MODEL_PROPOSAL",
        }:
            raise ValueError("REPRODUCIBILITY_METHOD_SCOPE_DENIED")
        blocks = []
        for evidence in method.get("evidence", []):
            block = structure.locate(evidence["page"], evidence["quote"])
            if (
                block is None
                or not block.reliable
                or block.kind == "BIBLIOGRAPHY"
                or document.pages[evidence["page"]].count(evidence["quote"]) != 1
            ):
                raise ValueError("REPRODUCIBILITY_METHOD_EVIDENCE_DENIED")
            if block not in blocks:
                blocks.append(block)
        if not blocks:
            raise ValueError("REPRODUCIBILITY_METHOD_EVIDENCE_REQUIRED")
        checks = []
        for key in REPRO_METHOD_ASPECTS[method["family"]]:
            label, pattern = REPRO_ASPECTS[key]
            passages = []
            for block in blocks:
                match = re.search(pattern, block.text, re.I)
                if match:
                    # Preserve the original block as context; a term match is never adequacy.
                    context_start = max(0, min(match.start() - 200, len(block.text) - 800))
                    nearby = block.text[max(0, match.start() - 120) : match.end() + 160]
                    reasons = []
                    if INTERPRETATION_CUES.search(nearby):
                        reasons.append("NEGATION_OR_UNCERTAINTY_CUE")
                    if any(
                        q["page"] == block.page
                        and q["start"] <= block.start + match.start() < q["end"]
                        for q in structure.quotations
                    ):
                        reasons.append("QUOTED_TEXT_REQUIRES_ATTRIBUTION")
                    passages.append(
                        {
                            "page": block.page,
                            "start": block.start + match.start(),
                            "end": block.start + match.end(),
                            "quote": match.group(),
                            "context": block.text[context_start : context_start + 800],
                            "context_start": block.start + context_start,
                            "review_reasons": reasons,
                            "documentation_adequacy_verified": False,
                        }
                    )
            checks.append(
                {
                    "aspect": key,
                    "label": label,
                    "status": "DOCUMENTATION_UNCERTAINTY_REQUIRES_HUMAN"
                    if any(p["review_reasons"] for p in passages)
                    else "TEXT_MENTION_REQUIRES_HUMAN"
                    if passages
                    else "NOT_LOCATED_IN_METHOD_CONTEXT",
                    "passages": passages,
                    "missing_information_proven": False,
                    "applicability": "METHOD_DEPENDENT_REQUIRES_HUMAN",
                }
            )
        report["methods"].append(
            {
                "family": method["family"],
                "criterion_id": method["criterion_id"],
                "origin": method["origin"],
                "evidence": method["evidence"],
                "checks": checks,
                "scope": "EVIDENCED_METHOD_BLOCKS_ONLY",
            }
        )
    if report["methods"]:
        report["status"] = "DOCUMENTATION_CHECKLIST_REQUIRES_HUMAN"
    return report


def applied_method_candidates(document, profile, findings):
    """Reuse the existing semantic plan and recheck its exact original chunk references."""
    from app.services.context_management import LocalContextIndex

    if not findings:
        return []
    plan = findings[0].provenance.get("adaptive_planning", {})
    if plan.get("status") != "VALIDATED_PROPOSAL":
        return []
    procedures = plan.get("understanding", {}).get("procedures", [])
    criteria = [c.id for c in profile.criteria if c.category == "methodology"]
    if not criteria:
        return []
    result = []
    with LocalContextIndex(document) as index:
        chunks = {c.id: c for c in index.chunks}
        for procedure in procedures[:6]:
            if procedure.get("use") != "APPLIED":
                continue
            evidence = []
            for reference in procedure.get("evidence", []):
                chunk = chunks.get(reference.get("span_id"))
                quote = reference.get("quote", "")
                if chunk and chunk.reliable and quote and chunk.text.count(quote) == 1:
                    evidence.append({"page": chunk.page, "quote": quote})
            if evidence:
                result.append(
                    {
                        "family": procedure.get("family", "UNKNOWN"),
                        "use": "APPLIED",
                        "criterion_id": criteria[0],
                        "origin": "VALIDATED_MODEL_PROPOSAL",
                        "evidence": evidence[:3],
                    }
                )
    return result
