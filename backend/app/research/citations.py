"""Offline citation extraction/consistency and metadata checking with bounded claims."""

import re
from collections import Counter
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher

from app.assessments.routine_checks import DOI
from app.research.isbn import normalize_isbn
from app.research.provider_registry import (
    SOURCE_PROVIDERS,
    LocalResearchCache,
    SourceType,
    normalize_doi,
)
from app.security.classification import Classification, classify, combine

STATUSES = frozenset(
    {
        "VERIFIED_METADATA",
        "VERIFIED_ABSTRACT",
        "VERIFIED_FULLTEXT",
        "METADATA_MISMATCH",
        "NOT_FOUND",
        "RETRACTED",
        "CORRECTED",
        "UPDATED_VERSION_AVAILABLE",
        "INTERNAL_SOURCE",
        "RESEARCH_BLOCKED_BY_PRIVACY",
        "PROVIDER_UNAVAILABLE",
        "MANUAL_REVIEW_REQUIRED",
        "FUZZY_MATCH_CANDIDATE",
        "PROVIDER_CONFLICT",
        "PARTIAL_METADATA",
    }
)


@dataclass(frozen=True)
class BibliographicEntry:
    id: str
    page: int
    start: int
    end: int
    raw: str
    doi: str | None
    author: str | None
    year: int | None
    title: str | None
    source_type: SourceType = SourceType.UNKNOWN
    version: str | None = None
    classification: Classification = Classification.RESTRICTED
    analysis_id: str = ""
    document_id: str = ""
    isbn: str = ""

    def __post_init__(self):
        object.__setattr__(self, "classification", classify(self.classification))


def extract_citations(document) -> dict:
    scope = {
        "classification": classify(document.classification),
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
    }
    entries, mentions, warnings = [], [], []
    in_bibliography = False
    for page, text in sorted(document.pages.items()):
        pending = None

        def flush(text=text, page=page):
            nonlocal pending
            if pending is None:
                return
            start, end, _ = pending
            raw = text[start:end]
            line = " ".join(raw.split())
            parsed = re.match(
                r"(?:\[(?P<number>\d+)\]\s*)?(?P<author>[\wÀ-ž'-]+)"
                r"(?:,?\s+(?:et al\.\s*)?)\((?P<year>\d{4})\)"
                r"[.:]?\s*(?P<title>.+?)(?:\.\s*(?:https?://|doi:|10\.|ISBN)|$)",
                line,
            )
            doi = DOI.search(line)
            internal = bool(re.search(r"\bintern(?:al|e|es|er)?\b|unternehmensintern", line, re.I))
            isbn_match = re.search(r"ISBN(?:-1[03])?\s*:?\s*([0-9Xx -]{10,22})", line)
            entries.append(
                BibliographicEntry(
                    parsed.group("number")
                    if parsed and parsed.group("number")
                    else f"p{page}-r{len(entries) + 1}",
                    page,
                    start,
                    end,
                    raw,
                    normalize_doi(doi.group()) if doi else None,
                    parsed.group("author") if parsed else None,
                    int(parsed.group("year")) if parsed else None,
                    parsed.group("title").rstrip(". ") if parsed else None,
                    SourceType.INTERNAL
                    if internal
                    else SourceType.BOOK
                    if isbn_match and normalize_isbn(isbn_match.group(1))
                    else SourceType.PREPRINT
                    if re.search(r"\b(?:arxiv|preprint)\b", line, re.I)
                    else SourceType.UNKNOWN,
                    isbn=normalize_isbn(isbn_match.group(1)) if isbn_match else "",
                    **scope,
                )
            )
            if not parsed or "\n" in raw or "\r" in raw:
                warnings.append("UNPARSED_OR_MULTILINE_REFERENCE")
            pending = None

        for match in re.finditer(r"[^\r\n]+", text):
            line = match.group().strip()
            if re.fullmatch(
                r"(?:#{1,3}\s*)?(?:Literaturverzeichnis|Quellenverzeichnis|References)", line, re.I
            ):
                flush()
                in_bibliography = True
                continue
            if in_bibliography and re.match(r"^(?:#{1,3}\s*)?(?:Anhang|Appendix)\b", line, re.I):
                flush()
                in_bibliography = False
            if in_bibliography and line:
                indent = len(match.group()) - len(match.group().lstrip())
                start, end = match.start() + indent, match.start() + len(match.group().rstrip())
                new_entry = re.match(r"\[\d+\]|[\wÀ-ž'-]+.*\(\d{4}\)", line)
                # Only a deeper hanging indent is grouped. Ambiguous lines stay separate.
                if pending and indent > pending[2] and not new_entry:
                    pending = (pending[0], end, pending[2])
                else:
                    flush()
                    pending = (start, end, indent)
            else:
                for citation in re.finditer(
                    r"\[(\d+)\]|\(([\wÀ-ž'-]+)(?: et al\.)?,? (\d{4})\)", match.group()
                ):
                    mentions.append(
                        {
                            **scope,
                            "page": page,
                            "start": match.start() + citation.start(),
                            "end": match.start() + citation.end(),
                            "number": citation.group(1),
                            "author": citation.group(2),
                            "year": int(citation.group(3)) if citation.group(3) else None,
                        }
                    )
        flush()
    ids = Counter(e.id for e in entries)
    return {
        **scope,
        "entries": entries,
        "mentions": mentions,
        "warnings": sorted(
            set(
                warnings + (["AMBIGUOUS_REFERENCE_IDS"] if any(n > 1 for n in ids.values()) else [])
            )
        ),
        "method": "local-span-citation-candidates.v2",
        "complete_parser": False,
    }


