"""Backend <-> Ollama provider over real HTTP against the CI mock service (no model, no GPU)."""

import threading
from collections.abc import Iterator
from unittest.mock import patch

import pytest
from app.config import Settings
from app.llm.providers.ollama import OllamaProvider
from app.main import create_app
from app.security.egress_policy import ENDPOINTS
from fastapi.testclient import TestClient

from tests.fixtures import CONFIG
from tests.fixtures.mock_ollama import CHAT_ANSWER, create_server


@pytest.fixture
def mock_ollama(monkeypatch) -> Iterator[str]:
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Explicitly authorize only this controlled mock listener for this test.
    monkeypatch.setitem(
        ENDPOINTS, ("http", "127.0.0.1", server.server_address[1]), frozenset({"127.0.0.1"})
    )
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def test_end_to_end_over_http_with_mock_service(mock_ollama, tmp_path) -> None:
    settings = Settings(
        _env_file=None,
        ollama_base_url=mock_ollama,
        config_dir=CONFIG,
        document_store_dir=tmp_path / "documents",
    )
    application = create_app(settings)
    with (
        patch("app.main.create_provider", side_effect=OllamaProvider),
        TestClient(application) as client,
    ):
        status = client.get("/api/v1/status").json()
        assert status["ollama"] == "available" and status["model_available"], status
        chat = client.post("/api/v1/chat", json={"prompt": "Test"})
        assert chat.status_code == 200 and chat.json()["answer"] == CHAT_ANSWER
        models = client.get("/api/v1/models/status").json()["models"]
        assert {m["availability"] for m in models} == {"available"}

        created = client.post("/api/v1/runs", json={"mode": "D"})
        assert created.status_code == 202
        run_id = created.json()["run_id"]

        async def wait() -> None:
            await application.state.runtime.tasks[run_id]

        client.portal.call(wait)
        run = client.get(f"/api/v1/runs/{run_id}").json()
        assert run["status"] == "WAITING_FOR_REVIEW", run["error"]
        assert run["findings_count"] > 0 and run["final_report"] is None
        graph = client.get(f"/api/v1/runs/{run_id}/graph").json()
        assert sum(node["dynamic"] for node in graph["nodes"]) == 2


def test_unknown_model_is_reported_unavailable(mock_ollama, tmp_path) -> None:
    settings = Settings(
        _env_file=None,
        ollama_base_url=mock_ollama,
        llm_model="unknown:1b",
        config_dir=CONFIG,
        document_store_dir=tmp_path / "documents",
    )
    with (
        patch("app.main.create_provider", side_effect=OllamaProvider),
        TestClient(create_app(settings)) as client,
    ):
        status = client.get("/api/v1/status").json()
        assert status["ollama"] == "available" and not status["model_available"]
        assert client.post("/api/v1/chat", json={"prompt": "Test"}).status_code == 503
