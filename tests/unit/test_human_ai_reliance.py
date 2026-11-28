import pytest
from app.assessments.schemas import AIObservation, CriterionReview
from app.evaluation.metrics import reliance_metrics
from pydantic import ValidationError


def trial(**changes):
    return {
        "condition": "D_DISCUSSION",
        "trial_id": "synthetic-1",
        "participant_code": "P1",
        "reference_id": "human-validated-synthetic",
        "ai_correct": False,
        "adopted_ai": True,
        "initial_correct": True,
        "final_correct": False,
        "elapsed_seconds": 12,
        **changes,
    }


def test_reliance_metrics_distinguish_correct_and_incorrect_adoption():
    result = reliance_metrics(
        [
            trial(),
            trial(
                trial_id="synthetic-2",
                ai_correct=True,
                initial_correct=False,
                final_correct=True,
                perceived_control=6,
            ),
            trial(trial_id="synthetic-3", adopted_ai=False, final_correct=True),
        ],
        approved_protocol="SYNTHETIC_TEST_ONLY",
        dataset_kind="SYNTHETIC",
        validated_reference_ids={"human-validated-synthetic"},
    )
    condition = result["conditions"]["D_DISCUSSION"]
    assert condition["correct_ai_adoption"] == 1
    assert condition["incorrect_ai_adoption"] == 0.5
    assert condition["unsupported_criticism_rejection"] == 0.5
    assert condition["paired_initial_final_outcome_changes"] == 2
    assert condition["final_reference_accuracy"] == 2 / 3
    assert not result["empirical_effectiveness_established"]


@pytest.mark.parametrize(
    "changes",
    [
        {"approved_protocol": " "},
        {"dataset_kind": "REAL_EXAM"},
        {"validated_reference_ids": set()},
        {"validated_reference_ids": {"unknown"}},
    ],
)
def test_reliance_analysis_requires_approved_experiment_and_reference(changes):
    arguments = {
        "approved_protocol": "SYNTHETIC_PROTOCOL",
        "dataset_kind": "SYNTHETIC",
        "validated_reference_ids": {"human-validated-synthetic"},
        **changes,
    }
    with pytest.raises(ValueError):
        reliance_metrics([trial()], **arguments)


def test_duplicate_trials_are_rejected_and_no_missing_denominator_is_zero():
    kwargs = {
        "approved_protocol": "SYNTHETIC_PROTOCOL",
        "dataset_kind": "SYNTHETIC",
        "validated_reference_ids": {"human-validated-synthetic"},
    }
    with pytest.raises(ValueError):
        reliance_metrics([trial(), trial()], **kwargs)
    result = reliance_metrics([trial(initial_correct=None)], **kwargs)
    row = result["conditions"]["D_DISCUSSION"]
    assert row["correct_ai_adoption"] is None and row["paired_n"] == 0


@pytest.mark.parametrize(
    "reason",
    [
        "INSUFFICIENT_EVIDENCE",
        "OUTSIDE_MODEL_COMPETENCE",
        "NOT_ASSESSABLE",
        "MANUAL_REVIEW_REQUIRED",
    ],
)
def test_abstention_cannot_be_a_negative_judgment(reason):
    data = {
        "kind": "UNVERIFIABLE",
        "description": "No supported assessment",
        "rationale": "Insufficient original evidence",
        "abstention": reason,
    }
    assert AIObservation(judgment="NOT_ASSESSABLE", **data).abstention == reason
    with pytest.raises(ValidationError):
        AIObservation(judgment="NEGATIVE", **data)


def test_human_review_does_not_force_criticism_or_word_count():
    row = CriterionReview(
        criterion_id="methodology",
        judgment="POSITIVE",
        observations="Nachvollziehbar.",
        rationale="Originalbeleg.",
    )
    assert row.weaknesses == "" and row.strengths == ""
