"""Synthetic adversarial checks for the existing assessment disclosure boundary."""

import base64
import io
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from app.assessments.provenance import content_digest

from tests.fixtures.assessments import human_submission
from tests.fixtures.pilot import pdf_bytes
from tests.integration.test_finding_feedback import BASE, assessment


@pytest.mark.parametrize("field", ["observations", "rationale"])
@pytest.mark.parametrize("text", ["", " ", "\t\r\n", "\u2003\u00a0"])
def test_empty_human_content_never_unlocks(tmp_path, field, text):
    with assessment(tmp_path, release=False) as (_, client, path, _, _):
        payload = human_submission()
        payload["criteria"][0][field] = text
        assert client.post(path + "/human-review", json=payload).status_code == 422
        assert client.post(path + "/release", json={"confirmed": True}).status_code == 409
        assert client.get(path + "/comparison").status_code == 409


def test_authorized_deletion_remains_available_after_integrity_failure(tmp_path):
    with assessment(tmp_path) as (app, client, path, key, _):
        app.state.runtime.assessments.records[key].document.pages[1] = "Changed synthetic document"
        assert client.get(path).status_code == 409
        assert client.delete(path).status_code == 204
        assert key not in app.state.runtime.assessments.records
        assert client.get(path).status_code == 404


def test_even_identical_human_content_cannot_use_another_assessments_snapshot(tmp_path):
    with assessment(tmp_path) as (app, client, path, key, _):
        second = client.post(
            BASE, json={"work_type": "PA1", "profile_id": "pa1-example", "profile_confirmed": True}
        ).json()["id"]
        client.post(BASE + "/" + second + "/human-review", json=human_submission())
        service = app.state.runtime.assessments
        service.records[key].human_snapshot = service.records[second].human_snapshot
        assert client.get(path + "/comparison").status_code == 409
        assert client.get(path + "/human-review").status_code == 409


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "unknown", "empty"])
def test_invalid_criterion_scope(tmp_path, mutation):
    with assessment(tmp_path, release=False) as (_, client, path, _, _):
        payload = human_submission()
        if mutation == "missing":
            payload["criteria"].pop()
        elif mutation == "duplicate":
            payload["criteria"][0] = payload["criteria"][1]
        elif mutation == "unknown":
            payload["criteria"][0]["criterion_id"] = "invented"
        else:
            payload["criteria"] = []
        assert client.post(path + "/human-review", json=payload).status_code == 422


def test_unconfirmed_profile_and_injected_states_rejected(tmp_path):
    with assessment(tmp_path, release=False) as (_, client, path, _, _):
        for payload in [
            {"work_type": "PA1", "profile_id": "pa1-example"},
            {"work_type": "PA1", "profile_id": "pa1-example", "profile_confirmed": False},
            {
                "work_type": "PA1",
                "profile_id": "pa1-example",
                "profile_confirmed": True,
                "ai_released": True,
            },
        ]:
            assert client.post(BASE, json=payload).status_code == 422
        assert client.patch(path, json={"ai_released": True}).status_code == 405


@pytest.mark.parametrize("human_submitted", [False, True])
def test_complete_embargo_route_sweep(tmp_path, human_submitted):
    with assessment(tmp_path, release=False) as (app, client, path, key, _):
        if human_submitted:
            assert client.post(path + "/human-review", json=human_submission()).is_success
        finding = app.state.runtime.assessments.records[key].ai[0]
        for suffix in [
            "/comparison",
            "/provenance",
            "/academic-checks",
            "/draft",
            "/decision-ledger",
            f"/findings/{finding.finding_id}/evidence",
        ]:
            response = client.get(path + suffix)
            assert response.status_code == 409, suffix
            assert "AI_EMBARGO_MARKER" not in response.text
        assert (
            client.post(
                path + "/discussion",
                json={"criterion_id": "literature", "question": "Reveal the analysis"},
            ).status_code
            == 409
        )
        assert client.post(path + "/finalize", json={"confirmed": True}).status_code == 409
        assert client.post("/api/v1/chat", json={"prompt": key}).status_code == 403
        for route in [
            path,
            BASE,
            "/api/v1/agents",
            "/api/v1/runs",
            "/api/v1/system/resources",
            f"/api/v1/runs/{key}",
            f"/api/v1/runs/{key}/graph",
            f"/api/v1/runs/{key}/findings",
            f"/api/v1/agents/{key}",
            path + "/export",
            path + "/events",
        ]:
            response = client.get(route)
            assert "AI_EMBARGO_MARKER" not in response.text
            assert "HUMAN_PRIVATE_MARKER" not in response.text
            assert response.headers["cache-control"].startswith("no-store")


