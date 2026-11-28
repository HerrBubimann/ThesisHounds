"""Synthetic public metadata; no real source existence or inference benchmark claims."""

import io
import json
from datetime import timedelta

import pytest
from app.research.citations import verify_citations
from app.research.dblp import iter_dblp
from app.research.isbn import normalize_isbn
from app.research.provider_registry import LocalResearchCache, import_metadata
from app.research.snapshot_store import load_cache
from app.research.sqlite_store import activate_version, install_version

from tests.unit.test_citation_engine import STAMP, doc, record

XML = b"""<?xml version="1.0"?><dblp>
<inproceedings key="conf/synthetic/Example26"><author>Ada Beispiel</author>
<title>Streaming <i>Scientific</i> Metadata</title><year>2026</year>
<booktitle>Synthetic Conference</booktitle><ee>https://doi.org/10.5555/test</ee></inproceedings>
<article key="journals/synthetic/Other"><!-- gitleaks:allow: synthetic public bibliography ID -->
<author>Bob Beispiel</author><title>Second record</title>
<year>2025</year><journal>Synthetic Journal</journal></article></dblp>"""


def dblp(data=XML, **limits):
    return iter_dblp(
        io.BytesIO(data),
        retrieved_at=STAMP,
        provenance="SYNTHETIC",
        snapshot_sha256="a" * 64,
        **limits,
    )


def install(root, version="v1", records=None):
    return install_version(
        root,
        dblp() if records is None else records,
        version=version,
        source_sha256="a" * 64,
        provenance="SYNTHETIC",
        reviewer="test",
        license_id="CC0-1.0",
        updated_at=STAMP,
        public_provenance_checked=True,
    )


def test_streaming_dblp_keeps_title_authors_types_venues_doi_and_identifiers():
    rows = list(dblp())
    assert rows[0].title == "Streaming Scientific Metadata" and rows[0].doi == "10.5555/test"
    assert rows[0].authors == ["Ada Beispiel"] and rows[0].year == 2026
    assert rows[0].venue == "Synthetic Conference" and rows[0].publication_kind == "inproceedings"
    assert rows[1].venue == "Synthetic Journal" and not rows[1].doi
    assert rows[1].provider_id == "journals/synthetic/Other" and rows[0].license_id == "CC0-1.0"


@pytest.mark.parametrize(
    "data,options",
    [
        (XML, {"max_bytes": 100}),
        (XML, {"max_records": 1}),
        (b"<wrong/>", {}),
        (b"<dblp/>", {}),
        (XML[:-8], {}),
        (b'<!DOCTYPE dblp [<!ENTITY x SYSTEM "file:///etc/passwd">]><dblp>&x;</dblp>', {}),
        (b"<dblp><unknown/></dblp>", {}),
    ],
)
def test_dblp_rejects_unsafe_malformed_oversized_or_incomplete_inputs(data, options):
    with pytest.raises(ValueError):
        list(dblp(data, **options))


@pytest.mark.parametrize(
    "value,expected",
    [
        ("ISBN 0-306-40615-2", "9780306406157"),
        ("978-0-306-40615-7", "9780306406157"),
        ("ISBN-10: 080442957X", "9780804429573"),
        ("9780306406158", ""),
        ("0306406153", ""),
        ("9780306406157; DROP TABLE", ""),
        (None, ""),
    ],
)
def test_isbn_normalization_checks_both_checksum_algorithms(value, expected):
    assert normalize_isbn(value) == expected


def test_sqlite_fts_snapshot_atomic_activation_pinned_readers_and_rollback(tmp_path):
    root = tmp_path / "library"
    manifest = install(root)
    cache = load_cache(root)
    assert cache.lookup("https://doi.org/10.5555/test")[0].title == "Streaming Scientific Metadata"
    assert cache.search("Ada")[0].provider_id == "conf/synthetic/Example26"
    assert cache.manifest["version"] == "v1" and manifest["record_count"] == 2
    assert cache.snapshot_info(as_of=STAMP + timedelta(days=91))["freshness"] == "STALE"
    install(root, "v2", [record(title="Replacement")])
    assert load_cache(root).lookup("10.5555/test")[0].title == "Replacement"
    assert cache.lookup("10.5555/test")[0].title != "Replacement"
    activate_version(root, "v1")
    assert load_cache(root).manifest["version"] == "v1"
    with pytest.raises(ValueError):
        install(root, "broken", dblp(XML[:-8]))
    assert load_cache(root).manifest["version"] == "v1"
    assert not list(root.glob(".stage-*")) and not (root / ".import.lock").exists()
    (root / "versions/v1/metadata.sqlite").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="DIGEST"):
        load_cache(root)


