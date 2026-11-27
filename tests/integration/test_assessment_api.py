import json
from unittest.mock import patch

import pytest
from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider, human_submission

BASE = "/api/v1/assessments"


@pytest.mark.parametrize("human_first", [True, False])
def test_independent_reviews_comparison_discussion_and_finalization(tmp_path, human_first):
    provider = AssessmentProvider()
    application = create_app(
        Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path)
    )
    with (
        patch("app.main.create_provider", return_value=provider),
        TestClient(application) as client,
    ):
        assert len(client.get(BASE + "/profiles").json()) == 3
        response = client.post(BASE, json={"work_type": "PA1", "profile_id": "ba-example"})
        assert response.status_code == 422
        record = client.post(BASE, json={"work_type": "PA1", "profile_id": "pa1-example"}).json()
        path, key = BASE + "/" + record["id"], record["id"]
        assert client.get(path + "/document").json()["classification"] == "PUBLIC"
        for suffix in ["/comparison", "/draft"]:
            assert client.get(path + suffix).status_code == 409
        assert client.post(path + "/release", json={"confirmed": True}).status_code == 409
        assert client.post(path + "/release", json={"confirmed": False}).status_code == 422
        invalid = human_submission()
        invalid["criteria"].pop()
        assert client.post(path + "/human-review", json=invalid).status_code == 422
        duplicate = human_submission()
        duplicate["criteria"][0] = duplicate["criteria"][1]
        assert client.post(path + "/human-review", json=duplicate).status_code == 422
        human = human_submission()
        if human_first:
            assert client.post(path + "/human-review", json=human).status_code == 200
        assert client.post(path + "/ai-review").status_code == 202

        async def wait():
            await application.state.runtime.assessments.tasks[key]

        client.portal.call(wait)
        assert client.post(path + "/ai-review").status_code == 409
        assert client.get(path).json()["ai_state"] == "COMPLETED"
        # Sweep every old generic list/status/output route for a disclosure bypass.
        for route in [path, "/api/v1/runs", "/api/v1/agents", "/api/v1/system/resources"]:
            content = client.get(route).text
            assert "AI_EMBARGO_MARKER" not in content
            assert "HUMAN_PRIVATE_MARKER" not in content
        assert client.get(f"/api/v1/runs/{key}/findings").status_code == 404
        if not human_first:
            assert client.post(path + "/release", json={"confirmed": True}).status_code == 409
            assert client.post(path + "/human-review", json=human).status_code == 200
        # Independent AI prompts never contain a human first review.
        assert "HUMAN_PRIVATE_MARKER" not in json.dumps(provider.contexts)
        # Three mandatory calls, one controlled topic supplement and four adversarial reviews.
        assert len(provider.contexts) == 8
        assert (
            sum("adversarial academic verifier" in c[0]["content"] for c in provider.contexts) == 4
        )
        assert client.get(path + "/comparison").status_code == 409
        assert client.post(path + "/release", json={"confirmed": True}).status_code == 200
        before = client.get(path + "/comparison").json()
        assert all(row["status"] == "AGREEMENT" for row in before["criteria"])
        assert client.post(path + "/human-review", json=human).status_code == 409
        assert client.get(path + "/draft").status_code == 409
        decision = {
            "criterion_id": "literature",
            "include_ai_finding": False,
            "conclusion": "Menschliche Schlussfolgerung",
            "rationale": "Begründung",
        }
        assert client.post(path + "/decisions", json=decision).status_code == 409
        question = {"criterion_id": "unknown", "question": "Welche Gegenargumente gibt es?"}
        assert client.post(path + "/discussion", json=question).status_code == 422
        question["criterion_id"] = "literature"
        calls_before = len(provider.contexts)
        assert client.post(path + "/discussion", json=question).status_code == 403
        assert len(provider.contexts) == calls_before
        assert client.post(path + "/manual-review", json={"confirmed": True}).status_code == 200
        for row in before["criteria"]:
            decision["criterion_id"] = row["criterion_id"]
            assert client.post(path + "/decisions", json=decision).status_code == 200
        # Revisions append instead of changing first reviews or older decisions.
        decision["conclusion"] = "Korrigierte menschliche Schlussfolgerung"
        assert client.post(path + "/decisions", json=decision).status_code == 200
        after = client.get(path + "/comparison").json()

        def without_approval(value):
            if isinstance(value, dict):
                return {k: without_approval(v) for k, v in value.items() if k != "human_approval"}
            if isinstance(value, list):
                return [without_approval(v) for v in value]
            return value

        assert without_approval(before["criteria"]) == without_approval(after["criteria"])
        assert all(row["ai"]["human_approval"] == "REJECTED" for row in after["criteria"])
        assert len(after["decisions"]) == 4
        draft = client.get(path + "/draft").json()
        assert draft["label"] == "Gutachtenentwurf"
        assert "AI_EMBARGO_MARKER" not in draft["text"]
        assert "MOCK:" not in draft["text"]  # Discussion output is not a released finding.
        assert client.post(path + "/finalize", json={"confirmed": True}).status_code == 200
        assert client.get(path).json()["state"] == "FINALIZED"
        assert client.post(path + "/decisions", json=decision).status_code == 409
        assert client.post(path + "/discussion", json=question).status_code == 409


def test_invalid_model_output_fails_closed(tmp_path):
    app = create_app(Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path))
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider(fail=True)),
        TestClient(app) as client,
    ):
        record = client.post(BASE, json={"work_type": "BA", "profile_id": "ba-example"}).json()
        key, path = record["id"], BASE + "/" + record["id"]
        assert client.post(path + "/ai-review").status_code == 202

        async def wait():
            await app.state.runtime.assessments.tasks[key]

        client.portal.call(wait)
        assert client.get(path).json()["state"] == "FAILED"
        assert client.post(path + "/release", json={"confirmed": True}).status_code == 409
        assert client.get(path + "/comparison").status_code == 409
        assert not app.state.runtime.assessments.get(key).ai


def test_cancellation_and_shared_active_run_limit(tmp_path):
    from app.schemas.domain import RunRequest

    app = create_app(Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path))
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider(delay=30)),
        TestClient(app) as client,
    ):
        record = client.post(BASE, json={"work_type": "BA", "profile_id": "ba-example"}).json()
        path = BASE + "/" + record["id"]
        assert client.post(path + "/ai-review").status_code == 202
        assert client.post("/api/v1/runs", json=RunRequest().model_dump()).status_code == 429
        assert client.post(path + "/cancel").status_code == 200
        assert client.get(path).json()["state"] == "CANCELLED"
        assert client.post(path + "/human-review", json=human_submission()).status_code == 409
        assert client.post(path + "/ai-review").status_code == 409
