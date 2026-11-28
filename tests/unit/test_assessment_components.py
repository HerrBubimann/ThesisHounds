import asyncio
import json
from datetime import timedelta

import pytest
import yaml
from app.assessments.comparison import compare
from app.assessments.profile_registry import ProfileRegistry
from app.assessments.routine_checks import inventory
from app.assessments.rubric_importer import import_candidate
from app.assessments.schemas import AssessmentRequest, CriterionReview, HumanReviewSubmission
from app.config import Settings
from app.evaluation.model_benchmark import CASES, benchmark
from app.llm.errors import LLMError
from app.llm.model_registry import HuggingFaceArtifact, ModelDefinition
from app.schemas.domain import now
from app.services.document_store import Document
from pydantic import ValidationError

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider, human_submission
from tests.fixtures.providers import runtime


def test_doi_inventory_does_not_claim_citation_verification():
    result = inventory(
        Document(
            document_id="synthetic",
            pages={
                1: "Test DOI 10.1234/EXAMPLE. Nochmals 10.1234/example.",
            },
        )
    )
    # A terminal dot may be part of the DOI; candidates preserve it until reviewed.
    assert result["repeated_doi_mentions"] == {"10.1234/example.": 2}
    assert result["verification"] == "UNVERIFIED"


def test_profile_types_and_reviewed_import():
    registry = ProfileRegistry(CONFIG / "assessment_profiles")
    for kind in ["PA1", "PA2", "BA"]:
        profile = registry.get(kind.lower() + "-example", kind)
        assert profile.status == "EXAMPLE"
        for format in ["json", "yaml"]:
            data = profile.model_dump()
            data.update(status="APPROVED", approved_by="forged", approved_at="forged")
            text = json.dumps(data) if format == "json" else yaml.safe_dump(data)
            candidate = import_candidate(text, format)
            assert candidate.status == "CANDIDATE" and not candidate.approved_by
            assert candidate.source.startswith("import-sha256:")
            assert candidate.criteria == profile.criteria
    for text, format in [("[]", "json"), ("x" * 65537, "yaml"), ("", "docx")]:
        with pytest.raises(ValueError):
            import_candidate(text, format)
    data = profile.model_dump()
    data["criteria"].append(data["criteria"][0])
    with pytest.raises(ValueError):
        type(profile).model_validate(data)
    data = profile.model_dump()
    data["status"] = "APPROVED"
    with pytest.raises(ValueError):
        type(profile).model_validate(data)


def test_huggingface_approval_gates_enabled_models():
    from app.llm.model_registry import ModelRegistry

    data = ModelRegistry.load(CONFIG / "models.yaml").get("qwen").model_dump()
    artifact = HuggingFaceArtifact(
        repository="synthetic/model",
        revision="a" * 40,
        license="test-only",
        format="GGUF",
        quantization="test",
        sha256="b" * 64,
        languages=["de"],
    )
    data["huggingface"] = artifact
    with pytest.raises(ValidationError):
        ModelDefinition.model_validate(data)
    data["enabled"] = False
    assert ModelDefinition.model_validate(data).huggingface.approval == "CANDIDATE"
    artifact = artifact.model_copy(
        update={
            "approval": "APPROVED",
            "ollama_compatible": True,
            "license_reviewed": True,
            "provenance_reviewed": True,
            "security_reviewed": True,
            "reviewed_by": "synthetic reviewer",
            "review_date": "2026-11-26",
        }
    )
    data.update(enabled=True, huggingface=artifact)
    assert ModelDefinition.model_validate(data).huggingface.deployable()


def test_university_endpoint_and_environment_aliases(monkeypatch):
    monkeypatch.setenv("OLLAMA_DEFAULT_MODEL", "mistral:7b")
    monkeypatch.setenv("OLLAMA_REQUEST_TIMEOUT", "123")
    settings = Settings(
        _env_file=None,
        deployment_mode="university",
        ollama_base_url="https://inference.example.invalid",
        university_ollama_hosts=["inference.example.invalid"],
        ollama_auth_token="test-token",
    )
    assert settings.llm_model == "mistral:7b" and settings.llm_chat_timeout == 123
    assert "test-token" not in repr(settings)
    for overrides in [
        {"university_ollama_hosts": []},
        {"deployment_mode": "local"},
        {"ollama_base_url": "http://inference.example.invalid"},
        {"ollama_base_url": "https://inference.example.invalid/path"},
    ]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **{**settings.model_dump(), **overrides})
    for flag in ["enable_public_research", "enable_ai_scoring"]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **{flag: True})


def test_lifecycle_limits_cleanup_and_benchmark(tmp_path):
    async def scenario():
        app = runtime(tmp_path)
        provider = AssessmentProvider()
        app.gateway.providers["ollama"] = provider
        flow = app.assessments
        record = flow.create(
            AssessmentRequest(work_type="BA", profile_confirmed=True, profile_id="ba-example")
        )
        key = record["id"]
        flow.submit_human(key, HumanReviewSubmission.model_validate(human_submission()))
        flow.start_ai(key)
        second = flow.create(
            AssessmentRequest(work_type="PA2", profile_confirmed=True, profile_id="pa2-example")
        )
        with pytest.raises(LLMError, match="aktiver"):
            flow.start_ai(second["id"])
        await flow.tasks[key]
        flow.release_ai(key)
        record = flow.get(key)
        ai = record.ai[0]
        human = CriterionReview.model_validate(human_submission()["criteria"][0])
        assert compare(human, ai) == "AGREEMENT"
        assert compare(human.model_copy(update={"judgment": "POSITIVE"}), ai) == "PARTIAL_AGREEMENT"
        assert (
            compare(
                human.model_copy(update={"judgment": "POSITIVE"}),
                ai.model_copy(update={"judgment": "NEGATIVE"}),
            )
            == "DISAGREEMENT"
        )
        assert (
            compare(human, ai.model_copy(update={"evidence_status": "UNVERIFIED"}))
            == "INSUFFICIENT_EVIDENCE"
        )
        report = await benchmark(app.gateway, ["qwen"])
        assert len(report["results"]) == len(CASES)
        assert all(r["schema_valid"] for r in report["results"])
        assert all(r["human_quality_score"] is None for r in report["results"])
        provider.fail = True
        report = await benchmark(app.gateway, ["qwen"])
        assert all(r["error_status"] == 502 for r in report["results"])
        with pytest.raises(ValueError):
            await benchmark(app.gateway, ["qwen"], repeats=11)
        record.created_at = now() - timedelta(hours=2)
        flow.cleanup()
        with pytest.raises(LLMError):
            flow.get(key)
        await app.close()

    asyncio.run(scenario())
