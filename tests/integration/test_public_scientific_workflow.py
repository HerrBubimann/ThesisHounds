import json
from unittest.mock import patch

import httpx
from app.config import Settings
from app.main import create_app
from app.services.language_tool import LocalLanguageTool
from fastapi.testclient import TestClient

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider, human_submission
from tests.integration.test_finding_feedback import assessment
from tests.unit.test_public_library import install


def test_assessment_pins_bibliographic_version_and_uses_same_citation_report(tmp_path):
    root = tmp_path / "public-library"
    install(root)
    app = create_app(
        Settings(
            _env_file=None,
            config_dir=CONFIG,
            document_store_dir=tmp_path / "runtime",
            public_metadata_dir=root,
        )
    )
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider()),
        TestClient(app) as client,
    ):
        key = client.post(
            "/api/v1/assessments",
            json={"work_type": "PA1", "profile_confirmed": True, "profile_id": "pa1-example"},
        ).json()["id"]
        path = "/api/v1/assessments/" + key
        assert client.get(path + "/provenance").status_code == 409
        client.post(path + "/ai-review")

        async def wait():
            await app.state.runtime.assessments.tasks[key]

        client.portal.call(wait)
        client.post(path + "/human-review", json=human_submission())
        client.post(path + "/release", json={"confirmed": True})
        provenance = client.get(path + "/provenance").json()
        assert provenance["bibliographic_snapshot"]["version"] == "v1"
        assert provenance["bibliographic_snapshot"]["freshness"] == "STALE"
        comparison = client.get(path + "/comparison").json()
        assert comparison["source_checks"]["snapshot"]["version"] == "v1"
        assert comparison["source_checks"]["citations"] == comparison["source_checks"]["references"]
        assert comparison["source_checks"]["external_requests"] == 0


def test_local_language_suggestions_share_embargo_and_require_explicit_formal_criterion(tmp_path):
    with assessment(tmp_path, release=False) as (app, client, path, key, provider):
        # The completed default workflow did not enable a language checker for structure.
        record = app.state.runtime.assessments.records[key]
        assert record.language_checks[0]["status"] == "DISABLED"
        assert "language_checks" not in client.get(path).json()
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(200, json={"matches": []})

        service = app.state.runtime.assessments.academic
        service.language_tool = LocalLanguageTool(
            enabled=True, transport=httpx.MockTransport(handler)
        )
        profile = record.profile.model_copy(deep=True)
        profile.criteria[-1].local_checks = ["language"]  # Synthetic test mandate only.

        async def check():
            return await service.check_language(record.document, profile)

        result = client.portal.call(check)
        assert result[0]["status"] == "COMPLETED_BOUNDED_TEXT_CHECK" and calls
        assert all(request.url.host == "127.0.0.1" for request in calls)
        assert "HUMAN_PRIVATE_MARKER" not in json.dumps([str(r.content) for r in calls])
