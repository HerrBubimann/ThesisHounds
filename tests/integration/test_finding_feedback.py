from contextlib import contextmanager
from unittest.mock import patch

import pytest
from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider, human_submission

BASE = "/api/v1/assessments"


@contextmanager
def assessment(tmp_path, *, release=True):
    app = create_app(Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path))
    provider = AssessmentProvider()
    with patch("app.main.create_provider", return_value=provider), TestClient(app) as client:
        key = client.post(BASE, json={"work_type": "PA1", "profile_id": "pa1-example"}).json()["id"]
        path = BASE + "/" + key
        client.post(path + "/ai-review")

        async def wait():
            await app.state.runtime.assessments.tasks[key]

        client.portal.call(wait)
        if release:
            client.post(path + "/human-review", json=human_submission())
            client.post(path + "/release", json={"confirmed": True})
        yield app, client, path, key, provider


def feedback(finding_id, **changes):
    return {
        "finding_id": finding_id,
        "action": "ACCEPT",
        "rationale": "SYNTHETIC_FEEDBACK_ONLY",
        **changes,
    }


def test_provenance_and_feedback_share_the_embargo_and_acl(tmp_path):
    with assessment(tmp_path, release=False) as (app, client, path, key, provider):
        assert client.get(path + "/provenance").status_code == 409
        identifier = app.state.runtime.assessments.records[key].ai[0].finding_id
        assert client.post(path + "/finding-feedback", json=feedback(identifier)).status_code == 409
        assert "model_digest" not in client.get(path).text
        client.post(path + "/human-review", json=human_submission())
        client.post(path + "/release", json={"confirmed": True})
        app.state.runtime.assessments.access.assignments[key] = frozenset({"foreign"})
        assert client.get(path + "/provenance").status_code == 404
        assert client.post(path + "/finding-feedback", json=feedback(identifier)).status_code == 404


@pytest.mark.parametrize(
    "action", ["ACCEPT", "REJECT", "CORRECT", "SUPPLEMENT", "NOT_RELEVANT", "INSUFFICIENT_EVIDENCE"]
)
def test_feedback_is_versioned_private_never_trains_and_preserves_original_model_output(
    tmp_path, action
):
    with assessment(tmp_path) as (app, client, path, key, provider):
        original = client.get(path + "/comparison").json()["criteria"][0]["ai"]
        calls = len(provider.contexts)
        payload = feedback(
            original["finding_id"],
            action=action,
            reason="MISSING_CONTEXT",
            correction="Synthetic human correction",
        )
        result = client.post(path + "/finding-feedback", json=payload)
        assert result.status_code == 200
        assert (
            result.json()["classification"] == "RESTRICTED"
            and not result.json()["automatic_training"]
        )
        assert result.json()["revision"] == 1
        assert client.post(path + "/finding-feedback", json=payload).json()["revision"] == 2
        after = client.get(path + "/comparison").json()["criteria"][0]["ai"]
        assert (
            after["description"] == original["description"] and len(after["feedback_history"]) == 2
        )
        assert after["human_approval"] == "PENDING" and len(provider.contexts) == calls
        provenance = client.get(path + "/provenance").json()
        assert provenance["finding_feedback"][-1]["action"] == action
        assert provenance["classification"] == "RESTRICTED" and not provenance["automatic_training"]


def test_invalid_feedback_and_foreign_finding_are_rejected(tmp_path):
    with assessment(tmp_path) as (app, client, path, key, provider):
        identifier = client.get(path + "/comparison").json()["criteria"][0]["ai"]["finding_id"]
        for payload in [
            feedback(identifier, action="REJECT"),
            feedback(identifier, action="CORRECT", reason="MISSING_CONTEXT"),
            feedback(identifier, classification="PUBLIC"),
        ]:
            assert client.post(path + "/finding-feedback", json=payload).status_code == 422
        assert client.post(path + "/finding-feedback", json=feedback("foreign")).status_code == 404
        assert not app.state.runtime.assessments.records[key].finding_feedback


