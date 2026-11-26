"""Dynamic agents: tool permissions, AgentSpec validation, delegation depth and agent limits."""

import asyncio
import json

import pytest
from app.agents.agent_factory import AgentFactory
from app.agents.agent_registry import AgentRegistry
from app.core.configuration import ExecutionLimits, RuntimeConfig
from app.llm.errors import LLMError
from app.schemas.domain import AgentProposals, AgentRecord, AgentSpec, RunRequest
from app.security.tool_permissions import validate_tools
from pydantic import ValidationError

from tests.fixtures import CONFIG
from tests.fixtures.providers import WorkflowProvider, runtime

SPEC = {
    "agent_id": "leaf",
    "name": "Synthetic",
    "description": "Synthetisch",
    "task": "Prüfe synthetisch",
    "category": "methodology",
    "model_id": "mistral",
    "supervisor_id": "sup",
}


def supervisor(registry: AgentRegistry, agent_id="sup", role="methodology", depth=1):
    return registry.register(
        AgentRecord(
            agent_id=agent_id,
            run_id="run",
            name=agent_id,
            role=role,
            model_id="mistral",
            manufacturer="Mistral AI",
            task="synthetic",
            depth=depth,
            can_delegate=True,
        )
    )


def factory() -> AgentFactory:
    config = RuntimeConfig(CONFIG)
    return AgentFactory(config, AgentRegistry(config.limits))


@pytest.mark.parametrize(
    "tools", [["shell.execute"], ["network.fetch"], ["python.exec"], ["document.read", "fs.write"]]
)
def test_unapproved_tools_are_rejected_even_if_policy_lists_them(tools) -> None:
    with pytest.raises(LLMError) as error:
        validate_tools(tools, policy_allowlist=["document.read", *tools])
    assert error.value.status_code == 403


@pytest.mark.parametrize(
    "change",
    [
        {"agent_id": "../../etc/passwd"},
        {"agent_id": "Admin"},
        {"agent_id": "a" * 41},
        {"role": "orchestrator"},
        {"can_delegate": True},
        {"allowed_tools": ["shell.execute"]},
        {"output_schema": "python.v1"},
        {"max_iterations": 0},
        {"task": ""},
        {"privacy_mode": "EXPERIMENTAL"},
    ],
)
def test_agent_spec_rejects_unsafe_values(change) -> None:
    with pytest.raises(ValidationError):
        AgentSpec.model_validate({**SPEC, **change})


def test_factory_revalidates_specs_that_bypassed_pydantic() -> None:
    agents = factory()
    parent = supervisor(agents.registry)
    forged = AgentSpec.model_construct(**{**SPEC, "allowed_tools": ["shell.execute"]})
    with pytest.raises(LLMError) as error:
        agents.create(forged, parent)
    assert error.value.status_code == 422
    assert [a.agent_id for a in agents.registry.records.values()] == ["sup"]


def test_delegation_depth_is_capped_by_server_limit() -> None:
    agents = factory()
    deep = supervisor(agents.registry, depth=agents.config.limits.max_delegation_depth)
    with pytest.raises(LLMError) as error:
        agents.create(AgentSpec.model_validate(SPEC), deep)
    assert error.value.status_code == 429


def test_supervisor_and_dynamic_agent_limits_hold_across_parents() -> None:
    agents = factory()
    limits = agents.config.limits
    parents = [
        supervisor(agents.registry, f"sup{i}", role)
        for i, role in enumerate(["content", "methodology", "formal"])
    ]
    with pytest.raises(LLMError) as error:
        supervisor(agents.registry, "sup_extra", "content")
    assert error.value.status_code == 429
    created = 0
    with pytest.raises(LLMError) as error:
        for index in range(limits.max_dynamic_agents + 1):
            parent = parents[index % len(parents)]
            spec = {**SPEC, "agent_id": f"leaf{index}", "category": parent.role}
            agents.create({**spec, "supervisor_id": parent.agent_id}, parent)
            created += 1
    assert error.value.status_code == 429
    assert created == limits.max_dynamic_agents


@pytest.mark.parametrize(
    "override",
    [
        {"max_dynamic_agents": 33},
        {"max_dynamic_agents": 0},
        {"max_delegation_depth": 3},
        {"max_supervisors": 4},
        {"max_parallel_agents": 9},
        {"max_model_calls": 101},
    ],
)
def test_execution_limits_have_hard_upper_bounds(override) -> None:
    with pytest.raises(ValidationError):
        ExecutionLimits(**override)


def test_model_cannot_propose_more_agents_than_schema_allows() -> None:
    with pytest.raises(ValidationError):
        AgentProposals.model_validate(
            {"agents": [{**SPEC, "agent_id": f"leaf{i}"} for i in range(7)]}
        )


def test_runaway_delegation_in_full_workflow_is_stopped(tmp_path) -> None:
    class FloodingProvider(WorkflowProvider):
        """Every supervisor proposes the schema maximum of agents."""

        async def complete(self, model, messages, output_schema, max_tokens, *, unload):
            response = await super().complete(
                model, messages, output_schema, max_tokens, unload=unload
            )
            if "task: delegate." in messages[0]["content"]:
                proposal = json.loads(response.text)
                template = proposal["agents"][0]
                proposal["agents"] = [
                    {**template, "agent_id": f"{template['agent_id']}{i}"} for i in range(6)
                ]
                response.text = json.dumps(proposal)
            return response

    async def scenario():
        app = runtime(tmp_path)
        app.gateway.providers["ollama"] = FloodingProvider()
        run = app.start(RunRequest(mode="D"))
        await app.tasks[run.run_id]
        dynamic = [a for a in app.agents.for_run(run.run_id) if a.dynamic]
        assert run.status == "FAILED"
        assert len(dynamic) <= app.config.limits.max_dynamic_agents
        await app.close()

    asyncio.run(scenario())
