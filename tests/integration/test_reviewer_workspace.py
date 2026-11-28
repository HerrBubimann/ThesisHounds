import json
from uuid import uuid4

import pytest

from tests.integration.test_finding_feedback import assessment


def decide_all(client, path, *, primary=None, duplicate=None):
    assert client.post(path + "/manual-review", json={"confirmed": True}).status_code == 200
    rows = client.get(path + "/comparison").json()["criteria"]
    for row in rows:
        body = {
            "criterion_id": row["criterion_id"],
            "include_ai_finding": row["criterion_id"] == primary,
            "include_finding_ids": [duplicate]
            if duplicate and row["criterion_id"] == primary
            else [],
            "conclusion": "SYNTHETIC_HUMAN_CONCLUSION",
            "rationale": "SYNTHETIC_HUMAN_REASON",
        }
        assert client.post(path + "/decisions", json=body).status_code == 200


@pytest.mark.parametrize(
    "route,body",
    [
        ("/reviewer-notes", {"criterion_id": "methodology", "text": "PRIVATE_REVIEW_NOTE"}),
        ("/reviewer-time", {"action": "START"}),
        (
            "/review-methods",
            {
                "criterion_id": "methodology",
                "family": "STATISTICS",
                "confirmed_applied": True,
                "evidence": [{"page": 2, "quote": "Methodik:"}],
            },
        ),
    ],
)
def test_workspace_mutations_share_independent_review_embargo(tmp_path, route, body):
    with assessment(tmp_path, release=False) as (app, client, path, key, provider):
        assert client.post(path + route, json=body).status_code == 409
        assert not app.state.runtime.assessments.records[key].reviewer_notes
        assert "reviewer_workspace" not in client.get(path).json()


def test_notes_are_private_versioned_scoped_and_explicitly_selected_for_draft(tmp_path):
    with assessment(tmp_path) as (app, client, path, key, provider):
        original = app.state.runtime.assessments.records[key].human.model_dump()
        calls = len(provider.contexts)
        body = {
            "criterion_id": "methodology",
            "text": "PRIVATE_REVIEW_NOTE",
            "include_in_draft": False,
        }
        first = client.post(path + "/reviewer-notes", json=body)
        assert first.status_code == 200 and first.json()["classification"] == "RESTRICTED"
        assert "PRIVATE_REVIEW_NOTE" not in client.get(path).text
        decide_all(client, path)
        assert "PRIVATE_REVIEW_NOTE" not in client.get(path + "/draft").json()["text"]
        body.update(note_id=first.json()["id"], include_in_draft=True, text="APPROVED_REVIEW_NOTE")
        assert client.post(path + "/reviewer-notes", json=body).status_code == 200
        draft = client.get(path + "/draft").json()["text"]
        assert "APPROVED_REVIEW_NOTE" in draft and "PRIVATE_REVIEW_NOTE" not in draft
        body.update(include_in_draft=False, text="WITHDRAWN_REVIEW_NOTE")
        assert client.post(path + "/reviewer-notes", json=body).status_code == 200
        assert "APPROVED_REVIEW_NOTE" not in client.get(path + "/draft").json()["text"]
        assert len(client.get(path + "/comparison").json()["reviewer_workspace"]["notes"]) == 1
        assert len(client.get(path + "/provenance").json()["reviewer_notes"]) == 3
        assert app.state.runtime.assessments.records[key].human.model_dump() == original
        assert len(provider.contexts) == calls
        assert "PRIVATE_REVIEW_NOTE" not in json.dumps(provider.contexts)
        assert (
            client.post(
                path + "/reviewer-notes", json={**body, "criterion_id": "foreign"}
            ).status_code
            == 422
        )
        assert (
            client.post(path + "/reviewer-notes", json={**body, "note_id": "foreign"}).status_code
            == 422
        )


