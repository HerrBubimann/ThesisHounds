from unittest.mock import patch
from uuid import uuid4

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider, human_submission


def test_evidence_is_scoped_embargoed_and_selectively_human_approved(tmp_path):
    application = create_app(
        Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path)
    )
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider()),
        TestClient(application) as client,
    ):
        key = client.post(
            "/api/v1/assessments",
            json={"work_type": "PA1", "profile_confirmed": True, "profile_id": "pa1-example"},
        ).json()["id"]
        path = "/api/v1/assessments/" + key
        client.post(path + "/ai-review")

        async def wait():
            await application.state.runtime.assessments.tasks[key]

        client.portal.call(wait)
        finding = application.state.runtime.assessments.get(key).ai[0]
        route = path + "/findings/" + finding.finding_id + "/evidence"
        assert client.get(route).status_code == 409
        client.post(path + "/human-review", json=human_submission())
        client.post(path + "/release", json={"confirmed": True})
        response = client.get(route)
        data = response.json()
        assert data["matched"] and data["quote"] in data["original_text"]
        assert data["page"] == 2 and data["chapter"] == "Methodik"
        assert data["finding"]["reviewer_model"] != data["finding"]["model_id"]
        assert data["finding"]["human_approval"] == "PENDING"
        assert response.headers["cache-control"].startswith("no-store")
        assert client.get(path + "/findings/" + str(uuid4()) + "/evidence").status_code == 404
        client.post(path + "/manual-review", json={"confirmed": True})
        decision = {
            "criterion_id": "literature",
            "include_ai_finding": True,
            "conclusion": "Synthetic human conclusion",
            "rationale": "Synthetic human rationale",
        }
        assert (
            client.post(
                path + "/decisions", json={**decision, "include_finding_ids": [str(uuid4())]}
            ).status_code
            == 422
        )
        assert client.post(path + "/decisions", json=decision).status_code == 200
        assert client.get(route).json()["finding"]["human_approval"] == "ACCEPTED"


def test_streamlit_navigates_from_finding_to_a_verified_original_span(tmp_path):
    from tests.integration.test_finding_feedback import assessment

    with assessment(tmp_path) as (_, client, path, _, _):
        finding = client.get(path + "/comparison").json()["criteria"][0]["ai"]
        expected = client.get(path + "/findings/" + finding["finding_id"] + "/evidence").json()
        calls = []

        def backend(method, target, **kwargs):
            calls.append(target)
            response = client.request(method, target, **kwargs)
            response.raise_for_status()
            return response.json()

        with (
            patch("frontend.assessment_review.request_backend", side_effect=backend),
            patch("frontend.api_client.request_backend", side_effect=backend),
        ):
            ui = AppTest.from_string(
                "from frontend.assessment_review import render_comparison, request_backend\n"
                f"render_comparison({path!r}, request_backend('GET', {path!r}))"
            ).run()
            assert not ui.exception
            next(b for b in ui.button if b.key == "evidence_" + finding["finding_id"]).click().run()
            assert not ui.exception
            assert any(t.value == expected["original_text"] for t in ui.text)
            assert any(f"/findings/{finding['finding_id']}/evidence" in p for p in calls)
