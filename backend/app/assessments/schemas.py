from typing import Literal
from uuid import uuid4

from app.schemas.domain import StrictModel
from pydantic import Field

Judgment = Literal["POSITIVE", "MIXED", "NEGATIVE", "NOT_ASSESSABLE"]


class AssessmentRequest(StrictModel):
    work_type: Literal["PA1", "PA2", "BA"]
    profile_id: str = Field(min_length=1, max_length=40)
    document_id: str = Field(
        default="synthetic-demo", pattern=r"^(synthetic-demo|pilot-[0-9a-f]{64})$"
    )
    program: Literal["data_science_ai", "wirtschaftsinformatik"] = "data_science_ai"
    cohort: str | None = Field(default=None, pattern=r"^(DS|WI)[0-9]{2}$")


class AcademicDecision(StrictModel):
    finding_id: str = Field(min_length=1, max_length=100)
    decision: Literal["ACCEPTED", "REJECTED"]
    rationale: str = Field(min_length=1, max_length=1000)


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
    claim_type: Literal["TEXT", "ABSENCE"] = "TEXT"
    required_context: list[int] = Field(default_factory=list, max_length=100)
    supporting_passages: list["EvidencePassage"] = Field(default_factory=list, max_length=4)
    relationships: list["ScientificRelationship"] = Field(default_factory=list, max_length=4)


class EvidencePassage(StrictModel):
    page: int = Field(ge=1)
    quote: str = Field(min_length=1, max_length=800)


class ScientificRelationship(StrictModel):
    source: Literal[
        "QUESTION",
        "OBJECTIVE",
        "THEORY",
        "PRIOR_WORK",
        "METHOD",
        "DATA",
        "ANALYSIS",
        "RESULTS",
        "DISCUSSION",
        "LIMITATIONS",
        "CONCLUSION",
    ]
    target: Literal[
        "QUESTION",
        "OBJECTIVE",
        "THEORY",
        "PRIOR_WORK",
        "METHOD",
        "DATA",
        "ANALYSIS",
        "RESULTS",
        "DISCUSSION",
        "LIMITATIONS",
        "CONCLUSION",
    ]
    relation: Literal[
        "ALIGNED",
        "POSSIBLE_CONTRADICTION",
        "UNANSWERED",
        "UNSUPPORTED_CONCLUSION",
        "NOT_ASSESSABLE",
    ]
    rationale: str = Field(min_length=1, max_length=400)
    passages: list[EvidencePassage] = Field(default_factory=list, max_length=4)


class AdversarialChallenge(StrictModel):
    verdict: Literal["SUPPORTED", "UNSUPPORTED", "UNCERTAIN"]
    rationale: str = Field(min_length=1, max_length=600)
    counterargument: str = Field(default="", max_length=600)
    missing_context: bool = False
    proposed_correction: str = Field(default="", max_length=600)
    counter_page: int | None = Field(default=None, ge=1)
    counter_quote: str = Field(default="", max_length=800)


class AssessmentFinding(AIObservation):
    data_classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"] = "RESTRICTED"
    finding_id: str = Field(default_factory=lambda: str(uuid4()))
    assessment_id: str
    criterion_id: str
    category: str
    model_id: str
    manufacturer: str
    agent_id: str
    reviewer_model: str | None = None
    evidence_status: Literal[
        "QUOTE_MATCHED", "UNVERIFIED", "REJECTED", "CONTEXT_REQUIRED", "ABSENCE_UNPROVEN"
    ] = "UNVERIFIED"
    sources: list[dict] = Field(default_factory=list)
    human_approval: Literal["PENDING"] = "PENDING"
    chapter: str | None = None
    block_id: str | None = None
    source_start: int | None = None
    source_end: int | None = None
    evidence_detail: str = ""
    model_digest: str = ""
    mocked: bool = True
    routing: dict = Field(default_factory=dict)
    verification_status: Literal[
        "NOT_REQUESTED", "MODEL_SUPPORTED", "UNRESOLVED", "CHALLENGED", "UNAVAILABLE"
    ] = "NOT_REQUESTED"
    verification_rounds: list[dict] = Field(default_factory=list, max_length=2)
    conflict: bool = False
    origin: Literal["MANDATORY", "ADAPTIVE"] = "MANDATORY"
    supplemental: list["AssessmentFinding"] = Field(default_factory=list, max_length=6)
    evidence_quality: Literal[
        "DIRECT_EVIDENCE",
        "MULTIPLE_EVIDENCE",
        "INFERRED",
        "CONTRADICTORY",
        "INSUFFICIENT",
        "NOT_ASSESSABLE",
    ] = "NOT_ASSESSABLE"
    supporting_evidence: list[dict] = Field(default_factory=list)
    contradicting_evidence: list[dict] = Field(default_factory=list)
    relationship_checks: list[dict] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    unverifiable_aspects: list[str] = Field(default_factory=list)
    context_trace: dict = Field(default_factory=dict)
    escalation: dict = Field(default_factory=dict)
    performance: dict = Field(default_factory=dict)
    provenance: dict = Field(default_factory=dict)


class FindingFeedback(StrictModel):
    finding_id: str = Field(min_length=1, max_length=100)
    action: Literal[
        "ACCEPT", "REJECT", "CORRECT", "SUPPLEMENT", "NOT_RELEVANT", "INSUFFICIENT_EVIDENCE"
    ]
    reason: (
        Literal[
            "WRONG_STATEMENT",
            "MISSING_CONTEXT",
            "WRONG_CRITERION",
            "SOURCE_ERROR",
            "UNJUSTIFIED_CRITICISM",
            "INSUFFICIENT_EVIDENCE",
            "DUPLICATE",
        ]
        | None
    ) = None
    rationale: str = Field(min_length=1, max_length=1000)
    correction: str = Field(default="", max_length=1600)


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
    include_finding_ids: list[str] = Field(default_factory=list, max_length=7)


class ExplicitRelease(StrictModel):
    confirmed: Literal[True]


class DocumentSecurityDecision(StrictModel):
    finding_ids: list[str] = Field(max_length=200)
    allow_public_processing: bool
    rationale: str = Field(min_length=1, max_length=1000)
    confirmed: Literal[True]
