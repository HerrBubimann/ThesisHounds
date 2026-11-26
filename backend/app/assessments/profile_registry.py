"""Versioned example rubrics; official activation requires source and human approval."""

from pathlib import Path
from typing import Literal

import yaml
from app.schemas.domain import Category, StrictModel
from pydantic import Field, model_validator


class Criterion(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    category: Category
    description: str = Field(min_length=1, max_length=300)
    expected_evidence: str = Field(min_length=1, max_length=300)
    instructions: str = Field(min_length=1, max_length=300)
    weight: float = Field(default=1, gt=0, le=100)
    max_points: float = Field(default=10, gt=0, le=100)
    required: bool = True
    source: str = Field(min_length=1, max_length=300)


class AssessmentProfile(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    work_type: Literal["PA1", "PA2", "BA"]
    version: str = Field(min_length=1, max_length=40)
    status: Literal["EXAMPLE", "CANDIDATE", "APPROVED"] = "CANDIDATE"
    source: str = Field(min_length=1, max_length=300)
    approved_by: str = Field(default="", max_length=100)
    approved_at: str = Field(default="", max_length=40)
    subject_notes: str = Field(default="", max_length=500)
    criteria: list[Criterion] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def validate_catalog(self):
        if len({c.id for c in self.criteria}) != len(self.criteria):
            raise ValueError("Duplicate criterion IDs")
        if self.status == "APPROVED" and not (self.approved_by and self.approved_at):
            raise ValueError("Official rubrics require explicit human approval")
        return self


class ProfileRegistry:
    def __init__(self, directory: Path):
        profiles = [
            AssessmentProfile.model_validate(yaml.safe_load(path.read_text("utf-8")))
            for path in sorted(directory.glob("*.yaml"))
        ]
        self.profiles = {p.id: p for p in profiles}
        if not profiles or len(self.profiles) != len(profiles):
            raise ValueError("Missing or duplicate assessment profiles")

    def get(self, profile_id: str, work_type: str) -> AssessmentProfile:
        profile = self.profiles.get(profile_id)
        if not profile or profile.work_type != work_type or profile.status == "CANDIDATE":
            raise ValueError("Profile is unavailable for this work type")
        return profile.model_copy(deep=True)
