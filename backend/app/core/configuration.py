from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.llm.model_registry import ModelRegistry
from app.llm.model_router import ResourceBudget
from app.schemas.domain import Category
from app.security.policy_engine import PolicyConfig, PolicyEngine


class ExecutionLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    adaptive_planning_mode: Literal["off", "regex_baseline", "semantic"] = "semantic"
    adaptive_planning_fallback: Literal["none", "regex_baseline"] = "none"
    max_planned_specialists: int = Field(default=2, ge=1, le=6)
    semantic_injection_model_id: str | None = Field(
        default=None, pattern=r"^[a-z][a-z0-9_-]{0,39}$"
    )
    max_supervisors: int = Field(default=3, ge=1, le=3)
    max_dynamic_agents: int = Field(default=6, ge=1, le=32)
    max_parallel_agents: int = Field(default=2, ge=1, le=8)
    max_parallel_model_calls: int = Field(default=1, ge=1, le=4)
    sequential_model_loading: bool = True
    max_delegation_depth: int = Field(default=2, ge=1, le=2)
    max_iterations: int = Field(default=3, ge=1, le=10)
    agent_timeout_seconds: float = Field(default=600, gt=0, le=3600)
    run_timeout_seconds: float = Field(default=3600, gt=0, le=14400)
    max_model_calls: int = Field(default=32, ge=1, le=100)
    max_tokens: int = Field(default=100000, ge=100, le=1000000)
    max_output_tokens: int = Field(default=2048, ge=128, le=4096)
    max_retries: int = Field(default=1, ge=0, le=2)
    max_conflict_reviews: int = Field(default=2, ge=0, le=6)
    max_context_bytes: int = Field(default=12000, ge=256, le=64000)
    capture_inference_resources: bool = False
    max_active_runs: int = Field(default=1, ge=1, le=2)
    max_retained_runs: int = Field(default=20, ge=1, le=100)
    retention_seconds: float = Field(default=3600, ge=1, le=86400)
    inference_ram_limit_gib: float | None = Field(default=None, ge=0)
    inference_vram_limit_gib: float | None = Field(default=None, ge=0)


class SupervisorDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: Category
    name: str
    model_id: str
    description: str


class AgentsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    orchestrator_model: str
    synthesis_model: str
    single_model: str
    default_supervisors: list[Category]
    supervisors: list[SupervisorDefinition]

    @field_validator("supervisors")
    @classmethod
    def unique_supervisors(cls, value):
        if len({s.id for s in value}) != len(value):
            raise ValueError("Duplicate supervisors")
        return value


class RuntimeConfig:
    def bind_local_pilot(self, settings):
        ids = [settings.pilot_model_id]
        if settings.pilot_architecture == "E":
            ids.append(settings.pilot_verifier_model_id)
        self.models = self.models.require_pilot_artifacts(ids, str(settings.ollama_base_url))
        self.policy.pilot_models = frozenset(ids)
        self.policy.pilot_endpoint = str(settings.ollama_base_url).rstrip("/")
        self.agents.single_model = settings.pilot_model_id
        self.agents.orchestrator_model = settings.pilot_model_id
        self.agents.synthesis_model = settings.pilot_model_id
        self.agents.supervisors = [
            s.model_copy(update={"model_id": settings.pilot_model_id})
            for s in self.agents.supervisors
        ]

    @property
    def resource_budget(self) -> ResourceBudget:
        ram, vram = self.limits.inference_ram_limit_gib, self.limits.inference_vram_limit_gib
        return ResourceBudget(
            ram_gib=ram,
            vram_gib=vram,
            source="OPERATOR_LIMIT" if ram is not None or vram is not None else "UNMEASURED",
        )

    def __init__(self, directory: Path):
        self.directory = directory

        def load(name):
            return yaml.safe_load((directory / name).read_text("utf-8"))

        self.models = ModelRegistry.load(directory / "models.yaml")
        self.limits = ExecutionLimits.model_validate(load("execution.yaml"))
        self.agents = AgentsConfig.model_validate(load("agents.yaml"))
        self.policy = PolicyEngine(PolicyConfig.model_validate(load("policies.yaml")))
        capability_file = directory / "model_capabilities.yaml"
        self.capabilities = (
            yaml.safe_load(capability_file.read_text("utf-8"))["records"]
            if capability_file.exists()
            else []
        )
        self.models.get(self.agents.orchestrator_model, "orchestrator")
        self.models.get(self.agents.synthesis_model, "synthesis")
        for supervisor in self.agents.supervisors:
            self.models.get(supervisor.model_id, supervisor.id)
        if not set(self.agents.default_supervisors) <= {s.id for s in self.agents.supervisors}:
            raise ValueError("Default supervisors must be configured")
