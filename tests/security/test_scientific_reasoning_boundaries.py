"""New scientific annotations preserve the existing private-processing boundaries."""

import asyncio

import pytest
from app.assessments.adversarial_verification import verify_finding
from app.assessments.schemas import ScientificClaim
from app.assessments.scientific_consistency import (
    consistency_map,
    interpretation_context,
    update_evidence,
)
from app.llm.errors import LLMError
from app.services.document_intelligence import structure_document
from pydantic import ValidationError

from tests.unit.test_review_intelligence import evidence_fixture
from tests.unit.test_semantic_planning import setup


@pytest.mark.parametrize(
    "forged",
    [
        {"factual_error_established": True},
        {"origin": "HUMAN_CONFIRMED"},
        {"status": "VERIFIED"},
        {"automatic_training": True},
    ],
)
def test_model_cannot_self_certify_truth_human_approval_or_training(forged):
    with pytest.raises(ValidationError):
        ScientificClaim.model_validate(
            {
                "category": "FACTUAL_ASSERTION",
                "statement": "Synthetic",
                "passage": {"page": 1, "quote": "Synthetic"},
                "rationale": "Synthetic",
                **forged,
            }
        )


def test_private_interpretation_and_graph_labels_never_downgrade_to_public():
    doc, finding = evidence_fixture(data_classification="RESTRICTED")
    context = interpretation_context(finding, doc)
    assert (
        context["classification"] == context["original_reference"]["classification"] == "RESTRICTED"
    )
    assert (
        consistency_map(doc, structure_document(doc), [finding])["classification"] == "RESTRICTED"
    )
    finding.assessment_id = "foreign"
    for operation in (interpretation_context, update_evidence):
        with pytest.raises(LLMError, match="SCOPE"):
            operation(finding, doc)


def test_private_counter_review_is_blocked_without_model_call_or_external_fallback():
    config, gateway, _, _, budget = setup()
    doc, finding = evidence_fixture(data_classification="RESTRICTED")
    provider = gateway.providers["ollama"]
    available = {m.name: m.digest for m in asyncio.run(provider.discover())}
    asyncio.run(
        verify_finding(gateway, config, finding, doc, structure_document(doc), budget, available)
    )
    assert not provider.contexts and budget.calls == 0
    assert finding.verification_status == "UNAVAILABLE"
    assert finding.debate_summary["human_decision_required"]
