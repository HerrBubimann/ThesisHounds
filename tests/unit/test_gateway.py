import asyncio

import httpx
import pytest
from app.config import Settings
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway, estimate_input_tokens
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


@pytest.mark.parametrize(
    "content", ["Deutsche Größe: äußere Prüfung", "你好世界", "👩🏽‍💻", '"\\\n']
)
def test_input_reservation_handles_unicode_escaping_and_schema(content):
    messages = [{"role": "user", "content": content}]
    plain = estimate_input_tokens(messages, None)
    structured = estimate_input_tokens(messages, Reply.model_json_schema())
    # Unicode must not be discounted using an average characters/token divisor.
    assert plain >= len(content.encode("utf-8")) + 512 + 32
    assert structured > plain
    assert estimate_input_tokens(messages * 2, None) >= plain + 32
    assert estimate_input_tokens([{"role": "system", "content": content}], None) > plain


@pytest.mark.parametrize("output_type", [None, Reply])
def test_context_and_token_budget_boundaries_before_provider_call(output_type):
    async def scenario():
        registry = ModelRegistry.load(CONFIG / "models.yaml")
        provider = FakeProvider()
        gateway = LLMGateway(registry, {"ollama": provider}, PolicyEngine(PolicyConfig()))
        messages = [{"role": "user", "content": 'Prüfe "Methodik".\n'}]
        schema = output_type.model_json_schema() if output_type else None
        required = estimate_input_tokens(messages, schema) + 100
        model = registry.get("qwen")
        registry.models["qwen"] = model.model_copy(update={"context_length": required - 1})
        budget = CallBudget(2, required)
        with pytest.raises(LLMError) as error:
            await gateway.complete(
                "qwen",
                "orchestrator",
                "SYNTHETIC",
                messages,
                budget,
                output_type=output_type,
                max_tokens=100,
            )
        assert error.value.status_code == 422
        assert not provider.calls and budget.calls == 0
        registry.models["qwen"] = model.model_copy(update={"context_length": required})
        with pytest.raises(LLMError) as error:
            await gateway.complete(
                "qwen",
                "orchestrator",
                "SYNTHETIC",
                messages,
                CallBudget(2, required - 1),
                output_type=output_type,
                max_tokens=100,
            )
        assert error.value.status_code == 429 and not provider.calls
        await gateway.complete(
            "qwen",
            "orchestrator",
            "SYNTHETIC",
            messages,
            budget,
            output_type=output_type,
            max_tokens=100,
        )
        assert len(provider.calls) == 1 and budget.reserved_tokens == required
        assert budget.observed_tokens == 15
        with pytest.raises(LLMError) as error:
            await gateway.complete(
                "qwen",
                "orchestrator",
                "SYNTHETIC",
                messages,
                budget,
                output_type=output_type,
                max_tokens=100,
            )
        assert error.value.status_code == 429 and len(provider.calls) == 1

    asyncio.run(scenario())


def test_many_empty_messages_cannot_bypass_context_limit():
    async def scenario():
        provider = FakeProvider()
        gateway = LLMGateway(
            ModelRegistry.load(CONFIG / "models.yaml"),
            {"ollama": provider},
            PolicyEngine(PolicyConfig()),
        )
        with pytest.raises(LLMError) as error:
            await gateway.complete(
                "qwen",
                "orchestrator",
                "SYNTHETIC",
                [{"role": "user", "content": ""}] * 256,
                CallBudget(1, 100000),
                max_tokens=100,
            )
        assert error.value.status_code == 422 and not provider.calls

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "input_tokens,output_tokens,unknown",
    [
        (150, 10, 0),
        (10, 90, 0),
        (None, 90, 1),
        (150, None, 1),
        (None, None, 1),
    ],
)
def test_observed_usage_reconciles_each_component_without_refunding(
    input_tokens,
    output_tokens,
    unknown,
):
    budget = CallBudget(2, 10000)
    budget.reserve(100, 50)
    budget.record(
        Completion(text="ok", model="mock", input_tokens=input_tokens, output_tokens=output_tokens),
        reserved_input=100,
        reserved_output=50,
    )
    assert budget.reserved_tokens == (max(100, input_tokens or 0) + max(50, output_tokens or 0))
    assert budget.observed_tokens == (input_tokens or 0) + (output_tokens or 0)
    assert budget.unknown_token_calls == unknown


