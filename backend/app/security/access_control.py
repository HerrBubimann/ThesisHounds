"""Authorization only. Identity must come from verified university authentication.

The development identity has access to synthetic demo objects only. Neither HTTP
headers nor role names establish an identity or grant document access.
"""

from contextvars import ContextVar
from dataclasses import dataclass

from app.llm.errors import LLMError


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[str] = frozenset()
    permissions: frozenset[str] = frozenset()


DEMO_PRINCIPAL = Principal(
    "synthetic-demo", frozenset({"developer"}), frozenset({"read", "process", "review", "delete"})
)
current_principal: ContextVar[Principal | None] = ContextVar("principal", default=None)


def principal() -> Principal:
    value = current_principal.get()
    if value is None:
        raise LLMError(401, "Authentifizierung erforderlich.")
    return value


class AccessControl:
    def __init__(self):
        self.assignments: dict[str, frozenset[str]] = {}

    def create(self, resource_id: str) -> None:
        actor = principal()
        if "process" not in actor.permissions or resource_id in self.assignments:
            raise LLMError(403, "Verarbeitung nicht autorisiert.")
        self.assignments[resource_id] = frozenset({actor.subject})

    def allows(self, resource_id: str, action: str = "read") -> bool:
        actor = current_principal.get()
        return bool(
            actor
            and action in actor.permissions
            and actor.subject in self.assignments.get(resource_id, frozenset())
        )

    def require(self, resource_id: str, action: str = "read") -> None:
        if not self.allows(resource_id, action):
            # Uniform response conceals whether an unassigned object exists.
            raise LLMError(404, "Objekt nicht gefunden oder nicht freigegeben.")

    def remove(self, resource_id: str) -> None:
        self.assignments.pop(resource_id, None)
