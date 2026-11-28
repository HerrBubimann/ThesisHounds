import json
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from app.research.provider_registry import SourceType, import_metadata
from app.research.snapshot_store import load_cache, main, store_snapshot

RIS = (
    b"TY  - JOUR\nTI  - Synthetic catalog article\nAU  - Meyer, Anna\nPY  - 2020/01/01\n"
    b"DO  - https://doi.org/10.5555/example\nER  -\n"
)


def imported(data=RIS, **changes):
    return import_metadata(
        data,
        "library_export",
        retrieved_at=datetime.now(UTC),
        provenance="SYNTHETIC_CATALOG_EXPORT_NOT_LICENSED_DATA",
        **{"public_provenance_checked": True, "export_rights_reviewed": True, **changes},
    )


def test_metadata_export_roundtrip_never_resolves_urls(tmp_path):
    with patch("socket.getaddrinfo", side_effect=AssertionError("No catalog access")):
        records = imported()
        assert records[0].doi == "10.5555/example"
        assert records[0].source_type == SourceType.PAPER
        assert records[0].export_rights_reviewed
        root = tmp_path / "library"
        store_snapshot(
            root,
            RIS,
            "library_export",
            reviewer="SYNTHETIC_TEST",
            provenance="SYNTHETIC",
            public_provenance_checked=True,
            export_rights_reviewed=True,
        )
        assert load_cache(root).lookup("10.5555/example")[0].title == "Synthetic catalog article"


def test_csl_metadata_import_preserves_book_fields():
    data = [
        {
            "id": "catalog-1",
            "type": "book",
            "title": "Synthetic book",
            "author": [{"given": "Anna", "family": "Meyer"}],
            "issued": {"date-parts": [[2020]]},
            "ISBN": "9780306406157",
            "URL": "https://example.invalid/never-fetch",
        }
    ]
    record = imported(json.dumps(data).encode())[0]
    assert record.provider_id == "catalog-1" and record.source_type == SourceType.BOOK
    assert record.authors == ["Anna Meyer"] and record.year == 2020
    assert record.isbn == "9780306406157"
    assert record.fulltext is None and record.abstract is None


@pytest.mark.parametrize(
    "changes", [{"public_provenance_checked": False}, {"export_rights_reviewed": False}]
)
def test_library_export_requires_both_public_provenance_and_rights_review(changes):
    with pytest.raises(ValueError):
        imported(**changes)


@pytest.mark.parametrize(
    "data",
    [
        b"TY  - JOUR\nTI  - Incomplete",
        b"TI  - No record\nER  -\n",
        b"TY  - JOUR\nTY  - JOUR\nER  -\n",
        b"not RIS",
        RIS.replace(b"ER  -", b"AB  - Private full abstract\nER  -"),
        RIS.replace(b"AU  - Meyer, Anna\n", b""),
        b'[{"type":"book", "title":"x", "file":"private.pdf"}]',
    ],
)
def test_unbounded_incomplete_or_non_metadata_payloads_are_rejected(data):
    with pytest.raises(ValueError):
        imported(data)


def test_hanging_title_lines_are_bounded_metadata_not_executable():
    data = RIS.replace(b"Synthetic catalog article", b"Synthetic\n   continued catalog article")
    assert imported(data)[0].title == "Synthetic continued catalog article"
    with pytest.raises(ValueError):
        imported(RIS * 1001)
    with pytest.raises(ValueError):
        imported(b"x" * 2_000_001)


def test_versioned_operator_import_requires_rights_flag(tmp_path, capsys):
    source = tmp_path / "synthetic.ris"
    source.write_bytes(RIS)
    root = tmp_path / "library"
    args = [
        "library-import",
        str(source),
        "--provider",
        "library_export",
        "--store",
        str(root),
        "--reviewer",
        "SYNTHETIC_TEST",
        "--provenance",
        "SYNTHETIC",
        "--version",
        "synthetic-v1",
        "--license-id",
        "SYNTHETIC_METADATA_RIGHTS",
        "--public-provenance-reviewed",
    ]
    with patch("sys.argv", args):
        assert main() == 1
    assert not (root / "CURRENT.json").exists()
    with patch("sys.argv", args + ["--export-rights-reviewed"]):
        assert main() == 0
    assert "Synthetic catalog article" not in capsys.readouterr().out
    record = load_cache(root).lookup("10.5555/example")[0]
    assert record.export_rights_reviewed and record.snapshot_version == "synthetic-v1"
