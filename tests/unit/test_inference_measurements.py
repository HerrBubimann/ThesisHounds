import asyncio
import json

import httpx
import pytest
from app.config import Settings
from app.core.configuration import RuntimeConfig
from app.evaluation.model_benchmark import CASES, benchmark
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.providers.base import Completion
from app.llm.providers.ollama import OllamaProvider
from app.monitoring.resources import completion_metrics, loaded_vram_bytes

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider


def test_token_throughput_uses_provider_generation_time_not_request_wall_time():
    measured = completion_metrics(
        Completion(
            text="synthetic",
            model="x",
            output_tokens=60,
            generation_duration_seconds=2,
            total_duration_seconds=10,
            load_duration_seconds=7,
            first_content_seconds=8,
        )
    )
    assert measured["tokens_per_second"] == 30 and measured["provider_total_seconds"] == 10
    assert measured["first_content_chunk_seconds"] == 8 and measured["ttft_seconds"] is None
    assert completion_metrics(Completion(text="x", model="x"))["tokens_per_second"] is None
    with pytest.raises(ValueError):
        Completion(text="x", model="x", generation_duration_seconds=float("nan"))
    with pytest.raises(ValueError):
        Completion(text="x", model="x", output_tokens=True)
    assert loaded_vram_bytes([{"vram_bytes": None}]) is None
    assert loaded_vram_bytes([{"vram_bytes": 0}]) == 0
    assert loaded_vram_bytes([{"vram_bytes": 20}, {"vram_bytes": 40}]) == 60


@pytest.mark.parametrize(
    "mode", ["valid", "incomplete", "wrong_model", "tools", "invalid_json", "after_done"]
)
def test_streamed_metric_protocol_uses_same_authorized_gateway(mode):
    async def scenario():
        config = RuntimeConfig(CONFIG)
        name = config.models.get("qwen").name
        chunks = [
            {"model": name, "message": {"content": "Syn"}, "done": False},
            {"model": name, "message": {"content": "thetic"}, "done": False},
            {
                "model": name,
                "message": {"content": ""},
                "done": True,
                "eval_count": 20,
                "prompt_eval_count": 10,
                "eval_duration": 2_000_000_000,
                "prompt_eval_duration": 500_000_000,
                "total_duration": 3_000_000_000,
                "load_duration": 400_000_000,
            },
        ]
        if mode == "incomplete":
            chunks.pop()
        elif mode == "wrong_model":
            chunks[0]["model"] = "foreign"
        elif mode == "tools":
            chunks[0]["message"]["tool_calls"] = [{"function": {"name": "shell"}}]
        elif mode == "after_done":
            chunks.append(chunks[0])
        raw = (
            b"not-json\n"
            if mode == "invalid_json"
            else b"\n".join(json.dumps(c).encode() for c in chunks)
        )

        class Stream(httpx.AsyncByteStream):
            async def __aiter__(self):
                # Real asynchronous split boundaries, with no artificial time-to-token claim.
                for part in (raw[:17], raw[17:]):
                    await asyncio.sleep(0)
                    yield part

        def handler(request):
            if request.url.path == "/api/tags":
                return httpx.Response(
                    200, json={"models": [{"name": name, "size": 1, "digest": "MOCK"}]}
                )
            assert json.loads(request.content)["stream"] is True
            return httpx.Response(200, stream=Stream())

        settings = Settings(_env_file=None)
        async with httpx.AsyncClient(
            base_url=str(settings.ollama_base_url), transport=httpx.MockTransport(handler)
        ) as client:
            provider = OllamaProvider(settings, client, measure_streaming=True)
            gateway = LLMGateway(config.models, {"ollama": provider}, config.policy)
            if mode != "valid":
                with pytest.raises(LLMError):
                    await gateway.complete(
                        "qwen",
                        "specialist",
                        "PUBLIC",
                        [{"role": "user", "content": "SYNTHETIC"}],
                        CallBudget(1, 20000),
                    )
            else:
                response, _ = await gateway.complete(
                    "qwen",
                    "specialist",
                    "PUBLIC",
                    [{"role": "user", "content": "SYNTHETIC"}],
                    CallBudget(1, 20000),
                )
                measured = completion_metrics(response)
                assert response.text == "Synthetic" and measured["tokens_per_second"] == 10
                assert measured["first_content_chunk_seconds"] >= 0
                assert measured["model_load_seconds"] == 0.4
            # Streaming is not an alternate route around dispatch authorization.
            with pytest.raises(LLMError, match="GATEWAY"):
                await provider.complete(config.models.get("qwen"), [], None, 10, unload=True)

    asyncio.run(scenario())


def test_benchmark_parallel_jobs_respect_existing_model_slots_and_keep_stable_cases():
    class SlowProvider(AssessmentProvider):
        active = peak = 0

        async def complete(self, *args, **kwargs):
            self.active += 1
            self.peak = max(self.peak, self.active)
            try:
                await asyncio.sleep(0.001)
                response = await super().complete(*args, **kwargs)
                return response.model_copy(
                    update={
                        "output_tokens": 20,
                        "generation_duration_seconds": 2,
                        "load_duration_seconds": 0.25,
                        "first_content_seconds": 0.5,
                    }
                )
            finally:
                self.active -= 1

    async def scenario():
        config, provider = RuntimeConfig(CONFIG), SlowProvider()
        gateway = LLMGateway(config.models, {"ollama": provider}, config.policy, max_parallel=1)
        result = await benchmark(gateway, ["qwen", "mistral"], parallelism=4)
        assert result["mocked"] is True and not result["automatic_capability_promotion"]
        assert result["peak_gateway_dispatches_observed"] == provider.peak == 1
        assert result["model_calls"] == len(CASES) * 2
        assert [r["case_id"] for r in result["results"][: len(CASES)]] == [c["id"] for c in CASES]
        assert all(r["inference"]["tokens_per_second"] == 10 for r in result["results"])
        assert all(
            r["human_quality_score"] is None and r["vram_peak_bytes"] is None
            for r in result["results"]
        )
        for model in result["capability_matrix"].values():
            for measured in model.values():
                assert measured["mean_model_load_seconds"] == 0.25
                assert measured["mean_first_content_chunk_seconds"] == 0.5
                assert measured["mean_ttft_seconds"] is None
                assert measured["inference_sample_counts"]["model_load_seconds"] == 1
                assert measured["mean_post_call_vram_bytes"] is None
                assert measured["model_calls"] == 1
        with pytest.raises(ValueError):
            await benchmark(gateway, ["qwen"], parallelism=5)

    asyncio.run(scenario())


def test_benchmark_matrix_keeps_unmeasured_metrics_null():
    from app.llm.providers.demo import DemoProvider

    async def scenario():
        config = RuntimeConfig(CONFIG)
        gateway = LLMGateway(config.models, {"ollama": DemoProvider()}, config.policy)
        result = await benchmark(gateway, ["qwen"])
        for measured in result["capability_matrix"]["qwen"].values():
            assert measured["mean_model_load_seconds"] is None
            assert measured["mean_first_content_chunk_seconds"] is None
            assert measured["mean_ttft_seconds"] is None
            assert measured["inference_sample_counts"]["model_load_seconds"] == 0

    asyncio.run(scenario())
