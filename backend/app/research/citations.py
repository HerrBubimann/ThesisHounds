"""Offline citation extraction/consistency and metadata checking with bounded claims."""

import re
from collections import Counter
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher

from app.assessments.routine_checks import DOI
from app.research.provider_registry import LocalResearchCache, SourceType, normalize_doi
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
                r"[.:]?\s*(?P<title>.+?)(?:\.\s*(?:https?://|doi:|10\.)|$)",
                line,
            )
            doi = DOI.search(line)
            internal = bool(re.search(r"\bintern(?:al|e|es|er)?\b|unternehmensintern", line, re.I))
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
                    else SourceType.PREPRINT
                    if re.search(r"\b(?:arxiv|preprint)\b", line, re.I)
                    else SourceType.UNKNOWN,
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
        snapshots = cache.lookup(entry.doi) if entry.doi else []
        metadata = [r for r in snapshots if r.provider != "retraction_watch"]
        checks, mismatches = [], []
        for record in metadata:
            checked = {"doi": "MATCH"}
            if entry.title and record.title:
                checked["title"] = (
                    "MATCH"
                    if SequenceMatcher(None, _norm(entry.title), _norm(record.title)).ratio()
                    >= 0.96
                    else "MISMATCH"
                )
            if entry.author and record.authors:
                checked["author"] = (
                    "MATCH"
                    if any(_norm(entry.author) in _norm(a) for a in record.authors)
                    else "MISMATCH"
                )
            if entry.year and record.year:
                checked["year"] = "MATCH" if entry.year == record.year else "MISMATCH"
            if entry.version and record.version:
                checked["version"] = "MATCH" if entry.version == record.version else "MISMATCH"
            if entry.source_type != SourceType.UNKNOWN and record.source_type != SourceType.UNKNOWN:
                checked["source_type"] = (
                    "MATCH" if entry.source_type == record.source_type else "MISMATCH"
                )
            checks.append(
                {
                    "provider": record.provider,
                    "retrieved_at": record.retrieved_at.isoformat(),
                    "snapshot_sha256": record.snapshot_sha256,
                    "provenance": record.provenance,
                    "fields": checked,
                    "scope": "LOCAL_METADATA_SNAPSHOT",
                }
            )
            mismatches.extend(k for k, v in checked.items() if v == "MISMATCH")
        statuses = []
        if entry.source_type == SourceType.INTERNAL:
            statuses = ["INTERNAL_SOURCE"]
            checks = []
        else:
            statuses.extend(sorted({r.notice for r in snapshots if r.notice in STATUSES}))
            if mismatches:
                statuses.append("METADATA_MISMATCH")
            elif metadata:
                statuses.append("VERIFIED_METADATA")
            else:
                statuses.extend(["NOT_FOUND", "MANUAL_REVIEW_REQUIRED"])
            if not snapshots and private:
                statuses.append("RESEARCH_BLOCKED_BY_PRIVACY")
        rows.append(
            {
                "classification": level,
                "analysis_id": document.analysis_id,
                "document_id": document.document_id,
                "entry": asdict(entry),
                "statuses": list(dict.fromkeys(statuses)),
                "checks": checks,
                "mismatched_fields": sorted(set(mismatches)),
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
    }