def test_reported_overrun_blocks_response_and_subsequent_calls():
    class OverrunProvider(FakeProvider):
        async def complete(self, *args, **kwargs):
            result = await super().complete(*args, **kwargs)
            return result.model_copy(update={"input_tokens": 1000, "output_tokens": 20})

    async def scenario():
        provider = OverrunProvider()
        gateway = LLMGateway(
            ModelRegistry.load(CONFIG / "models.yaml"),
            {"ollama": provider},
            PolicyEngine(PolicyConfig()),
        )
        budget = CallBudget(2, 1000)
        results = []
        with pytest.raises(LLMError) as error:
            await gateway.complete(
                "qwen",
                "orchestrator",
                "SYNTHETIC",
                [],
                budget,
                max_tokens=100,
                on_result=results.append,
            )
        assert error.value.status_code == 429
        assert budget.observed_tokens == 1020 and budget.reserved_tokens == 1100
        assert len(results) == 1 and budget.unknown_token_calls == 0
        with pytest.raises(LLMError) as error:
            await gateway.complete(
                "qwen",
                "orchestrator",
                "SYNTHETIC",
                [],
                budget,
                max_tokens=100,
            )
        assert error.value.status_code == 429 and len(provider.calls) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize("max_tokens", [-100000, 0, True, 1.5, "100"])
def test_invalid_output_limit_cannot_reduce_budget_or_reach_provider(max_tokens):
    async def scenario():
        provider = FakeProvider()
        gateway = LLMGateway(
            ModelRegistry.load(CONFIG / "models.yaml"),
            {"ollama": provider},
            PolicyEngine(PolicyConfig()),
        )
        budget = CallBudget(2, 10000)
        with pytest.raises(LLMError) as error:
            await gateway.complete(
                "qwen", "orchestrator", "SYNTHETIC", [], budget, max_tokens=max_tokens
            )
        assert error.value.status_code == 422
        assert budget.calls == budget.reserved_tokens == budget.observed_tokens == 0
        assert not provider.calls

    asyncio.run(scenario())


@pytest.mark.parametrize("bounds", [(-1, 10), (0, -1), (0, 0), (False, 10), (0, 1.5)])
def test_invalid_reservation_leaves_budget_unchanged(bounds):
    budget = CallBudget(2, 1000)
    with pytest.raises(LLMError) as error:
        budget.reserve(*bounds)
    assert error.value.status_code == 422
    assert budget.calls == budget.reserved_tokens == 0


@pytest.mark.parametrize("limited_by", ["calls", "tokens"])
def test_parallel_calls_share_budget_without_overspending(limited_by):
    class YieldingProvider(FakeProvider):
        async def complete(self, *args, **kwargs):
            await asyncio.sleep(0)
            return await super().complete(*args, **kwargs)

    async def scenario():
        provider = YieldingProvider()
        gateway = LLMGateway(
            ModelRegistry.load(CONFIG / "models.yaml"),
            {"ollama": provider},
            PolicyEngine(PolicyConfig()),
            max_parallel=2,
            sequential_loading=False,
        )
        per_call = estimate_input_tokens([], None) + 100
        budget = CallBudget(
            2 if limited_by == "calls" else 10, 10000 if limited_by == "calls" else 2 * per_call
        )
        results = await asyncio.wait_for(
            asyncio.gather(
                *(
                    gateway.complete(
                        "qwen", "orchestrator", "SYNTHETIC", [], budget, max_tokens=100
                    )
                    for _ in range(6)
                ),
                return_exceptions=True,
            ),
            timeout=2,
        )
        errors = [result for result in results if isinstance(result, LLMError)]
        assert len(errors) == 4 and all(error.status_code == 429 for error in errors)
        assert len(provider.calls) == budget.calls == 2
        assert budget.reserved_tokens == 2 * per_call
        assert budget.observed_tokens == 30 and budget.unknown_token_calls == 0
        assert all(call[2] is False for call in provider.calls)

    asyncio.run(scenario())


