"""Local allowlisted metadata only; caller text is never accepted as audit fields."""

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    analysis_id: UUID
    action: Literal["CREATE", "READ", "PROCESS", "REVIEW", "DELETE", "DENY"]
    decision: Literal["ALLOW", "DENY", "REQUIRE_AUTHORIZED_APPROVAL"]


class AuditService:
    def __init__(self, path: Path):
        self.path = path

    def record(self, event: AuditEvent) -> None:
        event = AuditEvent.model_validate(event.model_dump())
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(self.path, flags, 0o600), "a", encoding="utf-8") as stream:
            data = {**event.model_dump(mode="json"), "at": datetime.now(UTC).isoformat()}
            stream.write(json.dumps(data) + "\n")
            stream.flush()
        # OS ACLs/encryption and a separately administered collector remain deployment duties.


def disable_content_logging() -> None:
    for name in ("httpx", "httpcore", "langsmith", "langchain", "uvicorn.access", "pypdf"):
        logger = logging.getLogger(name)
        logger.handlers = [logging.NullHandler()]
        logger.propagate = False
