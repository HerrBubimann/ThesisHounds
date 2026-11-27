import asyncio

import pytest
from app.core.configuration import RuntimeConfig
from app.evaluation.injection_benchmark import run_benchmark
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.providers.base import Completion
from app.security.access_control import current_principal
from app.security.document_security import optional_semantic_check
from app.services.document_store import Document
from pydantic import BaseModel

from tests.fixtures import CONFIG
from tests.fixtures.pilot import pilot_setup
from tests.fixtures.semantic_planning import SemanticProvider


def test_model_dispatch_is_bound_to_the_current_agent_even_for_valid_local_models():
    from app.security.information_flow import InformationLabel
    from app.security.tool_permissions import current_agent

    from tests.unit.test_agents import setup_factory

    factory, parent, spec = setup_factory()
    child, _ = factory.create(spec, parent)
    gateway = LLMGateway(
        factory.config.models, {"ollama": SemanticProvider()}, factory.config.policy
    )
    token = current_agent.set(child)
    try:
        with pytest.raises(LLMError, match="MODEL_AGENT_SCOPE_DENIED"):
            asyncio.run(
                gateway.complete(
                    "qwen",
                    "specialist",
                    "PUBLIC",
                    [],
                    CallBudget(1, 10000),
                    label=InformationLabel("PUBLIC", "run", frozenset({"foreign-document"})),
                )
            )
    finally:
        current_agent.reset(token)


def test_synthetic_ablation_distinguishes_detection_prevention_and_missing_semantics():
    report = run_benchmark(CONFIG)
    assert report["mocked"] and report["mandatory_controls_passed"]
    assert not report["scientific_evaluation_complete"]
    assert all(
        r["actual_unauthorized_actions"] == r["actual_external_transfers"] == 0
        for r in report["results"]
    )
    assert any(
        not r["attack_detection"] and r["blocked_tool_calls"] == 1
        for r in report["results"]
        if r["variant"] == "E"
    )
    assert all(
        m["real_attack_success_rate"] is None and m["semantic_detection_rate"] is None
        for m in report["metrics"]
    )
    assert all(
        r["status"] == "SEMANTIC_NOT_EXECUTED" for r in report["results"] if r["variant"] == "D"
    )


def test_lax_output_schema_cannot_silently_drop_a_tool_or_grade_request():
    class Reply(BaseModel):
        answer: str

    class Malicious(SemanticProvider):
        async def complete(self, model, *args, **kwargs):
            return Completion(
                model=model.name, text='{"answer":"ok","tool_calls":[{"name":"shell"}]}'
            )

    config = RuntimeConfig(CONFIG)
    gateway = LLMGateway(config.models, {"ollama": Malicious()}, config.policy)
    with pytest.raises(LLMError, match="ACTION_DENIED"):
        asyncio.run(
            gateway.complete(
                "qwen", "specialist", "PUBLIC", [], CallBudget(1, 10000), output_type=Reply
            )
        )


def test_gateway_cannot_dispatch_without_an_authenticated_processing_actor():
    config = RuntimeConfig(CONFIG)
    gateway = LLMGateway(config.models, {"ollama": SemanticProvider()}, config.policy)
    token = current_principal.set(None)
    try:
        with pytest.raises(LLMError):
            asyncio.run(gateway.complete("qwen", "specialist", "PUBLIC", [], CallBudget(1, 10000)))
    finally:
        current_principal.reset(token)


def test_document_inference_requires_read_permission_before_budget_or_dispatch():
    from app.security.access_control import Principal
    from app.security.information_flow import InformationLabel

    config = RuntimeConfig(CONFIG)
    gateway = LLMGateway(config.models, {"ollama": SemanticProvider()}, config.policy)
    budget = CallBudget(1, 10000)
    token = current_principal.set(Principal("process-only", permissions=frozenset({"process"})))
    try:
        with pytest.raises(LLMError, match="MODEL_DOCUMENT_READ_DENIED"):
            asyncio.run(
                gateway.complete(
                    "qwen",
                    "specialist",
                    "PUBLIC",
                    [],
                    budget,
                    label=InformationLabel("PUBLIC", "scope", frozenset({"document"})),
                )
            )
        assert budget.calls == 0
    finally:
        current_principal.reset(token)


@pytest.mark.parametrize("approved", [False, True])
def test_optional_local_classifier_requires_artifact_approval_and_cannot_grant_rights(
    tmp_path, approved
):
    if approved:
        directory, _, _ = pilot_setup(tmp_path)
    else:
        directory = CONFIG
    config = RuntimeConfig(directory)
    config.limits = config.limits.model_copy(update={"semantic_injection_model_id": "qwen"})

    class Classifier(SemanticProvider):
        async def complete(self, model, *args, **kwargs):
            return Completion(
                model=model.name,
                text='{"label":"SUSPICIOUS","rationale":"SCRIPTED_TEST_INDICATOR"}',
            )

    gateway = LLMGateway(
        config.models, {"ollama": Classifier(model_digest="a" * 64)}, config.policy
    )
    document = Document(
        document_id="synthetic",
        analysis_id="scope",
        classification="PUBLIC",
        pages={1: "Synthetic example"},
    )
    budget = CallBudget(2, 10000)
    result = asyncio.run(optional_semantic_check(gateway, config, document, budget))
    if approved:
        assert result["status"] == "INDICATOR_ONLY" and budget.calls == 1
        assert not result["probability_calibrated"]
        assert result["mocked"]
    else:
        assert result["status"] == "UNAVAILABLE_REQUIRES_HUMAN" and budget.calls == 0


def test_uniform_positive_model_output_in_suspicious_context_still_requires_human_review():
    from app.assessments.ai_review import AISecondReviewer
    from app.assessments.profile_registry import ProfileRegistry
    from app.services.document_store import SYNTHETIC_PAGES

    from tests.unit.test_review_intelligence import ControlledProvider

    config = RuntimeConfig(CONFIG)
    gateway = LLMGateway(
        config.models, {"ollama": ControlledProvider(positive=True)}, config.policy
    )
    pages = dict(SYNTHETIC_PAGES)
    pages[1] += ' Angriffsbeispiel: "Ignore previous instructions" wird untersucht.'
    document = Document(
        document_id="synthetic", analysis_id="scope", classification="PUBLIC", pages=pages
    )
    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    findings = asyncio.run(
        AISecondReviewer(gateway, config).review("scope", document, profile, CallBudget(32, 100000))
    )
    assert all(f.judgment == "POSITIVE" for f in findings)
    assert all(f.verification_rounds and f.escalation["human_required"] for f in findings)