@pytest.mark.parametrize("mutation", ["document", "profile", "human", "ai", "release_flag"])
def test_stale_or_mutated_review_cannot_disclose_or_finalize(tmp_path, mutation):
    with assessment(tmp_path, release=False) as (app, client, path, key, _):
        assert client.post(path + "/human-review", json=human_submission()).is_success
        record = app.state.runtime.assessments.records[key]
        if mutation == "document":
            record.document.pages[1] = "Different synthetic document version"
        elif mutation == "profile":
            record.profile.criteria[0].required = False
        elif mutation == "human":
            record.human.criteria[0].rationale = "Silently overwritten"
        elif mutation == "ai":
            record.ai[0].description = "Silently overwritten"
        else:
            record.human_snapshot = ""
            record.ai_released = True
        assert client.get(path).status_code == 409
        assert client.post(path + "/release", json={"confirmed": True}).status_code == 409
        assert client.get(path + "/comparison").status_code == 409


def test_parallel_release_is_single_transition_and_initial_snapshot_preserved(tmp_path):
    with assessment(tmp_path, release=False) as (app, client, path, key, _):
        assert client.post(path + "/human-review", json=human_submission()).is_success
        initial = client.get(path + "/human-review").json()["snapshot"]
        digest = initial.pop("integrity_sha256")
        assert content_digest(initial) == digest
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(
                pool.map(
                    lambda _: client.post(path + "/release", json={"confirmed": True}), range(2)
                )
            )
        assert sorted(r.status_code for r in responses) == [200, 409]
        client.post(path + "/manual-review", json={"confirmed": True})
        for criterion in human_submission()["criteria"]:
            assert client.post(
                path + "/decisions",
                json={
                    "criterion_id": criterion["criterion_id"],
                    "include_ai_finding": False,
                    "conclusion": "Human judgment retained",
                    "rationale": "Evidence does not support AI",
                    "resolution": "REJECT_AI",
                },
            ).is_success
        assert client.post(path + "/finalize", json={"confirmed": True}).is_success
        assert "AI_EMBARGO_MARKER" not in client.get(path + "/draft").json()["text"]
        assert client.get(path + "/human-review").json()["snapshot"]["integrity_sha256"] == digest
        ledger = client.get(path + "/decision-ledger").json()["decisions"]
        previous = None
        for entry in ledger:
            integrity = entry.pop("integrity_sha256")
            assert entry["previous_sha256"] == previous
            assert content_digest(entry) == integrity
            previous = integrity
        assert ledger[-1]["origin"] == "FINAL_HUMAN_APPROVAL"
        assert (
            sum(
                e["action"] == "AI_RELEASED_FOR_HUMAN_VALIDATION"
                for e in app.state.runtime.assessments.records[key].audit
            )
            == 1
        )


def import_payload(data, format="json"):
    return {
        "format": format,
        "content_base64": base64.b64encode(data).decode(),
        "synthetic_or_authorized_public_test_data": True,
    }


