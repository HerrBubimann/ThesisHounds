import hashlib

import pytest
from app.core.configuration import RuntimeConfig
from app.llm.errors import LLMError
from app.llm.model_router import ModelRouter, ResourceBudget

from tests.fixtures import CONFIG


def router(records=()):
    config = RuntimeConfig(CONFIG)
    available = {m.name: hashlib.sha256(m.id.encode()).hexdigest() for m in config.models.enabled()}
    return ModelRouter(config.models, config.policy, records), available


def evidence(**overrides):
    return {
        "model_id": "llama",
        "model_digest": hashlib.sha256(b"llama").hexdigest(),
        "benchmark_version": "synthetic-test",
        "dataset_sha256": "a" * 64,
        "prompt_sha256": "b" * 64,
        "hardware_id": "synthetic-host",
        "evidence_id": "synthetic-reviewed-record",
        "reviewed_by": "synthetic-operator",
        "measured_at": "2026-11-26",
        "mocked": False,
        "scores": {"argumentation": 0.8},
        **overrides,
    }


def test_manual_default_is_explicit_when_no_real_measurements_exist():
    selection, available = router()
    value = selection.select("argumentation", "content", "PUBLIC", available, "qwen")
    assert value.model_id == "qwen" and value.source == "MANUAL_DEFAULT"
    assert value.evidence_id is None and not value.resources_verified


@pytest.mark.parametrize(
    "change", [{"mocked": True}, {"model_digest": "f" * 64}, {"scores": {"formal": 1.0}}]
)
def test_mock_stale_or_wrong_task_records_cannot_determine_routing(change):
    selection, available = router([evidence(**change)])
    assert (
        selection.select("argumentation", "content", "PUBLIC", available, "qwen").source
        == "MANUAL_DEFAULT"
    )


def test_reviewed_task_evidence_only_applies_to_the_exact_available_digest():
    selection, available = router([evidence()])
    value = selection.select("argumentation", "content", "PUBLIC", available, "qwen")
    assert value.model_id == "llama" and value.source == "MEASURED"
    assert value.evidence_id == "synthetic-reviewed-record"
    available.pop("llama3.1:8b")
    assert (
        selection.select("argumentation", "content", "PUBLIC", available, "qwen").model_id == "qwen"
    )


@pytest.mark.parametrize(
    "classification", [None, "UNKNOWN", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]
)
def test_capability_scores_never_override_privacy(classification):
    selection, available = router([evidence(scores={"argumentation": 1.0})])
    with pytest.raises(LLMError):
        selection.select("argumentation", "content", classification, available, "llama")


def test_resource_limits_and_independent_manufacturers_are_hard_constraints():
    selection, available = router()
    with pytest.raises(LLMError):
        selection.select(
            "methodology",
            "specialist",
            "PUBLIC",
            available,
            "mistral",
            resources=ResourceBudget(ram_gib=0, vram_gib=0),
        )
    value = selection.select(
        "evidence",
        "reviewer",
        "PUBLIC",
        available,
        "qwen",
        exclude_manufacturers=frozenset({"Alibaba"}),
    )
    assert value.model_id != "qwen"


def test_ambiguous_or_invalid_evidence_is_rejected():
    for records in ([evidence(), evidence()], [evidence(scores={"argumentation": float("nan")})]):
        with pytest.raises(ValueError):
            router(records)


def test_partial_skill_evidence_does_not_claim_measured_multiskill_routing():
    selection, available = router([evidence(scores={"methodology": 1.0})])
    result = selection.select(
        "methodology",
        "specialist",
        "PUBLIC",
        available,
        "mistral",
        required_tasks=("methodology", "evidence"),
    )
    assert result.source == "MANUAL_DEFAULT" and result.model_id == "mistral"


def test_multiskill_routing_requires_measurements_for_every_requested_task():
    selection, available = router([evidence(scores={"methodology": 0.8, "evidence": 0.7})])
    result = selection.select(
        "methodology",
        "specialist",
        "PUBLIC",
        available,
        "mistral",
        required_tasks=("methodology", "evidence"),
    )
    assert result.source == "MEASURED" and result.model_id == "llama"
