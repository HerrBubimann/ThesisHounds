"""Human-first assessment UI. API also enforces every disclosure gate."""

import base64
import json

import streamlit as st

from frontend.api_client import BackendError, request_backend
from frontend.design import assessment_phase
from frontend.evidence import review_explorer

BASE = "/api/v1/assessments"


def render_assessment_review():
    st.subheader("Unabhängige Begutachtung")
    st.caption(
        "Beispielprofile, keine offiziellen DHBW-Kriterien. Keine echten Arbeiten hochladen."
    )
    try:
        if "assessment_id" not in st.session_state:
            from frontend.pages import creation_wizard

            creation_wizard()
            return
        path = f"{BASE}/{st.session_state.assessment_id}"
        record = request_backend("GET", path)
        assessment_phase(record)
        st.caption(
            "Bewertungen liegen nur im flüchtigen RAM. Ein Neustart verliert den Fall; "
            "Hashes sind kein Nachweis revisionssicherer Archivierung."
        )
        pilot_document = record.get("document_id", "synthetic-demo") != "synthetic-demo"
        real_mode = record.get("security", {}).get("inference") == "LOCAL_OLLAMA_PILOT"
        with st.expander("Betriebsmodus, Dokument und Datenschutz"):
            st.caption(f"{record['state']} · Infrastruktur: {record['deployment_mode']}")
            st.caption(
                f"Schutzklasse: {record.get('classification', 'RESTRICTED')} · "
                f"Sperrvermerk erkannt: {record.get('sperrvermerk_detected', False)} · "
                "Zugriff: gemeinsame synthetische Demo-Identit?t · Speicherung: zeitlich begrenzt"
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
        if record.get("human_completed"):
            render_document_security(path)
        st.caption(
            "Inferenzmodus: Lokaler Ollama-Pilot; Laufstatus separat prüfen."
            if real_mode
            else "Inferenzmodus: Mock; keine reale Modellinferenz."
        )
        if not record.get("ai_released"):
            from frontend.evidence import document_reader

            with st.expander("Dokument vor der unabhängigen Erstbewertung lesen"):
                document_reader(path, record)
        if st.button("Begutachtungsstatus aktualisieren"):
            st.rerun()
        if st.button(
            "Weitere Pilotbegutachtung" if pilot_document else "Weitere synthetische Begutachtung"
        ):
            del st.session_state.assessment_id
            st.session_state.pop("evidence_finding", None)
            st.rerun()
        with st.expander("Begutachtung aus dem Backend löschen"):
            st.caption(
                "Entfernt diesen flüchtigen Fall und seine Bewertungen. "
                "Der separat verwaltete öffentliche Pilotkatalog bleibt bestehen."
            )
            delete_confirmed = st.checkbox(
                "Diesen Fall einschließlich Bewertungen löschen", key=path + "_delete"
            )
            if st.button("Begutachtung endgültig löschen", disabled=not delete_confirmed):
                request_backend("DELETE", path)
                for name in list(st.session_state):
                    if name.startswith(path):
                        del st.session_state[name]
                st.session_state.pop("assessment_id", None)
                st.session_state.pop("evidence_finding", None)
                st.session_state.page = "Dashboard"
                st.rerun()
        if record["state"] == "CANCELLED":
            st.info("Begutachtung abgebrochen.")
            return
        if record["state"] not in {"FINALIZED", "FAILED"}:
            with st.expander("Begutachtung abbrechen"):
                confirmed_cancel = st.checkbox(
                    "Die laufende Begutachtung wirklich abbrechen", key=path + "_cancel"
                )
                if st.button("Begutachtung abbrechen", disabled=not confirmed_cancel):
                    request_backend("POST", path + "/cancel")
                    st.rerun()
        if record["ai_state"] == "RUNNING":
            render_active_status(path)
        elif record.get("ai_released"):
            st.caption(
                f"Abgeschlossene KI-Kriterien: {record['criteria_completed']} "
                f"von {record['criteria_total']}. Ausführungsstand, keine Qualitätsbewertung."
            )
        else:
            st.info(
                {
                    "PENDING": "KI-Analyse noch nicht gestartet.",
                    "COMPLETED": "KI-Analyse abgeschlossen. Ergebnisse bleiben bis zur "
                    "vollständigen Erstbewertung und Ihrer Freigabe gesperrt.",
                    "FAILED": "KI-Analyse fehlgeschlagen.",
                }.get(record["ai_state"], "KI-Analyse abgebrochen.")
            )
        manual = record.get("mode") == "MANUAL_ONLY"
        if manual:
            st.info("Rein menschliche Begutachtung ohne KI-Unterstützung.")
        if (
            not manual
            and record["ai_state"] == "PENDING"
            and st.button("Unabhängige KI-Bewertung starten")
        ):
            request_backend("POST", path + "/ai-review")
            st.rerun()
        if record["ai_state"] == "FAILED":
            st.error(
                "KI-Bewertung fehlgeschlagen. Modelle und Ressourcen prüfen; neue Demo anlegen."
            )
            return
        if not record["human_completed"]:
            if (
                record.get("human_import_pending")
                and path + "_import_preview" not in st.session_state
            ):
                st.session_state[path + "_import_preview"] = request_backend(
                    "GET", path + "/human-review/import-preview"
                )
            render_human(path, record["profile"]["criteria"])
        elif manual:
            render_manual_final(path, record)
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
    if st.button("Eigene Erstbewertung beginnen"):
        request_backend("POST", path + "/human-review/start")
        st.rerun()
    st.caption("Alle Kriterien bearbeiten; bei fehlenden Informationen NOT_ASSESSABLE wählen.")
    st.caption(
        "Nur Pflichtkriterien sind erforderlich. Keine Kritik erfinden: 'Keine wesentlichen "
        "Schwächen festgestellt' ist zulässig. Nicht anwendbare oder nicht ausreichend "
        "beurteilbare Aspekte mit eigener Begründung kennzeichnen. Formale Vollständigkeit "
        "beweist weder das Lesen noch das Verständnis der Arbeit."
    )
    preview = render_human_import(path)
    saved = st.session_state.get(path + "_human_draft", {})
    st.caption(
        "Entwurf nur in dieser Sitzung. Vor einem Seitenwechsel speichern;"
        " kein automatischer Backend-Speicher. Beim Sitzungsverlust geht "
        "der Entwurf verloren."
    )
    with st.form(path + "_independent_human_review"):
        rows = []
        for criterion in criteria:
            st.write(
                criterion["description"]
                + (" · Pflicht" if criterion.get("required", True) else " · Optional")
            )
            key = f"{path}_{criterion['id']}"
            previous = saved.get(criterion["id"], {})
            for field, suffix in (
                ("judgment", "judgment"),
                ("observations", "observations"),
                ("strengths", "strengths"),
                ("weaknesses", "weaknesses"),
                ("rationale", "rationale"),
                ("open_questions", "questions"),
            ):
                if key + suffix not in st.session_state and previous.get(field) is not None:
                    st.session_state[key + suffix] = previous[field]
            judgment = st.selectbox(
                "Einschätzung",
                ["POSITIVE", "MIXED", "NEGATIVE", "NOT_ASSESSABLE"],
                index=None,
                key=key + "judgment",
            )
            row = {
                "criterion_id": criterion["id"],
                "judgment": judgment,
                "observations": st.text_area("Beobachtungen", key=key + "observations"),
                "strengths": st.text_area("Stärken", key=key + "strengths"),
                "weaknesses": st.text_area("Kritikpunkte", key=key + "weaknesses"),
                "rationale": st.text_area("Begründung", key=key + "rationale"),
                "open_questions": st.text_area("Offene Fragen", key=key + "questions"),
                "references": st.text_input(
                    "Relevante Seiten oder Kapitel", key=key + "references"
                ),
            }
            if criterion.get("required", True) or any(
                row[field] for field in ("judgment", "observations", "rationale")
            ):
                rows.append(row)
        confirmed = st.checkbox(
            "Ich schließe meine unabhängige Erstbewertung ausdrücklich ab.",
            key=path + "_human_confirm",
        )
        import_confirmed = (
            st.checkbox(
                "Import, Kriterienzuordnung und meine ergänzten Bewertungen verbindlich geprüft",
                key=path + "_import_confirmed",
            )
            if preview
            else False
        )
        if st.form_submit_button("Entwurf in Sitzung speichern"):
            st.session_state[path + "_human_draft"] = {row["criterion_id"]: row for row in rows}
            st.success(
                "Entwurf in dieser Sitzung gespeichert. Noch keine Erstbewertung freigegeben."
            )
        if st.form_submit_button("Erstbewertung unveränderlich freigeben"):
            if not confirmed:
                st.warning("Ausdrückliche Freigabe erforderlich.")
                return
            payload = {"criteria": rows, "release": True}
            if preview:
                if not import_confirmed:
                    st.warning("Import ausdrücklich prüfen und bestätigen.")
                    return
                payload.update(import_id=preview["import_id"], import_confirmed=True)
            request_backend("POST", path + "/human-review", json=payload)
            st.session_state.pop(path + "_human_draft", None)
            st.rerun()


def render_human_import(path):
    uploaded = st.file_uploader(
        "Bereits ausgefüllte Erstbewertung lokal importieren",
        type=["json", "yaml", "pdf", "docx"],
        key=path + "_human_import",
    )
    allowed = st.checkbox(
        "Import enthält ausschließlich synthetische oder autorisierte öffentliche Testdaten",
        key=path + "_import_test_data",
    )
    if st.button("Importvorschau lokal extrahieren", disabled=not uploaded or not allowed):
        preview = request_backend(
            "POST",
            path + "/human-review/import-preview",
            json={
                "format": uploaded.name.rsplit(".", 1)[-1].lower(),
                "content_base64": base64.b64encode(uploaded.getvalue()).decode(),
                "synthetic_or_authorized_public_test_data": True,
            },
        )
        st.session_state[path + "_import_preview"] = preview
        st.session_state[path + "_import_confirmed"] = False
        for entry in preview["mapped"]:
            row = entry.get("form_values", {})
            for field, suffix in (
                ("judgment", "judgment"),
                ("observations", "observations"),
                ("rationale", "rationale"),
                ("strengths", "strengths"),
                ("weaknesses", "weaknesses"),
                ("open_questions", "questions"),
                ("references", "references"),
            ):
                if field in row:
                    st.session_state[f"{path}_{entry['criterion_id']}{suffix}"] = row[field]
        st.rerun()
    preview = st.session_state.get(path + "_import_preview")
    if preview:
        with st.expander("Originaltext, Extraktion und Kriterienzuordnung", expanded=True):
            st.text(preview["original_text"])
            st.json(
                {
                    k: preview[k]
                    for k in ("mapped", "unrecognized", "ambiguous", "missing_required", "warnings")
                }
            )
            st.caption("Keine KI-Ergänzung. PDF-/DOCX-Text muss im Formular selbst ergänzt werden.")
        if st.button("Import verwerfen und manuell fortfahren"):
            request_backend("DELETE", path + "/human-review/import-preview")
            for entry in preview["mapped"]:
                prefix = f"{path}_{entry['criterion_id']}"
                for key in list(st.session_state):
                    if key.startswith(prefix):
                        del st.session_state[key]
            st.session_state.pop(path + "_human_draft", None)
            st.session_state.pop(path + "_import_preview", None)
            st.session_state.pop(path + "_import_confirmed", None)
            st.rerun()
    return preview


def render_manual_final(path, record):
    if record["state"] == "FINALIZED":
        render_draft(path)
        return
    with st.form(path + "_manual_final"):
        criterion = st.selectbox(
            "Menschliche Entscheidung für", [c["id"] for c in record["profile"]["criteria"]]
        )
        conclusion = st.text_area("Menschliche Schlussfolgerung")
        rationale = st.text_area("Begründung der Entscheidung")
        if st.form_submit_button("Entscheidung versioniert speichern"):
            request_backend(
                "POST",
                path + "/decisions",
                json={
                    "criterion_id": criterion,
                    "include_ai_finding": False,
                    "conclusion": conclusion,
                    "rationale": rationale,
                    "resolution": "KEEP_HUMAN",
                },
            )
            st.rerun()
    if record["state"] == "READY_FOR_FINALIZATION":
        render_draft(path)
        if st.button("Gutachtenentwurf abschließend menschlich freigeben"):
            request_backend("POST", path + "/finalize", json={"confirmed": True})
            st.rerun()


@st.fragment(run_every="5s")
def render_active_status(path):
    try:
        current = request_backend("GET", path)
    except BackendError as exc:
        st.error(str(exc))
        return
    st.caption("Aktive Statusabfrage · alle 5 Sekunden · kein erneuter Analyseauftrag")
    if current["ai_state"] != "RUNNING":
        st.rerun()


def render_comparison(path, record):
    comparison = request_backend("GET", path + "/comparison")
    combined = comparison.get("combined_result", {})
    if combined:
        with st.expander("Gemeinsames Ergebnis aller Prüfungen"):
            st.write("Status:", combined.get("status"))
            st.write("Prüfungen:", combined.get("checks", {}))
            st.write("Widersprüchliche Befunde:", combined.get("conflicting_finding_ids", []))
            st.write(
                "Nicht bewertbare Kriterien:", combined.get("not_assessable_criterion_ids", [])
            )
            st.write("Quellenstatus:", combined.get("source_status_counts", {}))
            st.write("Einschränkungen:", combined.get("limitations", []))
            st.caption(
                "Die fachliche Gesamtbewertung bleibt beim Menschen. "
                "Übereinstimmende Verfahren bestätigen keine wissenschaftliche Richtigkeit."
            )
        with st.expander("Fundstellenvergleich und Zitierformat"):
            st.json(comparison.get("retrieval_comparison", {}))
            st.json(comparison.get("citation_style", {}))
    coverage = comparison.get("coverage", {})
    if coverage.get("status") == "INCOMPLETE":
        st.warning("Analyse unvollständig: Abdeckung und offene menschliche Prüfungen beachten.")
    if coverage.get("status"):
        with st.expander("Abdeckung und offene Prüfungen"):
            st.write("Bearbeitete Pflichtkriterien:", coverage.get("required_reviewed", []))
            st.write("Bearbeitete optionale Kriterien:", coverage.get("optional_reviewed", []))
            st.write("Nicht bewertbar:", coverage.get("not_assessable", []))
            st.write("Offene menschliche Entscheidungen:", coverage.get("open_human_decisions", []))
            st.write("Lokal nicht überprüfbare Quellen:", coverage.get("unverifiable_sources", []))
            st.write("Teilanalysen mit Fehlern:", coverage.get("failed_subanalyses", []))
            st.write("Unverarbeitete Textbereiche:", coverage.get("unprocessed_regions", []))
            st.caption("Ausgewählter Textkontext belegt keine wissenschaftliche Vollständigkeit.")
    if record.get("cohort"):
        render_academic(path, record)
    review_explorer(path, record, comparison)
    render_finding_feedback(path, comparison, writable=record["state"] != "FINALIZED")
    with st.expander("Analyseherkunft und Ressourcen"):
        if st.button("Geschützte Provenance anzeigen"):
            provenance = request_backend("GET", path + "/provenance")
            render_adaptive_planning(provenance.get("adaptive_planning"))
            st.text(json.dumps(provenance, ensure_ascii=False, indent=2))
        if st.button("Menschlichen Entscheidungsverlauf anzeigen"):
            st.json(request_backend("GET", path + "/decision-ledger"))
    for entry in comparison["discussion"]:
        st.text(f"Frage: {entry['question']}\nPrüfung: {entry['answer']}")
    if record["state"] == "FINALIZED":
        render_draft(path)
        return
    ids = [row["criterion_id"] for row in comparison["criteria"]]
    with st.form(path + "_criterion_discussion"):
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
        with st.form(path + "_criterion_decision"):
            criterion = st.selectbox("Menschliche Entscheidung für", ids)
            include = st.selectbox("KI-Befund übernehmen?", ["Ja", "Nein"], index=None)
            resolution = st.selectbox(
                "Fachliche Konfliktentscheidung (optional)",
                [
                    "KEEP_HUMAN",
                    "ADOPT_AI",
                    "MERGE",
                    "CORRECT_AI",
                    "REJECT_AI",
                    "FURTHER_REVIEW",
                    "LEAVE_OPEN",
                ],
                index=None,
            )
            extras = [
                f
                for row in comparison["criteria"]
                for f in (row.get("ai") or {}).get("supplemental", [])
            ]
            selected_extras = st.multiselect(
                "Zusätzliche Befunde des gewählten Kriteriums übernehmen",
                [f["finding_id"] for f in extras if f["criterion_id"] == criterion],
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
                            "resolution": resolution,
                        },
                    )
                    st.rerun()
    if record["state"] == "READY_FOR_FINALIZATION":
        render_draft(path)
        if st.button("Gutachtenentwurf abschließend menschlich freigeben"):
            request_backend("POST", path + "/finalize", json={"confirmed": True})
            st.rerun()
    if comparison.get("reviewer_workspace"):
        render_reviewer_workspace(path, comparison, writable=record["state"] != "FINALIZED")


