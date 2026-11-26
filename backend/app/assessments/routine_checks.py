"""Conservative text-only inventory, not citation existence or PDF layout validation."""

import re
from collections import Counter

from app.services.document_store import Document

DOI = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


def inventory(document: Document) -> dict:
    occurrences = [
        {"doi_candidate": match.group().rstrip(".,;").lower(), "page": page}
        for page, text in document.pages.items()
        for match in DOI.finditer(text)
    ]
    counts = Counter(item["doi_candidate"] for item in occurrences)
    return {
        "method": "deterministic_text_inventory.v1",
        "doi_candidates": occurrences,
        "repeated_doi_mentions": {doi: count for doi, count in counts.items() if count > 1},
        "verification": "UNVERIFIED",
        "limitations": "Repeated mentions are not duplicate bibliography entries. "
        "No source existence, bibliographic completeness, PDF layout "
        "or semantic citation correctness is established.",
    }
