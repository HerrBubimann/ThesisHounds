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
