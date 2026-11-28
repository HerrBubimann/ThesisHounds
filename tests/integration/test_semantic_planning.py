"""Real PDF/API/lab integration with explicitly SCRIPTED mock semantic responses."""

import asyncio
import json
from unittest.mock import patch

import pytest
from app.config import Settings
from app.core.configuration import RuntimeConfig
from app.evaluation.lab import ExperimentRequest, export_results, run_experiment
from app.evaluation.metrics import HumanReferenceSet, digest, planning_metrics
from app.llm.errors import LLMError
from app.llm.gateway import LLMGateway
from app.main import create_app
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from tests.fixtures import CONFIG
from tests.fixtures.assessments import human_submission
from tests.fixtures.pilot import pdf_bytes, pilot_setup
from tests.fixtures.semantic_planning import SemanticProvider


def test_planning_is_embargoed_and_bound_to_a_registered_pdf(tmp_path):
    directory, catalog, document_id = pilot_setup(tmp_path)
    provider = SemanticProvider(model_digest="a" * 64)
    app = create_app(
        Settings(
            _env_file=None,
            config_dir=directory,
            document_store_dir=tmp_path / "runtime",
            pilot_document_dir=catalog,
            pilot_profile_id="pa1-example",
        )
    )
    with patch("app.main.create_provider", return_value=provider), TestClient(app) as client:
        response = client.post(
            "/api/v1/assessments",
            json={
                "work_type": "PA1",
                "profile_confirmed": True,
                "profile_id": "pa1-example",
                "document_id": document_id,
            },
        )
        assert response.status_code == 201
        path = "/api/v1/assessments/" + response.json()["id"]
        assert client.post(path + "/human-review", json=human_submission()).status_code == 200
        assert client.post(path + "/ai-review").status_code == 202

        async def wait():
            await app.state.runtime.assessments.tasks[response.json()["id"]]

        client.portal.call(wait)
        assert client.get(path).json()["ai_state"] == "COMPLETED"
        assert client.get(path + "/provenance").status_code == 409
        assert "understanding" not in client.get(path).text
        assert client.post(path + "/release", json={"confirmed": True}).status_code == 200
        provenance = client.get(path + "/provenance").json()
        assert provenance["adaptive_planning"]["status"] == "VALIDATED_PROPOSAL"
        assert provenance["adaptive_planning"]["mocked"]
        assert all("HUMAN_PRIVATE_MARKER" not in json.dumps(p) for p in provider.planning_calls)
        extra = next(
            row["ai"]
            for row in client.get(path + "/comparison").json()["criteria"]
            if row["criterion_id"] == "methodology"
        )["supplemental"][0]
        evidence = client.get(path + "/findings/" + extra["finding_id"] + "/evidence").json()
        assert evidence["matched"] and evidence["source_sha256"] == document_id[6:]


def test_a_b_c_planning_comparison_uses_same_documents_criteria_and_separate_repeat_groups(
    tmp_path,
):
    from datetime import UTC, datetime

    from app.evaluation.academic_benchmark import PLANNING_CASES
    from app.services.document_store import PilotApproval, register_pilot_pdf

    directory, catalog, _ = pilot_setup(tmp_path)
    ids = [
        register_pilot_pdf(
            catalog,
            pdf_bytes(text),
            PilotApproval(
                kind="SYNTHETIC",
                reviewed_by="SCRIPTED_TEST_NOT_EXPERT",
                reviewed_at=datetime.now(UTC),
                provenance=key,
            ),
        )
        for key, text in PLANNING_CASES.items()
    ]

    class ScriptedCorpusProvider(SemanticProvider):
        async def complete(self, model, messages, output_schema, max_tokens, *, unload):
            if "understanding" in output_schema["properties"]:
                text = " ".join(
                    s["text"] for s in json.loads(messages[-1]["content"])["untrusted_spans"]
                )
                # This is an explicit fixture lookup, not a real semantic classifier.
                self.applied = PLANNING_CASES["applied-without-keywords"] in text
                self.count = int(self.applied)
            return await super().complete(model, messages, output_schema, max_tokens, unload=unload)

    config = RuntimeConfig(directory)
    gateway = LLMGateway(
        config.models, {"ollama": ScriptedCorpusProvider(model_digest="a" * 64)}, config.policy
    )
    report = asyncio.run(
        run_experiment(
            gateway,
            config,
            ExperimentRequest(
                document_ids=ids, architectures=["D"], planning_variants=["A", "B", "C"], repeats=2
            ),
            pilot_dir=catalog,
        )
    )
    assert report["complete"] and report["mocked"] and len(report["results"]) == 12
    assert len(report["consistency"]) == 6 and all(
        len(g["comparisons"]) == 1 for g in report["consistency"]
    )
    for document_id in ids:
        rows = [r for r in report["results"] if r["document_id"] == document_id]
        assert (
            len({r["dataset_sha256"] for r in rows})
            == len({r["profile_sha256"] for r in rows})
            == 1
        )
    for row in report["results"]:
        assert row["coverage_complete"] and row["planning_execution_complete"]
        assert row["planning_evaluation"]["specialist_relevance"] is None
        assert row["quality"]["precision"] is None
    for key, expected in [(ids[0], {"A": 0, "B": 1, "C": 0}), (ids[1], {"A": 0, "B": 0, "C": 1})]:
        for row in report["results"]:
            if row["document_id"] == key:
                assert (
                    row["planning_evaluation"]["completed_specialists"]
                    == expected[row["planning_variant"]]
                )
    assert all(p.is_file() for p in export_results(report, tmp_path / "result"))