def render_draft(path):
    draft = request_backend("GET", path + "/draft")
    st.subheader("Gutachtenentwurf · Vorschau")
    st.caption(
        "Gliederung aus dem aktiven Bewertungskatalog. Nur menschliche "
        "Entscheidungen und ausdrücklich übernommene Befunde/Anmerkungen. "
        "Überarbeitungen über die versionierten Kriterienentscheidungen "
        "speichern."
    )
    st.text(draft["text"])
    left, right = st.columns(2)
    left.download_button(
        "Text (TXT) herunterladen",
        draft["text"],
        file_name="gutachtenentwurf.txt",
        mime="text/plain",
        on_click="ignore",
    )
    right.download_button(
        "Markdown herunterladen",
        draft["text"],
        file_name="gutachtenentwurf.md",
        mime="text/markdown",
        on_click="ignore",
    )
    st.caption(
        "Lokaler Export in Ihren Downloadordner. Keine Übermittlung an "
        "externe Systeme. PDF-/DOCX-Export ist nicht angebunden."
    )


def render_reviewer_workspace(path, comparison, *, writable=True):
    workspace = comparison["reviewer_workspace"]
    criteria = [r["criterion_id"] for r in comparison["criteria"]]
    with st.expander("Gutachter-Arbeitsbereich"):
        st.write("Bearbeitungsstand", workspace["progress"])
        groups = workspace["finding_groups"]
        st.write(
            "Befundvorschläge:",
            groups["findings_before"],
            "· Redundanzkandidaten:",
            groups["redundancy_candidates"],
        )
        for group in groups["groups"]:
            if len(group["finding_ids"]) > 1:
                st.write("Mögliche Dublette zu " + group["criterion_id"], group["finding_ids"])
        st.caption(
            "Unterschiedliche Perspektiven und Gegenbelege bleiben erhalten. "
            "Vorschläge sind keine nachgewiesenen Fehler; "
            "eine künstliche Balance wird nicht verlangt."
        )
        time_info = workspace["review_time"]
        st.write(
            "Erfasste Sitzungsdauer nach Freigabe:",
            round(time_info["elapsed_seconds"], 1),
            "Sekunden",
        )
        st.caption(
            "Nur ausdrücklich gestartete Sitzungen; "
            "keine Messung von Aufmerksamkeit oder Zeitersparnis."
        )
        if writable and st.button(
            "Gutachtersitzung beenden" if time_info["active"] else "Gutachtersitzung starten"
        ):
            request_backend(
                "POST",
                path + "/reviewer-time",
                json={"action": "STOP" if time_info["active"] else "START"},
            )
            st.rerun()
        st.write("Reproduzierbarkeit der Dokumentation:", workspace["reproducibility"]["status"])
        for method in workspace["reproducibility"].get("methods", []):
            st.write(method["criterion_id"], method["family"])
            st.write([{"Aspekt": c["label"], "Status": c["status"]} for c in method["checks"]])
            for check in method["checks"]:
                for passage in check["passages"]:
                    st.text(f"Seite {passage['page']}: {passage['context']}")
        st.caption(
            "Textfundstellen belegen keine vollständige Reproduzierbarkeit. "
            "Es werden keine Experimente ausgeführt."
        )
        numerical = workspace["numerical"]
        for row in numerical.get("unparsed_candidates", []):
            st.text(f"Seite {row['page']}: {row['quote']}")
            st.caption(
                "Zahlenschreibweise nicht sicher auswertbar; menschliche Prüfung erforderlich."
            )
        for row in numerical.get("arithmetic", []):
            st.text(f"Seite {row['page']}: {row['quote']} · {row['status']}")
        for row in numerical.get("comparisons", []):
            st.write("Zahlenvergleich", row)
        for item in numerical.get("objects", []):
            st.text(f"{item['kind']} · Seite {item['page']}")
            st.text(item["text"][:6000])
            st.caption("Extrahierter Text; Abbildung oder Tabellenlayout nicht visuell bestätigt.")
        for question in workspace["questions"]:
            st.write(question["criterion_id"] + " · " + question["reason"])
            st.text(question["text"])
            for passage in question["passages"]:
                st.text(f"Seite {passage['page']}: {passage['quote']}")
        for note in workspace["notes"]:
            st.text(note["criterion_id"] + ": " + note["text"])
            st.caption(
                "Für Entwurf freigegeben"
                if note["include_in_draft"]
                else "Nur lokale Gutachteranmerkung"
            )
        if not writable:
            return
        edit_id = st.selectbox(
            "Vorhandene Anmerkung überarbeiten",
            [None, *[n["id"] for n in workspace["notes"]]],
            format_func=lambda key: (
                "Neue Anmerkung"
                if key is None
                else next(n["text"][:80] for n in workspace["notes"] if n["id"] == key)
            ),
        )
        editing = next((n for n in workspace["notes"] if n["id"] == edit_id), None)
        criterion = st.selectbox(
            "Anmerkung zu Kriterium", [editing["criterion_id"]] if editing else criteria
        )
        with st.form(path + "_reviewer_workspace_note"):
            questions = [q for q in workspace["questions"] if q["criterion_id"] == criterion]
            question_id = st.selectbox(
                "Bezug zu Rückfrage",
                [None, *[q["id"] for q in questions]],
                format_func=lambda key: (
                    "Eigene Anmerkung"
                    if key is None
                    else next(q["text"] for q in questions if q["id"] == key)
                ),
            )
            text = st.text_area(
                "Gutachteranmerkung / Antwort", value=editing["text"] if editing else ""
            )
            include = st.checkbox("Diese Anmerkung für den Gutachtenentwurf freigeben", value=False)
            if st.form_submit_button("Gutachteranmerkung speichern"):
                if not text.strip():
                    st.warning("Bitte eine Anmerkung oder Antwort eintragen.")
                else:
                    request_backend(
                        "POST",
                        path + "/reviewer-notes",
                        json={
                            "criterion_id": criterion,
                            "note_id": edit_id,
                            "question_id": question_id,
                            "text": text,
                            "include_in_draft": include,
                        },
                    )
                    st.rerun()
        with st.form(path + "_reviewer_applied_method"):
            criterion = st.selectbox("Methodenprüfung zu Kriterium", criteria)
            family = st.selectbox(
                "Tatsächlich angewandte Methode",
                [
                    "MACHINE_LEARNING",
                    "DEEP_LEARNING",
                    "STATISTICS",
                    "QUALITATIVE",
                    "EXPERT_INTERVIEWS",
                    "LITERATURE_REVIEW",
                    "SOFTWARE_ENGINEERING",
                    "DATA_ENGINEERING",
                    "ECONOMIC_ANALYSIS",
                ],
                index=None,
            )
            page = st.number_input("Seite des Methodenbelegs", min_value=1, step=1)
            quote = st.text_area("Exaktes Originalzitat zur angewandten Methode")
            if st.form_submit_button("Angewandte Methode mit Originalbeleg bestätigen"):
                if family is None or not quote.strip():
                    st.warning("Methode auswählen und exaktes Originalzitat angeben.")
                else:
                    request_backend(
                        "POST",
                        path + "/review-methods",
                        json={
                            "criterion_id": criterion,
                            "family": family,
                            "evidence": [{"page": int(page), "quote": quote}],
                            "confirmed_applied": True,
                        },
                    )
                    st.rerun()


