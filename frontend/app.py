"""ThesisHounds shell. FastAPI owns workflow and disclosure policy."""

import streamlit as st

from frontend import api_client, pages
from frontend.api_client import BackendError
from frontend.assessment_review import render_assessment_review
from frontend.control_center import render_control_center
from frontend.design import install_design, page_header
from frontend.navigation import sidebar

st.set_page_config(page_title="ThesisHounds · Begutachtung", page_icon="TH", layout="wide")
install_design()
security = {}
connection_error = None
try:
    security = api_client.request_backend("GET", "/api/v1/security/status")
except BackendError as exc:
    connection_error = str(exc)
page = sidebar(security)
st.title("ThesisHounds")
st.caption("Wissenschaftlich prüfen. Belege nachvollziehen. Menschlich entscheiden.")
if security:
    st.info(
        "Testbetrieb · ausschließlich synthetische oder operatorgeprüfte "
        "öffentliche Dokumente. Keine vertraulichen Arbeiten. "
        "Hochschulfreigabe ausstehend."
    )
if connection_error:
    st.error(connection_error)
    st.write(
        "Der aktuelle Bestand kann nicht geladen werden. Bereits "
        "eingegebene Sitzungsentwürfe bleiben bis zum Sitzungsende "
        "erhalten."
    )
    if st.button("Verbindung erneut prüfen"):
        st.rerun()
else:
    try:
        if page == "Dashboard":
            pages.dashboard()
        elif page == "Neue Begutachtung":
            pages.creation_wizard()
        elif page == "Meine Begutachtungen":
            if st.session_state.get("assessment_id"):
                render_assessment_review()
            else:
                page_header(
                    "Meine Begutachtungen", "Zugängliche Fälle des gemeinsamen Demo-Bestands."
                )
                pages.assessment_list(api_client.request_backend("GET", pages.BASE))
        elif page == "Quellenprüfung":
            pages.sources()
        elif page == "DHBW-Richtlinien":
            pages.knowledge()
        elif page == "Agent Control Center":
            page_header(
                "Agent Control Center",
                "Tatsächliche Laufdaten; Legacy-Demo und Assessment getrennt.",
                area="Technik",
            )
            st.info(
                "Diese Live-Graphen gehören zur Legacy-Demo A–D. "
                "Assessment-Herkunft ist nach Vergleichsfreigabe im jeweiligen "
                "Arbeitsbereich verfügbar. Master-/Supervisor-Aktivität wird "
                "daraus nicht abgeleitet."
            )
            render_control_center()
        elif page == "Model Center":
            pages.models()
        elif page == "Evaluation Lab":
            pages.evaluation()
        elif page == "Security Center":
            pages.security_center(security)
        elif page == "Systemstatus":
            pages.system_status()
        elif page == "Einstellungen":
            pages.settings()
    except BackendError as exc:
        st.error(str(exc))
        st.caption(
            "Aktion nicht abgeschlossen. Keine automatische Wiederholung einer"
            " schreibenden Anfrage. Bei Zeitüberschreitung erst den Status "
            "prüfen."
        )
        if st.button("Ansicht erneut laden"):
            st.rerun()
