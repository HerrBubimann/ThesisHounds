import asyncio

import pytest
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget
from app.schemas.domain import FindingsOutput, RunRecord
from app.services.document_store import SYNTHETIC_PAGES, Document

from tests.fixtures.providers import runtime


def test_agent_parallelism_and_timeout(tmp_path):
    async def scenario():
        app = runtime(tmp_path)
        run = RunRecord(mode="D", document_id="synthetic-demo", criteria=["Test"])
        active, maximum = 0, 0

        async def operation():
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            try:
                await asyncio.sleep(0.01)
                return FindingsOutput(findings=[])
            finally:
                active -= 1

        agents = [
            app.orchestrator.record(run, "reviewer", "qwen", "Test", "Test") for _ in range(5)
        ]
        await asyncio.gather(*(app.engine.execute(agent, operation) for agent in agents))
        assert maximum == 2
        agent = app.orchestrator.record(run, "reviewer", "qwen", "Timeout", "Test")
        with pytest.raises(LLMError) as error:
            await app.engine.execute(agent, operation, runtime_limit=0.001)
        assert error.value.status_code == 504 and agent.status == "FAILED"
        await app.close()

    asyncio.run(scenario())


def test_bounded_retry_and_token_reservation(tmp_path):
    from app.llm.providers.base import Completion

    async def scenario():
        app = runtime(tmp_path)
        run = RunRecord(mode="D", document_id="synthetic-demo", criteria=["Test"])
        agent = app.orchestrator.record(run, "reviewer", "qwen", "Retry", "Test")
        document = Document(document_id="d", pages=SYNTHETIC_PAGES, classification="SYNTHETIC")

        class InvalidProvider:
            calls = 0

            async def complete(self, *args, **kwargs):
                self.calls += 1
                return Completion(text="INVALID", model="qwen3:8b")

        provider = InvalidProvider()
        app.gateway.providers["ollama"] = provider
        budget = CallBudget(10, 100000)
        with pytest.raises(LLMError):
            await app.engine.ask(
                agent, document, budget, "review", {}, FindingsOutput, iterations=3
            )
        assert provider.calls == 2 and agent.model_calls == 2
        assert budget.unknown_token_calls == 2
        with pytest.raises(LLMError) as error:
            await app.gateway.complete("qwen", "reviewer", "SYNTHETIC", [], CallBudget(1, 100))
        assert error.value.status_code == 429 and provider.calls == 2
        await app.close()

    asyncio.run(scenario())
