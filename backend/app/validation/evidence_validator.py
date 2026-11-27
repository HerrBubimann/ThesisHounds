from dataclasses import dataclass

from app.schemas.domain import Finding
from app.services.document_store import Document


@dataclass(frozen=True)
class EvidenceCheck:
    status: str
    detail: str
    start: int | None = None
    end: int | None = None


def check_evidence(
    document: Document, page: int | None, quote: str, *, claim_type="TEXT", required_context=()
) -> EvidenceCheck:
    if claim_type == "ABSENCE":
        if not document.complete or set(required_context) != set(document.pages):
            return EvidenceCheck("CONTEXT_REQUIRED", "Vollständiger Dokumentkontext erforderlich.")
        return EvidenceCheck(
            "ABSENCE_UNPROVEN", "Kontext vollständig; semantische Abwesenheit unbewiesen."
        )
    text = document.pages.get(page or 0, "")
    if not quote.strip() or quote not in text:
        return EvidenceCheck("REJECTED", "Kein wörtlicher Beleg auf dieser Seite.")
    start = text.index(quote)
    return EvidenceCheck(
        "QUOTE_MATCHED",
        "Textspanne gefunden; fachliche Begründung ungeprüft.",
        start,
        start + len(quote),
    )


class EvidenceValidator:
    def validate(self, finding: Finding, document: Document) -> None:
        result = check_evidence(
            document,
            finding.page,
            finding.quote,
            claim_type=finding.claim_type,
            required_context=finding.required_context,
        )
        finding.evidence_status = {
            "QUOTE_MATCHED": "VALIDATED",
            "ABSENCE_UNPROVEN": "NOT_CHECKED",
        }.get(result.status, result.status)
        finding.evidence_detail = result.detail
