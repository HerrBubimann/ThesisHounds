from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class LocalModel(BaseModel):
    name: str
    size: int = Field(ge=0)
    digest: str


class ModelsResponse(BaseModel):
    models: list[LocalModel]


class StatusResponse(BaseModel):
    backend: Literal["ok"] = "ok"
    ollama: Literal["available", "unavailable"]
    model: str
    model_available: bool
    detail: str


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1, max_length=16000)

    @field_validator("prompt")
    @classmethod
    def reject_blank_prompt(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Bitte einen Text eingeben.")
        return value


class ChatResponse(BaseModel):
    model: str
    answer: str


class ErrorResponse(BaseModel):
    detail: str