def render_document_security(path):
    with st.expander("Lokale Dokumentsicherheit"):
        st.caption("Verdacht ist kein Täuschungsnachweis und ändert keine fachliche Bewertung.")
        if st.button("Sicherheitsprüfung nach Erstbewertung öffnen"):
            st.session_state[path + "_security"] = request_backend(
                "GET", path + "/document-security"
            )
        report = st.session_state.get(path + "_security")
        if not report:
            return
        st.text("Verarbeitungsstatus: " + report["state"])
        for finding in report["findings"]:
            st.text(f"Seite {finding['page']}: {finding['suspicion_type']} · {finding['method']}")
            st.text(finding["quote"])
            st.text(finding["context"])
        with st.form(path + "_security_form"):
            decision = st.selectbox(
                "Weitere PUBLIC-Verarbeitung",
                ["Gesperrt lassen", "Nach Prüfung zulassen"],
                index=None,
            )
            reason = st.text_area("Begründung der Sicherheitsentscheidung")
            confirmed = st.checkbox(
                "Alle aufgeführten Hinweise geprüft; Datenschutzregeln bleiben bestehen"
            )
            if st.form_submit_button("Sicherheitsentscheidung dokumentieren"):
                if not confirmed or decision is None or not reason.strip():
                    st.warning("Entscheidung, Begründung und Bestätigung erforderlich.")
                else:
                    st.session_state[path + "_security"] = request_backend(
                        "POST",
                        path + "/document-security/review",
                        json={
                            "finding_ids": [f["finding_id"] for f in report["findings"]],
                            "allow_public_processing": decision == "Nach Prüfung zulassen",
                            "rationale": reason,
                            "confirmed": True,
                        },
                    )
                    st.rerun()


