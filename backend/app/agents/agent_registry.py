from app.core.configuration import ExecutionLimits
from app.llm.errors import LLMError
from app.schemas.domain import AgentRecord, AgentStatus, now


class AgentRegistry:
    def __init__(self, limits: ExecutionLimits):
        self.limits = limits
        self.records: dict[str, AgentRecord] = {}

    def register(self, record: AgentRecord) -> AgentRecord:
        return self.register_many([record])[0]

    def register_many(self, records: list[AgentRecord]) -> list[AgentRecord]:
        """Validate the complete batch before mutating this process-local registry."""
        identifiers = [record.agent_id for record in records]
        if len(set(identifiers)) != len(identifiers) or any(
            identifier in self.records for identifier in identifiers
        ):
            raise LLMError(422, "Agent-ID ist bereits vergeben.")
        for run_id in {record.run_id for record in records}:
            proposed = [record for record in records if record.run_id == run_id]
            run_agents = self.for_run(run_id)
            if (
                sum(a.role in {"content", "methodology", "formal"} for a in run_agents + proposed)
                > self.limits.max_supervisors
            ):
                raise LLMError(429, "Supervisor-Limit erreicht.")
            if sum(a.role == "specialist" for a in proposed) > self.remaining_specialists(run_id):
                raise LLMError(429, "Subagentenlimit erreicht.")
        proposed_by_id = {**self.records, **{r.agent_id: r for r in records}}
        for child in records:
            if child.parent_agent:
                parent = proposed_by_id.get(child.parent_agent)
                if (
                    parent is None
                    or parent.run_id != child.run_id
                    or not child.allowed_models <= parent.allowed_models
                    or not child.allowed_tools <= parent.allowed_tools
                    or not child.allowed_documents <= parent.allowed_documents
                    or not child.allowed_network_targets <= parent.allowed_network_targets
                    or child.data_classification != parent.data_classification
                ):
                    raise LLMError(403, "AGENT_INHERITANCE_DENIED")
        # No await between the quota checks and insertion: atomic on the runtime event loop.
        self.records.update((record.agent_id, record) for record in records)
        return records

    def remaining_specialists(self, run_id: str) -> int:
        return max(
            0,
            self.limits.max_dynamic_agents
            - sum(agent.role == "specialist" for agent in self.for_run(run_id)),
        )

    def for_run(self, run_id: str) -> list[AgentRecord]:
        return [a for a in self.records.values() if a.run_id == run_id]

    def transition(
        self, record: AgentRecord, status: AgentStatus, error: str | None = None
    ) -> None:
        allowed = {
            AgentStatus.CREATED: {AgentStatus.QUEUED, AgentStatus.CANCELLED},
            AgentStatus.QUEUED: {AgentStatus.RUNNING, AgentStatus.CANCELLED, AgentStatus.FAILED},
            AgentStatus.RUNNING: {
                AgentStatus.COMPLETED,
                AgentStatus.FAILED,
                AgentStatus.CANCELLED,
                AgentStatus.WAITING_FOR_REVIEW,
            },
            AgentStatus.WAITING_FOR_REVIEW: {AgentStatus.COMPLETED, AgentStatus.CANCELLED},
        }
        if status not in allowed.get(record.status, set()):
            raise LLMError(409, "Ungültiger Agenten-Zustandswechsel.")
        record.status = status
        record.error = error
        if status == AgentStatus.RUNNING:
            record.started_at = now()
        if status in {AgentStatus.COMPLETED, AgentStatus.CANCELLED, AgentStatus.FAILED}:
            record.finished_at = now()
        self.refresh(record)

    @staticmethod
    def refresh(record: AgentRecord) -> None:
        if record.started_at:
            record.runtime_seconds = (
                (record.finished_at or now()) - record.started_at
            ).total_seconds()

    def remove_run(self, run_id: str) -> None:
        self.records = {key: a for key, a in self.records.items() if a.run_id != run_id}