def test_applied_method_and_questions_are_bound_to_original_evidence_and_criterion(tmp_path):
    with assessment(tmp_path) as (_, client, path, _, provider):
        body = {
            "criterion_id": "methodology",
            "family": "STATISTICS",
            "confirmed_applied": True,
            "evidence": [{"page": 2, "quote": "Es wurden sechs synthetische Arbeiten"}],
        }
        assert client.post(path + "/review-methods", json=body).status_code == 200
        workspace = client.get(path + "/comparison").json()["reviewer_workspace"]
        assert workspace["reproducibility"]["methods"][0]["origin"] == "HUMAN_CONFIRMED"
        question = next(
            q for q in workspace["questions"] if q["reason"] == "REPRODUCIBILITY_CONTEXT"
        )
        note = {
            "criterion_id": "methodology",
            "question_id": question["id"],
            "text": "SYNTHETIC_RESPONSE",
        }
        assert client.post(path + "/reviewer-notes", json=note).status_code == 200
        assert (
            client.post(
                path + "/reviewer-notes", json={**note, "criterion_id": "structure"}
            ).status_code
            == 422
        )
        assert (
            client.post(
                path + "/review-methods",
                json={**body, "evidence": [{"page": 2, "quote": "invented"}]},
            ).status_code
            == 422
        )
        assert "SYNTHETIC_RESPONSE" not in json.dumps(provider.contexts)


def test_elapsed_review_sessions_are_explicit_and_close_on_human_finalization(tmp_path):
    with assessment(tmp_path) as (app, client, path, key, _):
        assert client.post(path + "/reviewer-time", json={"action": "STOP"}).status_code == 409
        assert client.post(path + "/reviewer-time", json={"action": "START"}).status_code == 200
        assert client.post(path + "/reviewer-time", json={"action": "START"}).status_code == 409
        app.state.runtime.assessments.records[key].active_review_session["monotonic"] -= 12
        result = client.post(path + "/reviewer-time", json={"action": "STOP"}).json()
        assert result["elapsed_seconds"] >= 12 and result["completed_sessions"] == 1
        assert result["human_time_saved_seconds"] is None
        decide_all(client, path)
        assert client.post(path + "/reviewer-time", json={"action": "START"}).status_code == 200
        assert client.post(path + "/finalize", json={"confirmed": True}).status_code == 200
        info = client.get(path + "/comparison").json()["reviewer_workspace"]["review_time"]
        assert not info["active"] and info["completed_sessions"] == 2
        assert (
            client.post(
                path + "/reviewer-notes", json={"criterion_id": "methodology", "text": "late"}
            ).status_code
            == 409
        )


def test_exact_selected_duplicates_are_printed_once_with_both_original_ids(tmp_path):
    def duplicate_first(findings):
        primary = findings[0]
        primary.conflict = False
        duplicate = primary.model_copy(
            deep=True,
            update={"finding_id": str(uuid4()), "model_id": "mistral", "supplemental": []},
        )
        primary.supplemental.append(duplicate)

    # Inject synthetic model output before the immutable independent snapshot is made.
    with assessment(tmp_path, ai_transform=duplicate_first) as (app, client, path, key, _):
        primary = app.state.runtime.assessments.records[key].ai[0]
        duplicate = primary.supplemental[0]
        workspace = client.get(path + "/comparison").json()["reviewer_workspace"]
        assert workspace["finding_groups"]["redundancy_candidates"] == 1
        decide_all(client, path, primary=primary.criterion_id, duplicate=duplicate.finding_id)
        text = client.get(path + "/draft").json()["text"]
        assert text.count("Freigegebener Befund:") == 1
        assert (
            "Identischer freigegebener Befund zusammengefasst" in text
            and duplicate.finding_id in text
        )
        # Both original findings remain available in the comparison/evidence workspace.
        assert client.get(path + "/comparison").json()["criteria"][0]["ai"]["supplemental"]


def test_workspace_routes_enforce_existing_assessment_acl(tmp_path):
    with assessment(tmp_path) as (app, client, path, key, _):
        app.state.runtime.assessments.access.assignments[key] = frozenset({"foreign"})
        assert client.get(path + "/comparison").status_code == 404
        assert (
            client.post(
                path + "/reviewer-notes", json={"criterion_id": "methodology", "text": "secret"}
            ).status_code
            == 404
        )
        assert client.post(path + "/reviewer-time", json={"action": "START"}).status_code == 404
