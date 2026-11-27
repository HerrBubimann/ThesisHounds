import hashlib
import json
from unittest.mock import patch

import pytest
from app.config import Settings
from app.research.snapshot_store import load_cache, main, store_snapshot

from tests.fixtures import ROOT

DATA = b'{"DOI":"10.5555/test","title":["Synthetic public snapshot"]}'


def test_verified_public_snapshot_roundtrip_and_tamper_rejection(tmp_path):
    root = tmp_path / "public-library"
    result = store_snapshot(
        root,
        DATA,
        "crossref",
        reviewer="synthetic-reviewer",
        provenance="SYNTHETIC",
        public_provenance_checked=True,
    )
    assert result["sha256"] == hashlib.sha256(DATA).hexdigest() and result["records"] == 1
    assert load_cache(root).lookup("10.5555/test")[0].title == "Synthetic public snapshot"
    assert not load_cache(None).records
    path = next(root.glob("*.json"))
    wrapper = json.loads(path.read_text("utf-8"))
    wrapper["raw_utf8"] = "{}"
    path.write_text(json.dumps(wrapper), "utf-8")
    with pytest.raises(ValueError, match="DIGEST"):
        load_cache(root)


def test_snapshot_cli_is_public_only_and_summary_only(tmp_path, capsys):
    source = tmp_path / "crossref.json"
    source.write_bytes(DATA)
    args = [
        "snapshot-import",
        str(source),
        "--provider",
        "crossref",
        "--store",
        str(tmp_path / "cache"),
        "--reviewer",
        "synthetic",
        "--provenance",
        "SYNTHETIC",
    ]
    with patch("sys.argv", args):
        assert main() == 1
    assert "PUBLIC_METADATA_IMPORT_REJECTED" in capsys.readouterr().out
    with patch("sys.argv", args + ["--public-provenance-reviewed"]):
        assert main() == 0
    assert "Synthetic public snapshot" not in capsys.readouterr().out


def test_repository_private_snapshots_missing_review_and_boundaries_denied(tmp_path):
    with pytest.raises(ValueError, match="BOUNDARY"):
        store_snapshot(
            ROOT / ".runtime/public-cache",
            DATA,
            "crossref",
            reviewer="x",
            provenance="test",
            public_provenance_checked=True,
        )
    with pytest.raises(ValueError, match="REVIEW"):
        store_snapshot(
            tmp_path / "cache",
            DATA,
            "crossref",
            reviewer="",
            provenance="test",
            public_provenance_checked=True,
        )
    with pytest.raises(ValueError):
        Settings(_env_file=None, public_metadata_dir=ROOT / ".runtime/cache")
    root = tmp_path / "cache"
    store_snapshot(
        root, DATA, "crossref", reviewer="x", provenance="test", public_provenance_checked=True
    )
    path = next(root.iterdir())
    wrapper = json.loads(path.read_text("utf-8"))
    wrapper["classification"] = "RESTRICTED"
    path.write_text(json.dumps(wrapper), "utf-8")
    with pytest.raises(ValueError, match="PROVENANCE"):
        load_cache(root)
