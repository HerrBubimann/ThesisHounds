import json
from datetime import UTC, datetime

import pytest
from app.evaluation.academic_benchmark import run_benchmarks
from app.research.citations import BibliographicEntry, extract_citations, verify_citations
from app.research.provider_registry import (
    PROVIDERS,
    LocalResearchCache,
    MetadataRecord,
    SourceType,
    import_metadata,
)
from app.services.document_store import Document

STAMP = datetime(2026, 1, 1, tzinfo=UTC)


def doc(text=None, classification="PUBLIC"):
    return Document(
        document_id="synthetic",
        classification=classification,
        complete=True,
        pages={
            1: "Einleitung\nErgebnis [1] und (Fehlt, 2024).",
            2: text
            or "Literaturverzeichnis\n[1] Muster (2020). Synthetischer Titel. doi:10.5555/test",
        },
    )


def record(**updates):
    return MetadataRecord(
        **(
            dict(
                doi="10.5555/test",
                title="Synthetischer Titel",
                authors=["Muster"],
                year=2020,
                provider="crossref",
                retrieved_at=STAMP,
                snapshot_sha256="a" * 64,
                provenance="SYNTHETIC",
            )
            | updates
        )
    )


def test_exact_citation_offsets_and_supported_missing_reference_candidates():
    document = doc()
    data = extract_citations(document)
    entry = data["entries"][0]
    assert document.pages[entry.page][entry.start : entry.end] == entry.raw
    assert entry.title == "Synthetischer Titel" and entry.author == "Muster" and entry.year == 2020
    result = verify_citations(document, LocalResearchCache([record()]))
    assert result["references"][0]["statuses"] == ["VERIFIED_METADATA"]
    assert result["references"][0]["checks"][0]["fields"] == dict(
        doi="MATCH", title="MATCH", author="MATCH", year="MATCH"
    )
    assert len(result["missing_reference_candidates"]) == 1
    assert not result["fabrication_inferred"] and result["external_requests"] == 0


@pytest.mark.parametrize(
    "change,field",
    [
        ({"title": "Anderer Titel"}, "title"),
        ({"authors": ["Anders"]}, "author"),
        ({"year": 2022}, "year"),
    ],
)
def test_metadata_disagreements_are_visible(change, field):
    row = verify_citations(doc(), LocalResearchCache([record(**change)]))["references"][0]
    assert row["statuses"] == ["METADATA_MISMATCH"]
    assert row["mismatched_fields"] == [field]
    assert row["semantic_support"] == "MANUAL_REVIEW_REQUIRED"


def test_fulltext_availability_does_not_verify_semantic_use_and_old_sources_are_not_bad():
    row = verify_citations(
        doc(), LocalResearchCache([record(year=1900, abstract="Abstract", fulltext="Text")])
    )["references"][0]
    assert "VERIFIED_FULLTEXT" not in row["statuses"] and not row["age_is_negative"]
    assert row["quality"] == "UNASSESSED"


def test_private_not_found_never_calls_provider_and_internal_sources_are_not_fabricated():
    result = verify_citations(doc(classification="RESTRICTED"))
    assert "RESEARCH_BLOCKED_BY_PRIVACY" in result["references"][0]["statuses"]
    assert result["not_found_scope"] == "LOCAL_SNAPSHOT_ONLY"
    internal = verify_citations(
        doc("Literaturverzeichnis\n[1] Intern (2020). Interner Bericht. intern", "RESTRICTED")
    )
    assert internal["references"][0]["statuses"] == ["INTERNAL_SOURCE"]
    assert not internal["fabrication_inferred"]


def test_duplicates_unused_unparsed_and_appendix_boundaries():
    text = (
        "Literaturverzeichnis\n[1] Muster (2020). Titel. doi:10.5555/test\n"
        "[1] Muster (2020). Titel. doi:10.5555/test\n"
        "Unlesbarer Fortsetzungsblock\nAnhang\nText [9]"
    )
    result = verify_citations(doc(text))
    assert len(result["references"]) == 3
    assert result["references"][0]["duplicate_candidate"]
    assert not result["references"][2]["cited_in_extracted_text"]
    assert result["references"][2]["missing_fields"] == ["author", "title", "year"]
    assert "AMBIGUOUS_REFERENCE_IDS" in result["warnings"]
    assert "UNPARSED_OR_MULTILINE_REFERENCE" in result["warnings"]