def test_cancellation_keeps_reservation_and_releases_model_slot():
    class BlockingProvider(FakeProvider):
        def __init__(self):
            super().__init__()
            self.started = asyncio.Event()
            self.calls_started = 0

        async def complete(self, *args, **kwargs):
            self.calls_started += 1
            if self.calls_started == 1:
                self.started.set()
                await asyncio.Event().wait()
            return await super().complete(*args, **kwargs)

    async def scenario():
        provider = BlockingProvider()
        gateway = LLMGateway(
            ModelRegistry.load(CONFIG / "models.yaml"),
            {"ollama": provider},
            PolicyEngine(PolicyConfig()),
        )
        budget = CallBudget(2, 10000)
        first = asyncio.create_task(
            gateway.complete("qwen", "orchestrator", "SYNTHETIC", [], budget, max_tokens=100)
        )
        try:
            await asyncio.wait_for(provider.started.wait(), timeout=2)
        finally:
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
        reserved = budget.reserved_tokens
        assert budget.calls == budget.unknown_token_calls == 1 and reserved > 0
        result, _ = await asyncio.wait_for(
            gateway.complete("qwen", "orchestrator", "SYNTHETIC", [], budget, max_tokens=100),
            timeout=2,
        )
        assert result.text == provider.text
        assert budget.calls == 2 and budget.reserved_tokens == 2 * reserved
        assert budget.unknown_token_calls == 1 and budget.observed_tokens == 15

    asyncio.run(scenario())


def test_cancelling_queued_call_does_not_charge_or_block_next_call():
    class QueuedProvider(FakeProvider):
        def __init__(self):
            super().__init__()
            self.started = asyncio.Event()
            self.release = asyncio.Event()

        async def complete(self, *args, **kwargs):
            self.started.set()
            await self.release.wait()
            return await super().complete(*args, **kwargs)

    async def scenario():
        provider = QueuedProvider()
        gateway = LLMGateway(
            ModelRegistry.load(CONFIG / "models.yaml"),
            {"ollama": provider},
            PolicyEngine(PolicyConfig()),
        )
        budget = CallBudget(2, 10000)

        async def call():
            return await gateway.complete(
                "qwen", "orchestrator", "SYNTHETIC", [], budget, max_tokens=100
            )

        first = asyncio.create_task(call())
        waiting = None
        try:
            await asyncio.wait_for(provider.started.wait(), timeout=2)
            waiting = asyncio.create_task(call())
            await asyncio.sleep(0)  # Let the second task reach the occupied semaphore.
            reserved = budget.reserved_tokens
            waiting.cancel()
            with pytest.raises(asyncio.CancelledError):
                await waiting
            assert budget.calls == 1 and budget.reserved_tokens == reserved
            assert budget.unknown_token_calls == 0
            provider.release.set()
            await asyncio.wait_for(first, timeout=2)
            await asyncio.wait_for(call(), timeout=2)
            assert len(provider.calls) == budget.calls == 2
            assert budget.observed_tokens == 30 and budget.unknown_token_calls == 0
        finally:
            provider.release.set()
            for task in [first, waiting]:
                if task is not None:
                    task.cancel()
            await asyncio.gather(
                *(task for task in [first, waiting] if task is not None), return_exceptions=True
            )

    asyncio.run(scenario())
