import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from app.assessments.schemas import AssessmentRequest
from app.config import Settings
from app.llm.errors import LLMError
from app.main import create_app
from app.schemas.domain import RunRequest
from app.security.access_control import Principal, current_principal
from fastapi.testclient import TestClient

from frontend.api_client import BackendError, request_backend
from tests.fixtures.providers import runtime


def test_unauthorized_create_has_no_document_or_assessment_side_effect(tmp_path):
    app = runtime(tmp_path)
    token = current_principal.set(Principal("read-only", permissions=frozenset({"read"})))
    try:
        with pytest.raises(LLMError):
            app.start(RunRequest())
        with pytest.raises(LLMError):
            app.assessments.create(
                AssessmentRequest(work_type="PA1", profile_confirmed=True, profile_id="pa1-example")
            )
        assert not app.runs and not app.assessments.records
        assert not app.store.root.exists()
    finally:
        current_principal.reset(token)


def test_default_mock_supports_full_synthetic_analysis_without_http_calls(tmp_path):
    application = create_app(Settings(_env_file=None, document_store_dir=tmp_path))
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as outgoing:
        with TestClient(application) as client:
            run = client.post("/api/v1/runs", json={"mode": "D"}).json()

            async def wait():
                await application.state.runtime.tasks[run["run_id"]]

            client.portal.call(wait)
            result = client.get("/api/v1/runs/" + run["run_id"]).json()
            assert result["mocked"] and result["status"] == "WAITING_FOR_REVIEW"
            assert result["data_classification"] == "PUBLIC"
            assert client.delete("/api/v1/runs/" + run["run_id"]).status_code == 204
            record = client.post(
                "/api/v1/assessments",
                json={"work_type": "PA1", "profile_confirmed": True, "profile_id": "pa1-example"},
            ).json()
            path = "/api/v1/assessments/" + record["id"]
            assert client.post(path + "/ai-review").status_code == 202

            async def wait_assessment():
                await application.state.runtime.assessments.tasks[record["id"]]

            client.portal.call(wait_assessment)
            assert client.get(path).json()["ai_state"] == "COMPLETED"
            assert client.delete(path).status_code == 204
            assert client.get(path).status_code == 404
        outgoing.assert_not_called()


@pytest.mark.parametrize(
    "target",
    [
        "https://external.invalid",
        "http://external.invalid:8000",
        "http://backend:8001",
        "http://user:secret@backend:8000",
        "http://backend:8000/private",
    ],
)
def test_frontend_cannot_send_content_to_an_unapproved_backend(monkeypatch, target):
    monkeypatch.setenv("BACKEND_URL", target)
    with patch("httpx.Client.request") as outgoing:
        with pytest.raises(BackendError):
            request_backend("POST", "/api/v1/chat", json={"prompt": "SYNTHETIC_CANARY"})
        outgoing.assert_not_called()


def test_shutdown_clears_all_document_derived_process_state(tmp_path):
    async def scenario():
        app = runtime(tmp_path)
        run = app.start(RunRequest())
        await app.tasks[run.run_id]
        await app.close()
        assert not any((app.runs, app.findings, app.budgets, app.tasks, app.agents.records))
        assert not app.access.assignments and not app.store.path(run.run_id).exists()

    asyncio.run(scenario())
