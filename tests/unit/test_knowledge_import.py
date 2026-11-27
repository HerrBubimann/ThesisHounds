import hashlib
import io
import json
import zipfile
from unittest.mock import patch

import pytest
from app.knowledge.importer import (
    ImportAuthority,
    ImportRejected,
    KnowledgeStore,
    extract_candidate,
)
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject

from tests.fixtures import ROOT
from tests.unit.test_institutional_rules import source


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as bundle:
        for name, data in files.items():
            bundle.writestr(name, data)
    return stream.getvalue()


@pytest.mark.parametrize(
    "suffix,content,expected",
    [
        (".md", "# Public guideline", "Public guideline"),
        (".yaml", "title: Public guideline", "Public guideline"),
        (".json", '{"title":"Public guideline"}', "Public guideline"),
        (
            ".html",
            '<h1>Public guideline</h1><script>secret()</script><img src="https://external.invalid">',
            "Public guideline",
        ),
    ],
)
def test_text_formats_do_not_fetch_or_execute(suffix, content, expected):
    with patch("socket.socket", side_effect=AssertionError("NETWORK_NOT_ALLOWED")):
        result = extract_candidate(content.encode(), suffix)
    assert expected in result["text"] and "secret()" not in result["text"]
    assert result["release"] == "CANDIDATE" and result["classification"] == "RESTRICTED"


def test_office_import_retains_text_without_macros_formulas_or_remote_resources():
    word = (
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>Public rule</w:t></w:r></w:p></w:body></w:document>"
    )
    data = archive(
        {
            "[Content_Types].xml": "<Types/>",
            "word/document.xml": word,
            "word/_rels/document.xml.rels": '<Relationships><Relationship TargetMode="External" Target="https://external.invalid"/></Relationships>',
        }
    )
    for suffix in (".docx", ".dotx"):
        result = extract_candidate(data, suffix)
        assert result["text"] == "Public rule"
        assert "EXTERNAL_RELATIONSHIPS_IGNORED" in result["warnings"]
    sheet = (
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData><row><c t="s"><v>0</v></c><c><f>WEBSERVICE()</f><v>999</v></c>'
        '<c t="inlineStr"><is><t>Label</t></is></c></row></sheetData></worksheet>'
    )
    data = archive(
        {
            "[Content_Types].xml": "<Types/>",
            "xl/worksheets/sheet1.xml": sheet,
            "xl/sharedStrings.xml": '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>Public</t></si></sst>',
        }
    )
    result = extract_candidate(data, ".xlsx")
    assert result["text"] == "Public\nLabel" and "FORMULA_NOT_EVALUATED" in result["warnings"]


@pytest.mark.parametrize(
    "name",
    [
        "../escape.xml",
        "/absolute",
        "word/vbaProject.bin",
        "word/embeddings/file.bin",
        "C:/file",
        "word\\evil",
    ],
)
def test_unsafe_archives_are_rejected_without_extracting_files(name):
    with pytest.raises(ImportRejected, match="ARCHIVE|FILE_TYPE"):
        extract_candidate(archive({name: "x"}), ".docx")


def test_pdf_text_only_and_dormant_active_content_denied():
    writer = PdfWriter()
    writer.add_blank_page(width=600, height=800)
    stream = io.BytesIO()
    writer.write(stream)
    result = extract_candidate(stream.getvalue(), ".pdf")
    assert (
        result["pages"] == {1: ""} and "TEXT_ONLY_NO_OCR_OR_LAYOUT_GUARANTEE" in result["warnings"]
    )
    writer._root_object[NameObject("/OpenAction")] = DictionaryObject()
    stream = io.BytesIO()
    writer.write(stream)
    with pytest.raises(ImportRejected, match="ACTIVE_CONTENT"):
        extract_candidate(stream.getvalue(), ".pdf")
    writer = PdfWriter()
    writer.add_blank_page(width=600, height=800)
    writer.encrypt("synthetic-test-password")
    stream = io.BytesIO()
    writer.write(stream)
    with pytest.raises(ImportRejected, match="ENCRYPTED"):
        extract_candidate(stream.getvalue(), ".pdf")


def test_limits_type_confusion_and_yaml_expansion_denied():
    for data, suffix in [
        (b"", ".md"),
        (b"x" * 8_000_001, ".md"),
        (b"text", ".exe"),
        (b"text", ".pdf"),
        (b"a: &a [1]\nb: *a", ".yaml"),
    ]:
        with pytest.raises(ValueError):
            extract_candidate(data, suffix)
    with patch("app.knowledge.importer.MAX_EXPANDED", 1):
        with pytest.raises(ImportRejected, match="EXPANSION"):
            extract_candidate(archive({"word/document.xml": "xx"}), ".docx")
    with pytest.raises(ImportRejected, match="LOCAL_EXTRACTION_REJECTED"):
        extract_candidate(
            archive(
                {
                    "[Content_Types].xml": "<Types/>",
                    "word/document.xml": '<!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><a>&x;</a>',
                }
            ),
            ".docx",
        )


def test_operator_public_import_resets_approval_and_keeps_content_outside_repo(tmp_path):
    store = KnowledgeStore(tmp_path / "kb")
    data = b"# Public source"
    metadata = source(sha256=hashlib.sha256(data).hexdigest())
    result = store.import_public(data, ".md", metadata, ImportAuthority("curator", True, True))
    assert result["source"]["release"] == "CANDIDATE" and result["source"]["binding"] == "CANDIDATE"
    assert "text" not in result
    stored = json.loads(next((tmp_path / "kb/public").glob("*.json")).read_text("utf-8"))
    assert stored["text"] == "# Public source" and stored["classification"] == "PUBLIC"
    with pytest.raises(FileExistsError):
        store.import_public(data, ".md", metadata, ImportAuthority("curator", True, True))
    with pytest.raises(ImportRejected, match="BOUNDARY"):
        KnowledgeStore(ROOT / ".runtime/kb")


@pytest.mark.parametrize(
    "authority,level",
    [
        (ImportAuthority("", True, True), "PUBLIC"),
        (ImportAuthority("x", False, True), "PUBLIC"),
        (ImportAuthority("x", True, False), "PUBLIC"),
        (ImportAuthority("x", True, True), "RESTRICTED"),
    ],
)
def test_no_unreviewed_or_private_import(authority, level, tmp_path):
    with pytest.raises(ImportRejected, match="AUTHORIZED"):
        KnowledgeStore(tmp_path / "kb").import_public(
            b"# text", ".md", source(classification=level), authority
        )


def test_import_checks_actual_file_digest(tmp_path):
    with pytest.raises(ImportRejected, match="DIGEST"):
        KnowledgeStore(tmp_path / "kb").import_public(
            b"text", ".md", source(), ImportAuthority("x", True, True)
        )


def test_public_subdirectory_cannot_redirect_store(tmp_path, monkeypatch):
    original = type(tmp_path).is_symlink
    store = KnowledgeStore(tmp_path / "kb")
    monkeypatch.setattr(
        type(tmp_path), "is_symlink", lambda path: path.name == "public" or original(path)
    )
    data = b"# Public synthetic"
    with pytest.raises(ImportRejected, match="BOUNDARY"):
        store.import_public(
            data,
            ".md",
            source(sha256=hashlib.sha256(data).hexdigest()),
            ImportAuthority("reviewer", True, True),
        )
