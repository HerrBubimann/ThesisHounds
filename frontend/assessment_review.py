"""Human-first assessment UI. API also enforces every disclosure gate."""

import json

import streamlit as st

from frontend.api_client import BackendError, request_backend

BASE = "/api/v1/assessments"


def render_assessment_review():
    st.subheader("Unabhängige Begutachtung")
    st.caption(
        "Beispielprofile, keine offiziellen DHBW-Kriterien. Keine echten Arbeiten hochladen."
    )
    try:
        if "assessment_id" not in st.session_state:
            if st.button("Kontrollierte Pilotdatei auswählen"):
                st.session_state.pilot_catalog = request_backend("GET", BASE + "/pilot-documents")
                st.rerun()
            pilot = st.session_state.get("pilot_catalog", {})
            selected_document = "synthetic-demo"
            if pilot:
                documents = pilot.get("documents", [])
                if not documents or not pilot.get("profile_id"):
                    st.info("Geprüfte Pilotdateien oder bestätigter Experimentkatalog fehlen.")
                    return
                selected_document = st.selectbox(
                    "Geprüfte Test-PDF", [d["document_id"] for d in documents]
                )
                st.caption("Operatorgeprüfte Datei; keine Freigabe vertraulicher Arbeiten.")
            work_type = st.selectbox("Arbeitstyp", ["PA1"] if pilot else ["PA1", "PA2", "BA"])
            program = st.selectbox(
                "Studiengang",
                ["data_science_ai"] if pilot else ["data_science_ai", "wirtschaftsinformatik"],
                format_func=lambda value: (
                    "Data Science und KI" if value == "data_science_ai" else "Wirtschaftsinformatik"
                ),
            )
            cohort = st.selectbox(
                "Jahrgang für die Richtlinienvorschau",
                ["DS23", "DS24", "DS25"]
                if program == "data_science_ai"
                else ["WI23", "WI24", "WI25"],
                index=None,
            )
            if st.button(
                "Pilotbegutachtung anlegen" if pilot else "Synthetische Begutachtung anlegen"
            ):
                record = request_backend(
                    "POST",
                    BASE,
                    json={
                        "work_type": work_type,
                        "profile_id": pilot["profile_id"]
                        if pilot
                        else work_type.lower() + "-example",
                        "document_id": selected_document,
                        "program": program,
                        "cohort": cohort,
                    },
                )
                st.session_state.assessment_id = record["id"]
                st.rerun()
            return
        path = f"{BASE}/{st.session_state.assessment_id}"
        record = request_backend("GET", path)
        pilot_document = record.get("document_id", "synthetic-demo") != "synthetic-demo"
        real_mode = record.get("security", {}).get("inference") == "LOCAL_OLLAMA_PILOT"
        st.caption(f"{record['state']} · Infrastruktur: {record['deployment_mode']}")
        st.caption(
            f"Schutzklasse: {record.get('classification', 'RESTRICTED')} · "
            f"Sperrvermerk erkannt: {record.get('sperrvermerk_detected', False)} · "
            "Zugriff: synthetische Einzelsitzung · Speicherung: zeitlich begrenzt"
        )
        st.caption(
            f"Dokument: {record.get('document_classification', 'PUBLIC')} "
            + (
                "(operatorgeprüfte Pilot-PDF)"
                if pilot_document
                else "(servereigene synthetische Fixture)"
            )
        )
        st.write("Öffentliche Recherche: deaktiviert · KI-Punktevergabe: deaktiviert")
        security = record.get("security", {})
        st.caption(
            (
                "Autorisierte lokale Modellkennungen: "
                if real_mode
                else "Autorisierte Mock-Modellkennungen: "
            )
            + ", ".join(security.get("authorized_demo_models", []))
        )
        st.caption(
            f"Modus: {security.get('mode', 'DEVELOPMENT')} · "
            f"Inferenz: {security.get('endpoint', 'in-process://demo')} · "
            "Lokal importierte öffentliche Metadaten · Hochschulfreigabe ausstehend"
        )
        if record.get("cohort"):
            render_rules(record.get("institutional_rules", {}))
        st.caption(
            "Inferenzmodus: Lokaler Ollama-Pilot; Laufstatus separat prüfen."
            if real_mode
            else "Inferenzmodus: Mock; keine reale Modellinferenz."
        )
        with st.expander(
            "Pilot-PDF lesen" if pilot_document else "Synthetisches Testdokument lesen"
        ):
            document = request_backend("GET", path + "/document")
            for page, text in document["pages"].items():
                st.text(f"Seite {page}: {text}")
        if st.button("Begutachtungsstatus aktualisieren"):
            st.rerun()
        if st.button(
            "Weitere Pilotbegutachtung" if pilot_document else "Weitere synthetische Begutachtung"
        ):
            del st.session_state.assessment_id
            st.session_state.pop("evidence_finding", None)
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
    if record.get("cohort"):
        render_academic(path, record)
    for row in comparison["criteria"]:
        with st.expander(f"{row['criterion_id']} · {row['status']}"):
            left, right = st.columns(2)
            left.write("Menschliche Erstbewertung")
            left.text(json.dumps(row["human"], ensure_ascii=False, indent=2))
            right.write("Unabhängige KI-Zweitbewertung")
            right.text(json.dumps(row["ai"], ensure_ascii=False, indent=2))
            value = row.get("ai")
            for finding in [value, *value.get("supplemental", [])] if value else []:
                if finding.get("conflict"):
                    st.warning("Ungeklärter Gegenbefund: fachliche Prüfung erforderlich.")
                if st.button("Textbeleg öffnen", key="evidence_" + finding["finding_id"]):
                    st.session_state.evidence_finding = finding["finding_id"]
    if st.session_state.get("evidence_finding"):
        evidence = request_backend(
            "GET", path + "/findings/" + st.session_state.evidence_finding + "/evidence"
        )
        st.subheader("Evidence Explorer")
        if evidence["matched"]:
            st.caption(
                f"Seite {evidence['page']} · Kapitel {evidence['chapter']} · {evidence['block_id']}"
            )
            st.text(evidence["original_text"])
            st.text("Originalzitat: " + evidence["quote"])
        else:
            st.warning("Keine verifizierte Originaltextstelle; Referenz wird nicht angezeigt.")
        st.caption("Texttreffer beweisen keine fachliche Richtigkeit. Extraktion: Textmodus.")
    st.caption(
        "Vergleichsstatus vergleicht Einschätzungen; er beweist keine sachliche Richtigkeit."
    )
    render_finding_feedback(path, comparison, writable=record["state"] != "FINALIZED")
    with st.expander("Analyseherkunft und Ressourcen"):
        if st.button("Geschützte Provenance anzeigen"):
            st.text(
                json.dumps(
                    request_backend("GET", path + "/provenance"), ensure_ascii=False, indent=2
                )
            )
    for entry in comparison["discussion"]:
        st.text(f"Frage: {entry['question']}\nPrüfung: {entry['answer']}")
    if record["state"] == "FINALIZED":
        st.text(request_backend("GET", path + "/draft")["text"])
        return
    ids = [row["criterion_id"] for row in comparison["criteria"]]
    with st.form("criterion_discussion"):
        criterion = st.selectbox("Kriterium für die Diskussion", ids)
        question = st.text_area("Frage / Gegenargument")
        if st.form_submit_button("Diskutieren"):
            try:
                request_backend(
                    "POST",
                    path + "/discussion",
                    json={"criterion_id": criterion, "question": question},
                )
            except BackendError as exc:
                st.error(str(exc))
            else:
                st.rerun()
    if not comparison["discussion"]:
        st.info(
            "Freie Diskussionsfragen und menschliche Bewertungen sind RESTRICTED. "
            "Im Entwicklungsmodus ist die Weitergabe an Modelle gesperrt."
        )
        if st.button("Ohne KI-Diskussion menschlich prüfen"):
            request_backend("POST", path + "/manual-review", json={"confirmed": True})
            st.rerun()

    if comparison["discussion"]:
        with st.form("criterion_decision"):
            criterion = st.selectbox("Menschliche Entscheidung für", ids)
            include = st.selectbox("KI-Befund übernehmen?", ["Ja", "Nein"], index=None)
            extras = [
                f
                for row in comparison["criteria"]
                for f in (row.get("ai") or {}).get("supplemental", [])
            ]
            selected_extras = st.multiselect(
                "Zusätzliche Befunde des gewählten Kriteriums übernehmen",
                [f["finding_id"] for f in extras],
                format_func=lambda key: next(
                    f["criterion_id"] + ": " + f["description"]
                    for f in extras
                    if f["finding_id"] == key
                ),
            )
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
                            "include_finding_ids": selected_extras,
                        },
                    )
                    st.rerun()
    if record["state"] == "READY_FOR_FINALIZATION":
        st.text(request_backend("GET", path + "/draft")["text"])
        if st.button("Gutachtenentwurf abschließend menschlich freigeben"):
            request_backend("POST", path + "/finalize", json={"confirmed": True})
            st.rerun()


