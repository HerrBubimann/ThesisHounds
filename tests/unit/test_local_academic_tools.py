import asyncio
import math

import httpx
import pytest
from app.assessments.profile_registry import Criterion
from app.assessments.provenance import content_digest
from app.evaluation.retrieval import RetrievalReference, evaluate_retrieval, ranking_metrics
from app.llm.errors import LLMError
from app.services.context_management import LocalContextIndex
from app.services.document_store import Document
from app.services.language_tool import LOCAL_CHECK_URL, LocalLanguageTool, python_offset


def criterion():
    return Criterion(
        id="language",
        category="formal",
        description="SYNTHETIC language criterion",
        expected_evidence="Original passages",
        instructions="Suggestions only",
        source="SYNTHETIC_TEST_ONLY",
        local_checks=["language"],
    )


def document(text="😀 Das ist ein Feler."):
    return Document(
        document_id="synthetic", analysis_id="scope", classification="PUBLIC", pages={1: text}
    )


def test_local_language_suggestions_preserve_utf16_original_offsets_and_never_change_document():
    calls = []

    def handler(request):
        calls.append(request)
        assert str(request.url) == LOCAL_CHECK_URL and request.method == "POST"
        return httpx.Response(
            200,
            json={
                "matches": [
                    {
                        "offset": 15,
                        "length": 5,
                        "message": "Synthetic spelling suggestion",
                        "rule": {"id": "TEST"},
                    }
                ]
            },
        )

    doc = document()
    original = dict(doc.pages)
    result = asyncio.run(
        LocalLanguageTool(enabled=True, transport=httpx.MockTransport(handler)).check(
            doc, criterion()
        )
    )
    assert result["status"] == "COMPLETED_BOUNDED_TEXT_CHECK" and len(calls) == 1
    proposal = result["suggestions"][0]
    assert doc.pages[1][proposal["start"] : proposal["end"]] == proposal["quote"] == "Feler"
    assert doc.pages == original and not result["original_changed"]


@pytest.mark.parametrize(
    "text",
    [
        '"Quoted Feler"',
        "```code Feler```",
        "$x = Feler$",
        "Literaturverzeichnis\nFeler (2020). Book.",
    ],
)
def test_generic_language_rules_do_not_criticize_quotes_code_formulas_or_bibliography(text):
    transport = httpx.MockTransport(
        lambda r: httpx.Response(
            200,
            json={
                "matches": [{"offset": 0, "length": 1, "message": "Synthetic", "rule": {"id": "T"}}]
            },
        )
    )
    result = asyncio.run(
        LocalLanguageTool(enabled=True, transport=transport).check(document(text), criterion())
    )
    assert not result["suggestions"]


def test_language_engine_requires_explicit_criterion_and_preserves_private_processing_denial():
    calls = []
    tool = LocalLanguageTool(enabled=True, transport=httpx.MockTransport(lambda r: calls.append(r)))
    c = criterion()
    c.local_checks = []
    assert (
        asyncio.run(tool.check(document(), c))["status"] == "NOT_APPLICABLE_TO_CONFIGURED_CRITERION"
    )
    c.local_checks = ["language"]
    private = document().model_copy(update={"classification": "RESTRICTED"})
    with pytest.raises(LLMError, match="PRIVATE"):
        asyncio.run(tool.check(private, c))
    assert not calls
    assert python_offset("😀x", 2) == 1
    with pytest.raises(ValueError):
        python_offset("😀x", 1)


def test_language_service_failure_is_visible_without_cloud_fallback():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(302, headers={"Location": "https://api.languagetool.org/v2/check"})

    result = asyncio.run(
        LocalLanguageTool(enabled=True, transport=httpx.MockTransport(handler)).check(
            document(), criterion()
        )
    )
    assert result["status"] == "UNAVAILABLE_REQUIRES_HUMAN" and len(calls) == 1


def test_retrieval_metrics_have_hand_calculated_values_and_no_invented_labels():
    metrics = ranking_metrics(["irrelevant", "relevant"], {"relevant": 2, "missed": 1}, 2)
    assert metrics["precision_at_k"] == metrics["recall_at_k"] == metrics["mrr_at_k"] == 0.5
    assert math.isclose(metrics["ndcg_at_k"], (3 / math.log2(3)) / (3 + 1 / math.log2(3)))
    report = evaluate_retrieval(document("Methodik: Die Auswahl ist begrenzt."), ["Methodik"])
    assert all(row["metrics"] is None for row in report["results"])
    assert all(row["status"].startswith("BLOCKED") for row in report["results"][2:])


def test_fts_uses_same_document_passages_and_checks_reference_scope():
    doc = document("Methodik: Zwölf Fälle.\n\nFazit: Begrenzte Übertragbarkeit.")
    index = LocalContextIndex(doc)
    found = index.search_fulltext("Methodik", analysis_id="scope", document_id="synthetic")
    assert found and all(doc.pages[c.page][c.start : c.end] == c.text for c, _, _ in found)
    reference = RetrievalReference(
        document_sha256=content_digest(doc.pages),
        reviewed_by="SYNTHETIC_TEST",
        query="Methodik",
        relevance={found[0][0].id: 1},
    )
    report = evaluate_retrieval(doc, ["Methodik"], references=[reference], k=1)
    assert report["results"][1]["metrics"]["recall_at_k"] == 1
    reference.document_sha256 = "0" * 64
    with pytest.raises(ValueError, match="SCOPE"):
        evaluate_retrieval(doc, ["Methodik"], references=[reference])
    with pytest.raises(LLMError, match="SCOPE"):
        index.search_fulltext("Methodik", analysis_id="foreign", document_id="synthetic")
