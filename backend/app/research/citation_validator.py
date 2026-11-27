"""Evidence metadata contract. A record never implies content verification."""

from datetime import date, datetime
from typing import Literal

from app.schemas.domain import StrictModel
from pydantic import Field, HttpUrl, model_validator


class ResearchEvidence(StrictModel):
    title: str = Field(min_length=1, max_length=500)
    authors: list[str] = Field(default_factory=list, max_length=100)
    published_at: date | None = None
    doi: str | None = None
    url: HttpUrl | None = None
    publication_type: str | None = None
    version: str | None = None
    provider: str
    retrieved_at: datetime
    criterion_id: str
    verification: Literal["UNVERIFIED", "METADATA", "ABSTRACT", "FULLTEXT"] = "UNVERIFIED"
    verification_note: str = ""
    correction_status: Literal["UNKNOWN", "CORRECTED", "RETRACTED", "NONE_REPORTED"] = "UNKNOWN"

    @model_validator(mode="after")
    def require_verification_provenance(self):
        if self.verification != "UNVERIFIED" and not self.verification_note:
            raise ValueError("Verification requires a scoped provenance note")
        return self
