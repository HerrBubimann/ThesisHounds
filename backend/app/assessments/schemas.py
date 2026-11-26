from typing import Literal
from uuid import uuid4

from app.schemas.domain import StrictModel
from pydantic import Field

Judgment = Literal["POSITIVE", "MIXED", "NEGATIVE", "NOT_ASSESSABLE"]


class AssessmentRequest(StrictModel):
    work_type: Literal["PA1", "PA2", "BA"]
    profile_id: str = Field(min_length=1, max_length=40)
    document_id: Literal["synthetic-demo"] = "synthetic-demo"


class CriterionReview(StrictModel):
    criterion_id: str = Field(min_length=1, max_length=40)
    judgment: Judgment
    observations: str = Field(min_length=1, max_length=1000)
    strengths: str = Field(default="", max_length=600)
    weaknesses: str = Field(default="", max_length=600)
    rationale: str = Field(min_length=1, max_length=1000)
    open_questions: str = Field(default="", max_length=600)


class HumanReviewSubmission(StrictModel):
    criteria: list[CriterionReview] = Field(min_length=1, max_length=6)
    release: Literal[True]


class AIObservation(StrictModel):
    judgment: Judgment
    kind: Literal[
        "STRENGTH",
        "WEAKNESS",
        "FORMAL_ISSUE",
        "SOURCE_ISSUE",
        "OPEN_QUESTION",
        "UNVERIFIABLE",
        "SECURITY_INCIDENT",
    ]
    description: str = Field(min_length=1, max_length=600)
    rationale: str = Field(min_length=1, max_length=600)
    strengths: str = Field(default="", max_length=400)
    weaknesses: str = Field(default="", max_length=400)
    page: int | None = Field(default=None, ge=1)
    quote: str = Field(default="", max_length=800)
    uncertainty: Literal["LOW", "HIGH", "UNKNOWN"] = "UNKNOWN"


class AssessmentFinding(AIObservation):
    finding_id: str = Field(default_factory=lambda: str(uuid4()))
    assessment_id: str
    criterion_id: str
    category: str
    model_id: str
    manufacturer: str
    agent_id: str
    reviewer_model: str | None = None
    evidence_status: Literal["QUOTE_MATCHED", "UNVERIFIED"] = "UNVERIFIED"
    sources: list[dict] = Field(default_factory=list)
    human_approval: Literal["PENDING"] = "PENDING"


class DiscussionRequest(StrictModel):
    criterion_id: str = Field(min_length=1, max_length=40)
    question: str = Field(min_length=1, max_length=1000)


class DiscussionOutput(StrictModel):
    answer: str = Field(min_length=1, max_length=1800)


class CriterionDecision(StrictModel):
    criterion_id: str = Field(min_length=1, max_length=40)
    include_ai_finding: bool  # Deliberately no preselected agreement.
    conclusion: str = Field(min_length=1, max_length=1000)
    rationale: str = Field(min_length=1, max_length=1000)


class ExplicitRelease(StrictModel):
    confirmed: Literal[True]
