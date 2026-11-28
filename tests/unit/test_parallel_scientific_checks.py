import asyncio
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.agents.academic_review import AcademicReviewServices
from app.assessments.profile_registry import ProfileRegistry
from app.assessments.provenance import content_digest
from app.evaluation.retrieval import RetrievalReference, review_retrieval
from app.llm.errors import LLMError
from app.services.context_management import LocalContextIndex
from app.services.document_store import Document
from app.services.local_embeddings import EmbeddingArtifact, LocalEmbeddingRunner

from tests.fixtures import CONFIG


def document(classification="PUBLIC"):
    return Document(
        document_id="synthetic",
        analysis_id="scope",
        classification=classification,
        pages={
            1: "1 Methodik\n\nDie Erhebung umfasst zwölf Interviews.",
            2: "2 Fazit\n\nDie Ergebnisse sind begrenzt übertragbar.",
        },
    )


def profile():
    return ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")


def artifact(tmp_path):
    root = tmp_path / "weights"
    root.mkdir()
    # Deliberately fake weight bytes; inference is mocked, never claimed as a model run.
    raw = b"SYNTHETIC_NOT_MODEL_WEIGHTS"
    (root / "model.safetensors").write_bytes(raw)
    return EmbeddingArtifact(
        id="multilingual-e5-small",
        repository="intfloat/multilingual-e5-small",
        revision="1" * 40,
        root=root,
        dimensions=384,
        license_id="MIT",
        files={"model.safetensors": hashlib.sha256(raw).hexdigest()},
        approved_by="SYNTHETIC_TEST",
        license_reviewed=True,
        security_reviewed=True,
        runtime_reviewed=True,
    )


def test_fts_index_reused_across_threads_and_closed_explicitly():
    with LocalContextIndex(document()) as index:

        def search(_):
            return index.search_fulltext("Methodik", analysis_id="scope", document_id="synthetic")

        with ThreadPoolExecutor(max_workers=4) as pool:
            rows = list(pool.map(search, range(12)))
        assert rows[0] and all(r == rows[0] for r in rows)
        assert index.fts_build_count == 1
        ranking = rows[0]
        fused = index.fuse_rankings([ranking, ranking])
        assert fused[0][1] == 2 / 61
        foreign = LocalContextIndex(document())
        with pytest.raises(LLMError, match="SCOPE"):
            index.fuse_rankings([[(foreign.chunks[0], 1, "foreign")]])
        with pytest.raises(ValueError, match="DUPLICATE"):
            index.fuse_rankings([[ranking[0], ranking[0]]])
        with pytest.raises(ValueError, match="LIMIT"):
            index.fuse_rankings([], limit=0)
    with pytest.raises(LLMError, match="CLOSED"):
        search(0)


@pytest.mark.anyio
async def test_real_overlap_optional_failures_and_stable_order(monkeypatch):
    service = AcademicReviewServices(None)
    loop = asyncio.get_running_loop()
    academic_entered = asyncio.Event()
    review_entered = asyncio.Event()

    async def review():
        review_entered.set()
        await asyncio.wait_for(academic_entered.wait(), 2)
        return []

    def academic(*_):
        assert review_entered.is_set()
        loop.call_soon_threadsafe(academic_entered.set)
        return {"citations": {"references": []}}

    monkeypatch.setattr(service, "check", academic)
    monkeypatch.setattr(service, "check_language", AsyncMock(side_effect=ValueError("SECRET")))
    monkeypatch.setattr(
        "app.agents.academic_review.review_retrieval", AsyncMock(return_value={"models": {}})
    )
    bundle = await service.run_checks(
        document(), profile(), {}, review, slots=asyncio.Semaphore(2), runtime_limit=3
    )
    assert list(bundle["results"]) == [
        "scientific_review",
        "academic",
        "language",
        "retrieval",
        "citation_style",
        "numerical",
    ]
    summary = service.summarize(bundle, [])
    assert summary["execution_complete"] is False
    assert summary["limitations"] == [{"check": "language", "status": "FAILED_REQUIRES_HUMAN"}]
    assert "SECRET" not in json.dumps(bundle)
    assert not summary["automatic_grade_effect"] and not summary["consensus_establishes_truth"]
    assert summary["checks"]["citation_style"]["result_status"] == "NOT_APPLICABLE"


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["cancel", "required_failure", "required_timeout"])
async def test_failure_timeout_and_cancellation_drain_async_siblings(monkeypatch, mode):
    service = AcademicReviewServices(None)
    entered, stopped = asyncio.Event(), asyncio.Event()

    async def waiting(*_):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    async def review():
        await entered.wait()
        if mode == "required_failure":
            raise ValueError("SECRET")
        await asyncio.Event().wait()

    monkeypatch.setattr(service, "check", lambda *_: {"citations": {"references": []}})
    monkeypatch.setattr(service, "check_language", waiting)
    task = asyncio.create_task(
        service.run_checks(
            document(),
            profile(),
            {},
            review,
            slots=asyncio.Semaphore(2),
            runtime_limit=0.05 if mode == "required_timeout" else 3,
        )
    )
    await asyncio.wait_for(entered.wait(), 2)
    if mode == "cancel":
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    else:
        with pytest.raises(ExceptionGroup):
            await task
    assert stopped.is_set()
    assert not any(t.get_name().startswith("assessment:") for t in asyncio.all_tasks())


