"""Synthetic contracts and mechanical checks, never scientific model quality evidence."""

import asyncio
from types import SimpleNamespace

import pytest
from app.agents.adaptive_assessment import METHOD_CHECKS
from app.assessments.adversarial_verification import verify_finding
from app.assessments.coverage import assessment_coverage
from app.assessments.schemas import EvidencePassage, ScientificClaim, ScientificRelationship
from app.assessments.scientific_consistency import (
    consistency_map,
    interpretation_context,
    update_evidence,
)
from app.core.configuration import RuntimeConfig
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget
from app.research.citations import verify_citations
from app.research.provider_registry import LocalResearchCache
from app.services.document_intelligence import structure_document

from tests.fixtures import CONFIG
from tests.fixtures.semantic_planning import SemanticProvider
from tests.unit.test_citation_engine import record
from tests.unit.test_review_intelligence import evidence_fixture
from tests.unit.test_semantic_planning import review


def claim(document, **changes):
    return ScientificClaim(
        **(
            {
                "category": "GENERALIZATION",
                "statement": "Synthetic scientific statement",
                "passage": {"page": 1, "quote": document.pages[1]},
                "rationale": "Synthetic interpretation, not truth",
            }
            | changes
        )
    )


@pytest.mark.parametrize(
    "category",
    [
        "FACTUAL_ASSERTION",
        "HYPOTHESIS",
        "OWN_RESULT",
        "CONCLUSION",
        "METHODOLOGICAL_ASSUMPTION",
        "GENERALIZATION",
        "LITERATURE_BASED",
    ],
)
def test_claim_categories_are_grounded_candidates_and_missing_support_is_not_error(category):
    doc, f = evidence_fixture()
    f.scientific_claims = [claim(doc, category=category)]
    update_evidence(f, doc)
    result = f.claim_checks[0]
    assert result["original"]["status"] == "QUOTE_MATCHED"
    assert "MISSING_SUPPORT_NOT_FACTUAL_ERROR" in result["issues"]
    assert not result["factual_error_established"] and result["status"] == "CANDIDATE"
    assert result["argumentation_status"] == "HUMAN_REVIEW_REQUIRED"


def test_claim_support_and_counterevidence_are_rechecked_and_do_not_verify_interpretation():
    doc, f = evidence_fixture(data_classification="RESTRICTED")
    f.scientific_claims = [
        claim(
            doc,
            support=[{"page": 2, "quote": "Invented evidence"}],
            counterevidence=[{"page": 3, "quote": doc.pages[3]}],
            concern="POSSIBLE_FACTUAL_ERROR",
        )
    ]
    update_evidence(f, doc)
    check = f.claim_checks[0]
    assert check["support_checks"][0]["status"] == "REJECTED"
    assert check["counterevidence_checks"][0]["status"] == "QUOTE_MATCHED"
    assert "POSSIBLE_CONTRADICTION_REQUIRES_HUMAN" in check["issues"]
    assert check["classification"] == check["original"]["classification"] == "RESTRICTED"
    assert not check["factual_error_established"]


def test_claim_links_reuse_offline_citation_engine_without_promoting_metadata_to_truth():
    doc, f = evidence_fixture()
    doc.pages[4] = "Literaturverzeichnis\n[1] Muster (2020). Synthetischer Titel. doi:10.5555/test"
    report = verify_citations(doc, LocalResearchCache([record()]))
    f.scientific_claims = [claim(doc, category="LITERATURE_BASED", citation_ids=["1", "missing"])]
    update_evidence(f, doc, citation_report=report)
    sources = f.claim_checks[0]["source_checks"]
    assert "VERIFIED_METADATA" in sources[0]["statuses"] and sources[0]["checks"]
    assert sources[1]["statuses"] == ["NOT_FOUND"]
    assert sources[0]["semantic_support"] == "MANUAL_REVIEW_REQUIRED"
    assert not f.claim_checks[0]["factual_error_established"]
    with pytest.raises(LLMError, match="SCOPE"):
        update_evidence(f, doc, citation_report={**report, "document_id": "foreign"})
    report["references"].append(report["references"][0])
    update_evidence(f, doc, citation_report=report)
    assert f.claim_checks[0]["source_checks"][0]["statuses"] == ["AMBIGUOUS_REFERENCE_ID"]
    assert not f.claim_checks[0]["source_checks"][0]["checks"]


def test_graph_preserves_grounded_and_unverified_candidates_with_original_references():
    doc, f = evidence_fixture(data_classification="RESTRICTED")
    f.relationships = [
        ScientificRelationship(
            source="HYPOTHESIS",
            target="EXPERIMENT",
            relation="POSSIBLE_CONTRADICTION",
            rationale="Synthetic inference",
            passages=[
                EvidencePassage(page=1, quote=doc.pages[1]),
                EvidencePassage(page=2, quote=doc.pages[2]),
            ],
        )
    ]
    graph = consistency_map(doc, structure_document(doc), [f])["graph"]
    edge = graph["edges"][0]
    assert edge["status"] == "CANDIDATE" and edge["evidence_status"] == "GROUNDED_PROPOSAL"
    assert edge["source_node"] != edge["target_node"] and not edge["automatic_criticism"]
    assert all(n["reference"]["classification"] == "RESTRICTED" for n in graph["nodes"])
    f.relationships[0].passages[1].quote = "Invented"
    edge = consistency_map(doc, structure_document(doc), [f])["graph"]["edges"][0]
    assert edge["evidence_status"] == "INSUFFICIENT_EVIDENCE"
    assert edge["semantic_status"] == "HUMAN_REVIEW_REQUIRED"
    f.assessment_id = "foreign"
    with pytest.raises(LLMError, match="SCOPE"):
        consistency_map(doc, structure_document(doc), [f])


