import hashlib
import json
import os
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.security.classification import Classification, classify
from app.security.sperrvermerk_detector import detect_sperrvermerk


class Document(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    document_id: str
    analysis_id: str = ""
    classification: Classification = Classification.RESTRICTED
    pages: dict[int, str]
    complete: bool = False
    digest: str = ""

    @field_validator("classification", mode="before")
    @classmethod
    def safe_classification(cls, value):
        return classify(value)

    @property
    def sperrvermerk(self):
        return detect_sperrvermerk(self.pages)


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
        if root.is_symlink():
            raise ValueError("STORE_SYMLINK_DENIED")
        self.root = root

    def path(self, run_id: str) -> Path:
        return self.root / f"{UUID(run_id)}.json"

    def create_demo(self, run_id: str) -> Document:
        encoded = json.dumps(SYNTHETIC_PAGES, ensure_ascii=False, sort_keys=True)
        document = Document(
            document_id="synthetic-demo",
            analysis_id=run_id,
            classification="PUBLIC",
            pages=dict(SYNTHETIC_PAGES),
            complete=True,
            digest=hashlib.sha256(encoded.encode()).hexdigest(),
        )
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(self.path(run_id), flags, 0o600), "w", encoding="utf-8") as stream:
            stream.write(document.model_dump_json())
        return document

    def remove(self, run_id: str) -> None:
        self.path(run_id).unlink(missing_ok=True)


class DocumentInput(BaseModel):
    """Fixed document.v1 schema, not an executable agent-supplied JSON schema."""

    document: Document
    criteria: list[str] = Field(max_length=6)
