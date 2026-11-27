"""Bounded local candidate import. No macros, external resources, execution or promotion."""

import hashlib
import io
import json
import os
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from xml.etree.ElementTree import ParseError

import yaml
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from pypdf.errors import PyPdfError

from app.knowledge.schemas import SourceDocument
from app.security.classification import Classification, classify
from app.services.pdf_security import extract_pdf_subprocess

MAX_BYTES = 8_000_000
MAX_EXPANDED = 24_000_000


class ImportRejected(ValueError):
    pass


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.hidden = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def safe_yaml(text):
    if any(
        isinstance(t, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken)) for t in yaml.scan(text)
    ):
        raise ImportRejected("YAML_ALIASES_DENIED")
    return yaml.safe_load(text)


def extract_candidate(data: bytes, suffix: str) -> dict:
    try:
        return _extract_candidate(data, suffix)
    except ImportRejected:
        raise
    except (
        ValueError,
        KeyError,
        IndexError,
        RecursionError,
        zipfile.BadZipFile,
        yaml.YAMLError,
        DefusedXmlException,
        ParseError,
        PyPdfError,
    ):
        # Parser exceptions may include imported text. Never pass them to logs or CLI output.
        raise ImportRejected("LOCAL_EXTRACTION_REJECTED") from None


def _extract_candidate(data: bytes, suffix: str) -> dict:
    if not data or len(data) > MAX_BYTES:
        raise ImportRejected("IMPORT_SIZE_DENIED")
    suffix = suffix.casefold()
    warnings = ["CANDIDATE_ONLY", "HUMAN_VALIDATION_REQUIRED"]
    if suffix == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ImportRejected("FILE_TYPE_MISMATCH")
        try:
            extracted = extract_pdf_subprocess(data, allow_empty_candidate=True)
        except ValueError as exc:
            if str(exc) in {"PDF_ACTIVE_CONTENT", "PDF_ENCRYPTED"}:
                raise ImportRejected(str(exc)) from None
            raise
        pages = {int(k): v for k, v in extracted["pages"].items()}
        warnings.extend(extracted["warnings"])
        text = "\n".join(pages.values())
        warnings.append("TEXT_ONLY_NO_OCR_OR_LAYOUT_GUARANTEE")
    elif suffix in {".docx", ".dotx", ".xlsx"}:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 1000 or sum(e.file_size for e in entries) > MAX_EXPANDED:
                raise ImportRejected("ARCHIVE_EXPANSION_DENIED")
            for entry in entries:
                name = entry.filename
                if (
                    ".." in PurePosixPath(name).parts
                    or name.startswith(("/", "\\"))
                    or "\\" in name
                    or ":" in name
                    or entry.flag_bits & 1
                    or (entry.external_attr >> 16) & 0o170000 == 0o120000
                    or "vbaproject" in name.casefold()
                    or "/embeddings/" in name.casefold()
                ):
                    raise ImportRejected("ARCHIVE_CONTENT_DENIED")
                if name.endswith(".rels"):
                    relations = ElementTree.fromstring(archive.read(entry))
                    if any(r.attrib.get("TargetMode") == "External" for r in relations):
                        warnings.append("EXTERNAL_RELATIONSHIPS_IGNORED")
            if "[Content_Types].xml" not in archive.namelist():
                raise ImportRejected("FILE_TYPE_MISMATCH")
            parts = []
            if suffix in {".docx", ".dotx"}:
                tree = ElementTree.fromstring(archive.read("word/document.xml"))
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                for paragraph in tree.findall(".//w:p", ns):
                    parts.append("".join(t.text or "" for t in paragraph.findall(".//w:t", ns)))
                warnings.append("TABLE_AND_PAGE_LAYOUT_UNVERIFIED")
            else:
                ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                shared = []
                if "xl/sharedStrings.xml" in archive.namelist():
                    tree = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
                    shared = ["".join(n.itertext()) for n in tree.findall("s:si", ns)]
                sheets = [
                    n
                    for n in archive.namelist()
                    if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")
                ]
                if not sheets:
                    raise ImportRejected("FILE_TYPE_MISMATCH")
                for name in sorted(sheets):
                    sheet = ElementTree.fromstring(archive.read(name))
                    for cell in sheet.findall(".//s:c", ns):
                        if cell.find("s:f", ns) is not None:
                            warnings.append("FORMULA_NOT_EVALUATED")
                            continue
                        value = cell.findtext("s:v", "", ns)
                        if cell.attrib.get("t") == "s":
                            value = shared[int(value)]
                        elif cell.attrib.get("t") == "inlineStr":
                            value = "".join(cell.find("s:is", ns).itertext())
                        parts.append(value)
            text, pages = "\n".join(parts), {}
    elif suffix in {".md", ".html", ".yaml", ".yml", ".json"}:
        text = data.decode("utf-8-sig")
        if suffix in {".yaml", ".yml"}:
            safe_yaml(text)
        elif suffix == ".json":
            json.loads(text)
        elif suffix == ".html":
            parser = TextHTML()
            parser.feed(text)
            text = "\n".join(parser.parts)
            warnings.append("NO_EXTERNAL_RESOURCES_FETCHED")
        pages = {}
    else:
        raise ImportRejected("UNSUPPORTED_FORMAT")
    if len(text.encode("utf-8")) > MAX_EXPANDED:
        raise ImportRejected("EXTRACTED_TEXT_LIMIT")
    return {
        "sha256": hashlib.sha256(data).hexdigest(),
        "text": text,
        "pages": pages,
        "warnings": sorted(set(warnings)),
        "classification": "RESTRICTED",
        "release": "CANDIDATE",
    }


@dataclass(frozen=True)
class ImportAuthority:
    actor_id: str
    curator: bool = False
    public_provenance_checked: bool = False


class KnowledgeStore:
    """Operator library outside the repository, with no HTTP import or promotion endpoint."""

    def __init__(self, root: Path):
        root = root.absolute()
        repository = Path(__file__).resolve().parents[3]
        if root.resolve().is_relative_to(repository) or any(
            p.is_symlink() for p in (root, *root.parents)
        ):
            raise ImportRejected("KNOWLEDGE_STORAGE_BOUNDARY")
        self.root = root

    def import_public(self, data, suffix, metadata: SourceDocument, authority: ImportAuthority):
        # Production private imports require identity/storage/parser approval; not implemented.
        if not (
            authority.actor_id
            and authority.curator
            and authority.public_provenance_checked
            and classify(metadata.classification) == Classification.PUBLIC
        ):
            raise ImportRejected("KNOWLEDGE_IMPORT_NOT_AUTHORIZED")
        result = extract_candidate(data, suffix)
        if metadata.sha256 and metadata.sha256 != result["sha256"]:
            raise ImportRejected("SOURCE_DIGEST_MISMATCH")
        metadata = metadata.model_copy(
            update={"sha256": result["sha256"], "release": "CANDIDATE", "binding": "CANDIDATE"}
        )
        result.update(classification="PUBLIC", source=metadata.model_dump(mode="json"))
        root = self.root / "public"
        if root.is_symlink():
            raise ImportRejected("KNOWLEDGE_STORAGE_BOUNDARY")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not root.resolve().is_relative_to(self.root.resolve()):
            raise ImportRejected("KNOWLEDGE_STORAGE_BOUNDARY")
        name = result["sha256"] + ".json"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(root / name, flags, 0o600), "w", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False)
        return {k: v for k, v in result.items() if k not in {"text", "pages"}}
