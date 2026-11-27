from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.llm.model_registry import Role
from app.security.classification import Classification


def now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


Category = Literal["content", "methodology", "formal"]


class AgentSpec(StrictModel):
    agent_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=300)
    role: Literal["specialist"] = "specialist"
    task: str = Field(min_length=1, max_length=600)
    category: Category
    model_id: str
    supervisor_id: str
    allowed_tools: list[Literal["document.read"]] = Field(default_factory=lambda: ["document.read"])
    input_schema: Literal["document.v1"] = "document.v1"
    output_schema: Literal["findings.v1"] = "findings.v1"
    max_iterations: int = Field(default=1, ge=1, le=10)
    max_runtime_seconds: int = Field(default=300, ge=1, le=3600)
    max_delegation_depth: int = Field(default=2, ge=0, le=5)
    can_delegate: Literal[False] = False


class AgentStatus(StrEnum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    WAITING_FOR_REVIEW = "WAITING_FOR_REVIEW"


class AgentRecord(BaseModel):
    agent_id: str
    run_id: str
    name: str
    role: Role
    model_id: str
    manufacturer: str
    parent_agent: str | None = None
    task: str
    depth: int = 0
    dynamic: bool = False
    can_delegate: bool = False
    status: AgentStatus = AgentStatus.CREATED
    created_at: datetime = Field(default_factory=now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    runtime_seconds: float = 0
    model_calls: int = 0
    tokens: int = 0
    token_usage_complete: bool = True
    error: str | None = None
    result_status: str | None = None
    specification: AgentSpec | None = None
    data_classification: Classification = Classification.RESTRICTED
    allowed_models: frozenset[str] = frozenset()
    allowed_tools: frozenset[str] = frozenset({"document.read"})
    allowed_documents: frozenset[str] = frozenset()
    allowed_network_targets: frozenset[str] = frozenset()
    security_mode: Literal["DEVELOPMENT"] = "DEVELOPMENT"


class AgentProposals(StrictModel):
    agents: list[AgentSpec] = Field(min_length=1, max_length=6)


class SupervisorTask(StrictModel):
    supervisor: Category
    task: str = Field(min_length=1, max_length=600)
    depends_on: list[Category] = Field(default_factory=list, max_length=3)


class ExecutionPlan(StrictModel):
    tasks: list[SupervisorTask] = Field(min_length=1, max_length=3)


class FindingDraft(StrictModel):
    category: Category
    statement: str = Field(min_length=1, max_length=600)
    kind: Literal["STRENGTH", "CRITICISM"]
    page: int | None = Field(default=None, ge=1)
    quote: str = Field(default="", max_length=800)
    rationale: str = Field(min_length=1, max_length=600)
    claim_type: Literal["TEXT", "ABSENCE"] = "TEXT"
    required_context: list[int] = Field(default_factory=list, max_length=20)


class FindingsOutput(StrictModel):
    findings: list[FindingDraft] = Field(default_factory=list, max_length=3)


class ReviewOutput(StrictModel):
    verdict: Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "UNSUPPORTED", "UNCERTAIN"]
    rationale: str = Field(min_length=1, max_length=600)
    missing_context: bool = False
    possible_hallucination: bool = False


class ModelReview(ReviewOutput):
    model_id: str
    manufacturer: str
    independent: bool = True


class Finding(FindingDraft):
    data_classification: Classification = Classification.RESTRICTED
    finding_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    agent_id: str
    model_id: str
    model: str
    manufacturer: str
    evidence_status: Literal["VALIDATED", "REJECTED", "CONTEXT_REQUIRED", "NOT_CHECKED"] = (
        "NOT_CHECKED"
    )
    evidence_detail: str = "Noch nicht geprüft."
    reviews: list[ModelReview] = Field(default_factory=list)
    superseded_reviews: list[ModelReview] = Field(default_factory=list)
    original_statement: str | None = None
    review_status: Literal["PENDING", "REVIEWED", "MISSING", "NOT_REQUESTED"] = "PENDING"
    human_status: Literal["PENDING", "ACCEPTED", "REJECTED"] = "PENDING"
    human_note: str = ""
    conflict: bool = False


class HumanReview(StrictModel):
    decision: Literal["ACCEPTED", "REJECTED"]
    note: str = Field(default="", max_length=1000)
    edited_statement: str | None = Field(default=None, min_length=1, max_length=600)


class RunRequest(StrictModel):
    # Server-owned fixture: no user data-classification field or arbitrary document path.
    document_id: Literal["synthetic-demo"] = "synthetic-demo"
    mode: Literal["A", "B", "C", "D"] = "D"
    task: str = Field(
        default="Prüfe die synthetische Arbeit anhand der Bewertungskriterien.",
        min_length=1,
        max_length=300,
    )
    criteria: list[str] = Field(
        default_factory=lambda: ["Forschungsfrage", "Methodik"], min_length=1, max_length=6
    )


class RunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    mode: Literal["A", "B", "C", "D"]
    document_id: str
    document_digest: str = ""
    criteria: list[str]
    status: Literal[
        "QUEUED", "RUNNING", "WAITING_FOR_REVIEW", "COMPLETED", "FAILED", "CANCELLED"
    ] = "QUEUED"
    privacy_mode: str = "LOCAL_ONLY"
    data_classification: Classification = Classification.RESTRICTED
    mocked: bool = False
    stage: str = "queued"
    progress: float = 0
    created_at: datetime = Field(default_factory=now)
    finished_at: datetime | None = None
    runtime_seconds: float = 0
    model_calls: int = 0
    tokens: int = 0
    reserved_tokens: int = 0
    unknown_token_calls: int = 0
    findings_count: int = 0
    validated_count: int = 0
    unsupported_count: int = 0
    conflicts_count: int = 0
    resource_samples: list[dict] = Field(default_factory=list)
    resource_peaks: dict = Field(default_factory=dict)
    model_snapshot: list[dict] = Field(default_factory=list)
    execution_snapshot: dict = Field(default_factory=dict)
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    synthesis_draft: str = ""
    final_report: str | None = None