def test_unverified_prior_review_never_becomes_a_deterministic_fact_for_the_next_model():
    doc, f = evidence_fixture()
    f.verification_rounds = [
        {
            "round": 1,
            "verdict": "SUPPORTED",
            "rationale": "Untrusted model summary",
            "counter_page": 3,
            "counter_quote": "Invented counterquote",
            "counter_evidence_status": "QUOTE_MATCHED",  # Forged stored status is not trusted.
        }
    ]
    context = interpretation_context(f, doc)
    prior = context["prior_challenges"][0]
    assert prior["origin"] == "MODEL_INTERPRETATION" and not prior["semantic_truth_verified"]
    assert prior["counter_reference"]["status"] == "REJECTED"
    assert context["original_reference"]["origin"] == "ORIGINAL_DOCUMENT"
    assert not context["semantic_truth_verified"]


@pytest.mark.parametrize("family", list(METHOD_CHECKS))
def test_method_check_suggestions_require_semantic_applied_evidence_and_existing_criterion(family):
    provider = SemanticProvider(
        mutate=lambda p: p["understanding"]["procedures"][0].update(family=family)
    )
    findings, _, _, _ = review(provider)
    proposal = findings[0].provenance["adaptive_planning"]["proposals"][0]
    assert proposal["method_family"] == family and proposal["criterion_id"] == "methodology"
    assert proposal["scientific_check_suggestions"] == METHOD_CHECKS[family]
    assert proposal["method_evidence"] and not proposal["checks_are_official_requirements"]
    assert not proposal["method_use_expert_verified"]


def test_counter_review_deadline_hands_failure_to_human_without_fallback():
    doc, f = evidence_fixture()
    config = RuntimeConfig(CONFIG)
    config.limits = config.limits.model_copy(update={"agent_timeout_seconds": 0.001})

    async def stalled_route(*args, **kwargs):
        await asyncio.sleep(1)

    budget = CallBudget(5, 100000)
    asyncio.run(
        verify_finding(
            SimpleNamespace(route=stalled_route),
            config,
            f,
            doc,
            structure_document(doc),
            budget,
            {},
        )
    )
    assert f.verification_status == "UNAVAILABLE" and f.conflict
    assert f.verification_rounds[0]["error_code"] == 504 and budget.calls == 0
    assert f.debate_summary["human_decision_required"]


def coverage_record():
    doc, f = evidence_fixture()
    from app.assessments.profile_registry import ProfileRegistry

    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    values = [f.model_copy(deep=True, update={"criterion_id": c.id}) for c in profile.criteria]
    return SimpleNamespace(
        profile=profile,
        document=doc,
        ai=values,
        ai_state="COMPLETED",
        decisions=[],
        finding_feedback=[],
        classification="PUBLIC",
    )


def test_coverage_unions_overlapping_spans_and_distinguishes_input_from_understanding():
    r = coverage_record()
    r.ai[0].context_trace = {
        "analysis_id": r.document.analysis_id,
        "document_id": r.document.document_id,
        "selection": [{"page": 1, "start": 0, "end": 10}, {"page": 1, "start": 5, "end": 15}],
    }
    report = assessment_coverage(r, verify_citations(r.document))
    assert report["required_review_ratio"] == 1 and report["selected_original_characters"] == 15
    assert report["context_selection_ratio"] == 15 / sum(map(len, r.document.pages.values()))
    assert report["unprocessed_regions"][0] == {
        "page": 1,
        "start": 15,
        "end": len(r.document.pages[1]),
    }
    assert report["status"] == "INCOMPLETE" and report["open_human_decisions"]
    r.ai[0].context_trace["document_id"] = "foreign"
    with pytest.raises(LLMError, match="SCOPE"):
        assessment_coverage(r, verify_citations(r.document))


def test_coverage_accounts_for_optional_criteria_errors_sources_and_resource_limits():
    r = coverage_record()
    r.profile.criteria[-1].required = False
    r.ai[0].judgment = "NOT_ASSESSABLE"
    r.ai[1].open_questions = ["SUPPLEMENT_FAILED_REQUIRES_HUMAN:429"]
    r.ai[1].verification_rounds = [{"round": 1, "error_code": 504}]
    r.document.pages[4] = "Literaturverzeichnis\n[1] Muster (2020). Test. doi:10.5555/test"
    report = assessment_coverage(r, verify_citations(r.document))
    assert report["required_review_ratio"] == 0.5 and report["optional_review_ratio"] == 1
    assert report["not_assessable"] == (r.ai[0].criterion_id,)
    assert len(report["failed_subanalyses"]) == 2 and report["unverifiable_sources"] == ["1"]
    assert report["resource_limitations"] and not report["analysis_complete"]
    r.ai, r.ai_state = [], "FAILED"
    assert len(assessment_coverage(r, verify_citations(r.document))["failed_subanalyses"]) == 3


def test_coverage_reports_complete_only_after_full_input_and_human_decisions():
    r = coverage_record()
    r.ai[0].context_trace = {
        "analysis_id": r.document.analysis_id,
        "document_id": r.document.document_id,
        "selection": [{"page": p, "start": 0, "end": len(t)} for p, t in r.document.pages.items()],
    }
    r.decisions = [{"criterion_id": c.id} for c in r.profile.criteria]
    report = assessment_coverage(r, verify_citations(r.document))
    assert report["analysis_complete"] and report["context_selection_ratio"] == 1
    assert report["status"] == "COMPLETE" and not report["unprocessed_regions"]
    with pytest.raises(LLMError, match="SCOPE"):
        assessment_coverage(r, {**verify_citations(r.document), "analysis_id": "foreign"})
