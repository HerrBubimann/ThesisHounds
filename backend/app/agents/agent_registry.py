from app.core.configuration import ExecutionLimits
from app.llm.errors import LLMError
from app.schemas.domain import AgentRecord, AgentStatus, now


class AgentRegistry:
    def __init__(self, limits: ExecutionLimits):
        self.limits = limits
        self.records: dict[str, AgentRecord] = {}

    def register(self, record: AgentRecord) -> AgentRecord:
        if record.agent_id in self.records:
            raise LLMError(422, "Agent-ID ist bereits vergeben.")
        run_agents = self.for_run(record.run_id)
        if record.role in {"content", "methodology", "formal"}:
            if (
                sum(a.role in {"content", "methodology", "formal"} for a in run_agents)
                >= self.limits.max_supervisors
            ):
                raise LLMError(429, "Supervisor-Limit erreicht.")
        if record.role == "specialist":
            if sum(a.role == "specialist" for a in run_agents) >= self.limits.max_dynamic_agents:
                raise LLMError(429, "Subagentenlimit erreicht.")
        self.records[record.agent_id] = record
        return record

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