@pytest.mark.anyio
async def test_parallel_private_gate_precedes_all_operations():
    service = AcademicReviewServices(None)
    review = AsyncMock()
    with pytest.raises(LLMError, match="PRIVATE"):
        await service.run_checks(
            document("RESTRICTED"),
            profile(),
            {},
            review,
            slots=asyncio.Semaphore(2),
            runtime_limit=1,
        )
    review.assert_not_awaited()


@pytest.mark.anyio
async def test_retrieval_reports_missing_models_and_scoped_original_offsets():
    doc = document()
    report = await review_retrieval(doc, profile(), LocalEmbeddingRunner())
    assert report["fts_index_builds"] == 1
    assert all(row["status"] == "BLOCKED_NO_APPROVED_ARTIFACT" for row in report["models"].values())
    assert report["semantic_advantage"] == "NOT_ESTABLISHED"
    for criterion in report["results"]:
        assert criterion["metrics"] is None
        for result in criterion["combined_locations"]:
            assert doc.pages[result["page"]][result["start"] : result["end"]]


@pytest.mark.anyio
async def test_approved_embedding_adapter_uses_shared_model_slot_and_fusion(monkeypatch, tmp_path):
    approved = artifact(tmp_path)
    resource = asyncio.Semaphore(1)
    runner = LocalEmbeddingRunner([approved], resource_slots=resource)
    calls = []

    async def encode(art, root, queries, chunks):
        assert resource.locked() and runner.slots.locked()
        calls.append(art.id)
        return [[1.0] + [0.0] * 383 for _ in range(len(queries) + len(chunks))]

    monkeypatch.setattr(runner, "_encode", encode)
    report = await review_retrieval(document(), profile(), runner)
    assert calls == [approved.id]
    assert report["models"][approved.id]["status"] == "COMPLETED"
    assert all(approved.id in row["methods"] for row in report["results"])
    assert "rankings" not in report["models"][approved.id]
    assert not resource.locked()


@pytest.mark.anyio
@pytest.mark.parametrize("bad", [[], [[float("nan")] * 384], [[0] * 384], [[True] * 384], None])
async def test_bad_embedding_output_is_visible_not_fused(monkeypatch, tmp_path, bad):
    approved = artifact(tmp_path)
    runner = LocalEmbeddingRunner([approved])
    with LocalContextIndex(document()) as index:
        count = 1 + len(index.chunks)
        output = bad * count if bad else bad
        monkeypatch.setattr(runner, "_encode", AsyncMock(return_value=output))
        result = await runner.rankings(index, ["Methodik"])
    assert result[approved.id]["status"] == "UNAVAILABLE_OR_UNAPPROVED_REQUIRES_HUMAN"


@pytest.mark.anyio
async def test_embeddings_private_and_query_limits_fail_before_worker():
    runner = LocalEmbeddingRunner()
    with LocalContextIndex(document("RESTRICTED")) as index:
        with pytest.raises(LLMError, match="PRIVATE"):
            await runner.rankings(index, ["Methodik"])
    with LocalContextIndex(document()) as index:
        with pytest.raises(ValueError, match="QUERY"):
            await runner.rankings(index, [])


@pytest.mark.parametrize("case", ["approval", "hash", "inventory", "type", "identity"])
def test_artifact_manifest_does_not_manufacture_approval_or_integrity(tmp_path, case):
    value = artifact(tmp_path)
    assert value.verify() == value.root
    if case == "approval":
        value.runtime_reviewed = False
    elif case == "hash":
        value.files["model.safetensors"] = "0" * 64
    elif case == "inventory":
        (value.root / "extra.json").write_text("{}")
    elif case == "type":
        (value.root / "weights.bin").write_bytes(b"unsafe")
        value.files["weights.bin"] = hashlib.sha256(b"unsafe").hexdigest()
    else:
        value.license_id = "Apache-2.0"
    with pytest.raises(ValueError):
        value.verify()


def test_manifest_loading_and_storage_boundaries(tmp_path):
    value = artifact(tmp_path)
    directory = tmp_path / "manifests"
    directory.mkdir()
    (directory / "e5.json").write_text(value.model_dump_json(), "utf-8")
    assert LocalEmbeddingRunner.load(directory).artifacts[value.id].verify() == value.root
    with pytest.raises(ValueError, match="STORAGE"):
        LocalEmbeddingRunner.load(CONFIG)
    with pytest.raises(ValueError, match="CONFIGURATION"):
        LocalEmbeddingRunner([value, value])
    assert not LocalEmbeddingRunner.load(None).artifacts
    for n in range(3):
        (directory / f"{n}.json").write_text("{}")
    with pytest.raises(ValueError, match="LIMIT"):
        LocalEmbeddingRunner.load(directory)


