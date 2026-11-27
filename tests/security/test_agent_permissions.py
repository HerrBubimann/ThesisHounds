import asyncio
from uuid import uuid4

import pytest
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget
from app.schemas.domain import AgentRecord, FindingsOutput, RunRecord

from tests.fixtures.providers import runtime
from tests.unit.test_agents import setup_factory


@pytest.mark.parametrize(
    "change",
    [
        {"allowed_tools": frozenset()},
        {"allowed_models": frozenset()},
    ],
)
def test_child_cannot_expand_parent_capabilities(change):
    factory, parent, spec = setup_factory()
    for field, value in change.items():
        setattr(parent, field, value)
    with pytest.raises(LLMError):
        factory.create(spec, parent)


def test_child_cannot_cross_analysis_or_downgrade_labels_even_through_registry():
    factory, parent, spec = setup_factory()
    child, _ = factory.create(spec, parent)
    for change in ({"run_id": "another"}, {"data_classification": "PUBLIC"}):
        parent.data_classification = "RESTRICTED"
        record = AgentRecord.model_validate(
            {
                **child.model_dump(),
                "agent_id": "new-child",
                **change,
            }
        )
        with pytest.raises(LLMError):
            factory.registry.register(record)


def test_document_with_same_name_from_another_analysis_cannot_enter_agent_context(tmp_path):
    async def scenario():
        app = runtime(tmp_path)
        run = RunRecord(
            mode="D", document_id="synthetic-demo", criteria=["Test"], data_classification="PUBLIC"
        )
        agent = app.orchestrator.record(run, "reviewer", "qwen", "Test", "Test")
        other_id = str(uuid4())
        document = app.store.create_demo(other_id)
        try:
            with pytest.raises(LLMError):
                await app.engine.ask(
                    agent, document, CallBudget(1, 10000), "review", {}, FindingsOutput
                )
            assert not app.provider.calls
        finally:
            app.store.remove(other_id)
            await app.close()

    asyncio.run(scenario())


@pytest.mark.parametrize("change", ["scope", "taint"])
def test_model_review_preserves_finding_scope_and_highest_class(tmp_path, change):
    from app.schemas.domain import RunRequest
    from app.services.document_store import SYNTHETIC_PAGES, Document
    from app.validation.cross_model_review import CrossModelReview

    async def scenario():
        app = runtime(tmp_path)
        run = app.start(RunRequest())
        await app.tasks[run.run_id]
        finding = app.findings[run.run_id][0]
        model = app.gateway.independent_reviewers(app.config.models.get(finding.model_id))[0]
        reviewer = app.orchestrator.record(run, "reviewer", model.id, "Test", "Test")
        document = Document(
            document_id=run.document_id,
            analysis_id=run.run_id,
            pages=SYNTHETIC_PAGES,
            classification="PUBLIC",
        )
        if change == "scope":
            finding = finding.model_copy(update={"run_id": str(uuid4())})
        else:
            finding.data_classification = "RESTRICTED"
        count = len(app.provider.calls)
        with pytest.raises(LLMError):
            await CrossModelReview(app.engine).review(
                finding, reviewer, document, CallBudget(1, 10000)
            )
        assert len(app.provider.calls) == count
        await app.close()

    asyncio.run(scenario())