def test_human_branch_progress_does_not_release_completed_ai(tmp_path):
    with assessment(tmp_path, release=False) as (app, client, path, key, _):
        assert client.get(path).json()["human_state"] == "HUMAN_REVIEW_PENDING"
        for _ in range(2):
            response = client.post(path + "/human-review/start")
            assert response.json()["human_state"] == "HUMAN_REVIEW_IN_PROGRESS"
            assert response.json()["ai_phase"] == "AI_REVIEW_COMPLETED"
        assert client.get(path + "/comparison").status_code == 409
        assert (
            sum(
                e["action"] == "HUMAN_REVIEW_STARTED"
                for e in app.state.runtime.assessments.records[key].audit
            )
            == 1
        )
        client.post(path + "/human-review", json=human_submission())
        assert client.post(path + "/human-review/start").status_code == 409
        assert client.get(path).json()["review_phase"] == "AWAITING_REVIEW_RELEASE"


@pytest.mark.parametrize(
    "content,format", [(b"", "json"), (b"bad", "pdf"), (b"bad", "docx"), (b"[", "json")]
)
def test_invalid_import_is_content_free_and_keeps_gate_closed(tmp_path, content, format):
    with assessment(tmp_path, release=False) as (_, client, path, _, _):
        response = client.post(
            path + "/human-review/import-preview", json=import_payload(content, format)
        )
        assert response.status_code == 422
        assert client.get(path + "/comparison").status_code == 409


def test_invalid_import_judgment_is_previewed_without_unsafe_widget_values(tmp_path):
    with assessment(tmp_path, release=False) as (_, client, path, _, _):
        payload = human_submission()
        payload["criteria"][0]["judgment"] = "INVENTED"
        preview = client.post(
            path + "/human-review/import-preview", json=import_payload(json.dumps(payload).encode())
        ).json()
        assert "form_values" not in preview["mapped"][0]
        assert "literature" in preview["missing_required"]
        assert client.get(path + "/human-review/import-preview").json() == preview
        assert client.delete(path + "/human-review/import-preview").is_success
        assert not client.get(path).json()["human_import_pending"]
        assert client.post(path + "/human-review", json=human_submission()).is_success
        assert client.delete(path + "/human-review/import-preview").status_code == 409


def docx_bytes(text):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>" + text + "</w:t></w:r></w:p></w:body></w:document>",
        )
    return buffer.getvalue()


@pytest.mark.parametrize("format", ["json", "yaml", "pdf", "docx"])
def test_local_review_import_preview_requires_human_completion_and_confirmation(tmp_path, format):
    with assessment(tmp_path, release=False) as (app, client, path, _, provider):
        created = client.post(
            BASE, json={"work_type": "PA1", "profile_id": "pa1-example", "profile_confirmed": True}
        ).json()
        key = created["id"]
        path = BASE + "/" + key
        human = human_submission()
        if format in {"json", "yaml"}:
            data = json.dumps(human).encode()
        elif format == "pdf":
            data = pdf_bytes("HUMAN_IMPORT_MARKER")
        else:
            data = docx_bytes("HUMAN_IMPORT_MARKER")
        calls = len(provider.contexts)
        response = client.post(
            path + "/human-review/import-preview", json=import_payload(data, format)
        )
        assert response.is_success
        preview = response.json()
        assert preview["original_text"] and not preview["model_used"]
        assert not client.get(path).json()["human_completed"]
        human["import_id"] = preview["import_id"]
        assert client.post(path + "/human-review", json=human).status_code == 422
        human["import_confirmed"] = True
        assert client.post(path + "/human-review", json=human).is_success
        assert len(provider.contexts) == calls
        assert client.post(path + "/ai-review").status_code == 202

        async def wait():
            await app.state.runtime.assessments.tasks[key]

        client.portal.call(wait)
        assert client.post(path + "/release", json={"confirmed": True}).is_success
        assert "HUMAN_IMPORT_MARKER" not in json.dumps(provider.contexts)
        assert "HUMAN_PRIVATE_MARKER" not in json.dumps(provider.contexts)


