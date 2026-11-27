import asyncio

import pytest
from app.assessments.profile_registry import ProfileRegistry
from app.evaluation.lab import ExperimentRequest, condition, run_experiment
from app.evaluation.metrics import outcome_change

from tests.fixtures import CONFIG
from tests.unit.test_evaluation_lab import lab


@pytest.mark.parametrize(
    "variation",
    [
        "student_name",
        "company_name",
        "gender_name",
        "criteria_order",
        "formatting",
        "expected_grade",
    ],
)
def test_fairness_interventions_preserve_scope_and_change_only_designated_inputs(variation):
    _, config = lab()
    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    base, catalog, _, _ = condition(config, profile, "baseline")
    doc, changed, local, order = condition(config, profile, variation)
    assert doc.classification == "PUBLIC" and doc.pages != {} and order is None
    if variation == "criteria_order":
        assert doc.pages == base.pages and changed.criteria == list(reversed(catalog.criteria))
    else:
        assert changed == catalog and local.agents == config.agents
        if variation != "formatting":
            assert {k: v for k, v in doc.pages.items() if k != 1} == {
                k: v for k, v in base.pages.items() if k != 1
            }


def test_each_ablation_changes_one_component_on_identical_document_and_catalog():
    gateway, config = lab()
    report = asyncio.run(
        run_experiment(
            gateway,
            config,
            ExperimentRequest(
                architectures=["E"],
                repeats=1,
                ablations=["baseline", "no_retrieval", "no_dynamic", "no_verification"],
            ),
        )
    )
    assert report["complete"] and len(report["results"]) == 4
    comparisons = report["ablation_comparisons"]
    assert len(comparisons) == 3 and all(
        c["same_document_and_catalog"] and len(c["changed_flags"]) == 1 for c in comparisons
    )
    assert all(c["causal_quality_benefit"].startswith("NOT_ESTABLISHED") for c in comparisons)
    assert len(report["consistency"]) == 4  # Different ablations are never pooled as repeats.
    assert all(r["quality"]["precision"] is None for r in report["results"])


def test_fairness_compares_criticism_kinds_evidence_and_judgments_without_inventing_points():
    a = {
        "findings": [
            {
                "criterion_id": "x",
                "kind": "STRENGTH",
                "judgment": "POSITIVE",
                "evidence_quality": "DIRECT_EVIDENCE",
            }
        ]
    }
    b = {
        "findings": [
            {
                "criterion_id": "x",
                "kind": "WEAKNESS",
                "judgment": "NEGATIVE",
                "evidence_quality": "INSUFFICIENT",
            }
        ]
    }
    change = outcome_change(a, b)
    assert change["criticism_count_delta"] == 1 and change["kind_distribution_changed"]
    assert change["evidence_quality_changed"] and not change["judgment_consistent"]
    assert change["point_deviation"] is None