def test_provenance_records_snapshot_versions_unknown_git_and_actual_models(tmp_path, monkeypatch):
    monkeypatch.setenv("THESISHOUNDS_GIT_SHA", "invalid")
    with assessment(tmp_path) as (app, client, path, key, provider):
        value = client.get(path + "/provenance").json()
        assert (
            len(value["document_version_sha256"]) == 64
            and value["current_document_matches_snapshot"]
        )
        assert value["catalog_status"] == "EXAMPLE" and value["git_commit_sha"] is None
        assert (
            value["git_evidence"] == "UNKNOWN"
            and value["exact_reproducibility"] == "NOT_GUARANTEED"
        )
        assert value["findings"] and value["model_calls"] > 0
        assert all(f["provenance"]["model_digest"] for f in value["findings"])
        original = value["catalog_version"]
        app.state.runtime.assessments.records[key].profile.version = "MUTATED_TEST"
        assert client.get(path + "/provenance").json()["catalog_version"] == original


def test_rejected_selected_finding_cannot_appear_in_final_draft(tmp_path):
    with assessment(tmp_path) as (app, client, path, key, provider):
        rows = client.get(path + "/comparison").json()["criteria"]
        first = rows[0]["ai"]
        client.post(path + "/manual-review", json={"confirmed": True})
        client.post(
            path + "/finding-feedback",
            json=feedback(first["finding_id"], action="REJECT", reason="UNJUSTIFIED_CRITICISM"),
        )
        decision = {
            "criterion_id": first["criterion_id"],
            "include_ai_finding": True,
            "conclusion": "Synthetic",
            "rationale": "Synthetic",
        }
        assert client.post(path + "/decisions", json=decision).status_code == 409
        client.post(
            path + "/finding-feedback",
            json=feedback(
                first["finding_id"],
                action="CORRECT",
                reason="MISSING_CONTEXT",
                correction="SYNTHETIC_CORRECTED_CONCLUSION",
            ),
        )
        # Accepting a correction later must not silently restore the original text.
        client.post(path + "/finding-feedback", json=feedback(first["finding_id"]))
        for row in rows:
            assert (
                client.post(
                    path + "/decisions", json={**decision, "criterion_id": row["criterion_id"]}
                ).status_code
                == 200
            )
        assert "SYNTHETIC_CORRECTED_CONCLUSION" in client.get(path + "/draft").json()["text"]
        assert client.post(path + "/finalize", json={"confirmed": True}).status_code == 200
        assert (
            client.post(path + "/finding-feedback", json=feedback(first["finding_id"])).status_code
            == 409
        )


def test_deleted_analysis_also_deletes_feedback_and_provenance(tmp_path):
    with assessment(tmp_path) as (app, client, path, key, provider):
        identifier = client.get(path + "/comparison").json()["criteria"][0]["ai"]["finding_id"]
        client.post(path + "/finding-feedback", json=feedback(identifier))
        assert client.delete(path).status_code == 204
        assert key not in app.state.runtime.assessments.records
        assert client.get(path + "/provenance").status_code == 404


def test_git_provenance_is_explicitly_operator_reported(tmp_path, monkeypatch):
    monkeypatch.setenv("THESISHOUNDS_GIT_SHA", "a" * 40)
    with assessment(tmp_path) as (app, client, path, key, provider):
        value = client.get(path + "/provenance").json()
        assert value["git_commit_sha"] == "a" * 40
        assert value["git_evidence"] == "OPERATOR_REPORTED_NOT_INDEPENDENTLY_VERIFIED"
        assert value["working_tree_state"] == "UNKNOWN"


def test_only_actually_checked_local_sources_enter_research_provenance(tmp_path):
    from app.research.provider_registry import LocalResearchCache

    from tests.unit.test_citation_engine import record

    with assessment(tmp_path) as (app, client, path, key, provider):
        service = app.state.runtime.assessments
        service.academic.cache = LocalResearchCache([record()])
        assert not client.get(path + "/provenance").json()["research_sources"]
        current = service.records[key].document
        service.records[key].document = current.model_copy(
            update={
                "pages": {
                    **current.pages,
                    4: (
                        "Literaturverzeichnis\n[1] Muster (2020). "
                        "Synthetischer Titel. doi:10.5555/test"
                    ),
                }
            }
        )
        client.get(path + "/academic-checks")
        value = client.get(path + "/provenance").json()
        assert value["research_sources"][0]["provider"] == "crossref"
        assert value["research_sources"][0]["snapshot_sha256"] == "a" * 64
        assert value["research_sources"][0]["checked_at"]
        assert not value["current_document_matches_snapshot"]
        assert value["combined_result"]["status"] == "STALE_REQUIRES_NEW_REVIEW"
        assert client.get(path + "/draft").status_code == 409