def test_summary_preserves_conflict_and_source_statuses():
    finding = SimpleNamespace(
        finding_id="f",
        criterion_id="methodology",
        conflict=True,
        judgment="NOT_ASSESSABLE",
        supplemental=[],
    )
    bundle = {
        "execution": {"academic": {"status": "COMPLETED"}},
        "results": {
            "citation_style": {"status": "BLOCKED_NO_REVIEWED_CSL_STYLE"},
            "retrieval": {"models": {}},
            "language": [],
            "academic": {
                "citations": {"references": [{"statuses": ["NOT_FOUND", "MANUAL_REVIEW_REQUIRED"]}]}
            },
        },
        "document_sha256": "0" * 64,
        "profile_sha256": "1" * 64,
        "analysis_id": "a",
        "document_id": "d",
    }
    report = AcademicReviewServices.summarize(bundle, [finding])
    assert report["conflicting_finding_ids"] == ["f"]
    assert report["source_status_counts"]["NOT_FOUND"] == 1
    assert report["not_assessable_criterion_ids"] == ["methodology"]
    assert not report["configured_checks_complete"]


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_shared_limit_bounds_two_simultaneous_assessments(monkeypatch):
    service = AcademicReviewServices(None)
    active, peak = 0, 0

    class Slots:
        semaphore = asyncio.Semaphore(2)

        async def __aenter__(self):
            nonlocal active, peak
            await self.semaphore.acquire()
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.002)

        async def __aexit__(self, *_):
            nonlocal active
            active -= 1
            self.semaphore.release()

    monkeypatch.setattr(service, "check", lambda *_: {"citations": {"references": []}})
    monkeypatch.setattr(service, "check_language", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        "app.agents.academic_review.review_retrieval", AsyncMock(return_value={"models": {}})
    )
    slots = Slots()
    await asyncio.gather(
        *(
            service.run_checks(
                document(), profile(), {}, AsyncMock(return_value=[]), slots=slots, runtime_limit=1
            )
            for _ in range(2)
        )
    )
    assert peak == 2 and active == 0


@pytest.mark.anyio
async def test_comparison_metrics_use_only_scoped_explicit_reference_labels():
    doc, rubric = document(), profile()
    criterion = rubric.criteria[0]
    with LocalContextIndex(doc) as index:
        reference = RetrievalReference(
            document_sha256=content_digest(doc.pages),
            reviewed_by="SYNTHETIC_TEST",
            query=criterion.description + " " + criterion.expected_evidence,
            relevance={c.id: 1 for c in index.chunks},
        )
    report = await review_retrieval(doc, rubric, LocalEmbeddingRunner(), references=[reference])
    assert report["results"][0]["human_relevance_labels"]
    assert report["results"][0]["metrics"]["combined"]["recall_at_k"] == 0.5
    assert all(row["metrics"] is None for row in report["results"][1:])
    reference.document_sha256 = "0" * 64
    with pytest.raises(ValueError, match="SCOPE"):
        await review_retrieval(doc, rubric, LocalEmbeddingRunner(), references=[reference])


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["success", "cancel", "timeout", "bad_json", "exit_error"])
async def test_embedding_worker_protocol_and_process_cleanup(monkeypatch, tmp_path, mode):
    approved = artifact(tmp_path)
    captured = {}

    class Process:
        returncode = None
        killed = False
        waited = False

        async def communicate(self, raw):
            captured["input"] = json.loads(raw)
            if mode in {"cancel", "timeout"}:
                await asyncio.Event().wait()
            self.returncode = 1 if mode == "exit_error" else 0
            return (b"invalid" if mode == "bad_json" else b'{"vectors": [[1]]}'), None

        def kill(self):
            self.killed = True
            self.returncode = -1

        async def wait(self):
            self.waited = True

    process = Process()

    async def create(*args, **kwargs):
        captured.update(kwargs)
        assert args[1] == "-I"
        return process

    monkeypatch.setattr("app.services.local_embeddings.asyncio.create_subprocess_exec", create)
    monkeypatch.setenv("SYNTHETIC_SECRET_TOKEN", "MUST_NOT_REACH_WORKER")
    runner = LocalEmbeddingRunner(timeout=0.02)
    with LocalContextIndex(document()) as index:
        task = asyncio.create_task(
            runner._encode(approved, approved.root, ["Methodik"], index.chunks)
        )
        if mode == "cancel":
            await asyncio.sleep(0)
            task.cancel()
        if mode == "success":
            assert await task == [[1]]
        else:
            with pytest.raises(
                asyncio.CancelledError
                if mode == "cancel"
                else TimeoutError
                if mode == "timeout"
                else ValueError
            ):
                await task
            assert process.waited
            if mode in {"cancel", "timeout"}:
                assert process.killed
    assert "SYNTHETIC_SECRET_TOKEN" not in captured["env"]
    assert captured["env"]["HF_HUB_OFFLINE"] == "1"
    assert captured["input"]["queries"] == ["Methodik"]
