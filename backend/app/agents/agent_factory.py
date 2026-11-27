from pydantic import ValidationError

from app.agents.agent_registry import AgentRegistry
from app.core.configuration import RuntimeConfig
from app.llm.errors import LLMError
from app.schemas.domain import AgentRecord, AgentSpec
from app.security.tool_permissions import validate_tools


class AgentFactory:
    def __init__(self, config: RuntimeConfig, registry: AgentRegistry):
        self.config = config
        self.registry = registry

    def create(
        self, specification: AgentSpec | dict, parent: AgentRecord, *, dynamic: bool = True
    ) -> tuple[AgentRecord, AgentSpec]:
        return self.create_batch([specification], parent, dynamic=dynamic)[0]

    def create_batch(
        self, specifications: list[AgentSpec | dict], parent: AgentRecord, *, dynamic: bool = True
    ) -> list[tuple[AgentRecord, AgentSpec]]:
        prepared = [self._prepare(spec, parent, dynamic=dynamic) for spec in specifications]
        self.registry.register_many([record for record, _ in prepared])
        return prepared

    def _prepare(
        self, specification: AgentSpec | dict, parent: AgentRecord, *, dynamic: bool
    ) -> tuple[AgentRecord, AgentSpec]:
        try:
            # Revalidate instances too: model_construct/model_copy must not bypass server checks.
            data = (
                specification.model_dump()
                if isinstance(specification, AgentSpec)
                else specification
            )
            spec = AgentSpec.model_validate(data)
        except ValidationError:
            raise LLMError(422, "Ungültige oder nicht freigegebene Agentenspezifikation.") from None
        limits = self.config.limits
        if self.registry.records.get(parent.agent_id) is not parent or not parent.can_delegate:
            raise LLMError(403, "Dieser Parent darf keine Agenten delegieren.")
        if parent.role not in {"content", "methodology", "formal"} or spec.category != parent.role:
            raise LLMError(403, "Subagent muss zur freigegebenen Supervisor-Rolle gehören.")
        if spec.supervisor_id != parent.agent_id:
            raise LLMError(403, "Supervisor-Zuordnung ist nicht freigegeben.")
        if parent.depth + 1 > min(limits.max_delegation_depth, spec.max_delegation_depth):
            raise LLMError(429, "Maximale Delegationstiefe erreicht.")
        if (
            spec.max_iterations > limits.max_iterations
            or spec.max_runtime_seconds > limits.agent_timeout_seconds
        ):
            raise LLMError(429, "Agentenspezifikation überschreitet das Ausführungsbudget.")
        validate_tools(spec.allowed_tools, self.config.policy.config.allowed_tools)
        if not set(spec.allowed_tools) <= parent.allowed_tools:
            raise LLMError(403, "Subagent darf Parent-Werkzeuge nicht erweitern.")
        if spec.model_id not in parent.allowed_models:
            raise LLMError(403, "Subagent darf Parent-Modellfreigaben nicht erweitern.")
        model = self.config.models.get(spec.model_id, "specialist")
        self.config.policy.check(model, parent.data_classification, "specialist")
        record = AgentRecord(
            agent_id=f"{parent.run_id}_{spec.agent_id}",
            run_id=parent.run_id,
            name=spec.name,
            role="specialist",
            model_id=model.id,
            manufacturer=model.manufacturer,
            parent_agent=parent.agent_id,
            task=spec.task,
            depth=parent.depth + 1,
            dynamic=dynamic,
            specification=spec,
            data_classification=parent.data_classification,
            allowed_models=parent.allowed_models,
            allowed_tools=frozenset(spec.allowed_tools),
            allowed_documents=parent.allowed_documents,
            allowed_network_targets=parent.allowed_network_targets,
        )
        return record, spec
