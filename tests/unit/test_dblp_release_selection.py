import hashlib
import io
import json
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from app.research.dblp import DBLPReleaseSelection, iter_selected_dblp
from app.research.snapshot_store import load_cache, main

XML = b"""<dblp>
<article key="journals/synthetic/a"><!-- gitleaks:allow: synthetic public bibliography ID -->
<author>Example</author>
<title>Synthetic article A</title><year>2020</year></article>
<inproceedings key="conf/synthetic/b"><author>Example</author>
<title>Synthetic article B</title><year>2021</year></inproceedings></dblp>"""


def selection(tmp_path, **updates):
    value = {
        "release_doi": "10.4230/dblp.xml.2026-11-01",
        "subset_sha256": hashlib.sha256(XML).hexdigest(),
        "keys": ["conf/synthetic/b"],
        "reviewed_by": "SYNTHETIC_TEST",
        "public_provenance_reviewed": True,
        **updates,
    }
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(value), "utf-8")
    return path


def records(value, data=XML):
    return list(
        iter_selected_dblp(
            io.BytesIO(data),
            value,
            retrieved_at=datetime.now(UTC),
            provenance="SYNTHETIC_SUBSET_NOT_PUBLISHER_DATA",
            snapshot_sha256=hashlib.sha256(data).hexdigest(),
        )
    )


def test_release_selection_retains_only_explicit_keys_and_lineage(tmp_path):
    value = DBLPReleaseSelection.load(selection(tmp_path))
    found = records(value)
    assert len(found) == 1 and found[0].provider_id == "conf/synthetic/b"
    assert found[0].source_release_doi == value.release_doi
    assert found[0].selection_sha256 == value.digest
    assert found[0].snapshot_sha256 == hashlib.sha256(XML).hexdigest()


@pytest.mark.parametrize(
    "updates",
    [
        {"public_provenance_reviewed": False},
        {"keys": ["duplicate", "duplicate"]},
        {"keys": ["bad\nkey"]},
        {"release_doi": "10.4230/dblp.xml"},
        {"release_doi": "10.4230/dblp.xml.2099-01-01"},
        {"release_doi": "10.4230/dblp.xml.2026-13-01"},
    ],
)
def test_unreviewed_ambiguous_or_invalid_release_rejected(tmp_path, updates):
    with pytest.raises(ValueError):
        DBLPReleaseSelection.load(selection(tmp_path, **updates))


def test_wrong_digest_missing_key_and_duplicate_input_cannot_succeed(tmp_path):
    value = DBLPReleaseSelection.load(selection(tmp_path, subset_sha256="0" * 64))
    with pytest.raises(ValueError, match="DIGEST"):
        records(value)
    value = DBLPReleaseSelection.load(selection(tmp_path, keys=["missing"]))
    with pytest.raises(ValueError, match="NOT_FOUND"):
        records(value)
    duplicate = XML.replace(
        b"</dblp>",
        b'<inproceedings key="conf/synthetic/b"><title>Duplicate</title></inproceedings></dblp>',
    )
    value = DBLPReleaseSelection.load(
        selection(tmp_path, subset_sha256=hashlib.sha256(duplicate).hexdigest())
    )
    with pytest.raises(ValueError, match="DUPLICATE"):
        records(value, duplicate)


def test_versioned_cli_records_release_selection_and_rejects_missing_keys_atomically(
    tmp_path, capsys
):
    source = tmp_path / "subset.xml"
    source.write_bytes(XML)
    path = selection(tmp_path)
    root = tmp_path / "library"
    args = [
        "snapshot-import",
        str(source),
        "--provider",
        "dblp",
        "--store",
        str(root),
        "--reviewer",
        "SYNTHETIC_TEST",
        "--provenance",
        "SYNTHETIC_SUBSET",
        "--license-id",
        "CC0-1.0",
        "--public-provenance-reviewed",
        "--version",
        "synthetic-v1",
        "--dblp-release-selection",
        str(path),
    ]
    with patch("sys.argv", args):
        assert main() == 0
    assert "Synthetic article" not in capsys.readouterr().out
    cache = load_cache(root)
    assert [r.provider_id for r in cache.iter_records()] == ["conf/synthetic/b"]
    manifest = json.loads((root / "versions/synthetic-v1/manifest.json").read_text("utf-8"))
    assert manifest["source_release_dois"] == ["10.4230/dblp.xml.2026-11-01"]
    assert manifest["selection_sha256"] == [DBLPReleaseSelection.load(path).digest]
    before = (root / "CURRENT.json").read_bytes()
    selection(tmp_path, keys=["missing"])
    args[args.index("synthetic-v1")] = "synthetic-v2"
    with patch("sys.argv", args):
        assert main() == 1
    assert (root / "CURRENT.json").read_bytes() == before
    assert not (root / "versions/synthetic-v2").exists()
