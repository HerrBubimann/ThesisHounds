import json
import math
from dataclasses import FrozenInstanceError
from unittest.mock import patch

import pytest
from app.assessments.schemas import AIObservation
from app.core.configuration import RuntimeConfig
from app.llm.errors import LLMError
from app.llm.gateway import estimate_input_tokens
from app.services.context_management import LocalContextIndex, embed, pseudonymize_identity_headers
from app.services.document_store import Document

from tests.fixtures import CONFIG


def document(**updates):
    return Document.model_validate(
        {
            "document_id": "synthetic",
            "analysis_id": "scope",
            "classification": "PUBLIC",
            "pages": {
                1: "1 Forschungsfrage\n\nWelche Wirkung besitzt die Methode?",
                2: "2 Methodik\n\nInterviews und Datenerhebung. " * 30,
                3: "3 Fazit\n\nDie Ergebnisse sind nicht übertragbar.",
            },
            **updates,
        }
    )


def builder(pages):
    return [{"role": "user", "content": json.dumps({"untrusted_pages": pages}, ensure_ascii=False)}]


def test_chunks_preserve_exact_original_offsets_and_cross_chapter_context():
    doc = document()
    with patch("socket.getaddrinfo", side_effect=AssertionError("No network")):
        index = LocalContextIndex(doc, chunk_chars=128)
    assert len(index.chunks) > 3
    for chunk in index.chunks:
        assert doc.pages[chunk.page][chunk.start : chunk.end] == chunk.text
        assert chunk.analysis_id == "scope" and chunk.classification == "PUBLIC"
        assert len(chunk.text) <= 128 and chunk.text not in repr(chunk)
    with pytest.raises(FrozenInstanceError):
        index.chunks[0].classification = "PUBLIC"
    rows = index.search(
        "Methode Wirkung Ergebnisse",
        analysis_id="scope",
        document_id="synthetic",
        category="methodology",
    )
    assert {row[0].page for row in rows[:3]} == {1, 2, 3}


@pytest.mark.parametrize("level", [None, "INTERNAL", "CONFIDENTIAL", "RESTRICTED"])
def test_unknown_and_private_embeddings_keep_their_classification(level):
    index = LocalContextIndex(document(classification=level))
    assert all(c.classification == (level or "RESTRICTED") for c in index.chunks)


def test_embedding_is_deterministic_finite_normalized_and_handles_empty_text():
    first = embed("Methodik und Forschungsfrage")
    assert first == embed("Methodik und Forschungsfrage") and len(first) == 128
    assert math.isclose(sum(v * v for v in first), 1)
    assert all(math.isfinite(v) for v in first)
    assert embed("") == (0.0,) * 128


def test_foreign_analysis_document_and_page_scope_never_mix():
    index = LocalContextIndex(document())
    for analysis, identifier in [("foreign", "synthetic"), ("scope", "foreign")]:
        with pytest.raises(LLMError, match="SCOPE"):
            index.search(
                "Methodik", analysis_id=analysis, document_id=identifier, category="methodology"
            )
    rows = index.search(
        "Methodik",
        analysis_id="scope",
        document_id="synthetic",
        category="methodology",
        allowed_pages={3},
        expanded=True,
    )
    assert rows and all(c.page == 3 for c, _, _ in rows)


def test_actual_serialized_prompt_schema_and_output_reservation_fit_model_limit():
    index = LocalContextIndex(document(), chunk_chars=128)
    model = RuntimeConfig(CONFIG).models.get("qwen").model_copy(update={"context_length": 5000})
    messages, trace = index.fit(
        builder, "Methodik", model=model, output_type=AIObservation, max_bytes=200
    )
    assert trace["selected_bytes"] <= 200
    assert estimate_input_tokens(messages, AIObservation.model_json_schema()) + 768 <= 5000
    assert not trace["absence_proven"] and not trace["document_complete"]
    with pytest.raises(LLMError, match="FIXED_PROMPT"):
        index.fit(
            builder,
            "Methodik",
            model=model.model_copy(update={"context_length": 512}),
            output_type=AIObservation,
        )


def test_no_hits_does_not_claim_absence_and_expansion_respects_scope():
    index = LocalContextIndex(document())
    model = RuntimeConfig(CONFIG).models.get("qwen")
    _, trace = index.fit(builder, "", model=model, output_type=AIObservation, category="unknown")
    assert trace["empty"] and not trace["absence_proven"]
    _, expanded = index.fit(
        builder,
        "",
        model=model,
        output_type=AIObservation,
        category="unknown",
        expanded=True,
        allowed_pages={3},
    )
    assert not expanded["empty"] and all(s["page"] == 3 for s in expanded["selection"])


def test_identity_header_masking_preserves_body_information_offsets_and_privacy():
    doc = document(
        pages={
            1: (
                "Studentin: Synthetische Maria\nUnternehmen: Synthetische GmbH\n\n"
                "Die Synthetische GmbH liefert methodisch relevante Daten."
            )
        }
    )
    masked, changes = pseudonymize_identity_headers(doc)
    assert len(masked.pages[1]) == len(doc.pages[1]) and len(changes) == 2
    assert masked.pages[1].endswith("Die Synthetische GmbH liefert methodisch relevante Daten.")
    assert "Maria" not in masked.pages[1] and "Maria" not in str(changes)
    assert doc.pages[1].startswith("Studentin: Synthetische Maria")


@pytest.mark.parametrize(
    "updates,error",
    [({"analysis_id": ""}, "SCOPE"), ({"pages": {1: "x" * 2_000_001}}, "TOO_LARGE")],
)
def test_invalid_or_excessive_context_is_rejected_before_indexing(updates, error):
    with pytest.raises(LLMError, match=error):
        LocalContextIndex(document(**updates))
