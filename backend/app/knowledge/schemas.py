from datetime import date, datetime
from enum import IntEnum
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_serializer, field_validator, model_validator

from app.schemas.domain import StrictModel
from app.security.classification import Classification, classify


class Hierarchy(IntEnum):
    EXAMINATION_LAW = 0
    MOSBACH_PROGRAM = 1
    MOSBACH_ASSESSMENT = 2
    MOSBACH_WI_DELEGATED = 3
    MOSBACH_FACULTY = 4
    DHBW_SUPPLEMENT = 5
    SCIENTIFIC_STANDARD = 6
    OTHER_CAMPUS = 7


class SourceDocument(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,79}$")
    title: str = Field(min_length=1, max_length=300)
    publisher: str = Field(min_length=1, max_length=150)
    campus: str
    faculty: str
    programs: list[str] = Field(min_length=1, max_length=10)
    cohorts: list[str] = Field(default_factory=list, max_length=20)
    work_types: list[Literal["PA1", "PA2", "BA"]] = Field(min_length=1, max_length=3)
    version: str
    published_at: date | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    original_url: str = Field(min_length=1, max_length=1000)
    retrieved_at: datetime | None = None
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    classification: Classification = Classification.RESTRICTED
    release: Literal["CANDIDATE", "APPROVED", "REJECTED"] = "CANDIDATE"
    binding: Literal["CANDIDATE", "BINDING", "ORIENTATION"] = "CANDIDATE"
    hierarchy: Hierarchy
    delegated_by: str | None = None
    availability: Literal["RETRIEVED", "MANUAL_IMPORT_REQUIRED", "UNAVAILABLE"]
    notes: str = Field(default="", max_length=1000)

    @field_validator("original_url")
    @classmethod
    def public_reference_url(cls, value):
        target = urlsplit(value)
        if target.scheme != "https" or not target.hostname or target.username or target.password:
            raise ValueError("INVALID_SOURCE_URL")
        return value

    @field_validator("classification", mode="before")
    @classmethod
    def safe_level(cls, value):
        return classify(value)

    @field_serializer("classification")
    def serialize_level(self, value):
        return value.value

    @model_validator(mode="after")
    def source_bounds(self):
        if self.valid_until and self.valid_from and self.valid_until < self.valid_from:
            raise ValueError("INVALID_VALIDITY_INTERVAL")
        if self.hierarchy == Hierarchy.OTHER_CAMPUS and self.binding == "BINDING":
            raise ValueError("OTHER_CAMPUS_IS_ORIENTATION_ONLY")
        if self.hierarchy == Hierarchy.MOSBACH_WI_DELEGATED and not self.delegated_by:
            raise ValueError("PROGRAM_DELEGATION_REQUIRED")
        return self


class Rule(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,79}$")
    description: str = Field(min_length=1, max_length=500)
    category: str
    requirement: Literal["MANDATORY", "RECOMMENDATION"] = "MANDATORY"
    weight: float | None = Field(default=None, gt=0, le=100)
    max_points: float | None = Field(default=None, gt=0, le=100)
    method: str = Field(min_length=1, max_length=80)
    parameters: dict = Field(default_factory=dict)
    scope: Literal["DOCUMENT", "ORGANIZATIONAL"] = "DOCUMENT"
    source_id: str
    source_location: str = Field(min_length=1, max_length=300)
    release: Literal["CANDIDATE", "APPROVED", "REJECTED"] = "CANDIDATE"
    conflict_key: str | None = None
    conflict_value: str | None = None


class InstitutionalProfile(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,79}$")
    campus: Literal["Mosbach"] = "Mosbach"
    program: Literal["data_science_ai", "wirtschaftsinformatik"]
    cohort: str = Field(pattern=r"^(DS|WI)[0-9]{2}$")
    work_type: Literal["PA1", "PA2", "BA"]
    version: str
    release: Literal["CANDIDATE", "APPROVED", "REJECTED"] = "CANDIDATE"
    rules: list[Rule] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_rules(self):
        if len({r.id for r in self.rules}) != len(self.rules):
            raise ValueError("DUPLICATE_RULE_ID")
        return self


class HumanApproval(StrictModel):
    """Stored separately from imported content; no API accepts this as a promotion command."""

    subject_id: str
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewer: str = Field(min_length=1, max_length=100)
    reviewed_at: datetime
    applicability_confirmed: Literal[True]
    validity_confirmed: Literal[True]
    public_provenance_confirmed: bool = False
    resolved_conflicts: dict[str, str] = Field(default_factory=dict)
