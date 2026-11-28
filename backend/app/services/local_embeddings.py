"""Approved local embedding artifacts and a bounded offline worker; never a hosted API."""

import asyncio
import hashlib
import json
import math
import os
import sys
import time
from contextlib import AsyncExitStack
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import Field

from app.llm.errors import LLMError
from app.schemas.domain import StrictModel
from app.security.classification import classify


class EmbeddingArtifact(StrictModel):
    id: Literal["qwen3-embedding-06b", "multilingual-e5-small", "bge-m3"]
    repository: Literal[
        "Qwen/Qwen3-Embedding-0.6B", "intfloat/multilingual-e5-small", "BAAI/bge-m3"
    ]
    revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    root: Path
    license_id: Literal["Apache-2.0", "MIT"]
    dimensions: int = Field(ge=128, le=1024)
    files: dict[str, str]
    approved_by: str = Field(default="", max_length=100)
    license_reviewed: bool = False
    security_reviewed: bool = False
    runtime_reviewed: bool = False

    def verify(self):
        expected = {
            "qwen3-embedding-06b": ("Qwen/Qwen3-Embedding-0.6B", "Apache-2.0", 1024),
            "multilingual-e5-small": ("intfloat/multilingual-e5-small", "MIT", 384),
            "bge-m3": ("BAAI/bge-m3", "MIT", 1024),
        }
        if (self.repository, self.license_id, self.dimensions) != expected[self.id] or not (
            self.approved_by
            and self.license_reviewed
            and self.security_reviewed
            and self.runtime_reviewed
        ):
            raise ValueError("EMBEDDING_ARTIFACT_APPROVAL_REQUIRED")
        root = self.root.resolve()
        repository = Path(__file__).resolve().parents[3]
        if root.is_relative_to(repository) or any(
            p.is_symlink() for p in (self.root, *self.root.parents)
        ):
            raise ValueError("EMBEDDING_ARTIFACT_STORAGE_DENIED")
        if not root.is_dir() or not 1 <= len(self.files) <= 200:
            raise ValueError("EMBEDDING_ARTIFACT_FILES_REQUIRED")
        actual, total = set(), 0
        for path in root.rglob("*"):
            if path.is_symlink():
                raise ValueError("EMBEDDING_ARTIFACT_SYMLINK_DENIED")
            if path.is_file():
                actual.add(path.relative_to(root).as_posix())
                total += path.stat().st_size
        if (
            actual != set(self.files)
            or total > 4_000_000_000
            or not any(n.endswith(".safetensors") for n in actual)
        ):
            raise ValueError("EMBEDDING_ARTIFACT_INVENTORY_DENIED")
        for name, expected_hash in self.files.items():
            parts = PurePosixPath(name)
            if (
                parts.is_absolute()
                or ".." in parts.parts
                or "\\" in name
                or ":" in name
                or (
                    parts.suffix not in {".json", ".safetensors", ".txt", ".model", ".tiktoken"}
                    and parts.name
                    not in {"LICENSE", "LICENSE.md", "NOTICE", "NOTICE.md", "README.md"}
                )
            ):
                raise ValueError("EMBEDDING_ARTIFACT_FORMAT_DENIED")
            digest = hashlib.sha256()
            with (root / name).open("rb") as stream:
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
            if digest.hexdigest() != expected_hash:
                raise ValueError("EMBEDDING_ARTIFACT_DIGEST_MISMATCH")
        return root


