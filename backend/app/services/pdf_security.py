"""Bounded pypdf preflight and layout indicators. No URL fetching or active execution."""

import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader, __version__
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, StreamObject

from app.security.injection_detection import detect_injection

ACTIVE = {
    "/JavaScript",
    "/JS",
    "/OpenAction",
    "/AA",
    "/Launch",
    "/EmbeddedFiles",
    "/EF",
    "/RichMedia",
    "/XFA",
}
ACTIONS = {"/JavaScript", "/Launch", "/SubmitForm", "/ImportData", "/GoToR", "/GoToE"}


def inspect_pdf(data: bytes) -> tuple[dict, dict]:
    if (
        len(data) > 8_000_000
        or not re.match(rb"%PDF-(?:1\.[0-7]|2\.0)(?:\s|$)", data[:16])
        or b"%%EOF" not in data[-1024:]
    ):
        raise ValueError("PDF_SIGNATURE_OR_TRAILER_DENIED")
    reader = PdfReader(io.BytesIO(data), strict=True)
    if reader.is_encrypted:
        raise ValueError("PDF_ENCRYPTED")
    if not 1 <= len(reader.pages) <= 200:
        raise ValueError("PDF_PAGE_LIMIT")
    indicators, visited, stack = [], set(), [reader.trailer]
    nodes = 0
    while stack:
        obj = stack.pop()
        nodes += 1
        if nodes > 20000:
            raise ValueError("PDF_OBJECT_LIMIT")
        if isinstance(obj, IndirectObject):
            key = (obj.idnum, obj.generation)
            if key in visited:
                continue
            visited.add(key)
            obj = obj.get_object()
        if isinstance(obj, DictionaryObject):
            if ACTIVE & set(obj) or str(obj.get("/S", "")) in ACTIONS:
                raise ValueError("PDF_ACTIVE_OR_EMBEDDED_CONTENT_DENIED")
            if str(obj.get("/Type", "")) == "/EmbeddedFile":
                raise ValueError("PDF_EMBEDDED_FILE_DENIED")
            if isinstance(obj, StreamObject) and len(obj._data) > 4_000_000:
                raise ValueError("PDF_EMBEDDED_OBJECT_SIZE_DENIED")
            for key, value in obj.items():
                if key == "/URI":
                    indicators.append(
                        {
                            "kind": "EXTERNAL_LINK",
                            "section": "PDF_LINK",
                            "quote": str(value)[:600],
                            "reason": "Passive link; never fetched or followed.",
                        }
                    )
                if (
                    key in {"/Contents", "/T", "/Subject", "/Author", "/Title", "/Keywords"}
                    and isinstance(value, str)
                    and (detect_injection(value) or len(value) > 1000)
                ):
                    indicators.append(
                        {
                            "kind": "SUSPICIOUS_METADATA",
                            "section": "METADATA_OR_ANNOTATION",
                            "quote": value[:600],
                            "reason": "Untrusted metadata/annotation; not evidence of an attack.",
                        }
                    )
            stack.extend(obj.values())
        elif isinstance(obj, (ArrayObject, list)):
            stack.extend(obj)
        if len(indicators) > 200:
            raise ValueError("PDF_INDICATOR_LIMIT")
    pages = {}
    for number, page in enumerate(reader.pages, 1):
        state = {"fill": (0.0, 0.0, 0.0), "render": 0, "alpha": 1.0, "clip": False}
        saved, operations, runs = [], 0, []

        def operand(op, args, cm, tm, state=state, saved=saved, page=page):
            nonlocal operations
            operations += 1
            if operations > 200000:
                raise ValueError("PDF_OPERATION_LIMIT")
            if op == b"q":
                saved.append(dict(state))
            elif op == b"Q" and saved:
                state.update(saved.pop())
            elif op == b"rg":
                state["fill"] = tuple(float(v) for v in args)
            elif op == b"g":
                state["fill"] = (float(args[0]),) * 3
            elif op == b"Tr":
                state["render"] = int(args[0])
            elif op in {b"W", b"W*"}:
                state["clip"] = True
            elif op == b"gs":
                resources = page.get("/Resources", {})
                if isinstance(resources, IndirectObject):
                    resources = resources.get_object()
                states = resources.get("/ExtGState", {})
                if isinstance(states, IndirectObject):
                    states = states.get_object()
                resource = states.get(args[0])
                if resource:
                    state["alpha"] = float(resource.get_object().get("/ca", 1))

        def text_run(text, cm, tm, font, size, state=state, page=page, runs=runs, number=number):
            if not text.strip():
                return
            x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
            y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            box = page.cropbox
            reasons = []
            if size <= 1.5:
                reasons.append("UNUSUALLY_SMALL_TEXT")
            if state["render"] in {3, 7}:
                reasons.append("INVISIBLE_TEXT_RENDER_MODE")
            if state["alpha"] < 0.05:
                reasons.append("TRANSPARENT_TEXT")
            if all(v > 0.98 for v in state["fill"]):
                reasons.append("WHITE_TEXT_WHITE_BACKGROUND_NOT_VERIFIED")
            if not box.left <= x <= box.right or not box.bottom <= y <= box.top:
                reasons.append("OUTSIDE_CROPBOX")
            if state["clip"]:
                reasons.append("CLIPPING_PATH_PRESENT")
            if any(abs(x - a) < 0.1 and abs(y - b) < 0.1 and text.strip() != t for a, b, t in runs):
                reasons.append("POSSIBLE_OVERLAPPING_TEXT")
            runs.append((x, y, text.strip()))
            if reasons:
                indicators.append(
                    {
                        "kind": "HIDDEN_TEXT",
                        "page": number,
                        "section": "PDF_LAYOUT",
                        "quote": text.strip()[:600],
                        "reason": ",".join(reasons),
                    }
                )

        pages[number] = (
            page.extract_text(visitor_operand_before=operand, visitor_text=text_run) or ""
        )
        if sum(len(t.encode()) for t in pages.values()) > 2_000_000 or len(indicators) > 200:
            raise ValueError("PDF_EXTRACTION_LIMIT")
    return pages, {
        "version": "secure-pdf-preflight.v1",
        "parser_version": __version__,
        "indicators": indicators,
        "ocr": "NOT_EXECUTED",
        "rendering": "NOT_EXECUTED",
    }


def extract_pdf_subprocess(data: bytes, *, allow_empty_candidate=False) -> dict:
    if not data.startswith(b"%PDF-") or not 0 < len(data) <= 8_000_000:
        raise ValueError("PDF_TYPE_OR_SIZE_DENIED")
    env = {k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP") if k in os.environ}
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(Path(__file__).with_name("pdf_worker.py")),
                *(["--allow-empty-candidate"] if allow_empty_candidate else []),
            ],
            input=data,
            capture_output=True,
            timeout=20,
            check=False,
            env=env,
        )
        if result.returncode or len(result.stdout) > 4_000_000:
            if (
                result.returncode
                and len(result.stdout) < 1000
                and json.loads(result.stdout).get("error")
                in {"PDF_ACTIVE_CONTENT", "PDF_ENCRYPTED"}
            ):
                raise ValueError(json.loads(result.stdout)["error"])
            raise ValueError("PDF_SECURITY_OR_PARSER_REJECTED")
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        raise ValueError("PDF_SECURITY_OR_PARSER_UNAVAILABLE") from None
