"""Bounded metadata-only RIS/CSL exports. No catalog login, URL fetching or full text."""

import json
import re

from app.research.provider_registry import MetadataRecord, SourceType

RIS_FIELDS = {
    "TY",
    "TI",
    "T1",
    "AU",
    "A1",
    "PY",
    "Y1",
    "DO",
    "SN",
    "JO",
    "JF",
    "T2",
    "ID",
    "UR",
    "VL",
    "IS",
    "SP",
    "EP",
    "PB",
    "ET",
    "LA",
    "ER",
    "CY",
    "DA",
    "KW",
}
CSL_FIELDS = {
    "id",
    "type",
    "title",
    "author",
    "issued",
    "DOI",
    "ISBN",
    "container-title",
    "publisher",
    "version",
    "page",
    "volume",
    "issue",
    "URL",
    "language",
    "accessed",
}
KINDS = {
    "JOUR": SourceType.PAPER,
    "CONF": SourceType.CONFERENCE,
    "CPAPER": SourceType.CONFERENCE,
    "BOOK": SourceType.BOOK,
    "CHAP": SourceType.BOOK,
    "DATA": SourceType.DATASET,
    "COMP": SourceType.SOFTWARE,
    "RPRT": SourceType.TECHNICAL_DOCUMENTATION,
    "article-journal": SourceType.PAPER,
    "paper-conference": SourceType.CONFERENCE,
    "book": SourceType.BOOK,
    "chapter": SourceType.BOOK,
    "dataset": SourceType.DATASET,
    "software": SourceType.SOFTWARE,
    "report": SourceType.TECHNICAL_DOCUMENTATION,
}


def parse_ris(text):
    rows, current, last = [], None, None
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([A-Z0-9]{2})  - ?(.*)", line)
        if not match:
            if current is not None and last and line.startswith((" ", "\t")):
                current[last][-1] += " " + line.strip()
                if len(current[last][-1]) > 4000:
                    raise ValueError("LIBRARY_EXPORT_FIELD_LIMIT")
                continue
            raise ValueError("LIBRARY_RIS_SYNTAX_DENIED")
        tag, value = match.groups()
        if len(value) > 4000:
            raise ValueError("LIBRARY_EXPORT_FIELD_LIMIT")
        if tag not in RIS_FIELDS:
            raise ValueError("LIBRARY_METADATA_ONLY_FIELD_DENIED")
        if tag == "TY":
            if current is not None:
                raise ValueError("LIBRARY_RIS_NESTED_RECORD")
            current = {}
        if current is None:
            raise ValueError("LIBRARY_RIS_RECORD_REQUIRED")
        current.setdefault(tag, []).append(value)
        last = tag
        if tag == "ER":
            rows.append(current)
            current, last = None, None
            if len(rows) > 1000:
                raise ValueError("LIBRARY_EXPORT_RECORD_LIMIT")
    if current is not None or not rows:
        raise ValueError("LIBRARY_RIS_INCOMPLETE_RECORD")
    return rows


def import_library_export(data, *, rights_reviewed=False, **base):
    if rights_reviewed is not True or len(data) > 2_000_000:
        raise ValueError("LIBRARY_EXPORT_RIGHTS_REVIEW_REQUIRED")
    text = data.decode("utf-8-sig")
    csl = text.lstrip().startswith(("[", "{"))
    rows = json.loads(text) if csl else parse_ris(text)
    rows = [rows] if isinstance(rows, dict) else rows
    if not isinstance(rows, list) or not 1 <= len(rows) <= 1000:
        raise ValueError("LIBRARY_EXPORT_RECORD_LIMIT")
    result = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("LIBRARY_EXPORT_SCHEMA_DENIED")
        if csl:
            if not set(row) <= CSL_FIELDS:
                raise ValueError("LIBRARY_METADATA_ONLY_FIELD_DENIED")
            kind, title = row.get("type", ""), row.get("title", "")
            authors = [
                " ".join(str(a.get(key, "")) for key in ("given", "family", "literal")).strip()
                for a in row.get("author", [])
            ]
            parts = row.get("issued", {}).get("date-parts", [[]])
            year = parts[0][0] if parts and parts[0] else None
            doi, isbn, identifier = row.get("DOI", ""), row.get("ISBN", ""), str(row.get("id", ""))
            venue = row.get("container-title", "")
        else:

            def first(*keys, row=row):
                return next((row[key][0] for key in keys if row.get(key)), "")

            kind, title = first("TY"), first("TI", "T1")
            authors = row.get("AU", row.get("A1", []))
            match = re.match(r"^(\d{4})(?:[/-]|$)", first("PY", "Y1"))
            year = int(match[1]) if match else None
            doi, identifier = first("DO"), first("ID")
            isbn = first("SN") if kind in {"BOOK", "CHAP"} else ""
            venue = first("JO", "JF", "T2")
        if (
            not title
            or not authors
            or any(not isinstance(a, str) or not a.strip() for a in authors)
        ):
            raise ValueError("LIBRARY_EXPORT_TITLE_AND_AUTHORS_REQUIRED")
        result.append(
            MetadataRecord(
                **base,
                provider_id=identifier or f"export-{index + 1}",
                doi=doi,
                isbn=isbn,
                title=title,
                authors=authors,
                year=year,
                source_type=KINDS.get(kind, SourceType.UNKNOWN),
                publication_kind=kind,
                venue=venue,
                export_rights_reviewed=True,
            )
        )
    return result
