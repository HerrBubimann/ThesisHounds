import asyncio

import httpx
import pytest
from app.config import Settings
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.model_registry import ModelRegistry
from app.llm.providers.base import Completion
from app.llm.providers.ollama import OllamaProvider
from app.security.policy_engine import PolicyConfig, PolicyEngine
from pydantic import BaseModel

from tests.fixtures import CONFIG


class Reply(BaseModel):
    answer: str


class FakeProvider:
    def __init__(self, text='{"answer":"ok"}'):
        self.text = text
        self.calls = []

    async def complete(self, model, messages, output_schema, max_tokens, *, unload):
        self.calls.append((model.id, messages, unload))
        return Completion(text=self.text, model=model.name, input_tokens=10, output_tokens=5)

    async def discover(self):
        return []


def test_registry_and_provider_structured_output():
    async def scenario():
        registry = ModelRegistry.load(CONFIG / "models.yaml")
        assert {m.manufacturer for m in registry.enabled()} == {"Alibaba", "Meta", "Mistral AI"}
        provider = FakeProvider()
        gateway = LLMGateway(registry, {"ollama": provider}, PolicyEngine(PolicyConfig()))
        budget = CallBudget(1, 10000)
        _, reply = await gateway.complete(
            "qwen", "orchestrator", "SYNTHETIC", [], budget, output_type=Reply
        )
        assert reply.answer == "ok"
        assert budget.calls == 1 and budget.observed_tokens == 15
        assert provider.calls[0][2] is True
        with pytest.raises(LLMError) as error:
            await gateway.complete("qwen", "orchestrator", "SYNTHETIC", [], budget)
        assert error.value.status_code == 429
        assert len(provider.calls) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("classification", [None, "UNKNOWN", "SYNTHETIC", "PUBLIC", "CONFIDENTIAL"])
def test_external_provider_is_always_blocked(classification):
    registry = ModelRegistry.load(CONFIG / "models.yaml")
    model = registry.get("qwen").model_copy(update={"local": False, "provider": "openai"})
    with pytest.raises(LLMError):
        PolicyEngine(PolicyConfig()).check(model, classification, "orchestrator")


def test_unknown_classification_treated_as_confidential():
    model = (
        ModelRegistry.load(CONFIG / "models.yaml")
        .get("qwen")
        .model_copy(update={"privacy": "PUBLIC"})
    )
    with pytest.raises(LLMError):
        PolicyEngine(PolicyConfig()).check(model, "untrusted-agent-label", "orchestrator")
    with pytest.raises(ValueError):
        PolicyEngine(PolicyConfig(mode="EXPERIMENTAL"))


def test_ollama_capabilities_resources_and_schema_contract():
    async def scenario():
        import json

        def handler(request):
            if request.url.path == "/api/tags":
                return httpx.Response(
                    200, json={"models": [{"name": "qwen3:8b", "size": 1, "digest": "d"}]}
                )
            if request.url.path == "/api/show":
                return httpx.Response(
                    200, json={"capabilities": ["completion"], "template": "PRIVATE"}
                )
            if request.url.path == "/api/ps":
                return httpx.Response(
                    200, json={"models": [{"name": "qwen3:8b", "size": 100, "size_vram": 50}]}
                )
            payload = json.loads(request.content)
            assert payload["format"] == Reply.model_json_schema()
            assert payload["keep_alive"] == 0
            return httpx.Response(
                200,
                json={"model": "qwen3:8b", "message": {"content": '{"answer":"ok"}'}, "done": True},
            )

        async with httpx.AsyncClient(
            base_url="http://ollama:11434", transport=httpx.MockTransport(handler)
        ) as client:
            provider = OllamaProvider(Settings(_env_file=None), client)
            assert await provider.health()
            assert "template" not in await provider.capabilities("qwen3:8b")
            assert (await provider.resources())["loaded_models"][0]["vram_bytes"] == 50
            result = await provider.complete(
                ModelRegistry.load(CONFIG / "models.yaml").get("qwen"),
                [],
                Reply.model_json_schema(),
                100,
                unload=True,
            )
            assert result.text == '{"answer":"ok"}'

    asyncio.run(scenario())


def test_invalid_structured_output_and_unknown_model():
    async def scenario():
        registry = ModelRegistry.load(CONFIG / "models.yaml")
        gateway = LLMGateway(
            registry, {"ollama": FakeProvider("PRIVATE_INVALID_JSON")}, PolicyEngine(PolicyConfig())
        )
        with pytest.raises(LLMError) as error:
            await gateway.complete(
                "qwen", "orchestrator", "SYNTHETIC", [], CallBudget(2, 10000), output_type=Reply
            )
        assert "PRIVATE" not in error.value.detail
        with pytest.raises(LLMError):
            registry.get("not-registered")
        with pytest.raises(ValueError):
            ModelRegistry([registry.get("qwen"), registry.get("qwen")])

    asyncio.run(scenario())
