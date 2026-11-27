"""Offline bibliographic checks over operator-supplied PUBLIC snapshots; no HTTP client."""

from datetime import date
from typing import Literal

from app.assessments.routine_checks import inventory
from app.research.citation_validator import ResearchEvidence
from app.schemas.domain import StrictModel
from app.services.document_intelligence import structure_document
from pydantic import Field, model_validator


class LocalSource(StrictModel):
    evidence: ResearchEvidence
    classification: Literal["PUBLIC"] = "PUBLIC"
    snapshot_provenance: str = Field(min_length=1, max_length=500)
    abstract: str | None = None
    fulltext: str | None = None

    @model_validator(mode="after")
    def require_inspected_material(self):
        if self.evidence.verification == "FULLTEXT" and not self.fulltext:
            raise ValueError("Fulltext verification requires locally available fulltext")
        if self.evidence.verification == "ABSTRACT" and not self.abstract:
            raise ValueError("Abstract verification requires a locally available abstract")
        return self


class CitationAssertion(StrictModel):
    doi: str
    page: int = Field(ge=1)
    quote: str = Field(default="", max_length=2000)
    cited_version: str | None = None


def normalize_doi(value: str) -> str:
    return value.strip().casefold().removeprefix("https://doi.org/").removeprefix("doi:").strip()


def verify_local_sources(
    document,
    sources: list[LocalSource],
    *,
    as_of: date | None = None,
    assertions: list[CitationAssertion] = (),
) -> dict:
    as_of = as_of or date.today()
    by_doi = {}
    for source in sources:
        if source.evidence.doi:
            key = normalize_doi(source.evidence.doi)
            if key in by_doi:
                raise ValueError("Ambiguous source snapshots; choose a version explicitly")
            by_doi[key] = source
    structure = structure_document(document)
    bibliography = [b for b in structure.blocks if b.kind == "BIBLIOGRAPHY"]
    rows = []
    for candidate in inventory(document)["doi_candidates"]:
        doi = normalize_doi(candidate["doi_candidate"])
        source = by_doi.get(doi)
        evidence = source.evidence if source else None
        claim = next(
            (a for a in assertions if normalize_doi(a.doi) == doi and a.page == candidate["page"]),
            None,
        )
        grounded = bool(claim and claim.quote and claim.quote in document.pages.get(claim.page, ""))
        rows.append(
            {
                **candidate,
                "existence": "SNAPSHOT_MATCH"
                if evidence and evidence.verification != "UNVERIFIED"
                else "UNKNOWN",
                "doi_match": bool(evidence),
                "version": evidence.version if evidence else None,
                "version_match": (
                    "MATCH" if claim.cited_version == evidence.version else "MISMATCH"
                )
                if claim and claim.cited_version and evidence and evidence.version
                else "UNKNOWN",
                "verification": evidence.verification if evidence else "UNVERIFIED",
                "correction_status": evidence.correction_status if evidence else "UNKNOWN",
                "snapshot_at": evidence.retrieved_at.isoformat() if evidence else None,
                "snapshot_age_days": (as_of - evidence.retrieved_at.date()).days
                if evidence
                else None,
                "publication_year": evidence.published_at.year
                if evidence and evidence.published_at
                else None,
                "in_bibliography": "FOUND"
                if any(doi in b.text.casefold() for b in bibliography)
                else "NOT_FOUND_IN_EXTRACTED_BIBLIOGRAPHY"
                if document.complete and bibliography
                else "UNKNOWN",
                "abstract_available": bool(source and source.abstract),
                "fulltext_available": bool(source and source.fulltext),
                "quote_grounded_in_document": grounded,
                "fulltext_quote_match": bool(claim.quote in source.fulltext)
                if grounded and source and source.fulltext
                else None,
                "semantic_support": "REQUIRES_HUMAN_REVIEW",
                "relevance": "UNASSESSED",
                "age_is_a_negative_judgment": False,
            }
        )
    return {
        "classification": document.classification,
        "method": "offline-source-snapshots.v1",
        "citations": rows,
        "external_requests": 0,
        "limitations": "Snapshot matching establishes neither current online existence "
        "nor semantic verification.",
    }
