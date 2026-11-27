from unittest.mock import patch

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

from tests.fixtures import CONFIG
from tests.fixtures.providers import WorkflowProvider


def test_control_api_run_graph_findings_and_human_review(tmp_path):
    application = create_app(
        Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path / "documents")
    )
    with (
        patch("app.main.create_provider", return_value=WorkflowProvider()),
        TestClient(application) as client,
    ):
        application.state.runtime.mocked = True
        assert len(client.get("/api/v1/models/status").json()["models"]) == 3
        assert client.get("/api/v1/system/resources").json()["privacy_mode"] == "LOCAL_ONLY"
        definitions = client.get("/api/v1/agents").json()["definitions"]
        assert len(definitions["supervisors"]) == 3
        response = client.post("/api/v1/runs", json={"mode": "D"})
        assert response.status_code == 202
        run_id = response.json()["run_id"]

        async def wait():
            await application.state.runtime.tasks[run_id]

        client.portal.call(wait)
        run = client.get(f"/api/v1/runs/{run_id}").json()
        assert run["status"] == "WAITING_FOR_REVIEW", run["error"]
        assert run["mocked"] is True and run["final_report"] is None
        assert all(model["digest"] == "MOCK" for model in run["model_snapshot"])
        graph = client.get(f"/api/v1/runs/{run_id}/graph").json()
        assert len([n for n in graph["nodes"] if n["dynamic"]]) == 2
        assert len(graph["edges"]) == len(graph["nodes"]) - 1
        assert client.get(f"/api/v1/agents/{graph['nodes'][0]['agent_id']}").status_code == 200
        findings = client.get(f"/api/v1/runs/{run_id}/findings").json()
        for index, finding in enumerate(findings):
            response = client.post(
                f"/api/v1/runs/{run_id}/findings/{finding['finding_id']}/review",
                json={"decision": "ACCEPTED" if index == 0 else "REJECTED"},
            )
            assert response.status_code == 200
        final = client.get(f"/api/v1/runs/{run_id}").json()
        assert final["status"] == "COMPLETED"
        assert final["final_report"] and "MOCK-Entwurf" not in final["final_report"]
        assert len(client.get("/api/v1/runs").json()) == 1
        assert client.get("/api/v1/agents/not-found").status_code == 404
        response = client.post(
            "/api/v1/runs",
            json={
                "classification": "PUBLIC",
                "document_id": "SECRET.pdf",
                "prompt": "PRIVATE_VALUE",
            },
        )
        assert response.status_code == 422 and "PRIVATE_VALUE" not in response.text


def test_api_cancellation(tmp_path):
    application = create_app(
        Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path / "documents")
    )
    with (
        patch("app.main.create_provider", return_value=WorkflowProvider(delay=60)),
        TestClient(application) as client,
    ):
        run = client.post("/api/v1/runs", json={}).json()
        response = client.post(f"/api/v1/runs/{run['run_id']}/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "CANCELLED"
