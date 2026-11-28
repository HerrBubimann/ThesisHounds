"""Privacy-first routing. Manual assignments are never presented as measured ability."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.llm.errors import LLMError
from app.llm.model_registry import ModelRegistry
from app.security.policy_engine import PolicyEngine

TaskType = Literal[
    "scientific_text",
    "methodology",
    "argumentation",
    "formal",
    "sources",
    "german",
    "structured_output",
    "tool_calling",
    "injection",
    "evidence",
    "resources",
]


class CapabilityRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    model_id: str
    model_digest: str = Field(pattern=r"^(sha256:)?[0-9a-f]{64}$")
    benchmark_version: str = Field(min_length=1)
    dataset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    hardware_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    reviewed_by: str = Field(min_length=1)
    measured_at: str = Field(min_length=1)
    mocked: bool = True
    scores: dict[TaskType, float] = Field(default_factory=dict)
    infrastructure: dict[str, Annotated[float, Field(ge=0, allow_inf_nan=False)] | None] = Field(
        default_factory=dict
    )


class ResourceBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    ram_gib: float | None = Field(default=None, ge=0)
    vram_gib: float | None = Field(default=None, ge=0)
    source: Literal["UNMEASURED", "OPERATOR_LIMIT", "INFERENCE_HOST_MEASURED"] = "UNMEASURED"


class RoutingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    model_id: str
    model_digest: str
    task_type: TaskType
    role: str
    source: Literal["MEASURED", "MANUAL_DEFAULT"]
    reason: str
    evidence_id: str | None = None
    resources_verified: bool = False
    required_tasks: tuple[TaskType, ...] = ()


class ModelRouter:
    def __init__(self, registry: ModelRegistry, policy: PolicyEngine, records=()):
        self.registry, self.policy = registry, policy
        self.records = tuple(CapabilityRecord.model_validate(r) for r in records)
        keys = [(r.model_id, r.model_digest) for r in self.records]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate capability evidence")
        if any(not 0 <= score <= 1 for r in self.records for score in r.scores.values()):
            raise ValueError("Capability scores must be in [0, 1]")

    def select(
        self,
        task: TaskType,
        role: str,
        classification: str,
        available: dict[str, str],
        manual_default: str,
        *,
        resources: ResourceBudget | None = None,
        exclude_manufacturers: frozenset[str] = frozenset(),
        required_tasks: tuple[TaskType, ...] = (),
    ) -> RoutingDecision:
        resources = resources or ResourceBudget()
        candidates = []
        for model in self.registry.enabled():
            if role not in model.allowed_roles or model.name not in available:
                continue
            if (
                model.expected_digest
                and available[model.name].removeprefix("sha256:") != model.expected_digest
            ):
                continue
            try:
                self.policy.check(model, classification, role)
            except LLMError:
                continue
            if model.manufacturer in exclude_manufacturers:
                continue
            if resources.ram_gib is not None and model.estimated_ram_gib > resources.ram_gib:
                continue
            if resources.vram_gib is not None and model.estimated_vram_gib > resources.vram_gib:
                continue
            candidates.append(model)
        if not candidates:
            raise LLMError(503, "Kein freigegebenes verfügbares Modell innerhalb der Grenzen.")
        scored = []
        for model in candidates:
            for record in self.records:
                if (
                    record.model_id == model.id
                    and record.model_digest == available[model.name]
                    and not record.mocked
                    and {task, *required_tasks} <= record.scores.keys()
                ):
                    scored.append(
                        (min(record.scores[t] for t in {task, *required_tasks}), model.id, record)
                    )
        if scored:
            _, model_id, evidence = sorted(scored, key=lambda x: (-x[0], x[1]))[0]
            model = next(m for m in candidates if m.id == model_id)
            source, reason = (
                "MEASURED",
                "Reviewed benchmark for every required task and exact digest",
            )
        else:
            model = next(
                (m for m in candidates if m.id == manual_default),
                sorted(candidates, key=lambda m: m.id)[0],
            )
            evidence = None
            source, reason = (
                "MANUAL_DEFAULT",
                "No eligible measured capability; operator assignment",
            )
        return RoutingDecision(
            model_id=model.id,
            model_digest=available[model.name],
            task_type=task,
            role=role,
            source=source,
            reason=reason,
            evidence_id=evidence.evidence_id if evidence else None,
            resources_verified=resources.source == "INFERENCE_HOST_MEASURED",
            required_tasks=required_tasks,
        )
