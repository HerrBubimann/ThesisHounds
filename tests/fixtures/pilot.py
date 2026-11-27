"""Explicit test-only artifact/catalog approvals and generated synthetic PDF bytes."""

import io
import shutil
from datetime import UTC, datetime

import yaml
from app.services.document_store import PilotApproval, register_pilot_pdf
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from tests.fixtures import CONFIG


def pdf_bytes(text="Forschungsfrage: Ist die Methode nachvollziehbar?"):
    writer = PdfWriter()
    page = writer.add_blank_page(width=595, height=842)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    stream = DecodedStreamObject()
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream.set_data(("BT /F1 12 Tf 30 760 Td (" + escaped + ") Tj ET").encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def pilot_setup(tmp_path):
    directory = tmp_path / "config"
    shutil.copytree(CONFIG, directory)
    models = yaml.safe_load((directory / "models.yaml").read_text("utf-8"))
    qwen = models["models"][0]
    qwen.update(
        approval_status="APPROVED",
        license_status="APPROVED",
        security_review_status="APPROVED",
        version="TEST_ONLY_NOT_A_REAL_APPROVAL",
        weights_origin="SYNTHETIC_TEST_FIXTURE",
        expected_digest="a" * 64,
    )
    (directory / "models.yaml").write_text(yaml.safe_dump(models), encoding="utf-8")
    profile = yaml.safe_load((directory / "assessment_profiles/pa1.yaml").read_text("utf-8"))
    profile.update(
        status="EXPERIMENT",
        approved_by="SYNTHETIC_TEST_NOT_A_REAL_EXPERT",
        approved_at="2026-11-27",
        source="TEST_ONLY_EXPERIMENT_CATALOG",
    )
    (directory / "assessment_profiles/pa1.yaml").write_text(
        yaml.safe_dump(profile), encoding="utf-8"
    )
    catalog = tmp_path / "public-pilot"
    key = register_pilot_pdf(
        catalog,
        pdf_bytes(),
        PilotApproval(
            kind="SYNTHETIC",
            reviewed_by="synthetic-test-operator",
            reviewed_at=datetime.now(UTC),
            provenance="GENERATED_TEST_PDF_NOT_A_REAL_WORK",
        ),
    )
    return directory, catalog, key
