"""Operator-only inspection of fixed public DHBW bundles; never runs in the application."""

import hashlib
import io
import json
import zipfile
from pathlib import Path

import httpx

BASE = "https://www.mosbach.dhbw.de/fileadmin/user_upload/dhbw/studiengaenge/"
URLS = {
    "ba-ds23": BASE + "wi/bachelorarbeit/Unterlagen_Bachelorarbeit_DS23.zip",
    "pa2-ds24": BASE + "ds/Unterlagen_Projektarbeit2_DS24.zip",
    "pa1-ds25": BASE + "ds/Unterlagen_Projektarbeit1_DS25.zip",
}
DOCUMENT_URLS = {
    "ds-work-page": "https://www.mosbach.dhbw.de/studium/studienangebot-bachelor/data-science-kuenstliche-intelligenz/projekt-und-bachelorarbeiten/",
    "faculty-5-0": "https://www.mosbach.dhbw.de/fileadmin/user_upload/dhbw/ressorts/esc/Lehrende/Richtlinien_Version2023-07-18.pdf",
    "confidentiality-may-2026": "https://www.dhbw.de/fileadmin/user_upload/Dokumente/Qualitaetsmanagement/Infoblatt_Vertraulichkeit.pdf",
}


def main():
    root = Path(".runtime/public-dhbw")
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, url in {**URLS, **DOCUMENT_URLS}.items():
        try:
            # Fixed PUBLIC allowlist only; this operator helper is never called by analysis.
            with httpx.Client(timeout=30, trust_env=False, follow_redirects=False) as client:
                with client.stream("GET", url) as response:
                    response.raise_for_status()
                    content = bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > 20_000_000:
                            raise ValueError("PUBLIC_BUNDLE_TOO_LARGE")
                    data = bytes(content)
            if len(data) > 20_000_000:
                raise ValueError("PUBLIC_BUNDLE_TOO_LARGE")
            extension = ".zip" if name in URLS else ".pdf" if url.endswith(".pdf") else ".html"
            (root / (name + extension)).write_bytes(data)
            members = []
            if extension == ".zip":
                with zipfile.ZipFile(io.BytesIO(data)) as bundle:
                    members = [
                        {"name": entry.filename, "size": entry.file_size}
                        for entry in bundle.infolist()
                    ]
            rows.append(
                {
                    "id": name,
                    "url": url,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "members": members,
                }
            )
        except Exception as error:
            rows.append({"id": name, "url": url, "error_type": type(error).__name__})
    (root / "manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(rows, ensure_ascii=False, indent=2))


def inspect_contents():
    from defusedxml import ElementTree
    from pypdf import PdfReader

    root = Path(".runtime/public-dhbw")
    for path in sorted(root.glob("*.zip")):
        sections = []
        with zipfile.ZipFile(path) as bundle:
            for item in bundle.infolist():
                data = bundle.read(item)
                sections.append(
                    "\nFILE: " + item.filename + " SHA256: " + hashlib.sha256(data).hexdigest()
                )
                if item.filename.endswith(".pdf"):
                    pdf = PdfReader(io.BytesIO(data))
                    for page, text in enumerate(pdf.pages, 1):
                        sections.append(f"\nPAGE {page}\n" + (text.extract_text() or ""))
                elif item.filename.endswith((".docx", ".dotx")):
                    with zipfile.ZipFile(io.BytesIO(data)) as office:
                        tree = ElementTree.fromstring(office.read("word/document.xml"))
                        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                        sections.extend("".join(p.itertext()) for p in tree.findall(".//w:p", ns))
        (root / (path.stem + ".md")).write_text("\n".join(sections), "utf-8")


if __name__ == "__main__":
    import sys

    inspect_contents() if sys.argv[1:] == ["inspect"] else main()