def render_adaptive_planning(plan):
    if not plan:
        return
    st.write("Begründung zusätzlicher Prüfungen")
    st.text("Planungsmodus: " + plan.get("mode", "UNKNOWN"))
    st.text("Planungsstatus: " + plan.get("status", "UNKNOWN"))
    if plan.get("mocked"):
        st.info("Simulierte Planung; kein Nachweis tatsächlicher Modellleistung.")
    for method in plan.get("understanding", {}).get("procedures", []):
        st.text("Verfahren: " + method["name"] + " · " + method["use"])
    if not plan.get("proposals"):
        st.text(plan.get("rationale", "Keine zusätzlichen Prüfaufträge erstellt."))
    for proposal in plan.get("proposals", []):
        st.text(proposal["name"])
        st.text("Kriterium: " + proposal.get("criterion_id", proposal["category"]))
        st.text(
            proposal.get("rationale", "Regelbasierter Vergleich; keine semantische Begründung.")
        )
        if "task" in proposal:
            st.text("Prüfauftrag: " + proposal["task"])
        for ref in proposal.get("resolved_evidence", []):
            st.text(f"Seite {ref['page']}, Zeichen {ref['start']}–{ref['end']}: {ref['quote']}")
    st.caption("Belegtreffer und Methodeneinordnung beweisen keine fachliche Notwendigkeit.")


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
        with st.form(path + "_finding_feedback"):
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
                "Manuelle Prüfung erforderlich": "MANUAL_REVIEW_REQUIRED",
            }
            reasons = {
                "Falsche fachliche Aussage": "WRONG_STATEMENT",
                "Fehlender Kontext": "MISSING_CONTEXT",
                "Unzutreffendes Kriterium": "WRONG_CRITERION",
                "Fehlerhafte Quellenprüfung": "SOURCE_ERROR",
                "Unberechtigte Kritik": "UNJUSTIFIED_CRITICISM",
                "Unzureichende Evidenz": "INSUFFICIENT_EVIDENCE",
                "Doppelter Befund": "DUPLICATE",
                "Fachlicher Fehler bestätigt": "FACTUAL_ERROR",
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
                with st.form(path + "_academic_decision"):
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