def _norm(text):
    return re.sub(r"[^\w]", "", text.casefold())


def verify_citations(document, cache: LocalResearchCache | None = None, *, extracted=None) -> dict:
    cache = cache or LocalResearchCache()
    extraction = extracted or extract_citations(document)
    entries, mentions = extraction["entries"], extraction["mentions"]
    level = combine(
        document.classification,
        extraction.get("classification"),
        *(e.classification for e in entries),
        *(m.get("classification") for m in mentions),
    )

    def matches(mention, entry):
        return (
            mention["number"] == entry.id
            if mention["number"]
            else bool(
                entry.author
                and _norm(mention["author"]) == _norm(entry.author)
                and mention["year"] == entry.year
            )
        )

    missing = [m for m in mentions if not any(matches(m, e) for e in entries)]
    duplicate_keys = Counter(e.doi or _norm(e.raw) for e in entries)
    rows = []
    private = level != Classification.PUBLIC
    for entry in entries:
        local_only = entry.source_type in {
            SourceType.INTERNAL,
            SourceType.INTERVIEW,
            SourceType.OWN_DATA,
        }
        snapshots = (
            []
            if local_only
            else (
                cache.lookup(entry.doi)
                if entry.doi
                else cache.lookup_isbn(entry.isbn)
                if entry.isbn
                else []
            )
        )
        fuzzy_candidates = []
        if not snapshots and entry.title and not local_only:
            terms = " ".join(re.findall(r"\w+", entry.title)[:2])
            fuzzy_candidates = [
                {
                    "provider": r.provider,
                    "provider_id": r.provider_id,
                    "doi": r.doi,
                    "isbn": r.isbn,
                    "title_similarity": round(
                        SequenceMatcher(None, _norm(entry.title), _norm(r.title)).ratio(), 4
                    ),
                    "status": "FUZZY_MATCH_CANDIDATE",
                    "snapshot_sha256": r.snapshot_sha256,
                }
                for r in cache.search(terms)
                if terms
            ]
        metadata = [r for r in snapshots if r.provider != "retraction_watch"]
        preferred = SOURCE_PROVIDERS.get(entry.source_type)
        unsuitable = preferred is not None and any(r.provider not in preferred for r in metadata)
        checks, mismatches, fuzzy, partial = [], [], False, False
        for record in metadata:
            checked = {"doi" if entry.doi else "isbn": "MATCH"}
            if entry.title and record.title:
                ratio = SequenceMatcher(None, _norm(entry.title), _norm(record.title)).ratio()
                checked["title"] = (
                    "MATCH"
                    if _norm(entry.title) == _norm(record.title)
                    else ("FUZZY_CANDIDATE" if ratio >= 0.85 else "MISMATCH")
                )
                fuzzy |= checked["title"] == "FUZZY_CANDIDATE"
            if entry.author and record.authors:
                checked["author"] = (
                    "MATCH"
                    if any(_norm(entry.author) == _norm(a) for a in record.authors)
                    else "PARTIAL_NAME_CANDIDATE"
                    if any(
                        _norm(entry.author) in [_norm(t) for t in a.split()] for a in record.authors
                    )
                    else "MISMATCH"
                )
                fuzzy |= checked["author"] == "PARTIAL_NAME_CANDIDATE"
            if entry.year and record.year:
                checked["year"] = "MATCH" if entry.year == record.year else "MISMATCH"
            if entry.version and record.version:
                checked["version"] = "MATCH" if entry.version == record.version else "MISMATCH"
            if entry.source_type != SourceType.UNKNOWN and record.source_type != SourceType.UNKNOWN:
                checked["source_type"] = (
                    "MATCH" if entry.source_type == record.source_type else "MISMATCH"
                )
            absent = [
                field
                for field, available in (
                    ("title", entry.title and record.title),
                    ("author", entry.author and record.authors),
                    ("year", entry.year and record.year),
                )
                if not available
            ]
            partial |= bool(absent)
            checks.append(
                {
                    "provider": record.provider,
                    "retrieved_at": record.retrieved_at.isoformat(),
                    "snapshot_sha256": record.snapshot_sha256,
                    "provenance": record.provenance,
                    "fields": checked,
                    "scope": "LOCAL_METADATA_SNAPSHOT",
                    "snapshot_version": record.snapshot_version,
                    "missing_comparison_fields": absent,
                }
            )
            mismatches.extend(k for k, v in checked.items() if v == "MISMATCH")
        statuses = []
        provider_conflicts = [
            field
            for field, values in {
                "title": {_norm(r.title) for r in metadata if r.title},
                "year": {r.year for r in metadata if r.year},
                "version": {r.version for r in metadata if r.version},
                "authors": {
                    tuple(sorted(_norm(a) for a in r.authors)) for r in metadata if r.authors
                },
            }.items()
            if len(values) > 1
        ]
        if local_only:
            statuses = ["INTERNAL_SOURCE"]
            checks = []
        else:
            statuses.extend(sorted({r.notice for r in snapshots if r.notice in STATUSES}))
            if mismatches:
                statuses.append("METADATA_MISMATCH")
            elif fuzzy:
                statuses.append("FUZZY_MATCH_CANDIDATE")
            elif (partial or unsuitable) and metadata:
                statuses.append("PARTIAL_METADATA")
            elif metadata:
                statuses.append("VERIFIED_METADATA")
            else:
                statuses.extend(["NOT_FOUND", "MANUAL_REVIEW_REQUIRED"])
            if not snapshots and private:
                statuses.append("RESEARCH_BLOCKED_BY_PRIVACY")
            if provider_conflicts:
                statuses.append("PROVIDER_CONFLICT")
                statuses = [s for s in statuses if s != "VERIFIED_METADATA"]
        rows.append(
            {
                "classification": level,
                "analysis_id": document.analysis_id,
                "document_id": document.document_id,
                "entry": asdict(entry),
                "statuses": list(dict.fromkeys(statuses)),
                "checks": checks,
                "mismatched_fields": sorted(set(mismatches)),
                "provider_conflicts": provider_conflicts,
                "preferred_providers": list(preferred) if preferred is not None else [],
                "provider_type_suitability": "UNVERIFIED"
                if unsuitable
                else "WITHIN_CONFIGURED_SCOPE",
                "fuzzy_candidates": fuzzy_candidates,
                "existence": "IDENTIFIER_IN_LOCAL_SNAPSHOT" if snapshots else "NOT_FOUND_LOCALLY",
                "metadata": "CONFLICT"
                if provider_conflicts or mismatches
                else "CANDIDATE"
                if fuzzy or partial
                else "EXACT_COMPARED_FIELDS"
                if metadata
                else "UNKNOWN",
                "cited_in_extracted_text": any(matches(m, entry) for m in mentions),
                "duplicate_candidate": duplicate_keys[entry.doi or _norm(entry.raw)] > 1,
                "missing_fields": [k for k in ("author", "title", "year") if not getattr(entry, k)],
                "retraction_coverage": "NOTICE_IN_SNAPSHOT"
                if any(r.notice == "RETRACTED" for r in snapshots)
                else "UNKNOWN",
                "semantic_support": "MANUAL_REVIEW_REQUIRED",
                "quality": "UNASSESSED",
                "age_is_negative": False,
                "automatic_grade_effect": False,
            }
        )
    return {
        "classification": level,
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
        "method": extraction["method"],
        "references": rows,
        "missing_reference_candidates": missing,
        "warnings": extraction["warnings"],
        "external_requests": 0,
        "not_found_scope": "LOCAL_SNAPSHOT_ONLY",
        "fabrication_inferred": False,
        "citation_style_coverage": "NUMERIC_SINGLE_AND_SIMPLE_AUTHOR_YEAR",
        "semantic_verification": "NOT_PERFORMED",
        "snapshot": cache.snapshot_info(),
    }
