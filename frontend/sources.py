"""Local Source Inspector; never turns document contents into external queries."""

import streamlit as st

from frontend import api_client
from frontend.design import details, empty_state, label, status_badges


def render_source_inspector(path):
    checks = api_client.request_backend("GET", path + "/academic-checks")
    report = checks["citations"]
    references = report["references"]
    st.caption(
        "Lokale Metadatenprüfung · kein automatischer Volltextabruf · kein"
        " Nachweis inhaltlicher Unterstützung"
    )
    if not references:
        empty_state(
            "Keine unterstützten Einträge extrahiert",
            "Das ist kein Nachweis fehlender Quellen. Literaturverzeichnis und"
            " Zitierweise manuell prüfen.",
        )
        return
    search = st.text_input("Quellen durchsuchen", max_chars=200)
    statuses = sorted({status for row in references for status in row["statuses"]})
    status = st.selectbox("Quellenstatus", ["Alle", *statuses], format_func=label)
    for row in references:
        entry = row["entry"]
        if (status != "Alle" and status not in row["statuses"]) or (
            search and search.casefold() not in entry["raw"].casefold()
        ):
            continue
        with st.container(border=True):
            st.text(entry.get("title") or entry["raw"])
            status_badges(*row["statuses"])
            st.text(
                f"Autor: {entry.get('author') or 'nicht extrahiert'} "
                f"· Jahr: {entry.get('year') or 'unbekannt'} "
                f"· Typ: {entry.get('source_type', 'UNKNOWN')}"
            )
            st.text(
                f"DOI: {entry.get('doi') or 'nicht extrahiert'} "
                f"· ISBN: {entry.get('isbn') or 'nicht extrahiert'} "
                f"· Literaturverzeichnis: Seite {entry['page']}"
            )
            st.caption(
                "Retraktionsabdeckung: "
                + row.get("retraction_coverage", "UNKNOWN")
                + " · Neuere Versionen: nicht vollständig erhoben"
            )
            st.caption(
                "Abstract/Volltext in dieser Ansicht: nicht geprüft. "
                "Metadatenbestätigung ist keine Volltextverifikation."
            )
            for check in row["checks"]:
                st.text(
                    f"Provider: {check['provider']} "
                    f"· Snapshot: {check.get('snapshot_version') or 'unbekannt'} "
                    f"· {check['snapshot_sha256']}"
                )
            details(row, title="Metadatenfelder, Konflikte und Nachweisumfang")
            if st.button("Originalstelle der Quelle öffnen", key="source_entry_" + entry["id"]):
                document = api_client.request_backend("GET", path + "/document")
                text = document["pages"].get(str(entry["page"]), "")
                if text[entry["start"] : entry["end"]] == entry["raw"]:
                    st.text(text)
                else:
                    st.warning("Originalstelle nicht mehr eindeutig verifizierbar.")
    details(
        {k: v for k, v in report.items() if k != "references"},
        title="Zitierverweise, Zuordnungen und Prüflücken",
    )
