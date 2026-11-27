import hashlib
import json
from unittest.mock import patch

from app.knowledge.cli import main

from tests.unit.test_institutional_rules import source


def test_public_import_cli_has_no_approval_or_content_console_output(tmp_path, capsys):
    data = b"# Synthetic public guideline"
    input_path = tmp_path / "synthetic.md"
    input_path.write_bytes(data)
    metadata = tmp_path / "source.json"
    metadata.write_text(source(sha256=hashlib.sha256(data).hexdigest()).model_dump_json(), "utf-8")
    args = [
        "knowledge-import",
        str(input_path),
        str(metadata),
        "--store",
        str(tmp_path / "kb"),
        "--curator",
        "synthetic-curator",
        "--public-provenance-reviewed",
    ]
    with patch("sys.argv", args):
        assert main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "CANDIDATE_IMPORTED" and result["release"] == "CANDIDATE"
    assert "text" not in result
    with patch("sys.argv", args[:-1]):
        assert main() == 1
    assert capsys.readouterr().out.strip() == '{"status":"IMPORT_REJECTED"}'


def test_invalid_metadata_does_not_echo_imported_data_or_paths(tmp_path, capsys):
    document = tmp_path / "public.md"
    metadata = tmp_path / "metadata.yaml"
    document.write_text("Synthetic public material", "utf-8")
    metadata.write_text("classification: [invalid yaml", "utf-8")
    with patch(
        "sys.argv",
        [
            "knowledge-import",
            str(document),
            str(metadata),
            "--store",
            str(tmp_path / "kb"),
            "--curator",
            "synthetic",
            "--public-provenance-reviewed",
        ],
    ):
        assert main() == 1
    assert capsys.readouterr().out.strip() == '{"status":"IMPORT_REJECTED"}'
