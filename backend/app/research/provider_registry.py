"""Free-provider metadata adapters. PRIVATE runtime exposes imports only, never HTTP."""

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.research.doi import normalize_doi
from app.research.isbn import normalize_isbn
from app.schemas.domain import StrictModel
from pydantic import Field, field_validator


class SourceType(StrEnum):
    PAPER = "PAPER"
    CONFERENCE = "CONFERENCE"
    PREPRINT = "PREPRINT"
    BOOK = "BOOK"
    TEXTBOOK = "TEXTBOOK"
    DATASET = "DATASET"
    SOFTWARE = "SOFTWARE"
    TECHNICAL_DOCUMENTATION = "TECHNICAL_DOCUMENTATION"
    STANDARD = "STANDARD"
    WEB = "WEB"
    INTERNAL = "INTERNAL"
    INTERVIEW = "INTERVIEW"
    OWN_DATA = "OWN_DATA"
    UNKNOWN = "UNKNOWN"


class MetadataRecord(StrictModel):
    doi: str = ""
    isbn: str = ""
    provider_id: str = Field(default="", max_length=300)
    venue: str = Field(default="", max_length=1000)
    publication_kind: str = Field(default="", max_length=80)
    license_id: str = Field(default="UNKNOWN", max_length=100)
    snapshot_version: str = Field(default="", max_length=100)
    source_release_doi: str = Field(default="", max_length=100)
    selection_sha256: str = Field(default="", max_length=64)
    export_rights_reviewed: bool = False
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

    @field_validator("isbn", mode="before")
    @classmethod
    def canonical_isbn(cls, value):
        result = normalize_isbn(value)
        if value and not result:
            raise ValueError("INVALID_ISBN_CHECKSUM")
        return result


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
        "dblp": "https://dblp.org/faq/How+to+parse+dblp+xml.html",
        "open_library": "https://openlibrary.org/developers/api",
        "zenodo": "https://developers.zenodo.org/",
        "software_heritage": "https://archive.softwareheritage.org/api/1/",
        "doaj": "https://doaj.org/docs/api/",
        "opencitations": "https://api.opencitations.net/",
        "europe_pmc": "https://europepmc.org/RestfulWebService",
        "library_export": "https://www.mosbach.dhbw.de/service-einrichtungen/bibliothek/literatursuche/",
    }.items()
}

# Preference/suitability only. A missing local provider never triggers an online lookup.
SOURCE_PROVIDERS = {
    SourceType.PAPER: ("crossref", "dblp", "openalex", "library_export"),
    SourceType.CONFERENCE: ("dblp", "crossref", "openalex", "library_export"),
    SourceType.PREPRINT: ("arxiv", "openalex", "crossref", "dblp"),
    SourceType.BOOK: ("open_library", "crossref", "library_export"),
    SourceType.TEXTBOOK: ("open_library", "crossref", "library_export"),
    SourceType.DATASET: ("datacite", "zenodo"),
    SourceType.SOFTWARE: ("software_heritage", "zenodo", "datacite"),
    SourceType.INTERNAL: (),
    SourceType.INTERVIEW: (),
    SourceType.OWN_DATA: (),
}


def import_metadata(
    data: bytes,
    provider: str,
    *,
    retrieved_at: datetime,
    provenance: str,
    public_provenance_checked: bool = False,
    export_rights_reviewed: bool = False,
) -> list[MetadataRecord]:
    try:
        return _import_metadata(
            data,
            provider,
            retrieved_at=retrieved_at,
            provenance=provenance,
            public_provenance_checked=public_provenance_checked,
            export_rights_reviewed=export_rights_reviewed,
        )
    except (AttributeError, TypeError, KeyError):
        raise ValueError("PUBLIC_METADATA_SCHEMA_INVALID") from None


