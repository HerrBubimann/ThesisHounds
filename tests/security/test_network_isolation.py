import asyncio
import socket
from unittest.mock import AsyncMock

import httpx
import pytest
import yaml
from app.config import Settings
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.model_registry import ModelRegistry
from app.llm.providers.ollama import OllamaProvider
from app.security.egress_policy import PinnedInferenceTransport, approved_target
from app.security.policy_engine import PolicyConfig, PolicyEngine

from tests.fixtures import CONFIG, MODEL, ROOT


@pytest.mark.parametrize(
    "url",
    [
        "https://api.openai.com/api/chat",
        "http://1.1.1.1:11434/api/chat",
        "http://ollama:443/api/chat",
        "http://ollama:11435/api/chat",
        "http://ollama.evil.invalid:11434/api/chat",
        "http://user:secret@ollama:11434/api/chat",
        "http://[2606:4700:4700::1111]:11434/api/chat",
        "http://ollama:11434/api/pull",
        "http://ollama:11434/api/chat?query=secret",
        "http://ollama:11434/api/chat#secret",
    ],
)
def test_unapproved_destinations_ports_protocols_and_downloads_are_denied(url):
    with pytest.raises(LLMError):
        approved_target(httpx.URL(url))


@pytest.mark.parametrize("addresses", [["1.1.1.1"], ["172.30.20.3", "1.1.1.1"], ["::1"]])
def test_dns_cannot_expand_the_trust_boundary(monkeypatch, addresses):
    async def scenario():
        transport = PinnedInferenceTransport()
        sink = AsyncMock()
        transport.transport = sink
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 11434)) for ip in addresses]
        monkeypatch.setattr(
            asyncio.get_running_loop(), "getaddrinfo", AsyncMock(return_value=records)
        )
        with pytest.raises(LLMError):
            await transport.handle_async_request(
                httpx.Request("GET", "http://ollama:11434/api/tags")
            )
        sink.handle_async_request.assert_not_called()

    asyncio.run(scenario())


def test_valid_dns_result_is_pinned_before_transport_and_no_proxy_is_used(monkeypatch):
    async def scenario():
        monkeypatch.setenv("HTTP_PROXY", "http://external.invalid:8080")
        transport = PinnedInferenceTransport()
        seen = []

        def sink(request):
            seen.append(request.url.host)
            return httpx.Response(200, json={})

        transport.transport = httpx.MockTransport(sink)
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("172.30.20.3", 11434))]
        monkeypatch.setattr(
            asyncio.get_running_loop(), "getaddrinfo", AsyncMock(return_value=records)
        )
        await transport.handle_async_request(httpx.Request("GET", "http://ollama:11434/api/tags"))
        assert seen == ["172.30.20.3"]
        await transport.aclose()

    asyncio.run(scenario())


def test_redirects_and_direct_provider_calls_cannot_bypass_gateway():
    async def scenario():
        seen = []

        def sink(request):
            seen.append(str(request.url))
            if request.url.path == "/api/tags":
                return httpx.Response(200, json={"models": [MODEL]})
            return httpx.Response(307, headers={"location": "https://external.invalid/api/chat"})

        async with httpx.AsyncClient(
            base_url="http://ollama:11434",
            follow_redirects=True,
            transport=httpx.MockTransport(sink),
        ) as client:
            provider = OllamaProvider(Settings(_env_file=None), client)
            model = ModelRegistry.load(CONFIG / "models.yaml").get("qwen")
            with pytest.raises(LLMError):
                await provider.complete(model, [], None, 100, unload=True)
            assert not seen
            gateway = LLMGateway(
                ModelRegistry([model]), {"ollama": provider}, PolicyEngine(PolicyConfig())
            )
            with pytest.raises(LLMError):
                await gateway.complete("qwen", "specialist", "PUBLIC", [], CallBudget(1, 10000))
            assert len(seen) == 2 and all("external.invalid" not in url for url in seen)

    asyncio.run(scenario())


def test_runtime_topology_is_private_and_does_not_include_research_mounts():
    data = yaml.safe_load((ROOT / "compose.yaml").read_text("utf-8"))
    assert all(network["internal"] for network in data["networks"].values())
    assert all(service["dns"] == ["127.0.0.1"] for service in data["services"].values())
    assert set(data["services"]) == {"frontend", "backend", "ollama"}
    assert all("docker.sock" not in str(service) for service in data["services"].values())
