"""Evidence Explorer: extracted coordinates never become invented PDF geometry."""

import streamlit as st

from frontend import api_client
from frontend.api_client import BackendError
from frontend.design import details, empty_state, label, status_badges


def document_reader(path, record):
    document = api_client.request_backend("GET", path + "/document")
    pages = document["pages"]
    st.subheader("Dokument")
    st.caption("Verifizierter extrahierter Text · kein Layout- oder OCR-Nachweis")
    page = st.selectbox("Dokumentseite", list(pages), key=path + "_page")
    search = st.text_input("Auf dieser Seite suchen", key=path + "_document_search", max_chars=200)
    text = pages[page]
    if search:
        count = text.casefold().count(search.casefold())
        st.caption(f"{count} Texttreffer auf dieser Seite")
    with st.container(height=440, border=True):
        st.text(text)
    if document.get("extraction_warnings"):
        st.warning("Extraktionshinweise vorhanden; das Original manuell prüfen.")
        for warning in document["extraction_warnings"]:
            st.text(warning)
    source_sha = document.get("source_sha256")
    show = st.toggle("Original-PDF anzeigen", key=path + "_show_pdf", disabled=not source_sha)
    if not source_sha:
        st.caption(
            "Das synthetische Testdokument besitzt keine Original-PDF. Es wird"
            " keine Ersatzdatei als Original ausgegeben."
        )
    elif show:
        try:
            data = api_client.request_pdf(path + "/original-pdf")
            st.pdf(
                data,
                height=620,
                key=path + "_pdf",
                alt="Registrierte Original-PDF der aktuellen Begutachtung",
            )
            st.caption(
                "Lokaler Viewer · Seite im PDF-Viewer selbst wählen. Keine "
                "automatisch synchronisierten PDF-Markierungen ohne bestätigte "
                "Layoutkoordinaten."
            )
        except BackendError as exc:
            st.warning(str(exc))
            st.caption(
                "PDF-Vorschau nicht freigegeben oder Original geändert. Der "
                "extrahierte Text bleibt separat verfügbar."
            )
    details(
        {
            "document_id": document["document_id"],
            "source_sha256": source_sha,
            "text_version": record.get("document_version"),
            "extraction_version": document.get("extraction_version"),
            "parser_version": document.get("parser_version"),
        },
        title="Dokumentversion und Extraktion",
    )


def evidence_card(path, finding_id):
    evidence = api_client.request_backend("GET", path + "/findings/" + finding_id + "/evidence")
    st.subheader("Originalbeleg")
    if not evidence["matched"]:
        st.warning(
            "Keine eindeutige verifizierte Originaltextstelle. Keine "
            "Markierung oder Bestätigung möglich."
        )
    else:
        st.caption(
            f"Seite {evidence['page']} · {evidence.get('chapter') or 'Kapitel nicht bestimmt'} "
            f"· Zeichen {evidence['source_start']}–{evidence['source_end']}"
        )
        st.text("Originalzitat: " + evidence["quote"])
        with st.expander("Textkontext", expanded=True):
            st.text(evidence["original_text"])
    st.caption(
        "Offsets beziehen sich auf den extrahierten Seitentext. Ein "
        "Texttreffer beweist keine fachliche Richtigkeit."
    )
    details(
        {
            k: evidence.get(k)
            for k in (
                "document_id",
                "document_version",
                "source_sha256",
                "block_id",
                "extraction_warnings",
            )
        },
        title="Belegversion und Zuordnung",
    )


def finding_card(path, finding, feedback):
    with st.container(border=True):
        status_badges(finding.get("kind"), finding.get("evidence_status"))
        st.text(finding.get("description", "Befund ohne Beschreibung"))
        st.text(finding.get("rationale", "Keine Begründung vorhanden"))
        if finding.get("conflict"):
            st.warning("Widersprechende Perspektive vorhanden. Menschliche Klärung erforderlich.")
        st.caption(
            f"Seite: {finding.get('page') or 'nicht zugeordnet'} "
            f"· Kriterium: {finding['criterion_id']} · Erzeugendes Modell: "
            f"{finding.get('model_id') or finding.get('model') or 'nicht ausgewiesen'}"
        )
        st.caption(
            "Menschliche Befundaktion: "
            + (feedback.get(finding["finding_id"], {}).get("action") or "noch offen")
        )
        st.caption(
            f"Gegenprüfendes Modell: {finding.get('reviewer_model') or 'nicht ausgewiesen'} "
            f"· Verifikation: {finding.get('verification_status') or 'nicht ausgewiesen'}"
        )
        if st.button("Textbeleg öffnen", key="evidence_" + finding["finding_id"]):
            st.session_state.evidence_finding = finding["finding_id"]
        with st.expander("Gegenbelege, Modellherkunft und Verifikation"):
            for key in (
                "strengths",
                "weaknesses",
                "quote",
                "supporting_passages",
                "counterevidence",
                "verification_rounds",
                "scientific_claims",
                "relationships",
            ):
                if finding.get(key):
                    st.text(key)
                    st.text(str(finding[key]))