class LocalEmbeddingRunner:
    def __init__(self, artifacts=(), *, timeout=120, resource_slots=None):
        self.artifacts = {a.id: a for a in artifacts}
        if len(self.artifacts) != len(artifacts) or not 0 < timeout <= 600:
            raise ValueError("EMBEDDING_CONFIGURATION_DENIED")
        self.timeout = timeout
        # A single local encoder at a time; parallel review must not multiply model RAM.
        self.slots = asyncio.Semaphore(1)
        self.resource_slots = resource_slots

    @classmethod
    def load(cls, directory, *, resource_slots=None):
        if directory is None:
            return cls(resource_slots=resource_slots)
        directory = Path(directory)
        repository = Path(__file__).resolve().parents[3]
        if directory.resolve().is_relative_to(repository) or any(
            p.is_symlink() for p in (directory, *directory.parents)
        ):
            raise ValueError("EMBEDDING_MANIFEST_STORAGE_DENIED")
        files = sorted(directory.glob("*.json"))
        if len(files) > 3:
            raise ValueError("EMBEDDING_MANIFEST_LIMIT")
        artifacts = []
        for path in files:
            if path.is_symlink() or path.stat().st_size > 100_000:
                raise ValueError("EMBEDDING_MANIFEST_DENIED")
            artifacts.append(EmbeddingArtifact.model_validate_json(path.read_text("utf-8")))
        return cls(artifacts, resource_slots=resource_slots)

    async def rankings(self, index, queries):
        if classify(index.classification) != "PUBLIC":
            raise LLMError(403, "EMBEDDING_PRIVATE_PROCESSING_NOT_RELEASED")
        if not 1 <= len(queries) <= 20 or any(not q or len(q) > 600 for q in queries):
            raise ValueError("EMBEDDING_QUERY_LIMIT")
        chunks = index.chunks[:256]
        results = {}
        for key in ("qwen3-embedding-06b", "multilingual-e5-small", "bge-m3"):
            artifact = self.artifacts.get(key)
            if artifact is None:
                results[key] = {"status": "BLOCKED_NO_APPROVED_ARTIFACT"}
                continue
            try:
                started = time.monotonic()
                async with AsyncExitStack() as stack:
                    await stack.enter_async_context(self.slots)
                    if self.resource_slots is not None:
                        await stack.enter_async_context(self.resource_slots)
                    root = await asyncio.to_thread(artifact.verify)
                    vectors = await self._encode(artifact, root, queries, chunks)
                if len(vectors) != len(queries) + len(chunks):
                    raise ValueError("EMBEDDING_VECTOR_COUNT_DENIED")
                normalized = []
                for vector in vectors:
                    if (
                        not isinstance(vector, list)
                        or len(vector) != artifact.dimensions
                        or any(type(v) not in {float, int} or not math.isfinite(v) for v in vector)
                    ):
                        raise ValueError("EMBEDDING_VECTOR_SCHEMA_DENIED")
                    norm = math.sqrt(sum(v * v for v in vector))
                    if not math.isfinite(norm) or norm == 0:
                        raise ValueError("EMBEDDING_VECTOR_NORM_DENIED")
                    normalized.append([v / norm for v in vector])
                values = []
                for query_vector in normalized[: len(queries)]:
                    ranked = [
                        (chunk, sum(a * b for a, b in zip(query_vector, vector, strict=True)), key)
                        for chunk, vector in zip(chunks, normalized[len(queries) :], strict=True)
                    ]
                    ranked.sort(key=lambda row: (-row[1], row[0].page, row[0].start))
                    values.append(ranked)
                results[key] = {
                    "status": "COMPLETED",
                    "rankings": values,
                    "revision": artifact.revision,
                    "artifact_hashes": artifact.files,
                    "selected_chunks": len(chunks),
                    "total_chunks": len(index.chunks),
                    "complete_document_search": len(chunks) == len(index.chunks),
                    "mocked": False,
                    "elapsed_seconds_including_queue_and_integrity_check": time.monotonic()
                    - started,
                    "token_window": 512,
                    "passage_truncation_possible": True,
                    "native_peak_memory_bytes": None,
                }
            except (ValueError, OSError, TimeoutError, KeyError, TypeError):
                results[key] = {"status": "UNAVAILABLE_OR_UNAPPROVED_REQUIRES_HUMAN"}
        return results

    async def _encode(self, artifact, root, queries, chunks):
        worker = Path(__file__).with_name("embedding_worker.py")
        payload = json.dumps(
            {
                "id": artifact.id,
                "root": str(root),
                "queries": queries,
                "passages": [c.text for c in chunks],
            }
        ).encode()
        if len(payload) > 2_000_000:
            raise ValueError("EMBEDDING_INPUT_LIMIT")
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-I",
            str(worker),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            env={
                **{
                    key: value
                    for key, value in os.environ.items()
                    if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG"}
                },
                "HF_HUB_OFFLINE": "1",
                "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
                "TRANSFORMERS_OFFLINE": "1",
                "HF_HUB_DISABLE_TELEMETRY": "1",
                "DO_NOT_TRACK": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "TOKENIZERS_PARALLELISM": "false",
            },
        )
        try:
            async with asyncio.timeout(self.timeout):
                output, _ = await process.communicate(payload)
            if process.returncode or len(output) > 16_000_000:
                raise ValueError("LOCAL_EMBEDDING_WORKER_UNAVAILABLE")
            return json.loads(output)["vectors"]
        except BaseException:
            if process.returncode is None:
                process.kill()
            await process.wait()
            raise
