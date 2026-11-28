"""Offline citeproc-js bridge bound to reviewed local styles and configured criteria."""

import asyncio
import hashlib
import json
import os
import shutil
from pathlib import Path
from xml.etree.ElementTree import ParseError

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from pydantic import Field

from app.assessments.provenance import content_digest
from app.llm.errors import LLMError
from app.research.citations import extract_citations
from app.schemas.domain import StrictModel
from app.security.classification import classify


class CitationStyleBundle(StrictModel):
    profile_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    criterion_ids: list[str] = Field(min_length=1, max_length=6)
    source: str = Field(min_length=1, max_length=1000)
    reviewed_by: str = Field(min_length=1, max_length=100)
    status: str = Field(pattern=r"^(EXAMPLE|APPROVED)$")
    style_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    locale_sha256: dict[str, str]
    processor_license_reviewed: bool = False


class LocalCitationStyle:
    def __init__(self, directory=None, *, worker=None):
        self.directory = Path(directory) if directory is not None else None
        self.worker = (
            worker or Path(__file__).resolve().parents[3] / "infrastructure/citeproc/worker.cjs"
        )

    def _bundle(self, profile, criteria):
        root = self.directory
        repository = Path(__file__).resolve().parents[3]
        if root.resolve().is_relative_to(repository) or any(
            p.is_symlink() for p in (root, *root.parents)
        ):
            raise ValueError("CSL_STORAGE_BOUNDARY")
        path = root / (profile.id + ".json")
        if path.is_symlink() or path.stat().st_size > 64000:
            raise ValueError("CSL_MANIFEST_DENIED")
        bundle = CitationStyleBundle.model_validate_json(path.read_text("utf-8"))
        if not bundle.processor_license_reviewed:
            raise ValueError("CITEPROC_LICENSE_REVIEW_REQUIRED")
        if bundle.profile_sha256 != content_digest(profile.model_dump()) or not set(
            criteria
        ) <= set(bundle.criterion_ids):
            raise ValueError("CSL_PROFILE_SCOPE_DENIED")
        if profile.status == "APPROVED" and bundle.status != "APPROVED":
            raise ValueError("CSL_OFFICIAL_STYLE_NOT_APPROVED")

        def checked(name, digest, element):
            file = root / name
            if file.is_symlink() or not file.is_file() or file.stat().st_size > 100000:
                raise ValueError("CSL_FILE_DENIED")
            raw = file.read_bytes()
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError("CSL_DIGEST_MISMATCH")
            xml = ElementTree.fromstring(
                raw, forbid_dtd=True, forbid_entities=True, forbid_external=True
            )
            if xml.tag != "{http://purl.org/net/xbiblio/csl}" + element:
                raise ValueError("CSL_XML_ROOT_DENIED")
            return raw.decode("utf-8")

        style = checked(profile.id + ".csl", bundle.style_sha256, "style")
        if not 1 <= len(bundle.locale_sha256) <= 4 or not set(bundle.locale_sha256) <= {
            "de-DE",
            "de-AT",
            "en-US",
            "en-GB",
        }:
            raise ValueError("CSL_LOCALE_DENIED")
        locales = {
            tag: checked("locales-" + tag + ".xml", digest, "locale")
            for tag, digest in bundle.locale_sha256.items()
        }
        return bundle, style, locales

    async def check(self, document, profile):
        criteria = [
            c.id
            for c in profile.criteria
            if c.category == "formal" and "citation_style" in c.local_checks
        ]
        report = {
            "status": "NOT_APPLICABLE",
            "criterion_ids": criteria,
            "checks": [],
            "classification": document.classification,
            "analysis_id": document.analysis_id,
            "document_id": document.document_id,
            "automatic_grade_effect": False,
        }
        if not criteria:
            return report
        if classify(document.classification) != "PUBLIC":
            raise LLMError(403, "CSL_PRIVATE_PROCESSING_NOT_RELEASED")
        if self.directory is None:
            return {**report, "status": "BLOCKED_NO_REVIEWED_CSL_STYLE"}
        try:
            bundle, style, locales = await asyncio.to_thread(self._bundle, profile, criteria)
            extraction = extract_citations(document)
            entries = extraction["entries"]
            if not entries or len(entries) > 100 or len({e.id for e in entries}) != len(entries):
                raise ValueError("CSL_BIBLIOGRAPHY_SCOPE_DENIED")
            if any(not e.title or not e.author or not e.year for e in entries):
                return {**report, "status": "NOT_ASSESSABLE_INCOMPLETE_METADATA"}
            items = [
                {
                    "id": e.id,
                    "type": "book" if e.isbn else "article-journal",
                    "title": e.title,
                    "author": [{"family": e.author}],
                    "issued": {"date-parts": [[e.year]]},
                    **({"DOI": e.doi} if e.doi else {}),
                    **({"ISBN": e.isbn} if e.isbn else {}),
                }
                for e in entries
            ]
            output = await self._render(
                {
                    "items": items,
                    "style": style,
                    "locales": locales,
                    "language": "de-DE" if "de-DE" in locales else "en-US",
                }
            )
            rendered = {key: row["text"] for row in output["entries"] for key in row["ids"]}
            if set(rendered) != {e.id for e in entries}:
                raise ValueError("CSL_RENDERED_IDS_DENIED")
            for entry in entries:
                report["checks"].append(
                    {
                        "reference_id": entry.id,
                        "page": entry.page,
                        "start": entry.start,
                        "end": entry.end,
                        "original": entry.raw,
                        "expected_format": rendered[entry.id],
                        "status": "FORMAT_MATCH_CANDIDATE"
                        if " ".join(entry.raw.split()) == " ".join(rendered[entry.id].split())
                        else "FORMAT_DIFFERENCE_CANDIDATE",
                        "human_review_required": True,
                        "metadata_extraction_expert_verified": False,
                    }
                )
            return {
                **report,
                "status": "COMPLETED_REQUIRES_HUMAN",
                "processor": output["processor"],
                "style_sha256": bundle.style_sha256,
                "style_source": bundle.source,
                "style_status": bundle.status,
            }
        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
            TimeoutError,
            ParseError,
            DefusedXmlException,
        ):
            return {**report, "status": "UNAVAILABLE_OR_UNAPPROVED_REQUIRES_HUMAN"}

    async def _render(self, payload):
        node = shutil.which("node")
        if node is None or not self.worker.is_file():
            raise ValueError("LOCAL_CITEPROC_RUNTIME_UNAVAILABLE")
        library = self.worker.parent / "node_modules/citeproc/citeproc_commonjs.js"
        if library.is_symlink() or not library.is_file() or library.stat().st_size > 2_000_000:
            raise ValueError("LOCAL_CITEPROC_DEPENDENCY_UNAVAILABLE")
        if hashlib.sha256(library.read_bytes()).hexdigest() != (
            "55abba1a8b8b48c14323fd053f9646013b4b7a0c977938064ecf5195a502b9f1"
        ):
            raise ValueError("LOCAL_CITEPROC_DEPENDENCY_CHANGED")
        raw = json.dumps(payload).encode()
        if len(raw) > 1_000_000:
            raise ValueError("LOCAL_CITEPROC_INPUT_LIMIT")
        process = await asyncio.create_subprocess_exec(
            node,
            "--max-old-space-size=128",
            str(self.worker),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env={
                key: value
                for key, value in os.environ.items()
                if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG"}
            },
        )
        try:
            async with asyncio.timeout(10):
                output, _ = await process.communicate(raw)
            if process.returncode or len(output) > 2_000_000:
                raise ValueError("LOCAL_CITEPROC_WORKER_REJECTED")
            value = json.loads(output)
            if value.get("status") != "COMPLETED":
                raise ValueError("LOCAL_CITEPROC_OUTPUT_REJECTED")
            return value
        except BaseException:
            if process.returncode is None:
                process.kill()
            await process.wait()
            raise
