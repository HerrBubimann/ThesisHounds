"""Multi-document software evaluation. No expert labels or real inference are fabricated."""

import asyncio

import pytest
from app.core.configuration import RuntimeConfig
from app.evaluation.academic_benchmark import generate_pilot_corpus
from app.evaluation.lab import ExperimentRequest, export_results, run_experiment
from app.llm.gateway import LLMGateway
from app.llm.providers.demo import DemoProvider
from app.services.document_store import pilot_documents

from tests.fixtures.pilot import pilot_setup


def test_generated_pdf_corpus_runs_a_and_e_without_cross_document_repeat_comparisons(tmp_path):
    directory, _, _ = pilot_setup(tmp_path)
    corpus_dir = tmp_path / "corpus"
    manifest = generate_pilot_corpus(corpus_dir)
    assert not manifest["expert_validated"] and manifest["quality_labels"] is None
    assert len(manifest["cases"]) == 6
    assert manifest["cases"][-1]["processing"] == "DENIED_BEFORE_INFERENCE"
    docs = pilot_documents(corpus_dir)
    assert len(docs) == 5
    config = RuntimeConfig(directory)
    gateway = LLMGateway(config.models, {"ollama": DemoProvider()}, config.policy)
    report = asyncio.run(
        run_experiment(
            gateway,
            config,
            ExperimentRequest(
                architectures=["A", "E"],
                document_ids=[d["document_id"] for d in docs],
                repeats=2,
            ),
            pilot_dir=corpus_dir,
        )
    )
    assert report["mocked"] and report["complete"] and len(report["results"]) == 20
    assert len(report["consistency"]) == 10
    assert all(len(c["comparisons"]) == 1 for c in report["consistency"])
    assert all(row["quality"]["precision"] is None for row in report["results"])
    assert len({row["source_pdf_sha256"] for row in report["results"]}) == 5
    first, second = export_results(report, tmp_path / "reports")
    assert first.is_file() and second.is_file()
    with pytest.raises(ValueError, match="EMPTY"):
        generate_pilot_corpus(corpus_dir)


def test_unregistered_corpus_cannot_enter_lab_through_a_public_label(tmp_path):
    directory, _, _ = pilot_setup(tmp_path)
    config = RuntimeConfig(directory)
    gateway = LLMGateway(config.models, {"ollama": DemoProvider()}, config.policy)
    with pytest.raises(ValueError):
        asyncio.run(
            run_experiment(
                gateway,
                config,
                ExperimentRequest(architectures=["A"], document_ids=["pilot-" + "a" * 64]),
            )
        )