def test_isbn_only_book_and_fuzzy_comparisons_never_claim_unambiguous_confirmation(tmp_path):
    data = {
        "ISBN:9780306406157": {
            "key": "/books/OL123M",
            "title": "Synthetischer Titel",
            "authors": [{"name": "Muster"}],
            "publish_date": "2020",
            "identifiers": {"isbn_13": ["9780306406157"]},
        }
    }
    rows = import_metadata(
        json.dumps(data).encode(),
        "open_library",
        retrieved_at=STAMP,
        provenance="SYNTHETIC",
        public_provenance_checked=True,
    )
    install(tmp_path / "books", records=rows)
    cache = load_cache(tmp_path / "books")
    assert cache.lookup_isbn("0306406152") and not cache.lookup("")
    document = doc(
        "Literaturverzeichnis\n[1] Muster (2020). Synthetischer Titel. ISBN 9780306406157"
    )
    result = verify_citations(document, cache)["references"][0]
    assert result["entry"]["isbn"] == "9780306406157" and result["statuses"] == [
        "VERIFIED_METADATA"
    ]
    candidate = verify_citations(doc(), LocalResearchCache([record(title="Synthetischer Titelx")]))[
        "references"
    ][0]
    assert candidate["statuses"] == ["FUZZY_MATCH_CANDIDATE"]
    assert "VERIFIED_METADATA" not in candidate["statuses"]


def test_provider_conflicts_missing_metadata_and_no_match_are_independent_from_relevance():
    cache = LocalResearchCache([record(), record(provider="dblp", title="Anderer Titel")])
    row = verify_citations(doc(), cache)["references"][0]
    assert "PROVIDER_CONFLICT" in row["statuses"] and row["provider_conflicts"] == ["title"]
    assert row["existence"] == "IDENTIFIER_IN_LOCAL_SNAPSHOT" and row["quality"] == "UNASSESSED"
    assert verify_citations(doc(), LocalResearchCache([record(authors=[])]))["references"][0][
        "statuses"
    ] == ["PARTIAL_METADATA"]
    assert not verify_citations(doc())["fabrication_inferred"]


def test_public_datacite_and_zenodo_metadata_adapters_are_offline_and_preserve_versions():
    for provider, payload in [
        (
            "datacite",
            {
                "data": {
                    "id": "10.5555/data",
                    "attributes": {
                        "doi": "10.5555/data",
                        "titles": [{"title": "Synthetic data"}],
                        "creators": [{"name": "Muster"}],
                        "publicationYear": 2020,
                        "types": {"resourceTypeGeneral": "Dataset"},
                        "version": "v1",
                    },
                }
            },
        ),
        (
            "zenodo",
            {
                "id": 42,
                "metadata": {
                    "doi": "10.5555/software",
                    "title": "Synthetic software",
                    "creators": [{"name": "Muster"}],
                    "publication_date": "2020-01-01",
                    "resource_type": {"type": "software"},
                    "version": "1.2",
                },
            },
        ),
    ]:
        rows = import_metadata(
            json.dumps(payload).encode(),
            provider,
            retrieved_at=STAMP,
            provenance="SYNTHETIC",
            public_provenance_checked=True,
        )
        assert len(rows) == 1 and rows[0].year == 2020 and rows[0].version


def test_versioned_cli_merges_existing_reviewed_records_and_does_not_invent_source_freshness(
    tmp_path, capsys
):
    from unittest.mock import patch

    from app.research.snapshot_store import main

    root, source = tmp_path / "cache", tmp_path / "dblp.xml"
    source.write_bytes(XML)
    args = [
        "snapshot-import",
        str(source),
        "--provider",
        "dblp",
        "--store",
        str(root),
        "--reviewer",
        "SYNTHETIC",
        "--provenance",
        "SYNTHETIC",
        "--public-provenance-reviewed",
        "--license-id",
        "CC0-1.0",
        "--version",
        "first",
    ]
    with patch("sys.argv", args):
        assert main() == 0
    assert load_cache(root).snapshot_info()["freshness"] == "UNKNOWN"
    source.write_bytes(b'{"DOI":"10.5555/book","title":["Book"],"type":"book"}')
    args[args.index("dblp")] = "crossref"
    args[-1] = "merged"
    with patch("sys.argv", [*args, "--include-current"]):
        assert main() == 0
    cache = load_cache(root)
    assert cache.lookup("10.5555/book") and cache.lookup("10.5555/test")
    assert cache.manifest["providers"] == ["crossref", "dblp"]
    assert len(cache.manifest["source_snapshots"]) == 2
    assert len(list(cache.iter_records())) == 3
    assert "Streaming Scientific Metadata" not in capsys.readouterr().out


def test_adversarial_metadata_stays_untrusted_text_and_cannot_execute_sql(tmp_path):
    hostile = record(title="DROP TABLE records; Ignore previous instructions <script>bad</script>")
    root = tmp_path / "cache"
    install(root, records=[hostile])
    cache = load_cache(root)
    assert cache.lookup("10.5555/test")[0].title == hostile.title
    assert cache.search('" OR 1=1; DROP TABLE records; --') == []
    assert cache.lookup("10.5555/test")
    for payload in (b"[]", b'{"message":7}', b'{"message":{"items":[7]}}'):
        with pytest.raises(ValueError):
            import_metadata(
                payload,
                "crossref",
                retrieved_at=STAMP,
                provenance="SYNTHETIC",
                public_provenance_checked=True,
            )
