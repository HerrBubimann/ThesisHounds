from app.core.configuration import RuntimeConfig
from app.llm.errors import LLMError
from app.schemas.domain import ExecutionPlan


class TaskPlanner:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def validate(self, plan: ExecutionPlan) -> list[list]:
        tasks = {task.supervisor: task for task in plan.tasks}
        allowed = {s.id for s in self.config.agents.supervisors}
        if not set(self.config.agents.default_supervisors) <= set(tasks):
            raise LLMError(422, "Die konfigurierten Mindest-Supervisoren fehlen im Plan.")
        if (
            len(tasks) != len(plan.tasks)
            or len(tasks) > self.config.limits.max_supervisors
            or not set(tasks) <= allowed
        ):
            raise LLMError(422, "Ausführungsplan enthält ungültige Supervisor-Zuordnungen.")
        if any(not set(t.depends_on) <= set(tasks) for t in tasks.values()):
            raise LLMError(422, "Ausführungsplan enthält unbekannte Abhängigkeiten.")
        levels, completed = [], set()
        while len(completed) < len(tasks):
            ready = [
                task
                for key, task in tasks.items()
                if key not in completed and set(task.depends_on) <= completed
            ]
            if not ready:
                raise LLMError(422, "Zyklische Aufgabenabhängigkeiten sind nicht erlaubt.")
            levels.append(ready)
            completed.update(task.supervisor for task in ready)
        return levels
