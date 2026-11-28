"""Only human annotations establish quality; synthetic measurements cover software behavior."""

import asyncio

from app.assessments.schemas import ScientificClaim
from app.evaluation.lab import ExperimentRequest, run_experiment
from app.evaluation.metrics import (
    Adjudication,
    HumanReferenceSet,
    ablation_comparisons,
    fingerprint,
    quality_metrics,
)
from app.schemas.domain import CompactSchemaModel
from pydantic import Field

from tests.unit.test_evaluation_lab import lab
from tests.unit.test_review_intelligence import evidence_fixture


def test_scientific_quality_metrics_require_explicit_scoped_human_annotations():
    _, f = evidence_fixture()
    missing = quality_metrics([f], None, "a" * 64, "b" * 64)
    assert missing["scientific_claim_correctness"] is None
    reference = HumanReferenceSet(
        dataset_sha256="a" * 64,
        profile_sha256="b" * 64,
        adjudicated_by=["SYNTHETIC_TEST_REVIEWER"],
        reference_ids=["reference-1"],
        adjudications=[
            Adjudication(
                prediction_fingerprint=fingerprint(f),
                correct=True,
                matched_reference_ids=["reference-1"],
                hallucinated=False,
                claim_correct=True,
                methodological_weakness_correct=False,
                propagated_error=False,
                reviewer_accepted=True,
            )
        ],
    )
    measured = quality_metrics([f], reference, "a" * 64, "b" * 64)
    assert measured["scientific_claim_correctness"] == measured["reviewer_acceptance"] == 1
    assert (
        measured["methodological_weakness_correctness"] == measured["error_propagation_rate"] == 0
    )
    assert measured["annotation_counts"]["claim_correct"] == 1
    assert measured["human_time_saved_seconds"] is None
    changed = f.model_copy(deep=True)
    changed.scientific_claims = [
        ScientificClaim(
            category="HYPOTHESIS",
            statement="Changed scientific interpretation",
            passage={"page": 1, "quote": f.quote},
            rationale="Synthetic changed claim",
        )
    ]
    assert fingerprint(changed) != fingerprint(f)
    assert (
        quality_metrics([changed], reference, "a" * 64, "b" * 64)["reference_status"]
        == "INCOMPLETE_HUMAN_ADJUDICATION"
    )


def test_ablation_rejects_comparison_when_same_document_id_has_different_content_or_rubric():
    gateway, config = lab()
    report = asyncio.run(
        run_experiment(
            gateway,
            config,
            ExperimentRequest(
                architectures=["E"], repeats=1, ablations=["baseline", "no_verification"]
            ),
        )
    )
    assert len(ablation_comparisons(report["results"])) == 1
    report["results"][1]["dataset_sha256"] = "c" * 64
    assert not ablation_comparisons(report["results"])


def test_compact_schema_preserves_field_named_title_and_all_validation_constraints():
    class Response(CompactSchemaModel):
        title: str = Field(min_length=1, max_length=8)

    schema = Response.model_json_schema()
    assert "title" not in schema and schema["additionalProperties"] is False
    assert schema["properties"]["title"] == {"minLength": 1, "maxLength": 8, "type": "string"}
    assert schema["required"] == ["title"]