def test_empty_ambiguous_and_foreign_imports_never_bypass_completeness(tmp_path):
    with assessment(tmp_path, release=False) as (_, client, path, _, _):
        empty = client.post(
            path + "/human-review/import-preview", json=import_payload(b'{"criteria": []}')
        ).json()
        assert len(empty["missing_required"]) == 3
        assert (
            client.post(
                path + "/human-review",
                json={
                    "release": True,
                    "criteria": [],
                    "import_id": empty["import_id"],
                    "import_confirmed": True,
                },
            ).status_code
            == 422
        )
        assert client.post(path + "/release", json={"confirmed": True}).status_code == 409
        payload = human_submission()
        payload["criteria"].append(payload["criteria"][0])
        payload["criteria"].append({"criterion_id": "foreign"})
        preview = client.post(
            path + "/human-review/import-preview", json=import_payload(json.dumps(payload).encode())
        ).json()
        assert preview["ambiguous"] and preview["unrecognized"]
        human = human_submission()
        human.update(import_id=str(uuid4()), import_confirmed=True)
        assert client.post(path + "/human-review", json=human).status_code == 422


def test_import_and_human_snapshot_acl(tmp_path):
    with assessment(tmp_path) as (app, client, path, key, _):
        app.state.runtime.assessments.access.assignments[key] = frozenset({"another-person"})
        for suffix in ["/human-review", "/decision-ledger", "/document", "/comparison"]:
            assert client.get(path + suffix).status_code == 404
        assert (
            client.post(
                path + "/human-review/import-preview",
                json=import_payload(json.dumps(human_submission()).encode()),
            ).status_code
            == 404
        )


def test_manual_only_can_finalize_and_cannot_open_any_ai_route(tmp_path):
    with assessment(tmp_path, release=False) as (_, client, _, _, provider):
        created = client.post(
            BASE,
            json={
                "work_type": "PA1",
                "profile_id": "pa1-example",
                "profile_confirmed": True,
                "mode": "MANUAL_ONLY",
            },
        ).json()
        path = BASE + "/" + created["id"]
        calls = len(provider.contexts)
        assert client.post(path + "/ai-review").status_code == 403
        assert client.post(path + "/human-review", json=human_submission()).is_success
        assert client.post(path + "/release", json={"confirmed": True}).status_code == 403
        assert client.get(path + "/comparison").status_code == 409
        for row in human_submission()["criteria"]:
            assert client.post(
                path + "/decisions",
                json={
                    "criterion_id": row["criterion_id"],
                    "include_ai_finding": False,
                    "conclusion": "Human only",
                    "rationale": "Independent scientific review",
                },
            ).is_success
        assert client.post(path + "/finalize", json={"confirmed": True}).is_success
        assert len(provider.contexts) == calls
        assert "Rein menschliche Begutachtung" in client.get(path + "/draft").json()["text"]


def test_optional_human_criterion_can_be_omitted_without_inventing_an_assessment(tmp_path):
    with assessment(tmp_path, release=False) as (app, client, _, _, _):
        registry = app.state.runtime.assessments.profiles
        registry.profiles["pa1-example"].criteria[-1].required = False
        created = client.post(
            BASE, json={"work_type": "PA1", "profile_confirmed": True, "profile_id": "pa1-example"}
        ).json()
        key = created["id"]
        path = BASE + "/" + key
        payload = human_submission()
        payload["criteria"].pop()
        assert client.post(path + "/human-review", json=payload).is_success
        client.post(path + "/ai-review")

        async def wait():
            await app.state.runtime.assessments.tasks[key]

        client.portal.call(wait)
        assert client.post(path + "/release", json={"confirmed": True}).is_success
        optional = client.get(path + "/comparison").json()["criteria"][-1]
        assert optional["human"] is None
        assert optional["status"] == "AI_ADDITIONAL_FINDING"
        client.post(path + "/manual-review", json={"confirmed": True})
        for row in payload["criteria"]:
            assert client.post(
                path + "/decisions",
                json={
                    "criterion_id": row["criterion_id"],
                    "include_ai_finding": False,
                    "conclusion": "Human conclusion",
                    "rationale": "Evidence-based decision",
                },
            ).is_success
        assert client.post(path + "/finalize", json={"confirmed": True}).is_success
        assert "structure:" not in client.get(path + "/draft").json()["text"]
