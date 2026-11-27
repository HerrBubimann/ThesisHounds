import asyncio
from unittest.mock import patch

import pytest
from app.assessments.ai_review import AISecondReviewer
from app.assessments.profile_registry import ProfileRegistry
from app.core.configuration import RuntimeConfig
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.services.document_store import SYNTHETIC_PAGES, Document

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider


@pytest.mark.parametrize("classification", ["INTERNAL", "CONFIDENTIAL", "RESTRICTED", None])
def test_private_retrieval_never_opens_a_model_or_external_fallback(classification):
    provider = AssessmentProvider()
    config = RuntimeConfig(CONFIG)
    gateway = LLMGateway(config.models, {"ollama": provider}, config.policy)
    doc = Document(
        document_id="synthetic",
        analysis_id="scope",
        classification=classification,
        pages=dict(SYNTHETIC_PAGES),
        complete=True,
    )
    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    with patch("socket.getaddrinfo", side_effect=AssertionError("Network forbidden")):
        with pytest.raises(LLMError):
            asyncio.run(
                AISecondReviewer(gateway, config).review(
                    "scope", doc, profile, CallBudget(32, 100000)
                )
            )
    assert not provider.contexts


def test_new_feedback_and_provenance_are_not_a_disclosure_bypass(tmp_path):
    from tests.integration.test_finding_feedback import assessment, feedback

    with assessment(tmp_path, release=False) as (app, client, path, key, provider):
        identifier = app.state.runtime.assessments.records[key].ai[0].finding_id
        for suffix in ("/provenance", "/comparison"):
            response = client.get(path + suffix)
            assert response.status_code == 409
            assert "AI_EMBARGO_MARKER" not in response.text
        assert client.post(path + "/finding-feedback", json=feedback(identifier)).status_code == 409
        assert "SYNTHETIC_FEEDBACK_ONLY" not in str(provider.contexts)
