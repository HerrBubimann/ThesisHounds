import hashlib
import json
import shutil
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from app.assessments.profile_registry import ProfileRegistry
from app.assessments.provenance import content_digest
from app.llm.errors import LLMError
from app.services.citation_style import LocalCitationStyle
from app.services.document_store import Document

from tests.fixtures import CONFIG

STYLE = """<style xmlns="http://purl.org/net/xbiblio/csl" version="1.0" class="in-text">
<info><title>SYNTHETIC TEST ONLY</title><id>https://example.invalid/synthetic</id>
<updated>2026-01-01T00:00:00+00:00</updated></info>
<citation><layout><text variable="title"/></layout></citation>
<bibliography><layout><text variable="title"/></layout></bibliography></style>"""
LOCALE = """<locale xmlns="http://purl.org/net/xbiblio/csl" xml:lang="en-US">
<terms><term name="and">and</term></terms></locale>"""


def scope(tmp_path):
    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    formal = next(c for c in profile.criteria if c.category == "formal")
    formal.local_checks = ["citation_style"]
    directory = tmp_path / "styles"
    directory.mkdir()
    (directory / (profile.id + ".csl")).write_bytes(STYLE.encode())
    (directory / "locales-en-US.xml").write_bytes(LOCALE.encode())
    manifest = {
        "profile_sha256": content_digest(profile.model_dump()),
        "criterion_ids": [formal.id],
        "source": "SYNTHETIC TEST ONLY",
        "reviewed_by": "SYNTHETIC_TEST",
        "status": "EXAMPLE",
        "style_sha256": hashlib.sha256(STYLE.encode()).hexdigest(),
        "locale_sha256": {"en-US": hashlib.sha256(LOCALE.encode()).hexdigest()},
        "processor_license_reviewed": True,
    }
    path = directory / (profile.id + ".json")
    path.write_text(json.dumps(manifest), "utf-8")
    doc = Document(
        document_id="synthetic",
        analysis_id="scope",
        classification="PUBLIC",
        pages={1: "Literaturverzeichnis\n[1] Meyer (2020). Synthetic evidence."},
    )
    return LocalCitationStyle(directory), profile, doc, path, manifest


@pytest.mark.anyio
async def test_style_candidates_preserve_original_spans_and_require_human(tmp_path, monkeypatch):
    service, profile, doc, _, _ = scope(tmp_path)
    monkeypatch.setattr(
        service,
        "_render",
        AsyncMock(
            return_value={
                "entries": [{"ids": ["1"], "text": "Synthetic evidence"}],
                "processor": "MOCK",
            }
        ),
    )
    result = await service.check(doc, profile)
    assert result["status"] == "COMPLETED_REQUIRES_HUMAN"
    check = result["checks"][0]
    assert doc.pages[check["page"]][check["start"] : check["end"]] == check["original"]
    assert check["human_review_required"] and not check["metadata_extraction_expert_verified"]
    assert check["status"] == "FORMAT_DIFFERENCE_CANDIDATE"
    assert result["processor"] == "MOCK" and not result["automatic_grade_effect"]


@pytest.mark.anyio
@pytest.mark.parametrize(
    "case",
    ["hash", "license", "profile", "criterion", "xml", "locales", "official", "output", "metadata"],
)
async def test_changed_or_unreviewed_style_is_not_confirmed(tmp_path, monkeypatch, case):
    service, profile, doc, path, manifest = scope(tmp_path)
    render = AsyncMock(return_value={"entries": [], "processor": "MOCK"})
    monkeypatch.setattr(service, "_render", render)
    if case == "hash":
        manifest["style_sha256"] = "0" * 64
    elif case == "license":
        manifest["processor_license_reviewed"] = False
    elif case == "profile":
        manifest["profile_sha256"] = "0" * 64
    elif case == "criterion":
        manifest["criterion_ids"] = ["unknown"]
    elif case == "xml":
        raw = '<!DOCTYPE x [<!ENTITY e "bad">]><style>&e;</style>'
        (service.directory / (profile.id + ".csl")).write_text(raw, "utf-8")
        manifest["style_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    elif case == "locales":
        manifest["locale_sha256"] = {"../../secret": "0" * 64}
    elif case == "official":
        profile.status = "APPROVED"
        manifest["profile_sha256"] = content_digest(profile.model_dump())
    elif case == "metadata":
        doc = doc.model_copy(update={"pages": {1: "Literaturverzeichnis\nUnparsed reference"}})
    path.write_text(json.dumps(manifest), "utf-8")
    result = await service.check(doc, profile)
    assert result["status"] == (
        "NOT_ASSESSABLE_INCOMPLETE_METADATA"
        if case == "metadata"
        else "UNAVAILABLE_OR_UNAPPROVED_REQUIRES_HUMAN"
    )
    if case != "output":
        render.assert_not_awaited()


@pytest.mark.anyio
async def test_private_and_missing_style_gates_precede_subprocess(tmp_path):
    service, profile, doc, _, _ = scope(tmp_path)
    assert (await LocalCitationStyle().check(doc, profile))[
        "status"
    ] == "BLOCKED_NO_REVIEWED_CSL_STYLE"
    doc = doc.model_copy(update={"classification": "RESTRICTED"})
    with pytest.raises(LLMError, match="PRIVATE"):
        await service.check(doc, profile)
    for criterion in profile.criteria:
        criterion.local_checks = []
    assert (await service.check(doc, profile))["status"] == "NOT_APPLICABLE"
    with pytest.raises(ValueError, match="STORAGE"):
        LocalCitationStyle(CONFIG)._bundle(profile, [])


@pytest.mark.anyio
async def test_real_citeproc_renders_synthetic_title_locally():
    service = LocalCitationStyle()
    if not shutil.which("node") or not (service.worker.parent / "node_modules/citeproc").is_dir():
        pytest.skip("Optional local Node/citeproc runtime not installed; npm ci required")
    result = await service._render(
        {
            "style": STYLE,
            "locales": {"en-US": LOCALE},
            "language": "en-US",
            "items": [
                {"id": "synthetic", "type": "article-journal", "title": "Synthetic evidence"}
            ],
        }
    )
    assert result["entries"] == [{"ids": ["synthetic"], "text": "Synthetic evidence"}]
    assert result["processor"] == "citeproc-js/2.4.63"


@pytest.mark.anyio
async def test_missing_runtime_is_explicit(monkeypatch):
    monkeypatch.setattr("app.services.citation_style.shutil.which", lambda _: None)
    with pytest.raises(ValueError, match="RUNTIME"):
        await LocalCitationStyle(worker=Path("missing.cjs"))._render({})


@pytest.fixture
def anyio_backend():
    return "asyncio"
