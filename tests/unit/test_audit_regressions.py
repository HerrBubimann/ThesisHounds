"""G08/G15/G16/G17: regressions from the preserved 2026-11-27 audit."""

import asyncio
import socket
from unittest.mock import AsyncMock

import httpx
import pytest
from app.assessments.coverage import check_coverage, criterion_states
from app.assessments.profile_registry import ProfileRegistry
from app.assessments.schemas import AssessmentRequest, CriterionDecision, HumanReviewSubmission
from app.config import Settings
from app.llm.errors import LLMError
from app.research import local_verification, provider_registry
from app.research.citations import extract_citations
from app.security.egress_policy import PinnedInferenceTransport
from app.services.document_store import Document

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider, human_submission
from tests.fixtures.providers import runtime


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("indent", ["    ", "\t", "\u2003"])
def test_g15_original_spans_for_indented_and_multiline_references(newline, indent):
    text = newline.join(
        [
            "Literaturverzeichnis",
            indent + "[1] M\u00fcller (2024). Nachvollziehbare Forschung.",
            indent + "    Fortsetzung mit \u03b1 und doi:10.1234/example",
            indent + "[2] Meier (2023). Zweite Quelle. doi:10.1234/second",
        ]
    )
    document = Document(document_id="synthetic-audit", pages={1: text}, complete=True)
    entries = extract_citations(document)["entries"]
    assert len(entries) == 2
    assert "Fortsetzung" in entries[0].raw and entries[0].doi == "10.1234/example"
    for entry in entries:
        assert text[entry.start : entry.end] == entry.raw


@pytest.mark.parametrize(
    "value,expected",
    [
        (" http://doi.org/10.1234/Example ", "10.1234/example"),
        ("HTTPS://DOI.ORG/10.1234%2FEx%28ample%29", "10.1234/ex(ample)"),
        (" doi: 10.1234/Example ", "10.1234/example"),
        ("<https://doi.org/10.1234/Example>", "10.1234/example"),
        ("10.1234/Example.", "10.1234/example."),
        ("10.1234/Example;", "10.1234/example;"),
        ("10.1234/Example)", "10.1234/example)"),
        ("10.1234/Ex%2Fample", "10.1234/ex%2fample"),
        ("10.1234%2FExample", "10.1234/example"),
        ("10.1234/Ex ample", ""),
    ],
)
def test_g16_one_canonical_doi_function_preserves_ambiguous_suffixes(value, expected):
    assert local_verification.normalize_doi(value) == expected
    assert provider_registry.normalize_doi(value) == expected
    assert local_verification.normalize_doi is provider_registry.normalize_doi


def test_g08_explicit_https_pin_preserves_tls_hostname_and_denies_dns_rebinding(monkeypatch):
    async def scenario():
        settings = Settings(
            _env_file=None,
            deployment_mode="university",
            ollama_base_url="https://inference.example.invalid",
            university_ollama_hosts=["inference.example.invalid"],
            university_ollama_ips=["10.60.0.5"],
        )
        transport = PinnedInferenceTransport(settings)
        seen = []

        def sink(request):
            seen.append(request)
            return httpx.Response(200, json={})

        transport.transport = httpx.MockTransport(sink)
        resolver = AsyncMock(
            return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.60.0.5", 443))]
        )
        monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", resolver)
        await transport.handle_async_request(
            httpx.Request("GET", "https://inference.example.invalid/api/tags")
        )
        assert seen[0].url.host == "10.60.0.5"
        assert seen[0].headers["host"] == "inference.example.invalid"
        assert seen[0].extensions["sni_hostname"] == "inference.example.invalid"
        resolver.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443))]
        with pytest.raises(LLMError):
            await transport.handle_async_request(
                httpx.Request("GET", "https://inference.example.invalid/api/tags")
            )
        assert len(seen) == 1
        await transport.aclose()

    asyncio.run(scenario())


def test_g17_missing_optional_finding_can_be_compared_and_finalized(tmp_path):
    async def scenario():
        app = runtime(tmp_path)
        app.gateway.providers["ollama"] = AssessmentProvider()
        flow = app.assessments
        record = flow.create(AssessmentRequest(work_type="PA1", profile_id="pa1-example"))
        key = record["id"]
        item = flow.records[key]
        item.profile.criteria[-1].required = False
        item.ai = await flow.reviewer.review(key, item.document, item.profile, item.budget)
        item.ai = [f for f in item.ai if f.criterion_id != "structure"]
        item.ai_state = "COMPLETED"
        flow.submit_human(key, HumanReviewSubmission.model_validate(human_submission()))
        flow.release_ai(key)
        row = flow.comparison(key)["criteria"][-1]
        assert row["ai"] is None and row["ai_state"] == "OPTIONAL_NOT_REVIEWED"
        flow.acknowledge_manual_review(key)
        for criterion in item.profile.criteria:
            flow.decide(
                key,
                CriterionDecision(
                    criterion_id=criterion.id,
                    include_ai_finding=False,
                    conclusion="Synthetic human decision",
                    rationale="Synthetic human rationale",
                ),
            )
        assert flow.finalize(key)["label"] == "Menschlich freigegeben"
        await app.close()

    asyncio.run(scenario())


def test_g17_execution_states_and_required_coverage_are_distinct():
    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    profile.criteria[-1].required = False
    assert set(criterion_states(profile, [], "PENDING").values()) == {"PENDING"}
    assert set(criterion_states(profile, [], "FAILED").values()) == {"FAILED"}
    states = criterion_states(profile, [], "COMPLETED")
    assert states["structure"] == "OPTIONAL_NOT_REVIEWED"
    assert states["methodology"] == "FAILED"
    assert not check_coverage(profile, []).complete


def test_g16_retraction_adapter_preserves_semicolon_inside_identifier():
    from datetime import UTC, datetime

    records = provider_registry.import_metadata(
        b"OriginalPaperDOI,Title,RetractionNature\n10.1234/test;part,Test,Retraction\n",
        "retraction_watch",
        retrieved_at=datetime.now(UTC),
        provenance="SYNTHETIC_TEST",
        public_provenance_checked=True,
    )
    assert len(records) == 1 and records[0].doi == "10.1234/test;part"


@pytest.mark.parametrize("pins", [[], ["1.1.1.1"], ["169.254.169.254"], ["127.0.0.1"]])
def test_g08_public_link_local_and_unpinned_university_targets_stay_denied(pins):
    from app.security.egress_policy import approved_target

    settings = Settings(
        _env_file=None,
        deployment_mode="university",
        ollama_base_url="https://inference.example.invalid",
        university_ollama_hosts=["inference.example.invalid"],
        university_ollama_ips=pins,
    )
    with pytest.raises(LLMError):
        approved_target(httpx.URL("https://inference.example.invalid/api/tags"), settings)
    with pytest.raises(ValueError, match="TLS"):
        PinnedInferenceTransport(settings, verify=False)
