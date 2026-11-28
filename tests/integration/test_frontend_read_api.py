"""New UI projections must preserve ACL, embargo and original-file integrity."""

from unittest.mock import patch

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

from tests.fixtures.assessments import AssessmentProvider
from tests.fixtures.pilot import pilot_setup
from tests.integration.test_finding_feedback import assessment

BASE = "/api/v1/assessments"


def test_listing_is_metadata_only_during_embargo_and_filters_acl(tmp_path):
    with assessment(tmp_path, release=False) as (app, client, path, key, _):
        rows = client.get(BASE).json()
        assert len(rows) == 1 and rows[0]["id"] == key
        assert rows[0]["ai_state"] == "COMPLETED" and not rows[0]["ai_released"]
        assert not {"ai", "human", "findings", "conflicts", "decisions", "profile"} & rows[0].keys()
        assert "AI_EMBARGO_MARKER" not in client.get(BASE).text
        assert "HUMAN_PRIVATE_MARKER" not in client.get(BASE).text
        assert client.get(BASE).headers["cache-control"].startswith("no-store")
        assert client.get(path + "/original-pdf").status_code == 404
        app.state.runtime.assessments.access.assignments[key] = frozenset({"foreign"})
        assert client.get(BASE).json() == []
        assert client.get(path + "/original-pdf").status_code == 404


def test_rules_and_capabilities_are_read_only_projections(tmp_path):
    with assessment(tmp_path) as (_, client, _, _, _):
        response = client.post(
            BASE + "/rules-preview",
            json={"program": "data_science_ai", "cohort": "DS23", "work_type": "PA1"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "MANUAL_REVIEW_REQUIRED"
        assert not any(r["active"] for r in response.json()["rules"])
        assert (
            client.post(
                BASE + "/rules-preview",
                json={"program": "data_science_ai", "cohort": "../../private", "work_type": "PA1"},
            ).status_code
            == 422
        )
        capabilities = client.get("/api/v1/models/capabilities").json()
        assert capabilities["records"] == [] and not capabilities["configuration_is_approval"]
        assert (
            client.post("/api/v1/models/capabilities", json={"approved": True}).status_code == 405
        )


def test_original_pdf_is_verified_acl_scoped_and_rejects_changes(tmp_path):
    directory, catalog, key = pilot_setup(tmp_path)
    settings = Settings(
        _env_file=None,
        config_dir=directory,
        document_store_dir=tmp_path / "runtime",
        pilot_document_dir=catalog,
        pilot_profile_id="pa1-example",
    )
    app = create_app(settings)
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider()),
        TestClient(app) as client,
    ):
        record = client.post(
            BASE, json={"work_type": "PA1", "profile_id": "pa1-example", "document_id": key}
        ).json()
        path = BASE + "/" + record["id"] + "/original-pdf"
        response = client.get(path)
        assert response.status_code == 200 and response.content.startswith(b"%PDF-")
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["cache-control"].startswith("no-store")
        assert response.content == (catalog / (key[6:] + ".pdf")).read_bytes()
        service = app.state.runtime.assessments
        original = service.records[record["id"]].document
        service.records[record["id"]].document = original.model_copy(
            update={
                "security_inspection": {
                    **original.security_inspection,
                    "indicators": [{"kind": "EXTERNAL_LINK"}],
                }
            }
        )
        assert client.get(path).status_code == 409
        service.records[record["id"]].document = original
        service.access.assignments[record["id"]] = frozenset({"foreign"})
        assert client.get(path).status_code == 404
        service.access.assignments[record["id"]] = frozenset({"synthetic-demo"})
        (catalog / (key[6:] + ".pdf")).write_bytes(b"%PDF-changed")
        assert client.get(path).status_code == 403