def test_version_and_source_type_mismatch_are_explicit():
    entry = BibliographicEntry(
        "1",
        2,
        0,
        1,
        "fixture",
        "10.5555/test",
        "Muster",
        2020,
        "Synthetischer Titel",
        SourceType.PREPRINT,
        "v1",
    )
    result = verify_citations(
        doc(),
        LocalResearchCache([record(source_type=SourceType.PAPER, version="v2")]),
        extracted={"entries": [entry], "mentions": [], "warnings": [], "method": "synthetic"},
    )
    assert result["references"][0]["mismatched_fields"] == ["source_type", "version"]


def test_public_crossref_openalex_and_retraction_imports_are_local():
    crossref = {
        "message": {
            "items": [
                {
                    "DOI": "10.5555/TEST",
                    "title": ["Synthetischer Titel"],
                    "author": [{"family": "Muster"}],
                    "published": {"date-parts": [[2020, 1, 1]]},
                    "type": "journal-article",
                }
            ]
        }
    }
    records = import_metadata(
        json.dumps(crossref).encode(),
        "crossref",
        retrieved_at=STAMP,
        provenance="SYNTHETIC",
        public_provenance_checked=True,
    )
    assert records[0].year == 2020 and records[0].doi == "10.5555/test"
    openalex = {
        "results": [
            {
                "doi": "https://doi.org/10.5555/test",
                "title": "Synthetischer Titel",
                "authorships": [{"author": {"display_name": "Muster"}}],
                "publication_year": 2020,
                "type": "preprint",
                "is_retracted": False,
            }
        ]
    }
    records += import_metadata(
        json.dumps(openalex).encode(),
        "openalex",
        retrieved_at=STAMP,
        provenance="SYNTHETIC",
        public_provenance_checked=True,
    )
    assert records[1].notice == "UNKNOWN" and records[1].source_type == SourceType.PREPRINT
    for nature, expected in [
        ("Retraction", "RETRACTED"),
        ("Correction", "CORRECTED"),
        ("Expression of concern", "MANUAL_REVIEW_REQUIRED"),
    ]:
        csv = (
            f"OriginalPaperDOI,Title,RetractionNature\n10.5555/test,Synthetischer Titel,{nature}\n"
        )
        notices = import_metadata(
            csv.encode(),
            "retraction_watch",
            retrieved_at=STAMP,
            provenance="SYNTHETIC",
            public_provenance_checked=True,
        )
        assert notices[0].notice == expected
    notices = import_metadata(
        b"OriginalPaperDOI,Title,RetractionNature\n10.5555/test,Titel,Retraction\n",
        "retraction_watch",
        retrieved_at=STAMP,
        provenance="SYNTHETIC",
        public_provenance_checked=True,
    )
    result = verify_citations(doc(), LocalResearchCache([records[0], *notices]))
    assert "RETRACTED" in result["references"][0]["statuses"]
    assert LocalResearchCache(records).search("Synthetischer")
    assert all(not p.network_enabled and p.max_cost_usd == 0 for p in PROVIDERS.values())


def test_provenance_limits_and_no_unsupported_or_paid_fallback():
    kwargs = dict(retrieved_at=STAMP, provenance="SYNTHETIC")
    with pytest.raises(ValueError, match="PROVENANCE"):
        import_metadata(b"{}", "crossref", **kwargs)
    for provider, data, error in [
        ("unknown", b"{}", "DENIED"),
        ("crossref", b"x" * 8_000_001, "DENIED"),
        ("datacite", b"{}", "NOT_RELEASED"),
    ]:
        with pytest.raises(ValueError, match=error):
            import_metadata(data, provider, public_provenance_checked=True, **kwargs)
    assert (
        import_metadata(b'{"DOI":""}', "crossref", public_provenance_checked=True, **kwargs) == []
    )


def test_scientific_benchmark_executes_real_local_functions():
    report = run_benchmarks()
    assert (
        report["passed"] and len(report["citation_cases"]) == 6 and len(report["formal_cases"]) == 4
    )
    assert report["external_requests"] == 0 and not report["grobid_quality_evaluated"]
