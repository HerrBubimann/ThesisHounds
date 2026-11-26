"""Human-first assessment UI. API also enforces every disclosure gate."""

import json

import streamlit as st

from frontend.api_client import BackendError, request_backend

BASE = "/api/v1/assessments"


def render_assessment_review():
    st.subheader("Unabhängige Begutachtung · Synthetischer MVP")
    st.caption(
        "Beispielprofile, keine offiziellen DHBW-Kriterien. Keine echten Arbeiten hochladen."
    )
    try:
        if "assessment_id" not in st.session_state:
            work_type = st.selectbox("Arbeitstyp", ["PA1", "PA2", "BA"])
            if st.button("Synthetische Begutachtung anlegen"):
                record = request_backend(
                    "POST",
                    BASE,
                    json={
                        "work_type": work_type,
                        "profile_id": work_type.lower() + "-example",
                    },
                )
                st.session_state.assessment_id = record["id"]
                st.rerun()
            return
        path = f"{BASE}/{st.session_state.assessment_id}"
        record = request_backend("GET", path)
        st.caption(f"{record['state']} · Infrastruktur: {record['deployment_mode']}")
        st.write("Öffentliche Recherche: deaktiviert · KI-Punktevergabe: deaktiviert")
        with st.expander("Synthetisches Testdokument lesen"):
            document = request_backend("GET", path + "/document")
            for page, text in document["pages"].items():
                st.text(f"Seite {page}: {text}")
        if st.button("Begutachtungsstatus aktualisieren"):
            st.rerun()
        if st.button("Weitere synthetische Begutachtung"):
            del st.session_state.assessment_id
            st.rerun()
        if record["state"] == "CANCELLED":
            st.info("Begutachtung abgebrochen.")
            return
        if record["state"] not in {"FINALIZED", "FAILED"} and st.button("Begutachtung abbrechen"):
            request_backend("POST", path + "/cancel")
            st.rerun()
        st.progress(
            record["criteria_completed"] / record["criteria_total"],
            text=f"KI-Bearbeitung: {record['ai_state']}",
        )
        if record["ai_state"] == "PENDING" and st.button("Unabhängige KI-Bewertung starten"):
            request_backend("POST", path + "/ai-review")
            st.rerun()
        if record["ai_state"] == "FAILED":
            st.error(
                "KI-Bewertung fehlgeschlagen. Modelle und Ressourcen prüfen; neue Demo anlegen."
            )
            return
        if not record["human_completed"]:
            render_human(path, record["profile"]["criteria"])
        elif not record["ai_released"]:
            st.info(
                "Menschliche Erstbewertung unveränderlich freigegeben. KI-Inhalte noch gesperrt."
            )
            if record["ai_state"] == "COMPLETED" and st.button(
                "Beide Bewertungen zum Vergleich öffnen"
            ):
                request_backend("POST", path + "/release", json={"confirmed": True})
                st.rerun()
        else:
            render_comparison(path, record)
    except BackendError as exc:
        st.error(str(exc))


def render_human(path, criteria):
    st.write("Menschliche Erstbewertung")
    st.caption("Alle Kriterien bearbeiten; bei fehlenden Informationen NOT_ASSESSABLE wählen.")
    uploaded = st.file_uploader(
        "Optional: ausgefüllte strukturierte Erstbewertung (JSON)", type=["json"]
    )
    with st.form("independent_human_review"):
        rows = []
        for criterion in criteria:
            st.write(criterion["description"])
            key = f"{path}_{criterion['id']}"
            judgment = st.selectbox(
                "Einschätzung",
                ["POSITIVE", "MIXED", "NEGATIVE", "NOT_ASSESSABLE"],
                index=None,
                key=key + "judgment",
            )
            rows.append(
                {
                    "criterion_id": criterion["id"],
                    "judgment": judgment,
                    "observations": st.text_area("Beobachtungen", key=key + "observations"),
                    "strengths": st.text_area("Stärken", key=key + "strengths"),
                    "weaknesses": st.text_area("Kritikpunkte", key=key + "weaknesses"),
                    "rationale": st.text_area("Begründung", key=key + "rationale"),
                    "open_questions": st.text_area("Offene Fragen", key=key + "questions"),
                }
            )
        confirmed = st.checkbox("Ich schließe meine unabhängige Erstbewertung ausdrücklich ab.")
        if st.form_submit_button("Erstbewertung unveränderlich freigeben"):
            if not confirmed:
                st.warning("Ausdrückliche Freigabe erforderlich.")
                return
            payload = {"criteria": rows, "release": True}
            if uploaded:
                try:
                    payload = json.loads(uploaded.getvalue())
                    payload["release"] = True
                except (ValueError, TypeError):
                    st.error("Ungültiges JSON-Bewertungsobjekt.")
                    return
            request_backend("POST", path + "/human-review", json=payload)
            st.rerun()


def render_comparison(path, record):
    comparison = request_backend("GET", path + "/comparison")
    for row in comparison["criteria"]:
        with st.expander(f"{row['criterion_id']} · {row['status']}"):
            left, right = st.columns(2)
            left.write("Menschliche Erstbewertung")
            left.text(json.dumps(row["human"], ensure_ascii=False, indent=2))
            right.write("Unabhängige KI-Zweitbewertung")
            right.text(json.dumps(row["ai"], ensure_ascii=False, indent=2))
    st.caption(
        "Vergleichsstatus vergleicht Einschätzungen; er beweist keine sachliche Richtigkeit."
    )
    for entry in comparison["discussion"]:
        st.text(f"Frage: {entry['question']}\nKI-Vorschlag: {entry['answer']}")
    if record["state"] == "FINALIZED":
        st.text(request_backend("GET", path + "/draft")["text"])
        return
    ids = [row["criterion_id"] for row in comparison["criteria"]]
    with st.form("criterion_discussion"):
        criterion = st.selectbox("Kriterium für die Diskussion", ids)
        question = st.text_area("Frage / Gegenargument")
        if st.form_submit_button("Diskutieren"):
            request_backend(
                "POST", path + "/discussion", json={"criterion_id": criterion, "question": question}
            )
            st.rerun()
    if comparison["discussion"]:
        with st.form("criterion_decision"):
            criterion = st.selectbox("Menschliche Entscheidung für", ids)
            include = st.selectbox("KI-Befund übernehmen?", ["Ja", "Nein"], index=None)
            conclusion = st.text_area("Menschliche Schlussfolgerung")
            rationale = st.text_area("Begründung der Entscheidung")
            if st.form_submit_button("Entscheidung versioniert speichern"):
                if include is None:
                    st.warning("Übernahmeentscheidung ausdrücklich auswählen.")
                else:
                    request_backend(
                        "POST",
                        path + "/decisions",
                        json={
                            "criterion_id": criterion,
                            "include_ai_finding": include == "Ja",
                            "conclusion": conclusion,
                            "rationale": rationale,
                        },
                    )
                    st.rerun()
    if record["state"] == "READY_FOR_FINALIZATION":
        st.text(request_backend("GET", path + "/draft")["text"])
        if st.button("Gutachtenentwurf abschließend menschlich freigeben"):
            request_backend("POST", path + "/finalize", json={"confirmed": True})
            st.rerun()
