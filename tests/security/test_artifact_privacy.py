import base64
import json

import pytest

from infrastructure.scripts.privacy_dlp import inspect_artifacts
from tests.fixtures import ROOT

MARKERS = json.loads((ROOT / "tests/fixtures/synthetic/privacy_canaries.json").read_text("utf-8"))


@pytest.mark.parametrize("encoding", ["plain", "base64", "hex", "chunk_boundary"])
def test_ci_artifact_gate_rejects_canaries_including_encoded_and_split_markers(tmp_path, encoding):
    value = MARKERS[0].encode()
    if encoding == "base64":
        value = base64.b64encode(value)
    elif encoding == "hex":
        value = value.hex().encode()
    elif encoding == "chunk_boundary":
        value = b"." * (65536 - 5) + value
    (tmp_path / "synthetic-report.xml").write_bytes(value)
    assert inspect_artifacts(tmp_path, MARKERS) == 1


def test_ci_artifact_gate_accepts_clean_reports_and_fails_without_evidence(tmp_path):
    (tmp_path / "synthetic-report.xml").write_text("No content, technical status only.")
    assert inspect_artifacts(tmp_path, MARKERS) == 0
    assert inspect_artifacts(tmp_path, []) == 1
    assert inspect_artifacts(tmp_path / "missing", MARKERS) == 1
