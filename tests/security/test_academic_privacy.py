import asyncio
import json
import socket
from unittest.mock import AsyncMock

import httpx
import pytest
import yaml
from app.config import Settings
from app.evaluation.privacy_lab import run_privacy_benchmark
from app.knowledge.registry import InstitutionalRegistry
from app.llm.errors import LLMError
from app.research.gateway import ResearchGateway, ResearchQuery
from app.security.privacy_policy_engine import (
    Decision,
    PrivacyPolicyEngine,
    ProcessingContext,
    SecurityMode,
)
from app.services.grobid import (
    PARAMETERS,
    PARSER_URL,
    LocalGrobid,
    PinnedParserTransport,
    parse_tei,
    parser_dispatch,
)
from defusedxml.common import DefusedXmlException

from infrastructure.scripts.prepare_grobid import secure_config
from tests.fixtures import ROOT
from tests.unit.test_institutional_rules import profile, source

TEI = (
    b'<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body><p>Claim '
    b'<ref type="bibr" target="#b1">[1]</ref></p></body><back><listBibl>'
    b'<biblStruct xml:id="b1"><analytic><title>Synthetic paper</title>'
    b"<author><surname>Muster</surname></author></analytic>"
    b'<idno type="DOI">10.5555/test</idno></biblStruct></listBibl></back></text></TEI>'
)


@pytest.mark.parametrize(
    "classification", [None, "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "invalid"]
)
def test_private_or_unknown_library_cannot_be_exposed_with_claimed_clearance(classification):
    registry = InstitutionalRegistry([source(classification=classification)], [profile()])
    assert not registry.resolve("data_science_ai", "DS25", "PA1")["sources"]
    assert not registry.resolve("data_science_ai", "DS25", "PA1", clearance=classification)[
        "sources"
    ]


@pytest.mark.parametrize(
    "provider",
    [
        "crossref",
        "openalex",
        "semantic_scholar",
        "datacite",
        "unpaywall",
        "arxiv",
        "retraction_watch",
    ],
)
def test_confidential_doi_lists_never_dispatch(provider):
    query = ResearchQuery(
        terms="10.5555/project-doi-list", classification="RESTRICTED", provider=provider
    )
    with pytest.raises(LLMError):
        asyncio.run(ResearchGateway().search(query))


def test_provisioning_mode_never_gets_an_analysis_context():
    with pytest.raises(ValueError, match="PRODUCTION_NOT_READY"):
        Settings(_env_file=None, security_mode="MODEL_PROVISIONING")
    decision = PrivacyPolicyEngine().decide(
        ProcessingContext(
            classification="PUBLIC",
            mode=SecurityMode.MODEL_PROVISIONING,
            authorized=True,
            external=False,
            local_boundary_verified=True,
            target_approved=True,
        )
    )
    assert decision == Decision.DENY


def test_grobid_request_disables_all_consolidation_and_does_not_follow_redirects():
    async def scenario():
        captured = []

        def sink(request):
            captured.append(request)
            body = request.read()
            for name, value in PARAMETERS.items():
                assert f'name="{name}"'.encode() in body
                assert f"\r\n\r\n{value}\r\n".encode() in body
            return httpx.Response(200, content=TEI)

        async with httpx.AsyncClient(transport=httpx.MockTransport(sink)) as client:
            adapter = LocalGrobid(enabled=True, client=client)
            for classification in (None, "INTERNAL", "CONFIDENTIAL", "RESTRICTED"):
                with pytest.raises(LLMError):
                    await adapter.extract(
                        b"%PDF-synthetic",
                        classification,
                        authorized=True,
                        public_fixture_confirmed=True,
                    )
            assert not captured
            result = await adapter.extract(
                b"%PDF-synthetic", "PUBLIC", authorized=True, public_fixture_confirmed=True
            )
            assert len(captured) == 1 and str(captured[0].url) == PARSER_URL
            assert result["references"][0]["doi"] == "10.5555/test"
            assert not result["external_consolidation"]
            assert not result["citations"][0]["mapping_verified"]
        targets = []

        def redirect(request):
            targets.append(str(request.url))
            return httpx.Response(307, headers={"Location": "https://controlled-sink.invalid"})

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(redirect), follow_redirects=True
        ) as client:
            with pytest.raises(LLMError):
                await LocalGrobid(enabled=True, client=client).extract(
                    b"%PDF-synthetic", "PUBLIC", authorized=True, public_fixture_confirmed=True
                )
        assert targets == [PARSER_URL]

    asyncio.run(scenario())


def test_grobid_pin_cannot_be_bypassed_by_dns_or_arbitrary_paths(monkeypatch):
    async def scenario():
        transport = PinnedParserTransport()
        await transport.transport.aclose()
        sink = AsyncMock()
        transport.transport = sink
        for address, allowed in [("1.1.1.1", False), ("::1", False), ("172.30.30.3", True)]:
            records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 8070))]
            monkeypatch.setattr(
                asyncio.get_running_loop(), "getaddrinfo", AsyncMock(return_value=records)
            )
            token = parser_dispatch.set(True)
            try:
                request = httpx.Request("POST", PARSER_URL)
                if allowed:
                    await transport.handle_async_request(request)
                    assert request.url.host == "172.30.30.3"
                else:
                    with pytest.raises(LLMError):
                        await transport.handle_async_request(request)
            finally:
                parser_dispatch.reset(token)
        with pytest.raises(LLMError):
            await transport.handle_async_request(httpx.Request("POST", PARSER_URL))
        assert sink.handle_async_request.await_count == 1

    asyncio.run(scenario())


def test_grobid_configuration_routes_even_accidental_consolidation_to_dead_local_service():
    original = {
        "grobid": {
            "models": [{"name": "header"}],
            "consolidation": {"service": "crossref", "crossref": {"token": "synthetic-credential"}},
        }
    }
    secured = secure_config(original)["grobid"]
    assert secured["consolidation"]["service"] == "glutton"
    assert secured["consolidation"]["glutton"]["url"] == "http://127.0.0.1:9"
    assert secured["consolidation"]["crossref"]["token"] is None
    assert original["grobid"]["consolidation"]["service"] == "crossref"
    compose = yaml.safe_load((ROOT / "compose.grobid.yaml").read_text("utf-8"))
    grobid = compose["services"]["grobid"]
    assert not grobid.get("ports") and grobid["pull_policy"] == "never"
    assert grobid["logging"]["driver"] == "none" and grobid["user"] == "10001:10001"
    assert all(n["internal"] and not n["enable_ipv6"] for n in compose["networks"].values())
    assert "documents" not in str(grobid["volumes"]) and grobid["dns"] == ["127.0.0.1"]
    for bad in (
        b"",
        b"x" * 8_000_001,
        b'<!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><a>&x;</a>',
    ):
        with pytest.raises((ValueError, DefusedXmlException)):
            parse_tei(bad)


def test_privacy_ablation_is_in_memory_and_exports_no_canary_values():
    markers = json.loads(
        (ROOT / "tests/fixtures/synthetic/privacy_canaries.json").read_text("utf-8")
    )
    report = run_privacy_benchmark(markers)
    assert report["protected_variant_passed"] and len(report["rows"]) == 48
    assert report["aggregates"]["D"]["unauthorized_actions"] == 0
    assert report["aggregates"]["C"]["unauthorized_actions"] == 2
    assert report["actual_network_requests"] == 0
    assert not any(marker in json.dumps(report) for marker in markers)
    with pytest.raises(ValueError):
        run_privacy_benchmark([])
