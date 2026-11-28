"""Actual PDF worker and API; Ollama HTTP responses remain explicit CI mocks."""

import hashlib
import json
from unittest.mock import patch

import httpx
import pytest
from app.config import Settings
from app.llm.providers.demo import DemoProvider
from app.main import create_app, create_provider
from app.services.document_store import load_pilot_document
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from tests.fixtures.assessments import AssessmentProvider, human_submission
from tests.fixtures.frontend import create_case_ui
from tests.fixtures.pilot import pilot_setup


def test_local_pilot_needs_actual_artifact_and_catalog_evidence(tmp_path):
    directory, catalog, _ = pilot_setup(tmp_path)
    config = Settings(
        _env_file=None,
        config_dir=directory,
        inference_mode="local_pilot",
        pilot_model_id="qwen",
        pilot_profile_id="pa1-example",
        pilot_document_dir=catalog,
    )
    async_client = httpx.AsyncClient()
    assert not isinstance(create_provider(config, async_client), DemoProvider)
    config.config_dir = directory.parent / "does-not-exist"
    with pytest.raises(OSError):
        create_provider(config, async_client)


def test_pdf_to_human_finalization_through_real_adapter_with_mock_http(tmp_path):
    directory, catalog, key = pilot_setup(tmp_path)
    config = Settings(
        _env_file=None,
        config_dir=directory,
        document_store_dir=tmp_path / "runtime",
        inference_mode="local_pilot",
        pilot_model_id="qwen",
        pilot_profile_id="pa1-example",
        pilot_document_dir=catalog,
    )
    text = next(iter(load_pilot_document(catalog, key, "").pages.values())).strip()
    prompts = []

    async def controlled_http(_self, request):
        if request.url.path == "/api/tags":
            return httpx.Response(
                200, json={"models": [{"name": "qwen3:8b", "size": 1, "digest": "a" * 64}]}
            )
        assert request.url.path == "/api/chat"
        payload = json.loads(request.content)
        prompts.append(payload)
        data = json.loads(payload["messages"][-1]["content"])
        assert "HUMAN_PRIVATE_MARKER" not in request.content.decode()
        result = {
            "observations": [
                {
                    "criterion_id": c["id"],
                    "observation": {
                        "judgment": "MIXED",
                        "kind": "OPEN_QUESTION",
                        "description": "SIMULATED_HTTP_CI",
                        "rationale": "CI contract only, not real model inference",
                        "page": 1,
                        "quote": text,
                    },
                }
                for c in data["criteria"]
            ]
        }
        return httpx.Response(
            200,
            json={
                "model": payload["model"],
                "done": True,
                "message": {"content": json.dumps(result)},
                "prompt_eval_count": 100,
                "eval_count": 60,
            },
        )

    app = create_app(config)
    with patch(
        "app.security.egress_policy.PinnedInferenceTransport.handle_async_request", controlled_http
    ):
        with TestClient(app) as client:
            docs = client.get("/api/v1/assessments/pilot-documents").json()
            assert docs["documents"][0]["document_id"] == key
            assert client.post("/api/v1/runs", json={"mode": "D"}).status_code == 403
            created = client.post(
                "/api/v1/assessments",
                json={
                    "work_type": "PA1",
                    "profile_id": "pa1-example",
                    "document_id": key,
                },
            )
            assert created.status_code == 201
            path = "/api/v1/assessments/" + created.json()["id"]
            assert client.get(path + "/comparison").status_code == 409
            assert client.post(path + "/human-review", json=human_submission()).status_code == 200
            assert client.post(path + "/ai-review").status_code == 202

            async def wait():
                await app.state.runtime.assessments.tasks[created.json()["id"]]

            client.portal.call(wait)
            assert client.get(path).json()["ai_state"] == "COMPLETED"
            assert client.get(path + "/provenance").status_code == 409
            assert client.post(path + "/release", json={"confirmed": True}).status_code == 200
            comparison = client.get(path + "/comparison").json()
            finding = comparison["criteria"][0]["ai"]
            evidence = client.get(path + "/findings/" + finding["finding_id"] + "/evidence").json()
            assert evidence["matched"] and evidence["source_sha256"] == key.removeprefix("pilot-")
            assert evidence["quote"] in evidence["original_text"]
            assert (
                client.post(
                    path + "/discussion",
                    json={
                        "criterion_id": "literature",
                        "question": "RESTRICTED human question",
                    },
                ).status_code
                == 403
            )
            client.post(path + "/manual-review", json={"confirmed": True})
            for row in comparison["criteria"]:
                assert (
                    client.post(
                        path + "/decisions",
                        json={
                            "criterion_id": row["criterion_id"],
                            "include_ai_finding": False,
                            "conclusion": "Synthetic human decision",
                            "rationale": "Synthetic human rationale",
                        },
                    ).status_code
                    == 200
                )
            assert client.post(path + "/finalize", json={"confirmed": True}).status_code == 200
            provenance = client.get(path + "/provenance").json()
            assert provenance["source_pdf_sha256"] == key.removeprefix("pilot-")
            assert provenance["model_calls"] == 1 and len(prompts) == 1
            record = app.state.runtime.assessments.records[created.json()["id"]]
            original = record.document.pages[1]
            record.document.pages[1] = "Different document version"
            assert (
                client.get(path + "/findings/" + finding["finding_id"] + "/evidence").status_code
                == 409
            )
            record.document.pages[1] = original
            assert client.delete(path).status_code == 204
            assert client.get(path).status_code == 404
    # The public reference catalog is separately managed; deleting one run does not delete it.
    assert hashlib.sha256((catalog / (key[6:] + ".pdf")).read_bytes()).hexdigest() == key[6:]


