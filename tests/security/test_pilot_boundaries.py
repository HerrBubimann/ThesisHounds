"""No user label, unreviewed model or changed file may activate the local pilot."""

import json
from datetime import UTC, datetime
from unittest.mock import patch

import httpx
import pytest
import yaml
from app.config import Settings
from app.main import create_provider
from app.services.document_store import (
    PilotApproval,
    checked_pilot_root,
    load_pilot_document,
    register_pilot_pdf,
)

from tests.fixtures import ROOT
from tests.fixtures.pilot import pdf_bytes, pilot_setup


def approval():
    return PilotApproval(
        kind="SYNTHETIC",
        reviewed_by="CI_ONLY",
        reviewed_at=datetime.now(UTC),
        provenance="SERVER_GENERATED_NOT_AN_EXPERT_APPROVAL",
    )


def test_pilot_storage_cannot_be_inside_repository():
    with pytest.raises(ValueError, match="BOUNDARY"):
        checked_pilot_root(ROOT / ".runtime/pilot")


@pytest.mark.parametrize("data", [b"not a pdf", b"%PDF-" + b"x" * 8_000_001])
def test_type_and_size_rejected_before_parser_or_storage(tmp_path, data):
    with patch("app.services.pdf_security.subprocess.run") as worker:
        with pytest.raises(ValueError):
            register_pilot_pdf(tmp_path / "catalog", data, approval())
        worker.assert_not_called()
    assert not (tmp_path / "catalog").exists()


def test_synthetic_confidential_notice_is_not_automatically_declassified(tmp_path):
    with pytest.raises(ValueError, match="NOTICE"):
        register_pilot_pdf(
            tmp_path / "catalog", pdf_bytes("Confidential synthetic secret"), approval()
        )
    assert not (tmp_path / "catalog").exists()


@pytest.mark.parametrize("changed", ["pdf", "pages", "approval"])
def test_modified_pilot_material_is_rejected(tmp_path, changed):
    _, catalog, key = pilot_setup(tmp_path)
    if changed == "pdf":
        (catalog / (key[6:] + ".pdf")).write_bytes(b"%PDF-changed")
    else:
        path = catalog / (key[6:] + ".json")
        content = json.loads(path.read_text())
        if changed == "pages":
            content["document"]["pages"]["1"] = "Altered text"
        else:
            content["approval"] = {}
        path.write_text(json.dumps(content), encoding="utf-8")
    with pytest.raises(ValueError):
        load_pilot_document(catalog, key, "synthetic-test")


@pytest.mark.parametrize(
    "missing", ["license_status", "expected_digest", "weights_origin", "version"]
)
def test_unapproved_or_unpinned_artifact_cannot_create_network_provider(tmp_path, missing):
    directory, catalog, _ = pilot_setup(tmp_path)
    path = directory / "models.yaml"
    config = yaml.safe_load(path.read_text())
    config["models"][0].pop(missing)
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    settings = Settings(
        _env_file=None,
        inference_mode="local_pilot",
        config_dir=directory,
        pilot_model_id="qwen",
        pilot_profile_id="pa1-example",
        pilot_document_dir=catalog,
    )
    with pytest.raises(ValueError, match="APPROVAL"):
        create_provider(settings, httpx.AsyncClient())
