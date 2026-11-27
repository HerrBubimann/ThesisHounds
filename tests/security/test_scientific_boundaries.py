import asyncio
from uuid import uuid4

import pytest
from app.assessments.adversarial_verification import verify_finding
from app.assessments.ai_review import AISecondReviewer
from app.assessments.profile_registry import ProfileRegistry
from app.assessments.schemas import AssessmentFinding, AssessmentRequest
from app.core.configuration import RuntimeConfig
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.services.document_intelligence import structure_document
from app.services.document_store import Document

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider


def test_verification_inherits_confidential_taint_even_for_a_public_document():
    async def scenario():
        config, provider = RuntimeConfig(CONFIG), AssessmentProvider()
        gateway = LLMGateway(config.models, {"ollama": provider}, config.policy)
        key = str(uuid4())
        document = Document(
            document_id="synthetic",
            analysis_id=key,
            classification="PUBLIC",
            pages={1: "Synthetic text"},
        )
        finding = AssessmentFinding(
            assessment_id=key,
            criterion_id="methodology",
            category="methodology",
            model_id="qwen",
            manufacturer="Alibaba",
            agent_id="synthetic",
            judgment="NEGATIVE",
            kind="WEAKNESS",
            description="SYNTHETIC private observation",
            rationale="Synthetic rationale",
            data_classification="RESTRICTED",
            page=1,
            quote="Synthetic text",
        )
        available = {m.name: m.digest for m in await provider.discover()}
        await verify_finding(
            gateway,
            config,
            finding,
            document,
            structure_document(document),
            CallBudget(2, 10000),
            available,
        )
        assert not provider.contexts and finding.data_classification == "RESTRICTED"
        assert finding.verification_status == "UNAVAILABLE"

    asyncio.run(scenario())


def test_private_catalog_is_not_disclosed_by_the_development_create_route(tmp_path):
    from tests.fixtures.providers import runtime

    app = runtime(tmp_path)
    app.assessments.profiles.profiles["pa1-example"].data_classification = "RESTRICTED"
    with pytest.raises(LLMError):
        app.assessments.create(AssessmentRequest(work_type="PA1", profile_id="pa1-example"))
    assert not app.assessments.records and not app.provider.calls


def test_private_rubric_cannot_be_declassified_by_a_public_document():
    async def scenario():
        config, provider = RuntimeConfig(CONFIG), AssessmentProvider()
        gateway = LLMGateway(config.models, {"ollama": provider}, config.policy)
        profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
        profile.data_classification = "RESTRICTED"
        key = str(uuid4())
        document = Document(
            document_id="synthetic",
            analysis_id=key,
            classification="PUBLIC",
            pages={1: "Synthetic public text"},
        )
        with pytest.raises(LLMError):
            await AISecondReviewer(gateway, config).review(
                key, document, profile, CallBudget(20, 100000)
            )
        assert not provider.contexts

    asyncio.run(scenario())
