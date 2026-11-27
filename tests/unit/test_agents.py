import pytest
from app.agents.agent_factory import AgentFactory
from app.agents.agent_registry import AgentRegistry
from app.core.configuration import RuntimeConfig
from app.llm.errors import LLMError
from app.schemas.domain import AgentRecord, AgentSpec, AgentStatus
from pydantic import ValidationError

from tests.fixtures import CONFIG


def setup_factory():
    config = RuntimeConfig(CONFIG)
    registry = AgentRegistry(config.limits)
    parent = registry.register(
        AgentRecord(
            agent_id="parent",
            run_id="run",
            name="Methodology",
            role="methodology",
            model_id="mistral",
            manufacturer="Mistral AI",
            task="test",
            depth=1,
            can_delegate=True,
            data_classification="PUBLIC",
            allowed_models=frozenset({"mistral"}),
            allowed_documents=frozenset({"synthetic-demo"}),
        )
    )
    spec = AgentSpec(
        agent_id="child",
        name="Test",
        description="Test",
        task="Test",
        category="methodology",
        model_id="mistral",
        supervisor_id="parent",
    )
    return AgentFactory(config, registry), parent, spec


def test_factory_limits_parentage_and_states():
    factory, parent, spec = setup_factory()
    for index in range(6):
        child, _ = factory.create(spec.model_copy(update={"agent_id": f"child{index}"}), parent)
        assert child.parent_agent == "parent" and child.depth == 2
        factory.registry.transition(child, AgentStatus.QUEUED)
        factory.registry.transition(child, AgentStatus.RUNNING)
        factory.registry.transition(child, AgentStatus.COMPLETED)
    with pytest.raises(LLMError):
        factory.create(spec, parent)
    with pytest.raises(LLMError):
        factory.registry.transition(child, AgentStatus.RUNNING)
    factory.registry.remove_run("run")
    assert not factory.registry.records


@pytest.mark.parametrize(
    "change",
    [
        {"allowed_tools": ["shell"]},
        {"model_id": "openai"},
        {"can_delegate": True},
        {"supervisor_id": "other"},
        {"max_iterations": 4},
        {"max_runtime_seconds": 1000},
        {"max_delegation_depth": 1},
        {"category": "formal"},
        {"input_schema": "python.exe"},
    ],
)
def test_factory_rejects_privilege_and_limit_escalation(change):
    factory, parent, spec = setup_factory()
    with pytest.raises(LLMError):
        factory.create(spec.model_copy(update=change), parent)


def test_leaf_cannot_delegate_and_schema_forbids_unknown_fields():
    factory, parent, spec = setup_factory()
    child, _ = factory.create(spec, parent)
    with pytest.raises(LLMError):
        factory.create(spec, child)
    with pytest.raises(ValidationError):
        AgentSpec.model_validate({**spec.model_dump(), "classification": "PUBLIC"})


@pytest.mark.parametrize("failure", ["invalid_spec", "duplicate_batch", "existing_id", "quota"])
def test_factory_batch_rejection_does_not_register_valid_prefix(failure):
    factory, parent, spec = setup_factory()
    first = spec.model_copy(update={"agent_id": "first"})
    second = spec.model_copy(update={"agent_id": "second"})
    if failure == "invalid_spec":
        second = second.model_copy(update={"allowed_tools": ["shell.execute"]})
    elif failure == "duplicate_batch":
        second = first
    elif failure == "existing_id":
        factory.create(second, parent)
    else:
        for index in range(factory.config.limits.max_dynamic_agents - 1):
            factory.create(spec.model_copy(update={"agent_id": f"existing{index}"}), parent)
    snapshot = {key: record.model_dump() for key, record in factory.registry.records.items()}
    remaining = factory.registry.remaining_specialists(parent.run_id)
    with pytest.raises(LLMError) as error:
        factory.create_batch([first, second], parent)
    assert error.value.status_code == (429 if failure == "quota" else 422)
    assert {
        key: record.model_dump() for key, record in factory.registry.records.items()
    } == snapshot
    assert factory.registry.remaining_specialists(parent.run_id) == remaining
    # A rejected proposal must not consume IDs or prevent a corrected proposal.
    child, _ = factory.create(first, parent)
    assert child.agent_id == f"{parent.run_id}_first"


def test_batch_exactly_fills_quota_and_terminal_agents_do_not_refund_it():
    factory, parent, spec = setup_factory()
    limit = factory.config.limits.max_dynamic_agents
    created = factory.create_batch(
        [spec.model_copy(update={"agent_id": f"batch{index}"}) for index in range(limit)], parent
    )
    assert len(created) == limit
    assert factory.registry.remaining_specialists(parent.run_id) == 0
    assert factory.registry.remaining_specialists("other-run") == limit
    for child, _ in created:
        factory.registry.transition(child, AgentStatus.CANCELLED)
    with pytest.raises(LLMError) as error:
        factory.create(spec, parent)
    assert error.value.status_code == 429
    assert len(factory.registry.for_run(parent.run_id)) == limit + 1