def review_explorer(path, record, comparison):
    rows = comparison["criteria"]
    st.subheader("Wissenschaftlicher Arbeitsbereich")
    layout = st.radio(
        "Arbeitsbereich anzeigen als",
        ["Registerkarten", "Drei Spalten"],
        index=1 if st.session_state.get("workspace_layout") == "Drei Spalten" else 0,
        horizontal=True,
        key=path + "_layout",
    )

    def orientation():
        st.subheader("Orientierung")
        st.caption("Kriterien aus dem aktiven Bewertungskatalog")
        for criterion in record["profile"]["criteria"]:
            st.text(criterion["id"] + " · " + criterion["description"])
        st.caption(
            "Kapitel werden nur anhand extrahierter Textstruktur erkannt. "
            "Keine bestätigte PDF-Inhaltsverzeichnis-Zuordnung."
        )

    def review():
        focus = st.selectbox(
            "Kriterium anzeigen",
            ["Alle", *[r["criterion_id"] for r in rows]],
            key="review_workspace_focus",
        )
        query = st.text_input("Befunde durchsuchen", key=path + "_finding_search", max_chars=200)
        kinds = sorted(
            {
                f["kind"]
                for r in rows
                if r.get("ai")
                for f in [r["ai"], *r["ai"].get("supplemental", [])]
            }
        )
        kind = st.selectbox("Befundkategorie", ["Alle", *kinds], format_func=label)
        order = st.selectbox("Sortierung", ["Bewertungskatalog", "Seitenfolge"])
        feedback = {f["finding_id"]: f for f in comparison.get("finding_feedback", [])}
        visible = []
        for row in rows:
            if focus != "Alle" and row["criterion_id"] != focus:
                continue
            with st.expander(
                row["criterion_id"] + " · " + label(row["status"]), expanded=focus != "Alle"
            ):
                left, right = st.columns(2)
                with left:
                    st.write("**Menschliche Erstbewertung**")
                    human = row.get("human") or {}
                    status_badges(human.get("judgment", "NOT_ASSESSABLE"))
                    for key in (
                        "observations",
                        "strengths",
                        "weaknesses",
                        "rationale",
                        "open_questions",
                    ):
                        if human.get(key):
                            st.text(human[key])
                    st.caption(
                        "Status vergleicht Bewertungskategorien. Semantische Übereinstimmung "
                        "und wissenschaftliche Qualität sind dadurch nicht nachgewiesen."
                    )
                with right:
                    st.write("**Unabhängige KI-Zweitbewertung**")
                    if row.get("ai"):
                        status_badges(row["ai"]["judgment"])
                        st.text(row["ai"]["description"])
                        st.text(row["ai"]["rationale"])
                    else:
                        st.text("Kein bewertbarer KI-Befund vorhanden.")
            if row.get("ai"):
                visible.extend([row["ai"], *row["ai"].get("supplemental", [])])
        visible = [
            f
            for f in visible
            if (kind == "Alle" or f["kind"] == kind)
            and (
                not query
                or query.casefold() in (f["description"] + " " + f["rationale"]).casefold()
            )
        ]
        if order == "Seitenfolge":
            visible.sort(key=lambda f: (f.get("page") or 10**9, f["criterion_id"]))
        if not visible:
            empty_state(
                "Keine passenden Befunde",
                "Filter ändern. Daraus folgt keine Aussage zur Qualität der Arbeit.",
            )
        for finding in visible:
            finding_card(path, finding, feedback)
        allowed = {
            f["finding_id"]
            for r in rows
            if r.get("ai")
            for f in [r["ai"], *r["ai"].get("supplemental", [])]
        }
        selected = st.session_state.get("evidence_finding")
        if selected in allowed:
            evidence_card(path, selected)
        st.caption(
            "Beide Einschätzungen sind neutral dargestellt. Auch Modellkonsens"
            " belegt keine wissenschaftliche Richtigkeit."
        )

    areas = (
        st.columns([1, 2, 2], gap="medium")
        if layout == "Drei Spalten"
        else st.tabs(["Kriterien & Orientierung", "Dokument & Original", "Vergleich & Befunde"])
    )
    for area, renderer in zip(
        areas, (orientation, lambda: document_reader(path, record), review), strict=True
    ):
        with area:
            renderer()
