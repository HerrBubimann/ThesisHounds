from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Role = Literal[
    "orchestrator", "content", "methodology", "formal", "specialist", "reviewer", "synthesis"
]


class ModelDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    name: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,199}$")
    manufacturer: str = Field(min_length=1, max_length=100)
    provider: str
    local: bool
    enabled: bool = True
    capabilities: list[Literal["chat", "structured_output"]]
    context_length: int = Field(ge=512, le=32768)
    estimated_ram_gib: float = Field(gt=0)
    estimated_vram_gib: float = Field(ge=0)
    allowed_roles: list[Role]
    privacy: Literal["CONFIDENTIAL", "PUBLIC", "SYNTHETIC"] = "CONFIDENTIAL"

    @model_validator(mode="after")
    def local_tag(self) -> "ModelDefinition":
        if self.local and (":cloud" in self.name or self.name.endswith("-cloud")):
            raise ValueError("Cloud model tags are not local models")
        return self


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    models: list[ModelDefinition] = Field(min_length=1, max_length=30)


class ModelRegistry:
    def __init__(self, models: list[ModelDefinition]) -> None:
        self.models = {model.id: model for model in models}
        if len(self.models) != len(models):
            raise ValueError("Model IDs must be unique")
        if len({(m.provider, m.name) for m in models}) != len(models):
            raise ValueError("Provider/model tags must be unique")

    @classmethod
    def load(cls, path: Path) -> "ModelRegistry":
        return cls(ModelConfig.model_validate(yaml.safe_load(path.read_text("utf-8"))).models)

    def get(self, model_id: str, role: str | None = None) -> ModelDefinition:
        model = self.models.get(model_id)
        if model is None or not model.enabled or (role and role not in model.allowed_roles):
            from app.llm.errors import LLMError

            raise LLMError(422, "Modell oder Agentenrolle ist nicht freigegeben.")
        return model

    def enabled(self) -> list[ModelDefinition]:
        return [model for model in self.models.values() if model.enabled]
