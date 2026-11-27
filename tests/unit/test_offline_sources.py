from datetime import UTC, date, datetime

import pytest
from app.research.citation_validator import ResearchEvidence
from app.research.local_verification import CitationAssertion, LocalSource, verify_local_sources
from app.services.document_store import Document


def source():
    return LocalSource(
        evidence=ResearchEvidence(
            title="Synthetic public source",
            doi="10.1234/example",
            provider="fixture",
            retrieved_at=datetime(2026, 11, 26, tzinfo=UTC),
            criterion_id="literature",
            verification="METADATA",
            verification_note="Synthetic operator snapshot",
            published_at=date(1980, 1, 1),
            version="v2",
            correction_status="RETRACTED",
        ),
        snapshot_provenance="synthetic-test-only",
        fulltext="An exact synthetic quotation.",
    )


def test_offline_doi_version_retraction_and_quote_checks_keep_semantic_limits():
    document = Document(
        document_id="synthetic",
        pages={
            1: "An exact synthetic quotation. doi:10.1234/example",
            2: "Literaturverzeichnis\n\n10.1234/EXAMPLE Synthetic source",
        },
        complete=True,
    )
    result = verify_local_sources(
        document,
        [source()],
        as_of=date(2026, 11, 26),
        assertions=[
            CitationAssertion(
                doi="https://doi.org/10.1234/example",
                page=1,
                quote="An exact synthetic quotation.",
                cited_version="v1",
            )
        ],
    )
    row = result["citations"][0]
    assert row["existence"] == "SNAPSHOT_MATCH" and row["correction_status"] == "RETRACTED"
    assert row["version_match"] == "MISMATCH" and row["fulltext_quote_match"] is True
    assert row["in_bibliography"] == "FOUND"
    assert row["semantic_support"] == "REQUIRES_HUMAN_REVIEW"
    assert not row["age_is_a_negative_judgment"]
    assert result["classification"] == "RESTRICTED" and result["external_requests"] == 0


def test_missing_snapshots_never_claim_source_existence_or_retraction_absence():
    document = Document(document_id="synthetic", pages={1: "10.1234/missing"})
    row = verify_local_sources(document, [])["citations"][0]
    assert row["existence"] == "UNKNOWN" and row["correction_status"] == "UNKNOWN"
    assert row["verification"] == "UNVERIFIED" and row["fulltext_quote_match"] is None


def test_ambiguous_versions_require_operator_resolution():
    with pytest.raises(ValueError):
        verify_local_sources(Document(document_id="synthetic", pages={}), [source(), source()])
