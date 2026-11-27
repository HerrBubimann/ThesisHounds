from unittest.mock import patch

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from frontend.api_client import BackendError, request_backend
from frontend.control_center import render_tree
from tests.fixtures import MODEL, ROOT

APP_PATH = ROOT / "frontend/app.py"


def test_dashboard_and_chat() -> None:
    def backend(method, path, **kwargs):
        if path == "/health":
            return {"status": "ok"}
        if path == "/api/v1/status":
            return {
                "ollama": "available",
                "model": "qwen3:8b",
                "model_available": True,
                "detail": "Bereit",
            }
        if path == "/api/v1/models":
            return {"models": [MODEL]}
        if path == "/api/v1/models/status":
            return {"models": []}
        if path == "/api/v1/system/resources":
            return {
                "privacy_mode": "LOCAL_ONLY",
                "cpu_percent": 0,
                "ram_available_bytes": 1024,
                "active_agents": 0,
            }
        if path == "/api/v1/runs":
            return []
        assert method == "POST"
        assert kwargs["json"]["prompt"] == "Test"
        return {"model": "qwen3:8b", "answer": "Testantwort"}

    with (
        patch("frontend.api_client.request_backend", side_effect=backend),
        patch("frontend.control_center.request_backend", side_effect=backend),
    ):
        app = AppTest.from_file(APP_PATH, default_timeout=10).run()
        assert not app.exception
        assert app.title[0].value == "ThesisHounds"
        assert app.text_area[0].disabled and app.text_area[0].value == "Test"
        app.button[1].click().run()
        assert not app.exception
        assert app.text[0].value == "Testantwort"


def test_dashboard_when_backend_is_down() -> None:
    with patch(
        "frontend.api_client.request_backend", side_effect=BackendError("Backend nicht erreichbar")
    ):
        app = AppTest.from_file(APP_PATH, default_timeout=10).run()
        assert not app.exception
        assert app.error[0].value == "Backend nicht erreichbar"
        assert app.button[1].disabled


def test_frontend_client_sanitizes_upstream_errors() -> None:
    with patch("httpx.Client.send", return_value=httpx.Response(503, text="PRIVATE_UPSTREAM")):
        with pytest.raises(BackendError) as error:
            request_backend("GET", "/api/v1/models")
        assert "PRIVATE_UPSTREAM" not in str(error.value)


def test_control_center_displays_mock_run_and_graph():
    from app.schemas.domain import AgentRecord, RunRecord

    run = RunRecord(
        mode="D", document_id="synthetic-demo", criteria=["Test"], mocked=True
    ).model_dump(mode="json")
    node = AgentRecord(
        agent_id="test",
        run_id=run["run_id"],
        name="Master",
        role="orchestrator",
        model_id="qwen",
        manufacturer="Alibaba",
        task="Test",
    ).model_dump(mode="json")

    def backend(method, path, **kwargs):
        if path == "/api/v1/models/status":
            return {"models": []}
        if path == "/api/v1/system/resources":
            return {
                "privacy_mode": "LOCAL_ONLY",
                "cpu_percent": 0,
                "ram_available_bytes": 1024,
                "active_agents": 0,
            }
        if path == "/api/v1/runs":
            return [run] if method == "GET" else run
        if path.endswith("/graph"):
            return {"nodes": [node], "edges": []}
        if path.endswith("/findings"):
            return []
        return run

    with patch("frontend.control_center.request_backend", side_effect=backend):
        app = AppTest.from_string(
            "from frontend.control_center import render_control_center\nrender_control_center()"
        ).run()
        assert not app.exception
        assert any("MOCK-DATEN" in warning.value for warning in app.warning)
        assert app.get("graphviz_chart")
    dot = render_tree([{**node, "name": "PRIVATE_DOT_INJECTION", "role": "bad;role"}], [])
    assert "PRIVATE_DOT_INJECTION" not in dot and "bad;role" not in dot


@pytest.mark.parametrize("decision", ["ACCEPTED", "REJECTED"])
def test_finding_review_requires_explicit_decision_and_uses_run_endpoint(decision):
    from app.schemas.domain import Finding, RunRecord

    run = RunRecord(
        mode="D",
        document_id="synthetic-demo",
        criteria=["Methodik"],
        status="WAITING_FOR_REVIEW",
    ).model_dump(mode="json")
    finding = Finding(
        run_id=run["run_id"],
        agent_id="synthetic",
        model_id="qwen",
        model="qwen3:8b",
        manufacturer="Alibaba",
        category="methodology",
        kind="STRENGTH",
        statement="Synthetic finding",
        rationale="Synthetic rationale",
        page=1,
        quote="Synthetic quotation",
    ).model_dump(mode="json")
    with patch("frontend.control_center.request_backend", return_value=finding) as backend:
        app = AppTest.from_string(
            "from frontend.control_center import render_finding\n"
            f"render_finding({finding!r}, {run!r})"
        ).run()
        assert not app.exception and app.selectbox[0].value is None
        app.button[0].click().run()
        assert not app.exception and app.warning
        backend.assert_not_called()
        app.selectbox[0].select(decision)
        app.text_area[0].set_value("Human correction")
        app.text_input[0].set_value("Human rationale")
        app.button[0].click().run()
        assert not app.exception
        backend.assert_called_once_with(
            "POST",
            f"/api/v1/runs/{run['run_id']}/findings/{finding['finding_id']}/review",
            json={
                "decision": decision,
                "note": "Human rationale",
                "edited_statement": "Human correction",
            },
        )
