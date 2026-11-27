"""Review mutations must be confined to the explicitly selected run."""

from unittest.mock import patch
from uuid import uuid4

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

from tests.fixtures import CONFIG
from tests.fixtures.providers import WorkflowProvider


def test_review_endpoint_rejects_cross_run_and_unscoped_finding_ids(tmp_path):
    application = create_app(
        Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path / "documents")
    )
    with (
        patch("app.main.create_provider", return_value=WorkflowProvider()),
        TestClient(application) as client,
    ):
        run_ids = []
        for _ in range(2):
            response = client.post("/api/v1/runs", json={"mode": "A"})
            assert response.status_code == 202
            run_id = response.json()["run_id"]

            async def wait(run_id=run_id):
                await application.state.runtime.tasks[run_id]

            client.portal.call(wait)
            run_ids.append(run_id)
        first, second = run_ids
        first_path, second_path = (f"/api/v1/runs/{key}" for key in run_ids)
        original_runs = [client.get(path).json() for path in [first_path, second_path]]
        original_findings = [
            client.get(path + "/findings").json() for path in [first_path, second_path]
        ]
        first_finding, second_finding = (items[0]["finding_id"] for items in original_findings)
        review = {"decision": "ACCEPTED", "edited_statement": "Reviewed only within its run"}
        for run_id, finding_id in [(first, second_finding), (second, first_finding)]:
            response = client.post(
                f"/api/v1/runs/{run_id}/findings/{finding_id}/review", json=review
            )
            assert response.status_code == 404
            assert "statement" not in response.json()
        for run_id, finding_id, expected in [
            (str(uuid4()), first_finding, 404),
            (first, str(uuid4()), 404),
            ("invalid", first_finding, 422),
            (first, "invalid", 422),
        ]:
            assert (
                client.post(
                    f"/api/v1/runs/{run_id}/findings/{finding_id}/review", json=review
                ).status_code
                == expected
            )
        # Removing the old route prevents it remaining as an unscoped bypass.
        assert (
            client.post(f"/api/v1/findings/{first_finding}/review", json=review).status_code == 404
        )
        for index, path in enumerate([first_path, second_path]):
            assert client.get(path).json() == original_runs[index]
            assert client.get(path + "/findings").json() == original_findings[index]

        response = client.post(first_path + f"/findings/{first_finding}/review", json=review)
        assert response.status_code == 200
        assert response.json()["run_id"] == first
        assert response.json()["statement"] == review["edited_statement"]
        assert client.get(first_path).json()["status"] == "COMPLETED"
        assert client.get(second_path).json() == original_runs[1]
        assert client.get(second_path + "/findings").json() == original_findings[1]
