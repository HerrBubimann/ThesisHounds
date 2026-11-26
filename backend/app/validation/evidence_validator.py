from app.schemas.domain import Finding
from app.services.document_store import Document


class EvidenceValidator:
    def validate(self, finding: Finding, document: Document) -> None:
        if finding.claim_type == "ABSENCE":
            # A quoted passage cannot prove that a whole document lacks something.
            scope = set(finding.required_context)
            if not document.complete or scope != set(document.pages):
                finding.evidence_status = "CONTEXT_REQUIRED"
                finding.evidence_detail = (
                    "Fehlender Inhalt erfordert den vollständigen Dokumentkontext."
                )
            else:
                finding.evidence_status = "NOT_CHECKED"
                finding.evidence_detail = (
                    "Vollständiger Kontext vorhanden; semantische Abwesenheit "
                    "ist nicht deterministisch bewiesen."
                )
            return
        page = document.pages.get(finding.page or 0)
        if not finding.quote.strip() or page is None or finding.quote not in page:
            finding.evidence_status = "REJECTED"
            finding.evidence_detail = (
                "Textbeleg fehlt oder ist auf der angegebenen Seite nicht enthalten."
            )
        else:
            finding.evidence_status = "VALIDATED"
            finding.evidence_detail = (
                "Wörtlicher Beleg auf der angegebenen Seite gefunden; "
                "fachliche Richtigkeit bleibt zu prüfen."
            )
