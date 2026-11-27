"""Conservative deterministic checks. Candidate rules and unreliable facts never fail a work."""

import hashlib
import json
import math
import re
from dataclasses import dataclass, field


def document_hash(document):
    return hashlib.sha256(json.dumps(document.pages, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class FormalMeasurements:
    document_sha256: str
    # Operator-reviewed segmentation/measurements, never populated by an LLM or HTTP request.
    reviewed_by: str = ""
    content_pages: float | None = None
    page_count_basis: str | None = None
    values: dict = field(default_factory=dict)


HEADINGS = {
    "contents": r"inhaltsverzeichnis|contents",
    "bibliography": r"literaturverzeichnis|quellenverzeichnis|references",
    "declaration": r"ehrenwörtliche (?:eigenständigkeits)?erklärung|eigenständigkeitserklärung",
    "figures": r"abbildungsverzeichnis|list of figures",
    "tables": r"tabellenverzeichnis|list of tables",
}


def abstract_words(document, language):
    if language not in {"de", "en"}:
        return None, None
    title = "Abstract (Deutsch)" if language == "de" else "Abstract (English)"
    # Deliberately narrow: unknown headings/boundaries remain manual.
    matches = []
    for page, text in document.pages.items():
        match = re.search(
            r"(?m)^" + re.escape(title) + r"\s*\n(?P<body>[\s\S]*?)"
            r"(?=\n(?:#{1,3} |Abstract \((?:Deutsch|English)\))|\Z)",
            text,
        )
        if match:
            if match.end() == len(text) and page != max(document.pages):
                return None, None  # A page break cannot establish the abstract's end.
            matches.append((page, match))
    if len(matches) != 1 or not document.complete:
        return None, None
    page, match = matches[0]
    return len(re.findall(r"\b[\w]+(?:[-’'][\w]+)*\b", match["body"])), {
        "page": page,
        "start": match.start("body"),
        "end": match.end("body"),
        "method": "explicit_abstract_boundary.v1",
    }


def check_formal(document, resolved: dict, measurements: FormalMeasurements | None = None) -> dict:
    rows = []
    trusted = bool(
        measurements
        and measurements.reviewed_by
        and measurements.document_sha256 == document_hash(document)
    )
    for rule in resolved["rules"]:
        row = {
            "criterion_id": rule["id"],
            "description": rule["description"],
            "source_id": rule["source_id"],
            "source_location": rule["source_location"],
            "status": "MANUAL_REVIEW_REQUIRED",
            "reason": "RULE_NOT_APPROVED",
            "value": None,
            "evidence": None,
            "automatic_grade_effect": False,
        }
        if not rule["active"] or resolved["status"] != "ACTIVE":
            rows.append(row)
            continue
        row["reason"] = "RELIABLE_MEASUREMENT_UNAVAILABLE"
        method, params = rule["method"], rule["parameters"]
        value = None
        if rule["scope"] == "ORGANIZATIONAL":
            row["reason"] = "CANNOT_BE_ESTABLISHED_FROM_DOCUMENT"
        elif method == "signature":
            row["reason"] = "SIGNATURE_AUTHENTICITY_NOT_VERIFIED"
        elif method == "content_pages" and trusted:
            if measurements.page_count_basis == params.get("basis"):
                value = measurements.content_pages
                if type(value) not in {int, float} or not math.isfinite(value) or value < 0:
                    value = None
                row["evidence"] = {
                    "method": "reviewed_content_segmentation",
                    "document_sha256": measurements.document_sha256,
                }
        elif method == "abstract_words":
            value, row["evidence"] = abstract_words(document, params.get("language"))
        elif method == "presence":
            key = params.get("component")
            pattern = HEADINGS.get(key)
            if pattern:
                hits = [
                    (page, m)
                    for page, text in document.pages.items()
                    for m in re.finditer(r"(?im)^(?:#{1,3}\s*)?(?:" + pattern + r")\s*$", text)
                ]
                if hits:
                    page, match = hits[0]
                    value = True
                    row["evidence"] = {
                        "page": page,
                        "start": match.start(),
                        "end": match.end(),
                        "method": "heading_presence_only",
                    }
                elif document.complete:
                    row["reason"] = "HEADING_NOT_FOUND_NOT_PROOF_OF_ABSENCE"
        elif trusted and method in {
            "font_size",
            "font_family",
            "margins",
            "page_numbering",
            "section_numbering",
            "bibliographic_completeness",
            "citation_consistency",
        }:
            value = measurements.values.get(rule["id"])
        if value is not None:
            row["value"] = value
            if "min" in params and "max" in params and isinstance(value, (int, float)):
                ok = params["min"] <= value <= params["max"]
            elif "expected" in params:
                ok = value == params["expected"]
            elif method == "presence":
                ok = value is True
            else:
                rows.append(row)
                continue
            row.update(status="PASS" if ok else "FAIL", reason="DETERMINISTIC_RULE_COMPARISON")
        rows.append(row)
    return {
        "method": "formal-compliance.v1",
        "classification": document.classification,
        "checks": rows,
        "total_pdf_pages_used_as_content_count": False,
        "automatic_grade_effect": False,
    }
