"""Free-provider metadata adapters. PRIVATE runtime exposes imports only, never HTTP."""

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.research.doi import normalize_doi
from app.schemas.domain import StrictModel
from pydantic import Field, field_validator


class SourceType(StrEnum):
    PAPER = "PAPER"
    CONFERENCE = "CONFERENCE"
    PREPRINT = "PREPRINT"
    BOOK = "BOOK"
    TEXTBOOK = "TEXTBOOK"
    DATASET = "DATASET"
    TECHNICAL_DOCUMENTATION = "TECHNICAL_DOCUMENTATION"
    STANDARD = "STANDARD"
    WEB = "WEB"
    INTERNAL = "INTERNAL"
    INTERVIEW = "INTERVIEW"
    OWN_DATA = "OWN_DATA"
    UNKNOWN = "UNKNOWN"


class MetadataRecord(StrictModel):
    doi: str
    title: str = Field(default="", max_length=2000)
    authors: list[str] = Field(default_factory=list, max_length=1000)
    year: int | None = Field(default=None, ge=1000, le=2200)
    source_type: SourceType = SourceType.UNKNOWN
    version: str | None = None
    provider: str
    retrieved_at: datetime
    snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provenance: str = Field(min_length=1, max_length=1000)
    notice: str = "UNKNOWN"
    abstract: str | None = Field(default=None, max_length=100_000)
    fulltext: str | None = Field(default=None, max_length=1_000_000)

    @field_validator("doi", mode="before")
    @classmethod
    def canonical_identifier(cls, value):
        return normalize_doi(value)


@dataclass(frozen=True)
class ProviderDefinition:
    id: str
    docs: str
    mode: str = "LOCAL_IMPORT_ONLY"
    network_enabled: bool = False
    max_cost_usd: float = 0


PROVIDERS = {
    key: ProviderDefinition(key, url)
    for key, url in {
        "crossref": "https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
        "openalex": "https://help.openalex.org/api/",
        "retraction_watch": "https://gitlab.com/crossref/retraction-watch-data",
        "semantic_scholar": "https://www.semanticscholar.org/product/api",
        "datacite": "https://support.datacite.org/docs/rest-api",
        "unpaywall": "https://unpaywall.org/api",
        "arxiv": "https://info.arxiv.org/help/api/",
    }.items()
}


def import_metadata(
    data: bytes,
    provider: str,
    *,
    retrieved_at: datetime,
    provenance: str,
    public_provenance_checked: bool = False,
) -> list[MetadataRecord]:
    if not public_provenance_checked:
        raise ValueError("PUBLIC_SNAPSHOT_PROVENANCE_REQUIRED")
    if provider not in PROVIDERS or not data or len(data) > 8_000_000:
        raise ValueError("SNAPSHOT_IMPORT_DENIED")
    digest = hashlib.sha256(data).hexdigest()
    base = {
        "provider": provider,
        "retrieved_at": retrieved_at,
        "snapshot_sha256": digest,
        "provenance": provenance,
    }
    if provider == "retraction_watch":
        entries = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    else:
        payload = json.loads(data)
        if provider == "crossref":
            message = payload.get("message", payload)
            entries = message.get("items", [message])
        elif provider == "openalex":
            entries = payload.get("results", [payload])
        else:
            raise ValueError("PROVIDER_ADAPTER_NOT_RELEASED")
    if len(entries) > 5000:
        raise ValueError("SNAPSHOT_RECORD_LIMIT")
    result = []
    for entry in entries:
        if provider == "crossref":
            types = {
                "journal-article": SourceType.PAPER,
                "proceedings-article": SourceType.CONFERENCE,
                "book": SourceType.BOOK,
                "posted-content": SourceType.PREPRINT,
                "dataset": SourceType.DATASET,
            }
            parts = entry.get("published", {}).get("date-parts", [[]])[0]
            titles = entry.get("title", [])
            result.append(
                MetadataRecord(
                    **base,
                    doi=normalize_doi(entry.get("DOI")),
                    title=titles[0] if titles else "",
                    authors=[a.get("family", a.get("name", "")) for a in entry.get("author", [])],
                    year=parts[0] if parts else None,
                    source_type=types.get(entry.get("type"), SourceType.UNKNOWN),
                    version=entry.get("version"),
                    notice="UNKNOWN",
                )
            )
        elif provider == "openalex":
            result.append(
                MetadataRecord(
                    **base,
                    doi=normalize_doi(entry.get("doi")),
                    title=entry.get("title") or "",
                    authors=[a["author"]["display_name"] for a in entry.get("authorships", [])],
                    year=entry.get("publication_year"),
                    source_type=SourceType.PREPRINT
                    if entry.get("type") == "preprint"
                    else SourceType.PAPER
                    if entry.get("type") == "article"
                    else SourceType.UNKNOWN,
                    notice="RETRACTED" if entry.get("is_retracted") is True else "UNKNOWN",
                )
            )
        else:
            notice = {
                "Retraction": "RETRACTED",
                "Correction": "CORRECTED",
                "Expression of concern": "MANUAL_REVIEW_REQUIRED",
            }.get(entry.get("RetractionNature"), "MANUAL_REVIEW_REQUIRED")
            # A semicolon may be part of a DOI. Do not guess a multi-ID separator.
            for doi in [entry.get("OriginalPaperDOI", "")]:
                if normalize_doi(doi):
                    result.append(
                        MetadataRecord(
                            **base,
                            doi=normalize_doi(doi),
                            title=entry.get("Title", ""),
                            notice=notice,
                        )
                    )
    # Records without identifiers cannot be a DOI lookup success.
    return [r for r in result if r.doi.startswith("10.") and "/" in r.doi]


class LocalResearchCache:
    def __init__(self, records=()):
        self.records = tuple(r.model_copy(deep=True) for r in records)

    def lookup(self, doi):
        return [r.model_copy(deep=True) for r in self.records if r.doi == normalize_doi(doi)]

    def search(self, public_terms):
        terms = public_terms.casefold().split()
        return [
            r.model_copy(deep=True)
            for r in self.records
            if all(term in r.title.casefold() for term in terms)
        ][:20]
