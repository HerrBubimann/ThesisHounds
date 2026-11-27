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
            "/api/v1/assessments", json={"work_type": "PA1", "profile_id": "pa1-example"}
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


def test_streamlit_navigates_from_finding_to_a_verified_original_span():
    finding_id = str(uuid4())
    finding = {
        "finding_id": finding_id,
        "criterion_id": "methodology",
        "description": "Synthetic finding",
        "human_approval": "PENDING",
        "supplemental": [],
    }
    calls = []

    def backend(method, path, **kwargs):
        calls.append(path)
        if path.endswith("/comparison"):
            return {
                "criteria": [
                    {
                        "criterion_id": "methodology",
                        "status": "AGREEMENT",
                        "human": {},
                        "ai": finding,
                    }
                ],
                "discussion": [],
            }
        assert path.endswith(f"/findings/{finding_id}/evidence")
        return {
            "matched": True,
            "page": 2,
            "chapter": "Methodik",
            "block_id": "p2-b0",
            "original_text": "Original synthetic text",
            "quote": "synthetic",
        }

    with patch("frontend.assessment_review.request_backend", side_effect=backend):
        app = AppTest.from_string(
            "from frontend.assessment_review import render_comparison\n"
            "render_comparison('/api/v1/assessments/synthetic', {'state':'READY_FOR_COMPARISON'})"
        ).run()
        next(b for b in app.button if b.label == "Textbeleg öffnen").click().run()
        assert not app.exception
        assert any(t.value == "Original synthetic text" for t in app.text)
        assert any(f"/findings/{finding_id}/evidence" in p for p in calls)
