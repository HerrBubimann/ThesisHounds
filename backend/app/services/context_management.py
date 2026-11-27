"""Scoped, ephemeral local retrieval; no downloads, model server, persistence or I/O.

Sentence/paragraph boundaries and a small concept lexicon yield transparent candidates.
Feature-hash vectors are local embeddings, not pretrained semantic representations.
No retrieval score or missing hit establishes academic truth or content absence.
"""

import hashlib
import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field

from app.llm.errors import LLMError
from app.llm.gateway import estimate_input_tokens
from app.security.classification import classify
from app.services.document_intelligence import structure_document

VERSION = "local-hybrid-context.v1"
CONCEPTS = (
    ("question", r"forschungsfrag|research.question|zielsetz|objective"),
    ("method", r"method|datenerheb|interview|stichprob|sample|randomis"),
    ("result", r"ergebnis|result|analyse|auswert|finding"),
    ("limits", r"limitation|einschr.nk|grenz|validit|generalisi|.bertrag"),
    ("theory", r"theori|forschungsstand|literatur|reference|quell|beleg"),
    ("conclusion", r"fazit|schlussfolger|conclusion|diskussion"),
)
STOP = frozenset(
    "der die das ein eine und oder im in ist sind von zur zu mit auf des den the a of and".split()
)
ANCHORS = {
    "content": ("Forschungsfrage", "Forschungsstand", "Ergebnisse", "Diskussion", "Fazit"),
    "methodology": ("Forschungsfrage", "Methodik", "Datenerhebung", "Ergebnisse", "Limitationen"),
    "formal": ("Einleitung", "Literaturverzeichnis", "Fazit"),
}


def terms(text):
    return Counter(t for t in re.findall(r"[^\W\d_]{3,}", text.casefold()) if t not in STOP)


def embed(text, *, dimensions=128):
    counts = terms(text)
    counts.update(
        {"concept:" + key: 3 for key, pattern in CONCEPTS if re.search(pattern, text, re.I)}
    )
    vector = [0.0] * dimensions
    for token, count in counts.items():
        hashed = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "big")
        vector[hashed % dimensions] += (1 if hashed & 256 else -1) * (1 + math.log(count))
    norm = math.sqrt(sum(v * v for v in vector)) or 1
    return tuple(v / norm for v in vector)


@dataclass(frozen=True)
class ContextChunk:
    id: str
    analysis_id: str
    document_id: str
    classification: str
    page: int
    start: int
    end: int
    chapter: str | None
    text: str = field(repr=False)
    vector: tuple[float, ...] = field(repr=False)
    reliable: bool = True


def pseudonymize_identity_headers(document):
    """Mask explicitly labelled first-page identity headers, preserving offsets.

    No global entity replacement: company/method details inside the body survive.
    No reversible identity table or plaintext identity is emitted into diagnostics.
    """
    pages, changed = dict(document.pages), []
    if pages:
        first = min(pages)
        pattern = re.compile(
            r"(?im)^(?:Studierender|Student(?:in)?|Name|Unternehmen|Company):[ \t]*([^\n]+)"
        )
        text = pages[first]
        spans = [m.span(1) for m in pattern.finditer(text[:2000])]
        for start, end in reversed(spans):
            text = text[:start] + "X" * (end - start) + text[end:]
        pages[first] = text
        changed = [{"page": first, "start": a, "end": b} for a, b in spans]
    return document.model_copy(update={"pages": pages}), changed


