from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.llm.model_registry import ModelDefinition
from app.models.schemas import LocalModel


class Completion(BaseModel):
    text: str
    model: str
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)


class LLMProvider(Protocol):
    """Implement this contract for future explicitly enabled providers; no fallback chain."""

    async def complete(
        self,
        model: ModelDefinition,
        messages: list[dict[str, str]],
        output_schema: dict[str, Any] | None,
        max_tokens: int,
        *,
        unload: bool,
    ) -> Completion: ...

    async def health(self) -> bool: ...
    async def discover(self) -> list[LocalModel]: ...
    async def capabilities(self, name: str) -> dict[str, Any]: ...
    async def resources(self) -> dict[str, Any]: ...
