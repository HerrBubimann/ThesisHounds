import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal
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
    source_sha256: str | None = None
    extraction_version: str | None = None
    extraction_warnings: list[str] = Field(default_factory=list)

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


class PilotApproval(BaseModel):
    """Trusted operator input, not accepted by any HTTP endpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["SYNTHETIC", "REVIEWED_PUBLIC"]
    reviewed_by: str = Field(min_length=1, max_length=100)
    reviewed_at: datetime
    provenance: str = Field(min_length=1, max_length=1000)


def checked_pilot_root(root: Path) -> Path:
    source_root = Path(__file__).resolve().parents[2]
    repository = (
        source_root.parent if (source_root.parent / "pyproject.toml").is_file() else source_root
    )
    if root.resolve().is_relative_to(repository) or any(
        p.is_symlink() for p in (root, *root.parents)
    ):
        raise ValueError("PILOT_STORAGE_BOUNDARY")
    return root


def register_pilot_pdf(root: Path, data: bytes, approval: PilotApproval) -> str:
    """Offline operator registration; a browser cannot assert public provenance."""
    root = checked_pilot_root(root)
    approval = PilotApproval.model_validate(approval.model_dump())
    if not data.startswith(b"%PDF-") or not 0 < len(data) <= 8_000_000:
        raise ValueError("PILOT_PDF_TYPE_OR_SIZE_DENIED")
    worker = Path(__file__).with_name("pdf_worker.py")
    # Drop ambient credentials, proxy variables and tracing settings from the parser.
    env = {k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP") if k in os.environ}
    try:
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(worker)],
            input=data,
            capture_output=True,
            timeout=20,
            check=False,
            env=env,
        )
        if result.returncode or len(result.stdout) > 4_000_000:
            raise ValueError("PILOT_PARSER_REJECTED")
        extracted = json.loads(result.stdout)
        pages = {int(k): v for k, v in extracted["pages"].items()}
        if detect_sperrvermerk(pages).detected:
            raise ValueError("PILOT_NOTICE_REQUIRES_AUTHORIZED_REVIEW")
    except (OSError, subprocess.SubprocessError, KeyError, TypeError, json.JSONDecodeError):
        raise ValueError("PILOT_PARSER_UNAVAILABLE_OR_REJECTED") from None
    sha = hashlib.sha256(data).hexdigest()
    document = Document(
        document_id="pilot-" + sha,
        pages=pages,
        complete=True,
        classification="PUBLIC",
        digest=hashlib.sha256(
            json.dumps(pages, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest(),
        source_sha256=sha,
        extraction_version=extracted["parser"],
        extraction_warnings=extracted["warnings"],
    )
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if len(list(root.glob("*.json"))) >= 20:
        raise ValueError("PILOT_CATALOG_LIMIT")
    wrapper = {
        "document": document.model_dump(mode="json"),
        "approval": approval.model_dump(mode="json"),
    }
    # Atomic exclusive creation, no user-controlled path/name and no overwriting approvals.
    for suffix, content in (
        (".pdf", data),
        (".json", json.dumps(wrapper, ensure_ascii=False).encode()),
    ):
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(root / (sha + suffix), flags, 0o600), "wb") as stream:
            stream.write(content)
    return document.document_id


def load_pilot_document(root: Path, document_id: str, analysis_id: str) -> Document:
    import re

    root = checked_pilot_root(root)
    if not re.fullmatch(r"pilot-[0-9a-f]{64}", document_id):
        raise ValueError("PILOT_DOCUMENT_ID_DENIED")
    sha = document_id.removeprefix("pilot-")
    path, pdf = root / (sha + ".json"), root / (sha + ".pdf")
    if any(p.is_symlink() or not p.is_file() for p in (path, pdf)):
        raise ValueError("PILOT_DOCUMENT_NOT_REGISTERED")
    if path.stat().st_size > 4_000_000 or pdf.stat().st_size > 8_000_000:
        raise ValueError("PILOT_DOCUMENT_SIZE_DENIED")
    wrapper = json.loads(path.read_bytes())
    PilotApproval.model_validate(wrapper["approval"])
    document = Document.model_validate(wrapper["document"])
    text_digest = hashlib.sha256(
        json.dumps(document.pages, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    if not (
        document.document_id == document_id
        and document.source_sha256 == sha
        and hashlib.sha256(pdf.read_bytes()).hexdigest() == sha
        and document.digest == text_digest
        and document.classification == "PUBLIC"
        and document.extraction_version == "bounded-pypdf.v1"
        and not document.sperrvermerk.detected
    ):
        raise ValueError("PILOT_DOCUMENT_INTEGRITY_DENIED")
    return document.model_copy(update={"analysis_id": analysis_id}, deep=True)


def pilot_documents(root: Path | None) -> list[dict]:
    if root is None:
        return []
    root = checked_pilot_root(root)
    paths = sorted(root.glob("*.json"))
    if len(paths) > 20:
        raise ValueError("PILOT_CATALOG_LIMIT")
    return [
        {
            "document_id": (doc := load_pilot_document(root, "pilot-" + p.stem, "")).document_id,
            "source_sha256": doc.source_sha256,
            "pages": len(doc.pages),
        }
        for p in paths
    ]


def main():
    """Offline curator CLI. This is not an upload or approval endpoint."""
    import argparse

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    args = parser.parse_args()
    try:
        if (
            args.source.is_symlink()
            or args.approval.is_symlink()
            or args.source.stat().st_size > 8_000_000
            or args.approval.stat().st_size > 65536
        ):
            raise ValueError("PILOT_INPUT_DENIED")
        approval = PilotApproval.model_validate_json(args.approval.read_bytes())
        key = register_pilot_pdf(args.store, args.source.read_bytes(), approval)
        print(json.dumps({"status": "PUBLIC_PILOT_REGISTERED", "document_id": key}))
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        print('{"status":"PUBLIC_PILOT_REJECTED"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