def test_pilot_abort_delete_and_restart_explicitly_have_no_recovery(tmp_path):
    directory, catalog, key = pilot_setup(tmp_path)
    settings = Settings(
        _env_file=None,
        config_dir=directory,
        document_store_dir=tmp_path / "runtime",
        pilot_profile_id="pa1-example",
        pilot_document_dir=catalog,
    )
    app = create_app(settings)
    with patch("app.main.create_provider", return_value=AssessmentProvider(delay=30)):
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/assessments",
                json={
                    "work_type": "PA1",
                    "profile_id": "pa1-example",
                    "document_id": key,
                },
            )
            assert response.status_code == 201
            path = "/api/v1/assessments/" + response.json()["id"]
            client.post(path + "/ai-review")
            assert client.post(path + "/cancel").json()["state"] == "CANCELLED"
        assert not app.state.runtime.assessments.records
    # A new process/lifespan cannot recover volatile human reviews or old grants.
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get(path).status_code == 404
        assert restarted.get("/api/v1/assessments/pilot-documents").json()["documents"]


@pytest.mark.parametrize("mode", ["mock", "local_pilot"])
def test_pilot_pdf_can_be_selected_in_ui_with_explicit_inference_mode(tmp_path, mode):
    directory, catalog, key = pilot_setup(tmp_path)
    settings = Settings(
        _env_file=None,
        config_dir=directory,
        document_store_dir=tmp_path / "runtime",
        inference_mode=mode,
        pilot_model_id="qwen" if mode == "local_pilot" else None,
        pilot_profile_id="pa1-example",
        pilot_document_dir=catalog,
    )
    # The UI contract is tested with a fake provider; this is not a real model run.
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider()),
        TestClient(create_app(settings)) as client,
    ):

        def backend(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            assert response.is_success
            return response.json()

        with (
            patch("frontend.assessment_review.request_backend", side_effect=backend),
            patch("frontend.api_client.request_backend", side_effect=backend),
        ):
            ui = AppTest.from_string(
                "from frontend.assessment_review import render_assessment_review\n"
                "render_assessment_review()",
                default_timeout=10,
            ).run()
            create_case_ui(ui, document_id=key)
            assert not ui.exception
            assert any("operatorgeprüfte Pilot-PDF" in c.value for c in ui.caption)
            expected = (
                "Lokaler Ollama-Pilot" if mode == "local_pilot" else "keine reale Modellinferenz"
            )
            assert any(expected in c.value for c in ui.caption)
