from unittest.mock import patch

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from frontend.api_client import BackendError
from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider, human_submission
from tests.fixtures.frontend import create_case_ui


def test_local_check_ui_has_explicit_decisions_and_verified_citation_navigation():
    decisions = []
    calls = []
    entry = {"id": "1", "page": 2, "start": 0, "end": 15, "raw": "Synthetic source"}
    entry["end"] = len(entry["raw"])

    def backend(method, path, **kwargs):
        calls.append((method, path))
        if method == "POST":
            decisions.append(kwargs["json"])
            return kwargs["json"]
        if path.endswith("/document"):
            return {"pages": {"2": entry["raw"] + "\nFurther original text"}}
        return {
            "formal": {
                "checks": [
                    {
                        "criterion_id": "pages",
                        "status": "MANUAL_REVIEW_REQUIRED",
                        "reason": "RULE_NOT_APPROVED",
                        "source_id": "synthetic-rule",
                        "source_location": "fixture",
                        "finding_id": "formal:pages",
                    }
                ]
            },
            "citations": {
                "references": [
                    {
                        "entry": entry,
                        "statuses": ["NOT_FOUND", "MANUAL_REVIEW_REQUIRED"],
                        "finding_id": "citation:1",
                    }
                ]
            },
            "decisions": decisions,
        }

    with patch("frontend.assessment_review.request_backend", side_effect=backend):
        app = AppTest.from_string(
            "from frontend.assessment_review import render_academic\n"
            "render_academic('/synthetic', {'state':'READY_FOR_COMPARISON'})"
        ).run()
        assert not app.exception and not decisions
        next(b for b in app.button if b.label == "Originalstelle der Quelle öffnen").click().run()
        assert any(t.value.endswith("Further original text") for t in app.text)
        next(b for b in app.button if b.label == "Lokale Prüfentscheidung speichern").click().run()
        assert app.warning and not decisions
        next(b for b in app.selectbox if b.label == "Menschliche Bestätigung").select("ACCEPTED")
        app.text_area[0].set_value("Synthetic human decision")
        next(b for b in app.button if b.label == "Lokale Prüfentscheidung speichern").click().run()
        assert not app.exception
        assert decisions[0]["decision"] == "ACCEPTED"
        assert ("GET", "/synthetic/document") in calls


def test_local_checks_are_embargoed_scoped_and_human_confirmed(tmp_path):
    application = create_app(
        Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path)
    )
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider()),
        TestClient(application) as client,
    ):
        request = {
            "work_type": "PA1",
            "profile_confirmed": True,
            "profile_id": "pa1-example",
            "cohort": "DS25",
            "program": "data_science_ai",
        }
        response = client.post("/api/v1/assessments", json=request)
        record = response.json()
        assert response.status_code == 201 and record["cohort"] == "DS25"
        assert record["institutional_rules"]["profile"]["cohort"] == "DS25"
        assert record["institutional_rules"]["status"] == "MANUAL_REVIEW_REQUIRED"
        assert record["profile"]["status"] == "EXAMPLE"
        path = "/api/v1/assessments/" + record["id"]
        assert client.get(path + "/academic-checks").status_code == 409
        client.post(path + "/ai-review")

        async def wait():
            await application.state.runtime.assessments.tasks[record["id"]]

        client.portal.call(wait)
        assert client.get(path + "/academic-checks").status_code == 409
        client.post(path + "/human-review", json=human_submission())
        client.post(path + "/release", json={"confirmed": True})
        result = client.get(path + "/academic-checks")
        assert result.headers["cache-control"].startswith("no-store")
        data = result.json()
        assert data["external_requests"] == 0 and data["classification"] == "RESTRICTED"
        assert all(r["status"] == "MANUAL_REVIEW_REQUIRED" for r in data["formal"]["checks"])
        row = data["formal"]["checks"][0]
        assert (
            client.post(
                path + "/academic-decisions",
                json={
                    "finding_id": "other-work:123",
                    "decision": "ACCEPTED",
                    "rationale": "Synthetic human note",
                },
            ).status_code
            == 422
        )
        for decision in ("ACCEPTED", "REJECTED"):
            assert (
                client.post(
                    path + "/academic-decisions",
                    json={
                        "finding_id": row["finding_id"],
                        "decision": decision,
                        "rationale": "Synthetic human note",
                    },
                ).status_code
                == 200
            )
        decisions = client.get(path + "/academic-checks").json()["decisions"]
        assert [d["revision"] for d in decisions] == [1, 2]
        client.post(path + "/manual-review", json={"confirmed": True})
        for key in ("literature", "methodology", "structure"):
            client.post(
                path + "/decisions",
                json={
                    "criterion_id": key,
                    "include_ai_finding": False,
                    "conclusion": "Synthetic conclusion",
                    "rationale": "Synthetic rationale",
                },
            )
        assert "Synthetic human note" not in client.get(path + "/draft").json()["text"]
        client.post(
            path + "/academic-decisions",
            json={
                "finding_id": row["finding_id"],
                "decision": "ACCEPTED",
                "rationale": "Synthetic approved formal note",
            },
        )
        assert "Synthetic approved formal note" in client.get(path + "/draft").json()["text"]
        client.post(path + "/finalize", json={"confirmed": True})
        assert (
            client.post(
                path + "/academic-decisions",
                json={
                    "finding_id": row["finding_id"],
                    "decision": "REJECTED",
                    "rationale": "Cannot edit finalized",
                },
            ).status_code
            == 409
        )
        assert (
            client.post("/api/v1/assessments", json={**request, "cohort": "WI25"}).status_code
            == 422
        )


def test_delete_one_assessment_keeps_other_task_managed(tmp_path):
    application = create_app(
        Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path)
    )
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider(delay=0.02)),
        TestClient(application) as client,
    ):
        ids = [
            client.post(
                "/api/v1/assessments",
                json={"work_type": "PA1", "profile_confirmed": True, "profile_id": "pa1-example"},
            ).json()["id"]
            for _ in range(2)
        ]
        service = application.state.runtime.assessments
        client.post("/api/v1/assessments/" + ids[1] + "/ai-review")
        assert ids[1] in service.tasks
        assert client.delete("/api/v1/assessments/" + ids[0]).status_code == 204
        assert ids[1] in service.tasks

        async def wait():
            await service.tasks[ids[1]]

        client.portal.call(wait)
        assert service.get(ids[1]).ai_state == "COMPLETED"


def test_streamlit_selection_and_candidate_rules_display(tmp_path):
    api = create_app(Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path))
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider()),
        TestClient(api) as client,
    ):

        def backend(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            if response.is_error:
                raise BackendError("Synthetic API rejection")
            return response.json()

        with (
            patch("frontend.assessment_review.request_backend", side_effect=backend),
            patch("frontend.api_client.request_backend", side_effect=backend),
        ):
            app = AppTest.from_string(
                "from frontend.assessment_review import render_assessment_review\n"
                "render_assessment_review()",
                default_timeout=10,
            ).run()
            create_case_ui(app, cohort="DS25")
            assert not app.exception
            assert any("Regelkonflikt page_count_basis" in w.value for w in app.warning)
            assert any("keine aktivierten offiziellen" in w.value for w in app.warning)
            assert not any("Lokalen Prüfbefund" in b.label for b in app.selectbox)
