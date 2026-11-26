import hashlib
import json
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field


class Document(BaseModel):
    document_id: str
    classification: str = "CONFIDENTIAL"
    pages: dict[int, str]
    complete: bool = False
    digest: str = ""


SYNTHETIC_PAGES = {
    1: (
        "Forschungsfrage: Verbessert ein lokales Assistenzsystem die Nachvollziehbarkeit "
        "von Gutachten? Die Arbeit vergleicht manuelle und KI-gestützte Bewertungen "
        "anhand identischer Kriterien."
    ),
    2: (
        "Methodik: Es wurden sechs synthetische Arbeiten mit einem vorab definierten "
        "Kriterienraster bewertet. Es gab keine zufällige Zuteilung. "
        "Die geringe Stichprobe begrenzt die Übertragbarkeit der Ergebnisse."
    ),
    3: (
        "Ergebnisse: Belegstellen wurden mit Seitenangaben dokumentiert. "
        "Die Studie berichtet keine statistische Signifikanz. Alle Modellbefunde "
        "werden durch eine menschliche Gutachterin überprüft."
    ),
}


class DocumentStore:
    """Only server-generated synthetic documents are ingestible in this release."""

    def __init__(self, root: Path):
        self.root = root

    def path(self, run_id: str) -> Path:
        return self.root / f"{UUID(run_id)}.json"

    def create_demo(self, run_id: str) -> Document:
        encoded = json.dumps(SYNTHETIC_PAGES, ensure_ascii=False, sort_keys=True)
        document = Document(
            document_id="synthetic-demo",
            classification="SYNTHETIC",
            pages=SYNTHETIC_PAGES,
            complete=True,
            digest=hashlib.sha256(encoded.encode()).hexdigest(),
        )
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path(run_id).write_text(document.model_dump_json(), encoding="utf-8")
        return document

    def remove(self, run_id: str) -> None:
        self.path(run_id).unlink(missing_ok=True)


class DocumentInput(BaseModel):
    """Fixed document.v1 schema, not an executable agent-supplied JSON schema."""

    document: Document
    criteria: list[str] = Field(max_length=6)