def render_finding_feedback(path, comparison, *, writable):
    with st.expander("Strukturiertes Befundfeedback"):
        st.caption(
            "Versioniert und lokal. Kein Training; Befundfeedback ersetzt keine Schlussfreigabe."
        )
        for entry in comparison.get("finding_feedback", []):
            st.text(json.dumps(entry, ensure_ascii=False))
        if not writable:
            return
        findings = [
            f
            for row in comparison["criteria"]
            if row.get("ai")
            for f in [row["ai"], *row["ai"].get("supplemental", [])]
        ]
        if not findings:
            st.info("Keine KI-Befunde für Feedback vorhanden.")
            return
        with st.form("finding_feedback"):
            finding_id = st.selectbox(
                "Befund",
                [f["finding_id"] for f in findings],
                format_func=lambda key: next(
                    f["criterion_id"] + ": " + f["description"]
                    for f in findings
                    if f["finding_id"] == key
                ),
            )
            actions = {
                "Akzeptieren": "ACCEPT",
                "Ablehnen": "REJECT",
                "Korrigieren": "CORRECT",
                "Ergänzen": "SUPPLEMENT",
                "Nicht relevant": "NOT_RELEVANT",
                "Nicht ausreichend belegt": "INSUFFICIENT_EVIDENCE",
            }
            reasons = {
                "Falsche fachliche Aussage": "WRONG_STATEMENT",
                "Fehlender Kontext": "MISSING_CONTEXT",
                "Unzutreffendes Kriterium": "WRONG_CRITERION",
                "Fehlerhafte Quellenprüfung": "SOURCE_ERROR",
                "Unberechtigte Kritik": "UNJUSTIFIED_CRITICISM",
                "Unzureichende Evidenz": "INSUFFICIENT_EVIDENCE",
                "Doppelter Befund": "DUPLICATE",
            }
            action = st.selectbox("Befundaktion", list(actions), index=None)
            reason = st.selectbox("Feedbackgrund", list(reasons), index=None)
            rationale = st.text_area("Feedbackbegründung")
            correction = st.text_area("Korrektur / Ergänzung")
            if st.form_submit_button("Befundfeedback speichern"):
                if action is None:
                    st.warning("Befundaktion ausdrücklich auswählen.")
                else:
                    request_backend(
                        "POST",
                        path + "/finding-feedback",
                        json={
                            "finding_id": finding_id,
                            "action": actions[action],
                            "reason": reasons.get(reason),
                            "rationale": rationale,
                            "correction": correction,
                        },
                    )
                    st.rerun()


