"""Bounded streaming of reviewed PUBLIC DBLP XML subsets; no DTD or URL fetching."""

import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path
from xml.etree.ElementTree import ParseError

from app.research.doi import normalize_doi
from app.research.provider_registry import MetadataRecord, SourceType
from app.schemas.domain import StrictModel
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from pydantic import Field

KINDS = {
    "article": SourceType.PAPER,
    "inproceedings": SourceType.CONFERENCE,
    "proceedings": SourceType.CONFERENCE,
    "book": SourceType.BOOK,
    "incollection": SourceType.BOOK,
    "phdthesis": SourceType.UNKNOWN,
    "mastersthesis": SourceType.UNKNOWN,
    "www": SourceType.WEB,
}


class DBLPReleaseSelection(StrictModel):
    """Operator-reviewed lineage for an already bounded public XML subset."""

    release_doi: str = Field(pattern=r"^10\.4230/dblp\.xml\.\d{4}-\d{2}-\d{2}$")
    subset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    keys: list[str] = Field(min_length=1, max_length=1000)
    reviewed_by: str = Field(min_length=1, max_length=100)
    public_provenance_reviewed: bool = False

    @classmethod
    def load(cls, path):
        path = Path(path)
        if any(p.is_symlink() for p in (path, *path.parents)) or path.stat().st_size > 100_000:
            raise ValueError("DBLP_SELECTION_FILE_DENIED")
        value = cls.model_validate_json(path.read_text("utf-8"))
        release_date = date.fromisoformat(value.release_doi.rsplit(".", 1)[1])
        if release_date > datetime.now(UTC).date() or not value.public_provenance_reviewed:
            raise ValueError("DBLP_RELEASE_PROVENANCE_REQUIRED")
        if len(set(value.keys)) != len(value.keys) or any(
            not key or len(key) > 300 or any(ord(c) < 32 for c in key) for key in value.keys
        ):
            raise ValueError("DBLP_SELECTION_KEYS_DENIED")
        return value

    @property
    def digest(self):
        raw = json.dumps(self.model_dump(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(raw).hexdigest()


def iter_selected_dblp(stream, selection, **kwargs):
    """Filter reviewed public keys; a missing key prevents activation of a partial set."""
    if kwargs.get("snapshot_sha256") != selection.subset_sha256:
        raise ValueError("DBLP_RELEASE_SUBSET_DIGEST_MISMATCH")
    wanted, found = set(selection.keys), set()
    for record in iter_dblp(stream, **kwargs):
        if record.provider_id not in wanted:
            continue
        if record.provider_id in found:
            raise ValueError("DBLP_SELECTION_DUPLICATE_RECORD")
        found.add(record.provider_id)
        record.source_release_doi = selection.release_doi
        record.selection_sha256 = selection.digest
        yield record
    if found != wanted:
        raise ValueError("DBLP_SELECTION_KEYS_NOT_FOUND")


class BoundedReader:
    def __init__(self, stream, limit):
        self.stream, self.limit, self.read_bytes = stream, limit, 0

    def read(self, size=-1):
        data = self.stream.read(min(65536, size) if size >= 0 else 65536)
        self.read_bytes += len(data)
        if self.read_bytes > self.limit:
            raise ValueError("DBLP_XML_BYTE_LIMIT")
        return data


def iter_dblp(
    stream,
    *,
    retrieved_at,
    provenance,
    snapshot_sha256,
    provider="dblp",
    max_bytes=64_000_000,
    max_records=100_000,
):
    if provider != "dblp" or not 1 <= max_bytes <= 64_000_000 or not 1 <= max_records <= 100_000:
        raise ValueError("DBLP_IMPORT_LIMITS")
    count, depth, nodes, root = 0, 0, 0, None
    try:
        events = ElementTree.iterparse(
            BoundedReader(stream, max_bytes),
            events=("start", "end"),
            forbid_entities=True,
            forbid_external=True,
        )
        for event, element in events:
            if event == "start":
                depth, nodes = depth + 1, nodes + 1
                if depth > 16 or nodes > 10000:
                    raise ValueError("DBLP_XML_COMPLEXITY_LIMIT")
                if root is None:
                    root = element
                    if element.tag != "dblp":
                        raise ValueError("DBLP_ROOT_REQUIRED")
                continue
            if depth == 2:
                if element.tag not in KINDS:
                    raise ValueError("DBLP_RECORD_TYPE_DENIED")
                count += 1
                if count > max_records:
                    raise ValueError("DBLP_RECORD_LIMIT")

                def text(tag, element=element):
                    child = element.find(tag)
                    return "".join(child.itertext()).strip() if child is not None else ""

                if sum(len(t) for t in element.itertext()) > 64000:
                    raise ValueError("DBLP_RECORD_SIZE_LIMIT")
                doi = next(
                    (normalize_doi(e.text) for e in element.findall("ee") if normalize_doi(e.text)),
                    "",
                )
                key = element.get("key", "")
                if not key or not text("title"):
                    raise ValueError("DBLP_RECORD_ID_AND_TITLE_REQUIRED")
                yield MetadataRecord(
                    doi=doi,
                    title=text("title"),
                    authors=["".join(a.itertext()).strip() for a in element.findall("author")],
                    year=int(text("year")) if text("year") else None,
                    venue=text("booktitle") or text("journal"),
                    isbn=text("isbn"),
                    provider_id=key,
                    publication_kind=element.tag,
                    source_type=KINDS[element.tag],
                    provider="dblp",
                    license_id="CC0-1.0",
                    retrieved_at=retrieved_at,
                    snapshot_sha256=snapshot_sha256,
                    provenance=provenance,
                )
                root.clear()
                nodes = 1
            depth -= 1
        if root is None or not count:
            raise ValueError("DBLP_EMPTY_SUBSET")
    except (ParseError, DefusedXmlException):
        raise ValueError("DBLP_UNSAFE_OR_INVALID_XML") from None
