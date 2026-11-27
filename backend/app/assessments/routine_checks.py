"""Conservative text-only inventory, not citation existence or PDF layout validation."""

from collections import Counter

from app.research.doi import DOI, normalize_doi
from app.security.classification import classify
from app.services.document_store import Document


def inventory(document: Document) -> dict:
    scope = {
        "classification": classify(document.classification),
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
    }
    occurrences = [
        {**scope, "doi_candidate": normalize_doi(match.group()), "page": page}
        for page, text in document.pages.items()
        for match in DOI.finditer(text)
    ]
    counts = Counter(item["doi_candidate"] for item in occurrences)
    return {
        **scope,
        "method": "deterministic_text_inventory.v1",
        "doi_candidates": occurrences,
        "repeated_doi_mentions": {doi: count for doi, count in counts.items() if count > 1},
        "verification": "UNVERIFIED",
        "limitations": "Repeated mentions are not duplicate bibliography entries. "
        "No source existence, bibliographic completeness, PDF layout "
        "or semantic citation correctness is established.",
    }
