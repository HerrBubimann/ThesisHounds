"""Explicit navigation and session-scoped review selection, no browser persistence."""

import streamlit as st

WORK_PAGES = (
    "Dashboard",
    "Neue Begutachtung",
    "Meine Begutachtungen",
    "Quellenprüfung",
    "DHBW-Richtlinien",
)
TECH_PAGES = (
    "Agent Control Center",
    "Model Center",
    "Evaluation Lab",
    "Security Center",
    "Systemstatus",
    "Einstellungen",
)


def navigate(page):
    st.session_state.page = page


def select_assessment(key):
    if st.session_state.get("assessment_id") != key:
        for name in ("evidence_finding", "review_workspace_focus"):
            st.session_state.pop(name, None)
    st.session_state.assessment_id = key
    navigate("Meine Begutachtungen")


def sidebar(security):
    page = st.session_state.get("page", "Dashboard")
    if page not in (*WORK_PAGES, *TECH_PAGES):
        page = "Dashboard"
    with st.sidebar:
        st.markdown('<div class="th-brand">Thesis<span>Hounds</span></div>', unsafe_allow_html=True)
        st.caption("Wissenschaftliche Begutachtung")
        st.divider()
        st.caption("ARBEITSBEREICH")
        for item in WORK_PAGES:
            st.button(
                item,
                key="nav_" + item,
                type="primary" if page == item else "tertiary",
                width="stretch",
                on_click=navigate,
                args=(item,),
            )
        st.divider()
        with st.expander("Technik & Verwaltung", expanded=page in TECH_PAGES):
            for item in TECH_PAGES:
                st.button(
                    item,
                    key="nav_" + item,
                    type="primary" if page == item else "tertiary",
                    width="stretch",
                    on_click=navigate,
                    args=(item,),
                )
        st.divider()
        if security:
            st.caption(
                "DEVELOPMENT · "
                + (
                    "lokaler Modellpilot"
                    if security.get("inference") == "LOCAL_OLLAMA_PILOT"
                    else "Mock-Inferenz"
                )
            )
            st.caption("Local-Only · externe Recherche gesperrt")
            st.caption(
                "Gemeinsame Demo-Identität; keine Hochschulanmeldung. Keine vertraulichen Arbeiten."
            )
        else:
            st.caption("Verbindung unterbrochen · Betriebsstatus unbekannt")
        st.caption("Prototyp · kein offizielles DHBW-Produkt")
    return page
