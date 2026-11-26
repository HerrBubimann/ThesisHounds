import asyncio
import json

import pytest
from app.llm.errors import LLMError
from app.schemas.domain import AgentStatus, HumanReview, RunRequest

from tests.fixtures.providers import WorkflowProvider, runtime


@pytest.mark.parametrize("mode", ["A", "B", "C", "D"])
def test_complete_synthetic_workflow_and_human_gate(tmp_path, mode):
    async def scenario():
        app = runtime(tmp_path)
        run = app.start(RunRequest(mode=mode))
        await app.tasks[run.run_id]
        assert run.status == "WAITING_FOR_REVIEW", run.error
        assert run.mocked and run.final_report is None
        assert app.provider.maximum_active == 1
        agents = app.agents.for_run(run.run_id)
        leaves = [a for a in agents if a.role == "specialist"]
        assert len(leaves) == (0 if mode == "A" else 2)
        assert all(a.dynamic == (mode == "D") for a in leaves)
        assert sum(a.model_calls for a in agents) == run.model_calls
        values = app.findings[run.run_id]
        if mode == "D":
            assert all(f.evidence_status == "VALIDATED" for f in values)
        if mode in {"C", "D"}:
            assert all(f.reviews and f.reviews[0].manufacturer != f.manufacturer for f in values)
        if mode == "B":
            assert set(app.provider.calls) == {"qwen"}
        for finding in values:
            app.human_review(finding.finding_id, HumanReview(decision="ACCEPTED"))
        assert run.status == "COMPLETED" and run.final_report
        assert "MOCK-Entwurf" not in run.final_report
        await app.close()

    asyncio.run(scenario())


def test_global_deadline_and_retention_cleanup(tmp_path):
    from datetime import timedelta

    from app.schemas.domain import now

    async def scenario():
        app = runtime(tmp_path, delay=60)
        app.config.limits = app.config.limits.model_copy(update={"run_timeout_seconds": 0.02})
        run = app.start(RunRequest())
        await app.tasks[run.run_id]
        assert run.status == "FAILED" and "zeitlimit" in run.error.lower()
        assert app.store.path(run.run_id).exists()
        run.finished_at = now() - timedelta(hours=2)
        app.cleanup()
        assert not app.runs and not app.agents.records
        assert not app.store.path(run.run_id).exists()
        await app.close()

    asyncio.run(scenario())


def test_missing_independent_review_and_human_edit_history(tmp_path):
    class NoReviewer(WorkflowProvider):
        async def complete(self, model, messages, output_schema, max_tokens, *, unload):
            if "task: review." in messages[0]["content"]:
                raise LLMError(503, "Reviewer nicht verfügbar.")
            return await super().complete(model, messages, output_schema, max_tokens, unload=unload)

    async def scenario():
        app = runtime(tmp_path)
        app.provider = NoReviewer()
        app.gateway.providers["ollama"] = app.provider
        run = app.start(RunRequest())
        await app.tasks[run.run_id]
        assert run.status == "WAITING_FOR_REVIEW", run.error
        assert all(f.review_status == "MISSING" for f in app.findings[run.run_id])
        assert run.warnings
        await app.close()
        app = runtime(tmp_path)
        run = app.start(RunRequest())
        await app.tasks[run.run_id]
        finding = app.findings[run.run_id][0]
        previous = finding.statement
        app.human_review(
            finding.finding_id,
            HumanReview(decision="ACCEPTED", edited_statement="Menschlich bearbeitet"),
        )
        assert finding.original_statement == previous
        assert finding.superseded_reviews and not finding.reviews
        assert finding.evidence_status == "NOT_CHECKED"
        await app.close()

    asyncio.run(scenario())


def test_conflicts_are_not_erased_by_third_model(tmp_path):
    async def scenario():
        app = runtime(tmp_path, disagree=True)
        run = app.start(RunRequest())
        await app.tasks[run.run_id]
        assert run.status == "WAITING_FOR_REVIEW", run.error
        assert run.conflicts_count == 2
        assert all(len(f.reviews) == 2 and f.conflict for f in app.findings[run.run_id])
        await app.close()

    asyncio.run(scenario())


def test_cancel_running_run_and_reject_concurrent_run(tmp_path):
    async def scenario():
        app = runtime(tmp_path, delay=60)
        run = app.start(RunRequest())
        await asyncio.sleep(0.05)
        with pytest.raises(LLMError) as error:
            app.start(RunRequest())
        assert error.value.status_code == 429
        await app.cancel(run.run_id)
        assert run.status == "CANCELLED"
        assert all(
            a.status not in {AgentStatus.RUNNING, AgentStatus.QUEUED}
            for a in app.agents.for_run(run.run_id)
        )
        await app.close()

    asyncio.run(scenario())


def test_cancel_before_task_starts(tmp_path):
    async def scenario():
        app = runtime(tmp_path)
        run = app.start(RunRequest())
        await app.cancel(run.run_id)
        assert run.status == "CANCELLED"
        await app.close()

    asyncio.run(scenario())


def test_missing_model_and_global_call_budget(tmp_path):
    async def scenario():
        app = runtime(tmp_path, missing=["qwen3:8b"])
        run = app.start(RunRequest())
        await app.tasks[run.run_id]
        assert run.status == "FAILED"
        await app.close()
        app = runtime(tmp_path)
        app.config.limits = app.config.limits.model_copy(update={"max_model_calls": 1})
        run = app.start(RunRequest())
        await app.tasks[run.run_id]
        assert run.status == "FAILED" and run.model_calls == 1
        await app.close()

    asyncio.run(scenario())


def test_model_generated_tool_escalation_fails_without_execution(tmp_path):
    class InjectedProvider(WorkflowProvider):
        async def complete(self, model, messages, output_schema, max_tokens, *, unload):
            response = await super().complete(
                model, messages, output_schema, max_tokens, unload=unload
            )
            if "task: delegate." in messages[0]["content"]:
                proposal = json.loads(response.text)
                proposal["agents"][0]["allowed_tools"] = ["shell.execute"]
                response.text = json.dumps(proposal)
            return response

    async def scenario():
        app = runtime(tmp_path)
        app.gateway.providers["ollama"] = InjectedProvider()
        run = app.start(RunRequest())
        await app.tasks[run.run_id]
        assert run.status == "FAILED"
        assert not any(a.dynamic for a in app.agents.for_run(run.run_id))
        assert "shell.execute" not in (run.error or "")
        await app.close()

    asyncio.run(scenario())