def _import_metadata(
    data,
    provider,
    *,
    retrieved_at,
    provenance,
    public_provenance_checked,
    export_rights_reviewed=False,
):
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
    if provider == "library_export":
        from app.research.library_exports import import_library_export

        return import_library_export(data, rights_reviewed=export_rights_reviewed, **base)
    if provider == "dblp":
        from app.research.dblp import iter_dblp

        return list(iter_dblp(io.BytesIO(data), **base))
    if provider == "retraction_watch":
        entries = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
    else:
        payload = json.loads(data)
        if provider == "crossref":
            message = payload.get("message", payload)
            entries = message.get("items", [message])
        elif provider == "openalex":
            entries = payload.get("results", [payload])
        elif provider == "open_library":
            entries = (
                list(payload.values()) if any(k.startswith("ISBN:") for k in payload) else [payload]
            )
        elif provider == "datacite":
            rows = payload.get("data", [])
            entries = rows if isinstance(rows, list) else [rows]
        elif provider == "zenodo":
            entries = payload.get("hits", {}).get("hits", [payload])
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
        elif provider in {"open_library", "datacite", "zenodo"}:
            if provider == "open_library":
                identifiers = entry.get("identifiers", {})
                identifiers_list = identifiers.get("isbn_13", []) + identifiers.get("isbn_10", [])
                isbn = next((normalize_isbn(i) for i in identifiers_list if normalize_isbn(i)), "")
                result.append(
                    MetadataRecord(
                        **base,
                        isbn=isbn,
                        title=entry.get("title", ""),
                        provider_id=entry.get("key", ""),
                        authors=[a.get("name", "") for a in entry.get("authors", [])],
                        year=int(
                            re.search(r"\b[12][0-9]{3}\b", entry.get("publish_date", "")).group()
                        )
                        if re.search(r"\b[12][0-9]{3}\b", entry.get("publish_date", ""))
                        else None,
                        source_type=SourceType.BOOK,
                    )
                )
            else:
                meta = (
                    entry.get("attributes", {})
                    if provider == "datacite"
                    else entry.get("metadata", {})
                )
                is_data = meta.get("types", {}).get("resourceTypeGeneral") == "Dataset"
                is_software = meta.get("types", {}).get("resourceTypeGeneral") == "Software"
                if provider == "zenodo":
                    is_data = meta.get("resource_type", {}).get("type") == "dataset"
                    is_software = meta.get("resource_type", {}).get("type") == "software"
                titles = meta.get("titles", [])
                names = meta.get("creators", [])
                result.append(
                    MetadataRecord(
                        **base,
                        doi=meta.get("doi", entry.get("id", "")),
                        title=(titles[0].get("title", "") if titles else meta.get("title", "")),
                        authors=[a.get("name", "") for a in names],
                        year=meta.get("publicationYear")
                        or (
                            int(meta["publication_date"][:4])
                            if re.match(r"^[12][0-9]{3}-", meta.get("publication_date", ""))
                            else None
                        ),
                        version=meta.get("version"),
                        provider_id=str(entry.get("id", "")),
                        source_type=SourceType.DATASET
                        if is_data
                        else SourceType.SOFTWARE
                        if is_software
                        else SourceType.UNKNOWN,
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
    return [r for r in result if r.doi or r.isbn or r.provider_id]


class LocalResearchCache:
    def __init__(self, records=(), *, database=None, manifest=None):
        self.records = tuple(r.model_copy(deep=True) for r in records)
        self.database, self.manifest = database, manifest or {}

    def _query(self, sql, values):
        from app.research.sqlite_store import query_records

        return query_records(self.database, sql, values)

    def lookup(self, doi):
        if not normalize_doi(doi):
            return []
        if self.database:
            return self._query(
                "SELECT record_json FROM records WHERE doi=? LIMIT 100", (normalize_doi(doi),)
            )
        return [r.model_copy(deep=True) for r in self.records if r.doi == normalize_doi(doi)]

    def lookup_isbn(self, isbn):
        key = normalize_isbn(isbn)
        if not key:
            return []
        if self.database:
            return self._query("SELECT record_json FROM records WHERE isbn=? LIMIT 100", (key,))
        return [r.model_copy(deep=True) for r in self.records if r.isbn == key]

    def search(self, public_terms):
        if self.database:
            import re

            terms = re.findall(r"\w+", public_terms)[:20]
            if not terms:
                return []
            match = " AND ".join('"' + t + '"' for t in terms)
            return self._query(
                "SELECT record_json FROM records JOIN records_fts ON records.id=records_fts.rowid "
                "WHERE records_fts MATCH ? ORDER BY rank, records.id LIMIT 20",
                (match,),
            )
        terms = public_terms.casefold().split()
        return [
            r.model_copy(deep=True)
            for r in self.records
            if all(term in (r.title + " " + " ".join(r.authors)).casefold() for term in terms)
        ][:20]

    def snapshot_info(self, *, as_of=None, max_age_days=90):
        from datetime import UTC

        timestamp = self.manifest.get("updated_at")
        age = (
            (as_of or datetime.now(UTC)) - datetime.fromisoformat(timestamp) if timestamp else None
        )
        return {
            **self.manifest,
            "freshness": "UNKNOWN"
            if age is None
            else "STALE"
            if age.days > max_age_days
            else "WITHIN_CONFIGURED_AGE",
            "max_age_days": max_age_days,
            "online_currency_verified": False,
        }

    def iter_records(self):
        """Operator-side bounded merge source; never exposed as an agent tool."""
        if not self.database:
            yield from (r.model_copy(deep=True) for r in self.records)
            return
        import sqlite3
        from contextlib import closing

        with closing(
            sqlite3.connect(self.database.as_uri() + "?mode=ro&immutable=1", uri=True)
        ) as db:
            db.execute("PRAGMA trusted_schema=OFF")
            for row in db.execute("SELECT record_json FROM records ORDER BY id"):
                yield MetadataRecord.model_validate_json(row[0])