def render_rules(resolved):
    with st.expander("DHBW Mosbach: Richtlinien, Herkunft und Gültigkeit"):
        st.warning(
            "Richtlinienvorschau: keine aktivierten offiziellen Bewertungskriterien. "
            "Die Begutachtungsdemo verwendet ausdrücklich Beispielkriterien."
        )
        for source in resolved.get("sources", []):
            st.text(f"{source['title']} · {source['version']} · {source['release']}")
            st.link_button("Öffentliche Originalquelle öffnen", source["original_url"])
        for conflict in resolved.get("conflicts", []):
            st.warning(
                f"Regelkonflikt {conflict['key']}: {conflict['status']} – "
                "menschliche Klärung erforderlich."
            )
        if not resolved.get("profile"):
            st.info(
                "Für diese Kombination aus Studiengang, Jahrgang und Arbeitstyp "
                "liegt kein eindeutiges freigegebenes Profil vor."
            )


def render_academic(path, record):
    checks = request_backend("GET", path + "/academic-checks")
    with st.expander("Lokale Formalien- und Quellenprüfung"):
        st.caption(
            "Erst nach Abschluss der unabhängigen Bewertungen sichtbar. "
            "Keine automatische Notenwirkung. NOT_FOUND betrifft nur lokale Teilbestände."
        )
        rows = checks["formal"]["checks"]
        for row in rows:
            st.text(
                f"{row['criterion_id']}: {row['status']} · {row['reason']} · "
                f"{row['source_id']}, {row['source_location']}"
            )
        references = checks["citations"]["references"]
        for row in references:
            st.text(f"Seite {row['entry']['page']}: {row['entry']['raw']}")
            st.text(", ".join(row["statuses"]))
            if st.button("Originalstelle der Quelle öffnen", key="citation_" + row["finding_id"]):
                document = request_backend("GET", path + "/document")
                entry = row["entry"]
                text = document["pages"].get(str(entry["page"]), "")
                if text[entry["start"] : entry["end"]] == entry["raw"]:
                    st.text(text)
                else:
                    st.warning("Originalstelle nicht mehr eindeutig verifizierbar.")
        if not references:
            st.info(
                "Keine unterstützten Literaturverzeichniseinträge extrahiert; "
                "daraus folgt kein Nachweis fehlender Quellen."
            )
        for decision in checks.get("decisions", []):
            st.text(f"{decision['finding_id']}: {decision['decision']} · {decision['rationale']}")
        if record["state"] not in {"FINALIZED", "CANCELLED", "FAILED"}:
            choices = [r["finding_id"] for r in [*rows, *references]]
            if choices:
                with st.form("academic_decision"):
                    finding = st.selectbox("Lokalen Prüfbefund auswählen", choices)
                    decision = st.selectbox(
                        "Menschliche Bestätigung", ["ACCEPTED", "REJECTED"], index=None
                    )
                    rationale = st.text_area("Begründung zum lokalen Prüfbefund")
                    if st.form_submit_button("Lokale Prüfentscheidung speichern"):
                        if decision is None or not rationale.strip():
                            st.warning("Entscheidung und eigene Begründung erforderlich.")
                        else:
                            request_backend(
                                "POST",
                                path + "/academic-decisions",
                                json={
                                    "finding_id": finding,
                                    "decision": decision,
                                    "rationale": rationale,
                                },
                            )
                            st.rerun()
