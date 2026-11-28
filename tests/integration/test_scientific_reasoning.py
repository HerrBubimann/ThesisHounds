"""Scripted local model outputs through the real assessment API and disclosure gates."""

import json
from unittest.mock import patch

import pytest

from tests.fixtures.assessments import AssessmentProvider, human_submission
from tests.integration.test_finding_feedback import assessment, feedback


class ScientificProvider(AssessmentProvider):
    async def complete(self, model, messages, output_schema, max_tokens, *, unload):
        result = await super().complete(model, messages, output_schema, max_tokens, unload=unload)
        if "judgment" in output_schema["properties"]:
            data = json.loads(result.text)
            payload = json.loads(messages[-1]["content"])
            page, quote = next(iter(payload["untrusted_pages"].items()))
            data["scientific_claims"] = [
                {
                    "category": "OWN_RESULT",
                    "statement": "SCIENTIFIC_EMBARGO_CANDIDATE",
                    "passage": {"page": int(page), "quote": quote.split("\n…\n")[0]},
                    "rationale": "Synthetic model interpretation only",
                }
            ]
            return result.model_copy(update={"text": json.dumps(data)})
        return result


def test_claims_flow_from_mock_inference_to_released_scoped_review_without_becoming_facts(tmp_path):
    with patch("tests.integration.test_finding_feedback.AssessmentProvider", ScientificProvider):
        with assessment(tmp_path, release=False) as (app, client, path, key, provider):
            assert client.get(path).json()["ai_execution_complete"]
            assert "SCIENTIFIC_EMBARGO_CANDIDATE" not in client.get(path).text
            assert client.get(path + "/comparison").status_code == 409
            client.post(path + "/human-review", json=human_submission())
            client.post(path + "/release", json={"confirmed": True})
            comparison = client.get(path + "/comparison").json()
            ai = comparison["criteria"][0]["ai"]
            assert ai["claim_checks"][0]["original"]["status"] == "QUOTE_MATCHED"
            assert not ai["claim_checks"][0]["factual_error_established"]
            assert ai["information_origins"]["description"] == "UNVERIFIED_FINDING_PROPOSAL"
            assert comparison["coverage"]["status"] == "INCOMPLETE"
            assert not client.get(path).json()["analysis_complete"]
            assert comparison["scientific_consistency"]["graph"]["missing_links"]
            assert all("HUMAN_PRIVATE_MARKER" not in str(prompt) for prompt in provider.contexts)


@pytest.mark.parametrize(
    "action,reason,outcome,category",
    [
        ("ACCEPT", None, "ACCEPTED", None),
        ("REJECT", "MISSING_CONTEXT", "REJECTED", "MISSING_CONTEXT"),
        ("CORRECT", "WRONG_CRITERION", "CORRECTED", "INCORRECT_CRITERION"),
        (
            "INSUFFICIENT_EVIDENCE",
            "INSUFFICIENT_EVIDENCE",
            "INSUFFICIENT_EVIDENCE",
            "INSUFFICIENT_EVIDENCE",
        ),
        ("REJECT", "FACTUAL_ERROR", "REJECTED", "FACTUAL_ERROR"),
        ("REJECT", "DUPLICATE", "REJECTED", "DUPLICATE_FINDING"),
        ("MANUAL_REVIEW_REQUIRED", None, "MANUAL_REVIEW_REQUIRED", None),
    ],
)
def test_human_feedback_has_canonical_outcomes_and_local_latest_version_metrics(
    tmp_path, action, reason, outcome, category
):
    with assessment(tmp_path) as (app, client, path, key, provider):
        original = client.get(path + "/comparison").json()["criteria"][0]["ai"]
        payload = feedback(
            original["finding_id"], action=action, reason=reason, correction="SYNTHETIC_CORRECTION"
        )
        calls = len(provider.contexts)
        for _ in range(2):
            result = client.post(path + "/finding-feedback", json=payload)
            assert result.status_code == 200
            assert result.json()["outcome"] == outcome
            assert result.json()["error_category"] == category
        value = client.get(path + "/provenance").json()["feedback_evaluation"]
        assert value["feedback_versions"] == 2 and value["adjudicated_findings"] == 1
        assert value["groups"][0]["outcomes"] == {outcome: 1}
        assert value["groups"][0]["model_id"] == original["model_id"]
        assert value["classification"] == "RESTRICTED" and not value["automatic_training"]
        assert not value["automatic_model_routing_changes"] and len(provider.contexts) == calls
        if action == "MANUAL_REVIEW_REQUIRED":
            client.post(path + "/manual-review", json={"confirmed": True})
            decision = {
                "criterion_id": original["criterion_id"],
                "include_ai_finding": True,
                "conclusion": "Synthetic decision",
                "rationale": "Synthetic reason",
            }
            assert client.post(path + "/decisions", json=decision).status_code == 409
            assert (
                original["finding_id"]
                in client.get(path + "/comparison").json()["coverage"]["open_finding_decisions"]
            )
        app.state.runtime.assessments.access.assignments[key] = frozenset({"foreign"})
        assert client.get(path + "/comparison").status_code == 404
        assert client.get(path + "/provenance").status_code == 404