def test_unavailable_semantic_arm_does_not_count_as_a_successful_comparison():
    class UnavailablePlanner(SemanticProvider):
        async def complete(self, *args, **kwargs):
            if "understanding" in args[2]["properties"]:
                raise LLMError(503, "SCRIPTED_UNAVAILABLE")
            return await super().complete(*args, **kwargs)

    config = RuntimeConfig(CONFIG)
    gateway = LLMGateway(config.models, {"ollama": UnavailablePlanner()}, config.policy)
    report = asyncio.run(
        run_experiment(
            gateway,
            config,
            ExperimentRequest(architectures=["D"], planning_variants=["C"], repeats=1),
        )
    )
    assert not report["complete"] and report["results"][0]["status"] == "PLANNING_INCOMPLETE"


def test_planning_quality_requires_explicit_human_adjudication():
    proposal = {"key": "synthetic-proposal"}
    plan = {"proposals": [proposal], "execution": []}
    assert planning_metrics(plan, None)["unnecessary_specialists"] is None
    reference = HumanReferenceSet(
        dataset_sha256="a" * 64,
        profile_sha256="b" * 64,
        adjudicated_by=["SYNTHETIC_TEST_NOT_EXPERT"],
        reference_ids=[],
        adjudications=[],
        required_specialist_ids=["required-one", "required-two"],
    )
    assert planning_metrics(plan, reference)["specialist_relevance"] is None
    adjudications = [
        {
            "proposal_sha256": digest(proposal),
            "relevant": True,
            "matched_specialist_ids": ["required-one"],
        }
    ]
    reference = HumanReferenceSet.model_validate(
        {**reference.model_dump(), "specialist_adjudications": adjudications}
    )
    measured = planning_metrics(plan, reference)
    assert measured["specialist_relevance"] == 1 and measured["unnecessary_specialists"] == 0
    assert measured["missing_necessary_specialists"] == 1
    with pytest.raises(ValueError):
        ExperimentRequest(planning_variants=["A", "B", "C"])


def test_existing_review_view_can_explain_dynamic_tasks_and_their_original_spans():
    plan = {
        "mode": "semantic",
        "status": "VALIDATED_PROPOSAL",
        "mocked": True,
        "understanding": {"procedures": [{"name": "Gruppenvergleich", "use": "APPLIED"}]},
        "proposals": [
            {
                "name": "Freie fachliche Rolle",
                "category": "methodology",
                "criterion_id": "methodology",
                "rationale": "Begründete Zusatzprüfung",
                "task": "Prüfe alternative Erklärungen",
                "resolved_evidence": [
                    {"page": 2, "start": 10, "end": 24, "quote": "Originalstelle"}
                ],
            }
        ],
    }
    ui = AppTest.from_string(
        "from frontend.assessment_review import render_adaptive_planning\n"
        + "render_adaptive_planning("
        + repr(plan)
        + ")"
    ).run()
    assert not ui.exception and ui.info
    assert any("Freie fachliche Rolle" in t.value for t in ui.text)
    assert any("Seite 2, Zeichen 10–24: Originalstelle" in t.value for t in ui.text)
