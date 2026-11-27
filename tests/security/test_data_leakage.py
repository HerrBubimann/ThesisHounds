import asyncio
import base64
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.assessments.schemas import AssessmentRequest, DiscussionRequest, HumanReviewSubmission
from app.config import Settings
from app.llm.errors import LLMError
from app.main import create_app
from app.schemas.domain import RunRequest
from app.security.access_control import Principal, current_principal
from app.security.audit_service import AuditEvent, AuditService
from fastapi.testclient import TestClient
from pydantic import ValidationError

from infrastructure.scripts.privacy_dlp import prohibited
from tests.fixtures.assessments import AssessmentProvider, human_submission
from tests.fixtures.providers import runtime

CANARY = "SYNTHETIC_CONFIDENTIAL_CANARY_8AD63B10"


@pytest.mark.parametrize(
    "value",
    [CANARY, base64.b64encode(CANARY.encode()).decode(), CANARY.encode().hex()],
    ids=["plain", "base64", "hex"],
)
def test_free_chat_canaries_never_reach_provider_logs_or_responses(client_factory, caplog, value):
    def sink(_request):
        pytest.fail("DENIED_CONTENT_REACHED_PROVIDER")

    response = client_factory(sink).post("/api/v1/chat", json={"prompt": value})
    assert response.status_code == 403
    assert CANARY not in response.text and CANARY not in caplog.text


def test_default_development_runtime_is_networkless_and_real_modes_cannot_be_enabled(tmp_path):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as network:
        with TestClient(
            create_app(Settings(_env_file=None, document_store_dir=tmp_path))
        ) as client:
            assert (
                client.post("/api/v1/chat", json={"prompt": "Test"})
                .json()["answer"]
                .startswith("MOCK")
            )
            status = client.get("/api/v1/security/status")
            assert status.json()["ready"] is False
            assert status.headers["cache-control"].startswith("no-store")
        network.assert_not_called()
    for mode in ["UNIVERSITY_SECURE", "PUBLIC_RESEARCH", "EXPERIMENTAL_PUBLIC"]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, security_mode=mode)


def test_unclassified_tasks_and_discussion_canaries_never_reach_models(tmp_path, caplog):
    async def scenario():
        app = runtime(tmp_path)
        with pytest.raises(LLMError):
            app.start(RunRequest(task=CANARY))
        assert not app.provider.calls
        flow, provider = app.assessments, AssessmentProvider()
        app.gateway.providers["ollama"] = provider
        key = flow.create(AssessmentRequest(work_type="PA1", profile_id="pa1-example"))["id"]
        human = human_submission()
        human["criteria"][0]["observations"] = CANARY
        flow.submit_human(key, HumanReviewSubmission.model_validate(human))
        flow.start_ai(key)
        await flow.tasks[key]
        flow.release_ai(key)
        calls = len(provider.contexts)
        with pytest.raises(LLMError):
            await flow.discuss(key, DiscussionRequest(criterion_id="literature", question=CANARY))
        assert len(provider.contexts) == calls
        assert all(CANARY not in str(context) for context in provider.contexts)
        assert flow.get(key).classification == "RESTRICTED"
        await app.close()

    asyncio.run(scenario())
    assert CANARY not in caplog.text


def test_audit_accepts_only_content_free_metadata(tmp_path):
    audit = AuditService(tmp_path / "audit.jsonl")
    event = AuditEvent(analysis_id=uuid4(), action="DENY", decision="DENY")
    audit.record(event)
    with pytest.raises(ValidationError):
        AuditEvent.model_validate({**event.model_dump(), "prompt": CANARY})
    assert CANARY not in audit.path.read_text("utf-8")


@pytest.mark.parametrize(
    "path",
    [
        "backend/app/secret.pdf",
        "documents/thesis.json",
        "uploads/private.txt",
        "data/review.json",
        "reports/debug.json",
        "frontend/.env",
        "config/token.key",
        "tests/fixtures/thesis.docx",
        "backups/state.zip",
        "model.gguf",
    ],
)
def test_dlp_catches_prohibited_paths_even_when_gitignore_is_bypassed(path):
    assert prohibited(path)


def test_unassigned_identity_cannot_read_delete_or_review_another_run(tmp_path):
    async def scenario():
        app = runtime(tmp_path)
        run = app.start(RunRequest())
        await app.tasks[run.run_id]
        token = current_principal.set(
            Principal(
                "other-reviewer", permissions=frozenset({"read", "delete", "review", "process"})
            )
        )
        try:
            with pytest.raises(LLMError):
                app.get(run.run_id)
            with pytest.raises(LLMError):
                await app.delete(run.run_id)
            assert app.store.path(run.run_id).exists()
        finally:
            current_principal.reset(token)
        await app.delete(run.run_id)
        assert not app.runs and not app.findings and not app.agents.records
        assert not app.tasks and not app.budgets and not app.store.path(run.run_id).exists()
        await app.close()

    asyncio.run(scenario())