class LocalContextIndex:
    def __init__(self, document, *, chunk_chars=900, pseudonymize=True):
        if not document.analysis_id or not document.document_id:
            raise LLMError(403, "CONTEXT_SCOPE_REQUIRED")
        if not 128 <= chunk_chars <= 4000:
            raise ValueError("CONTEXT_CHUNK_SIZE_DENIED")
        if sum(len(t.encode("utf-8")) for t in document.pages.values()) > 2_000_000:
            raise LLMError(413, "CONTEXT_DOCUMENT_TOO_LARGE")
        self.analysis_id, self.document_id = document.analysis_id, document.document_id
        self.classification = classify(document.classification)
        working, self.masked_spans = (
            pseudonymize_identity_headers(document) if pseudonymize else (document, [])
        )
        self.structure = structure_document(working)
        chunks = []
        for block in self.structure.blocks:
            # Pack complete sentences within existing paragraph/chapter boundaries.
            spans = [m.span() for m in re.finditer(r"[^.!?]+(?:[.!?]+|$)\s*", block.text)]
            start, end = None, None
            for a, b in spans:
                if start is not None and b - start > chunk_chars:
                    self._append(chunks, block, start, end)
                    start = None
                if b - a > chunk_chars:
                    for pos in range(a, b, chunk_chars):
                        self._append(chunks, block, pos, min(b, pos + chunk_chars))
                else:
                    start, end = a if start is None else start, b
            if start is not None:
                self._append(chunks, block, start, end)
        if len(chunks) > 4096:
            raise LLMError(413, "CONTEXT_INDEX_TOO_LARGE")
        self.chunks = tuple(chunks)

    def _append(self, chunks, block, start, end):
        if len(chunks) >= 4096:
            raise LLMError(413, "CONTEXT_INDEX_TOO_LARGE")
        text = block.text[start:end]
        chunks.append(
            ContextChunk(
                id=f"{block.id}-s{start}",
                analysis_id=self.analysis_id,
                document_id=self.document_id,
                classification=self.classification,
                page=block.page,
                start=block.start + start,
                end=block.start + end,
                chapter=block.chapter,
                text=text,
                vector=embed(text),
                reliable=block.reliable,
            )
        )

    def search(
        self, query, *, analysis_id, document_id, category, allowed_pages=None, expanded=False
    ):
        if (analysis_id, document_id) != (self.analysis_id, self.document_id):
            raise LLMError(403, "CONTEXT_SCOPE_DENIED")
        allowed = set(allowed_pages) if allowed_pages is not None else {c.page for c in self.chunks}
        qterms, qvector = terms(query), embed(query)
        ranked = []
        for chunk in self.chunks:
            if chunk.page not in allowed:
                continue
            chunk_terms = terms(chunk.text)
            lexical = sum(min(n, chunk_terms[t]) for t, n in qterms.items()) / max(
                1, sum(qterms.values())
            )
            semantic = max(0.0, sum(a * b for a, b in zip(qvector, chunk.vector, strict=True)))
            anchor = any(
                a.casefold() in (chunk.chapter or "").casefold() for a in ANCHORS.get(category, ())
            )
            score = 0.6 * lexical + 0.4 * semantic
            if score > 0 or anchor or expanded:
                ranked.append(
                    (
                        chunk,
                        score,
                        "CHAPTER_ANCHOR" if anchor else "HYBRID" if score else "EXPANDED_SCAN",
                    )
                )
        # Deterministic reranking: chapter diversity, then hybrid relevance, then source order.
        ranked.sort(key=lambda row: (-row[1], row[0].page, row[0].start))
        selected, chapters = [], set()
        for row in ranked:
            chapter = row[0].chapter or f"page:{row[0].page}"
            if chapter not in chapters:
                selected.append(row)
                chapters.add(chapter)
        selected_ids = {row[0].id for row in selected}
        selected.extend(row for row in ranked if row[0].id not in selected_ids)
        return selected

    def fit(
        self,
        builder,
        query,
        *,
        model,
        output_type,
        max_tokens=768,
        category="content",
        expanded=False,
        allowed_pages=None,
        max_bytes=12000,
        retrieval=True,
    ):
        started = time.monotonic()
        ranked = self.search(
            query,
            analysis_id=self.analysis_id,
            document_id=self.document_id,
            category=category,
            allowed_pages=allowed_pages,
            expanded=expanded,
        )
        if not retrieval:
            ranked = [
                (c, 0.0, "FULL_CONTEXT_ABLATION")
                for c in self.chunks
                if allowed_pages is None or c.page in allowed_pages
            ]
        selected, used = [], 0
        for row in ranked:
            cost = len(row[0].text.encode("utf-8"))
            if used + cost <= max_bytes:
                selected.append(row)
                used += cost
        while True:
            pages = {}
            for chunk, _, _ in sorted(selected, key=lambda row: (row[0].page, row[0].start)):
                pages.setdefault(chunk.page, []).append(chunk.text)
            messages = builder({p: "\n…\n".join(parts) for p, parts in pages.items()})
            bound = estimate_input_tokens(messages, output_type.model_json_schema())
            if bound + max_tokens <= model.context_length:
                break
            if not selected:
                raise LLMError(422, "CONTEXT_FIXED_PROMPT_EXCEEDS_MODEL")
            selected.pop()
        trace = {
            "version": VERSION,
            "retrieval_seconds": time.monotonic() - started,
            "analysis_id": self.analysis_id,
            "document_id": self.document_id,
            "classification": self.classification,
            "estimated_input_tokens": bound,
            "output_reservation": max_tokens,
            "model_context_limit": model.context_length,
            "expanded": expanded,
            "retrieval": retrieval,
            "empty": not selected,
            "document_complete": False,
            "absence_proven": False,
            "selected_bytes": sum(len(c.text.encode("utf-8")) for c, _, _ in selected),
            "selection": [
                {
                    "chunk_id": c.id,
                    "page": c.page,
                    "start": c.start,
                    "end": c.end,
                    "chapter": c.chapter,
                    "score": round(score, 6),
                    "reason": reason,
                    "classification": c.classification,
                    "analysis_id": c.analysis_id,
                    "document_id": c.document_id,
                    "reliable": c.reliable,
                }
                for c, score, reason in selected
            ],
            "masked_identity_spans": len(self.masked_spans),
            "embedding": "LOCAL_FEATURE_HASH_128_WITH_CONCEPT_LEXICON_NOT_PRETRAINED",
            "query_sha256": hashlib.sha256(query.encode()).hexdigest(),
        }
        return messages, trace
