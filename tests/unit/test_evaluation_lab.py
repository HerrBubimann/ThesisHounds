import asyncio
import csv
import json
from typing import get_args
from unittest.mock import AsyncMock, patch

import pytest
from app.assessments.profile_registry import ProfileRegistry
from app.assessments.schemas import AssessmentFinding
from app.core.configuration import RuntimeConfig
from app.evaluation.lab import (
    ExperimentRequest,
    Variation,
    condition,
    export_results,
    run_experiment,
)
from app.evaluation.metrics import HumanReferenceSet, digest, fingerprint, quality_metrics
from app.llm.gateway import LLMGateway
from app.llm.providers.demo import DemoProvider
from pydantic import ValidationError

from tests.fixtures import CONFIG


def lab():
    config = RuntimeConfig(CONFIG)
    return LLMGateway(config.models, {"ollama": DemoProvider()}, config.policy), config


def test_a_to_e_are_real_distinct_executions_on_identical_synthetic_inputs(tmp_path):
    gateway, config = lab()
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as network:
        report = asyncio.run(run_experiment(gateway, config, ExperimentRequest()))
        network.assert_not_called()
    assert report["mocked"] and report["complete"] and len(report["results"]) == 10
    assert len({r["dataset_sha256"] for r in report["results"]}) == 1
    assert all(r["coverage_complete"] for r in report["results"])
    assert all(r["quality"]["precision"] is None for r in report["results"])
    calls = {r["architecture"]: r["model_calls"] for r in report["results"]}
    assert calls["A"] == 1 < calls["B"] == calls["C"] < calls["D"] < calls["E"]
    assert all(r["status"] == "MEASURED" for r in report["consistency"])
    first, second = export_results(report, tmp_path)
    assert json.loads(first.read_text("utf-8"))["mocked"]
    with second.open(encoding="utf-8") as stream:
        assert len(list(csv.DictReader(stream))) == 10


def test_global_call_limit_stops_experiments_without_external_fallback():
    gateway, config = lab()
    report = asyncio.run(
        run_experiment(gateway, config, ExperimentRequest(max_total_model_calls=1))
    )
    assert report["total_model_calls"] == 1 and not report["complete"]
    assert report["consistency"][0]["status"] == "NEEDS_REPEATS"


@pytest.mark.parametrize(
    "matrix_request",
    [
        ExperimentRequest(variations=list(get_args(Variation)), repeats=1),
        ExperimentRequest(
            ablations=["baseline", "no_retrieval", "no_dynamic", "no_verification"], repeats=1
        ),
    ],
    ids=["ci-all-variations", "ci-all-ablations"],
)
def test_complete_ci_experiment_matrices_fit_existing_limits(matrix_request):
    gateway, config = lab()
    model_limits = {m.id: m.context_length for m in config.models.enabled()}
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as network:
        report = asyncio.run(run_experiment(gateway, config, matrix_request))
        network.assert_not_called()
    assert len(report["results"]) == (
        5 * len(matrix_request.variations) * len(matrix_request.ablations)
    )
    assert report["complete"], [
        (row["architecture"], row["variation"], row["ablation"], row.get("error_code"))
        for row in report["results"]
        if row["status"] != "COMPLETED"
    ]
    assert all(row["coverage_complete"] for row in report["results"])
    assert report["total_model_calls"] <= matrix_request.max_total_model_calls
    assert {m.id: m.context_length for m in config.models.enabled()} == model_limits


def test_architecture_e_cannot_silently_disable_its_verification_component():
    gateway, config = lab()
    config.limits = config.limits.model_copy(update={"max_conflict_reviews": 0})
    report = asyncio.run(
        run_experiment(gateway, config, ExperimentRequest(architectures=["E"], repeats=1))
    )
    assert not report["complete"] and report["results"][0]["error_code"] == 503
    assert report["total_model_calls"] == 0


def test_variations_change_one_factor_and_preserve_the_public_synthetic_boundary():
    _, config = lab()
    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    base, catalog, _, _ = condition(config, profile, "baseline")
    for variation in (
        "student_name",
        "company_name",
        "formatting",
        "criteria_order",
        "agent_order",
        "model_assignment",
        "injection",
    ):
        document, changed, local, order = condition(config, profile, variation)
        assert (
            document.classification == "PUBLIC" and document.document_id == "synthetic-evaluation"
        )
        if variation in {"criteria_order", "agent_order", "model_assignment"}:
            assert document.pages == base.pages
        if variation == "criteria_order":
            assert changed.criteria == list(reversed(catalog.criteria)) and order is None
        if variation == "agent_order":
            assert changed == catalog and order == [c.id for c in reversed(catalog.criteria)]
        if variation == "model_assignment":
            assert local.agents.single_model != config.agents.single_model and changed == catalog


def test_quality_requires_explicit_human_adjudication_of_each_prediction():
    finding = AssessmentFinding(
        assessment_id="synthetic",
        criterion_id="methodology",
        category="methodology",
        model_id="qwen",
        manufacturer="Alibaba",
        agent_id="synthetic",
        judgment="NEGATIVE",
        kind="WEAKNESS",
        description="Synthetic claim",
        rationale="Synthetic rationale",
        page=1,
        quote="Synthetic quote",
    )
    dataset, profile = digest({"synthetic": 1}), digest({"catalog": 1})
    assert quality_metrics([finding], None, dataset, profile)["precision"] is None
    reference = HumanReferenceSet(
        dataset_sha256=dataset,
        profile_sha256=profile,
        adjudicated_by=["synthetic-test-adjudicator"],
        reference_ids=["truth"],
        adjudications=[],
    )
    assert quality_metrics([finding], reference, dataset, profile)["precision"] is None
    reference = HumanReferenceSet.model_validate(
        {
            **reference.model_dump(),
            "adjudications": [
                {
                    "prediction_fingerprint": fingerprint(finding),
                    "correct": False,
                    "matched_reference_ids": [],
                    "hallucinated": True,
                }
            ],
        }
    )
    metrics = quality_metrics([finding], reference, dataset, profile)
    assert metrics["precision"] == 0 and metrics["recall"] == 0
    assert metrics["false_positive_criticism"] == metrics["false_negatives"] == 1
    assert metrics["hallucination_rate"] == 1
    with pytest.raises(ValueError):
        quality_metrics([finding], reference, "c" * 64, profile)


def test_invalid_conditions_and_private_exports_are_rejected(tmp_path):
    with pytest.raises(ValidationError):
        ExperimentRequest(architectures=["A", "A"])
    with pytest.raises(ValidationError):
        ExperimentRequest(document_path="private.pdf")
    with pytest.raises(PermissionError):
        export_results(
            {"kind": "SYNTHETIC_EVALUATION", "data_classification": "RESTRICTED"}, tmp_path
        )
