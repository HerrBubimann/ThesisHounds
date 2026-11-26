"""Minimal local dashboard, with no document storage or agent logic."""

import streamlit as st

from frontend.api_client import BackendError, request_backend
from frontend.assessment_review import render_assessment_review
from frontend.control_center import render_control_center

st.set_page_config(page_title="ThesisHounds", page_icon="🐾", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background: #0e0e10; }
    .block-container { max-width: 1150px; padding-top: 2.5rem; }
    h1 { border-left: 6px solid #dc2626; padding-left: 1rem; }
    [data-testid="stMetric"] { border: 1px solid #333; padding: 1rem; border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("ThesisHounds")
st.caption("Lokale KI · Nachvollziehbare Begutachtung · Menschliche Entscheidung")
st.write(
    "Infrastruktur für die vertrauliche Analyse wissenschaftlicher Arbeiten. "
    "Dieses Dashboard prüft die Systemverbindung und ermöglicht einfache Modelltests."
)

if st.button("Systemstatus aktualisieren"):
    st.rerun()

backend_ok = False
status = {}
models = []
try:
    health = request_backend("GET", "/health")
    backend_ok = health.get("status") == "ok"
    status = request_backend("GET", "/api/v1/status")
    if status.get("ollama") == "available":
        models = request_backend("GET", "/api/v1/models").get("models", [])
except BackendError as exc:
    st.error(str(exc))

left, middle, right = st.columns(3)
left.metric("Backend", "Verfügbar" if backend_ok else "Nicht verfügbar")
middle.metric("Ollama", "Verfügbar" if status.get("ollama") == "available" else "Nicht verfügbar")
right.metric("Konfiguriertes Modell", status.get("model", "Unbekannt"))

if status:
    if status.get("model_available"):
        st.success(status["detail"])
    else:
        st.warning(status["detail"])

with st.expander("Lokal verfügbare Modelle", expanded=True):
    if models:
        st.dataframe(
            [
                {
                    "Modell": model["name"],
                    "Größe (GiB)": round(model["size"] / 1024**3, 2),
                    "Digest": model["digest"],
                }
                for model in models
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("Keine lokalen Modelle abrufbar. Bitte die Modellbereitstellung prüfen.")

st.subheader("LLM-Verbindung testen")
st.caption("Nur freigegebene Testtexte verwenden. Antworten müssen fachlich geprüft werden.")
with st.form("llm_test"):
    prompt = st.text_area("Testanfrage", max_chars=16000, height=140)
    submitted = st.form_submit_button(
        "Anfrage senden", disabled=not status.get("model_available", False), type="primary"
    )
if submitted:
    if not prompt.strip():
        st.warning("Bitte eine Testanfrage eingeben.")
    else:
        with st.spinner("Das lokale Modell antwortet …"):
            try:
                result = request_backend("POST", "/api/v1/chat", json={"prompt": prompt})
                st.subheader("Modellantwort")
                # Render model output as text; never execute or interpret HTML from a model.
                st.text(result["answer"])
                st.caption(f"Modell: {result['model']}")
            except BackendError as exc:
                st.error(str(exc))

st.divider()
st.subheader("Dokumente · In Vorbereitung")
st.file_uploader("PDF-Upload (noch nicht verfügbar)", type=["pdf"], disabled=True)
st.caption("Die unabhängige Begutachtung unten verwendet ein festes synthetisches Testdokument.")

st.divider()
if backend_ok:
    render_assessment_review()
    st.fragment(run_every="5s")(render_control_center)()
