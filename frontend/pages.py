"""Product pages backed by the existing FastAPI contracts."""

import streamlit as st

from frontend import api_client
from frontend.design import details, empty_state, label, page_header, status_badges
from frontend.navigation import navigate, select_assessment
from frontend.viewmodels import dashboard_counts, filter_assessments

BASE = "/api/v1/assessments"


def assessment_list(rows):
    if not rows:
        empty_state(
            "Noch keine Begutachtung",
            "Eine neue synthetische Begutachtung anlegen oder den Filter ändern.",
        )
        return
    left, middle, right = st.columns([2, 1, 1])
    search = left.text_input(
        "Begutachtungen durchsuchen", placeholder="Fall-ID, Jahrgang oder Arbeitstyp"
    )
    state = middle.selectbox(
        "Bearbeitungsstatus", ["Alle", *sorted({r["state"] for r in rows})], format_func=label
    )
    work_type = right.selectbox("Arbeitstyp filtern", ["Alle", "PA1", "PA2", "BA"])
    filtered = filter_assessments(rows, search, state, work_type)
    st.caption(
        f"{len(filtered)} von {len(rows)} sichtbaren Begutachtungen · gemeinsamer Demo-Bestand"
    )
    if not filtered:
        empty_state("Keine passenden Fälle", "Suche verkürzen oder Filter zurücksetzen.")
    for row in filtered:
        with st.container(border=True):
            main, action = st.columns([5, 1])
            with main:
                st.write(
                    f"**{row['work_type']} · {row.get('cohort') or 'Jahrgang offen'} "
                    f"· {row['id'][:8]}**"
                )
                status_badges(row["state"], row["classification"])
                st.caption(
                    f"Zuletzt geändert: {row['updated_at']} · "
                    + (
                        "synthetisches Testdokument"
                        if row["document_id"] == "synthetic-demo"
                        else "registrierte Pilotdatei"
                    )
                )
            action.button(
                "Öffnen",
                key="open_" + row["id"],
                width="stretch",
                on_click=select_assessment,
                args=(row["id"],),
            )


def dashboard():
    page_header("Dashboard", "Ihre nächsten Schritte und der aktuelle Begutachtungsbestand.")
    rows = api_client.request_backend("GET", BASE)
    for column, (title, count) in zip(st.columns(4), dashboard_counts(rows).items(), strict=True):
        column.metric(title, count)
    st.caption(
        "Live-Status des zugänglichen Demo-Bestands. Keine "
        "Qualitätskennzahlen oder KI-Befundzahlen vor Freigabe."
    )
    st.button(
        "Neue Begutachtung",
        type="primary",
        key="dashboard_create",
        on_click=navigate,
        args=("Neue Begutachtung",),
    )
    st.divider()
    st.subheader("Begutachtungen")
    assessment_list(rows)
    if rows:
        with st.expander("Letzte Statusänderungen"):
            for row in sorted(rows, key=lambda r: r["updated_at"], reverse=True)[:5]:
                st.text(f"{row['updated_at']} · {row['id'][:8]} · {label(row['state'])}")
            st.caption("Zeitpunkte aus dem Workflow; kein vollständiges Auditprotokoll.")


def creation_wizard():
    page_header("Neue Begutachtung", "Schrittweise zur unabhängigen Erst- und Zweitbewertung.")
    step = st.session_state.get("wizard_step", 1)
    steps = [
        "Arbeit & Studiengang",
        "Dokument",
        "Datenschutz",
        "Bewertungskatalog",
        "Prüfen & anlegen",
    ]
    st.caption(
        "  /  ".join(("✓ " if index < step else "") + title for index, title in enumerate(steps, 1))
    )
    st.progress((step - 1) / len(steps), text=f"Anlage · Schritt {step} von {len(steps)}")
    profiles = api_client.request_backend("GET", BASE + "/profiles")
    payload = dict(st.session_state.get("wizard_payload", {}))
    valid = True
    with st.container(border=True):
        st.subheader(steps[step - 1])
        if step == 1:
            payload["work_type"] = st.selectbox(
                "Arbeitstyp",
                ["PA1", "PA2", "BA"],
                index=["PA1", "PA2", "BA"].index(payload.get("work_type", "PA1")),
                key="wizard_work_type",
            )
            payload["program"] = st.selectbox(
                "Studiengang",
                ["data_science_ai", "wirtschaftsinformatik"],
                index=["data_science_ai", "wirtschaftsinformatik"].index(
                    payload.get("program", "data_science_ai")
                ),
                format_func=lambda v: (
                    "Data Science und KI" if v == "data_science_ai" else "Wirtschaftsinformatik"
                ),
                key="wizard_program",
            )
            prefix = "DS" if payload["program"] == "data_science_ai" else "WI"
            cohorts = [prefix + year for year in ("23", "24", "25")]
            payload["cohort"] = st.selectbox(
                "Jahrgang",
                cohorts,
                index=cohorts.index(payload["cohort"])
                if payload.get("cohort") in cohorts
                else None,
                key="wizard_cohort_" + prefix,
            )
            valid = payload["cohort"] is not None
            st.caption("Die Jahrgangsauswahl aktiviert keine unbestätigten Hochschulregeln.")
        elif step == 2:
            pilot = api_client.request_backend("GET", BASE + "/pilot-documents")
            candidates = ["synthetic-demo"] if pilot.get("inference_mode") != "local_pilot" else []
            if (
                payload["work_type"] == "PA1"
                and payload["program"] == "data_science_ai"
                and pilot.get("profile_id")
            ):
                candidates += [d["document_id"] for d in pilot.get("documents", [])]
            if not candidates:
                empty_state(
                    "Kein zulässiges Dokument",
                    "Der lokale Pilot benötigt eine operatorgeprüfte PUBLIC-Datei und "
                    "einen bestätigten Experimentkatalog. Administration prüfen.",
                )
                valid = False
            else:
                payload["document_id"] = st.selectbox(
                    "Zulässiges Dokument",
                    candidates,
                    format_func=lambda v: (
                        "Synthetisches Testdokument · 3 Seiten"
                        if v == "synthetic-demo"
                        else "Registrierte Pilot-PDF · " + v[6:18]
                    ),
                    key="wizard_document",
                )
                payload["profile_id"] = (
                    pilot.get("profile_id") if payload["document_id"] != "synthetic-demo" else None
                )
                st.info(
                    "Es werden ausschließlich serverseitig bereitgestellte Dokumente "
                    "verwendet. Vertrauliche Arbeiten können hier nicht hochgeladen "
                    "werden."
                )
        elif step == 3:
            st.write(
                "Dokumente werden lokal verarbeitet. Menschliche Bewertungen und "
                "Diskussionen gelten als RESTRICTED. Externe KI und "
                "dokumentbezogene öffentliche Recherche sind gesperrt."
            )
            st.write(
                "Sperrvermerke werden serverseitig geprüft. Die Auswahl PUBLIC ist"
                " keine eigene Freigabe. Eine Hochschulanmeldung und der "
                "produktive Betrieb sind noch nicht freigegeben."
            )
            st.warning(
                "Der Demo-Bestand nutzt eine gemeinsame Identität. "
                "Sitzungsentwürfe gehen beim Verlust der Browsersitzung verloren; "
                "der Backend-Bestand ist ebenfalls flüchtig."
            )
            valid = st.checkbox(
                "Ich verwende ausschließlich das synthetische oder "
                "operatorgeprüfte öffentliche Testdokument.",
                key="wizard_privacy",
            )
        elif step == 4:
            available = [
                p
                for p in profiles
                if p["work_type"] == payload["work_type"]
                and (not payload.get("profile_id") or p["id"] == payload["profile_id"])
            ]
            if not available:
                empty_state(
                    "Kein zulässiger Bewertungskatalog",
                    "Für diese Auswahl fehlt ein im Backend zugelassener Katalog.",
                )
                valid = False
            else:
                payload["profile_id"] = st.selectbox(
                    "Bewertungskatalog", [p["id"] for p in available], key="wizard_profile"
                )
                profile = next(p for p in available if p["id"] == payload["profile_id"])
                status_badges(profile.get("status"), profile.get("version"))
                st.warning("Beispiel-/Experimentkatalog: keine offizielle DHBW-Freigabe.")
                for criterion in profile["criteria"]:
                    st.text(criterion["id"] + " · " + criterion["description"])
                details(profile, title="Katalogversion, Herkunft und Prüfumfang")
        else:
            for key, title in (
                ("work_type", "Arbeitstyp"),
                ("program", "Studiengang"),
                ("cohort", "Jahrgang"),
                ("document_id", "Dokument"),
                ("profile_id", "Katalog"),
            ):
                st.text(f"{title}: {payload.get(key, 'Nicht gewählt')}")
            st.info(
                "Danach: menschliche Erstbewertung abschließen, unabhängige "
                "KI-Prüfung ausführen, Vergleich ausdrücklich öffnen und "
                "menschlich entscheiden."
            )
            valid = st.checkbox(
                "Diese Auswahl prüfen und Begutachtung anlegen", key="wizard_confirm"
            )
    st.session_state.wizard_payload = payload
    back, forward = st.columns([1, 3])
    if back.button("Zurück", disabled=step == 1):
        st.session_state.wizard_step = step - 1
        st.rerun()
    if step < 5:
        if forward.button("Weiter", type="primary", disabled=not valid):
            # Changing a prior step invalidates dependent catalog/document selections.
            if step == 1:
                payload.pop("profile_id", None)
                payload.pop("document_id", None)
                for key in ("wizard_document", "wizard_profile", "wizard_confirm"):
                    st.session_state.pop(key, None)
            st.session_state.wizard_step = step + 1
            st.rerun()
    elif forward.button("Begutachtung anlegen", type="primary", disabled=not valid):
        record = api_client.request_backend("POST", BASE, json=payload)
        select_assessment(record["id"])
        for key in list(st.session_state):
            if key.startswith("wizard_"):
                del st.session_state[key]
        st.rerun()


def choose_released_assessment():
    rows = api_client.request_backend("GET", BASE)
    options = [r for r in rows if r["ai_released"]]
    if not options:
        empty_state(
            "Noch kein Vergleich freigegeben",
            "Quellen- und Analyseergebnisse sind erst nach unabhängiger "
            "Erstbewertung und ausdrücklicher Vergleichsfreigabe sichtbar.",
        )
        return None
    key = st.selectbox(
        "Freigegebene Begutachtung",
        [r["id"] for r in options],
        format_func=lambda v: next(r["work_type"] + " · " + v[:8] for r in options if r["id"] == v),
    )
    return BASE + "/" + key


def sources():
    from frontend.sources import render_source_inspector

    page_header("Quellenprüfung", "Bibliografische Nachweise aus lokalen, versionierten Beständen.")
    path = choose_released_assessment()
    if path:
        render_source_inspector(path)


def knowledge():
    from frontend.assessment_review import render_rules

    page_header(
        "DHBW-Richtlinien", "Mosbach zuerst: Herkunft, Gültigkeit und offene Bestätigungen."
    )
    with st.form("knowledge_preview"):
        program = st.selectbox("Studiengang", ["data_science_ai", "wirtschaftsinformatik"])
        cohort = st.selectbox("Jahrgang", ["DS23", "DS24", "DS25", "WI23", "WI24", "WI25"])
        work_type = st.selectbox("Arbeitstyp", ["PA1", "PA2", "BA"])
        if st.form_submit_button("Richtlinienvorschau laden"):
            st.session_state.knowledge_preview = api_client.request_backend(
                "POST",
                BASE + "/rules-preview",
                json={"program": program, "cohort": cohort, "work_type": work_type},
            )
    preview = st.session_state.get("knowledge_preview")
    if preview:
        status_badges(preview["status"])
        render_rules(preview)
        details(preview, title="Regeln, Gültigkeitszeiträume und Konflikte")
    else:
        empty_state(
            "Geltungsbereich auswählen",
            "Die Vorschau weist Kandidaten und fehlende Freigaben aus. Andere "
            "Standorte ersetzen keine Mosbacher Vorgaben.",
        )


def models():
    page_header(
        "Model Center", "Lokale Modellregistrierung und nachgewiesene Fähigkeiten.", area="Technik"
    )
    security = api_client.request_backend("GET", "/api/v1/security/status")
    rows = api_client.request_backend("GET", "/api/v1/models/status")["models"]
    if security.get("inference") == "IN_PROCESS_MOCK_ONLY":
        st.warning(
            "MOCK · Registrierte Verfügbarkeit ist simuliert; keine Aussage "
            "über installierte Ollama-Artefakte."
        )
    if not rows:
        empty_state("Keine Modelle registriert", "Die serverseitige Modellkonfiguration prüfen.")
    else:
        st.dataframe(
            [
                {
                    "Modell": r["name"],
                    "Hersteller": r["manufacturer"],
                    "Status": r["availability"],
                    "Freigabe": r.get("approval_status"),
                    "Aufgaben": ", ".join(r.get("allowed_roles", [])),
                    "Digest": r.get("discovered_digest") or r.get("digest") or "Nicht nachgewiesen",
                }
                for r in rows
            ],
            hide_index=True,
            width="stretch",
        )
        for row in rows:
            details(row, title=row["name"] + " · Version, Artefakt und Ressourcenlimits")
    capabilities = api_client.request_backend("GET", "/api/v1/models/capabilities")
    st.subheader("Capability Matrix")
    if capabilities["records"]:
        for record in capabilities["records"]:
            status_badges("MOCK" if record.get("mocked", True) else "REAL MODEL BENCHMARK")
            details(record, title=record["model_id"] + " · Benchmark-Nachweis")
    else:
        empty_state(
            "Keine empirischen Fähigkeitsnachweise",
            "Das Routing verwendet gekennzeichnete manuelle "
            "Standardzuordnungen. Precision, Recall, F1, TTFT und "
            "Hardware-Spitzen sind nicht erhoben.",
        )
    st.caption("Modell- und Datenschutzfreigaben lassen sich hier nicht verändern.")


def evaluation():
    page_header(
        "Evaluation Lab",
        "Wissenschaftliche Ergebnisse benötigen versionierte Messungen und Referenzbewertungen.",
        area="Technik",
    )
    empty_state(
        "Report-Ansicht noch nicht angebunden",
        "Das bestehende CLI-Evaluationslabor erzeugt lokale Reports. Es "
        "gibt keine freigegebene HTTP-Report-Schnittstelle; hier werden "
        "keine Ergebnisdateien oder Kennzahlen erfunden.",
    )
    st.write(
        "Unterstützte CLI-Auswertungen: Single LLM, homogene und "
        "heterogene Agenten, adaptive Spezialisten, Gegenprüfung, "
        "Retrieval und Prompt-Injection-Tests."
    )
    st.caption(
        "MOCK, SYNTHETIC TEST, REAL MODEL BENCHMARK und HUMAN-VALIDATED "
        "RESULT müssen getrennt ausgewiesen werden. Humanvalidierung "
        "erfordert echte Referenzurteile."
    )
    st.code("python -m app.evaluation.model_benchmark --help", language="bash")
    st.caption(
        "Im Backend-Pythonpfad starten; Anleitung unter docs/evaluation. "
        "Keine Ausführung über die Oberfläche."
    )


def security_center(security):
    page_header(
        "Security Center",
        "Technischer Schutz, Zielinfrastruktur und organisatorische Freigabe getrennt betrachten.",
        area="Technik",
    )
    status_badges(
        security.get("mode"), security.get("inference"), security.get("classification_default")
    )
    st.warning(
        "Produktiver Betrieb gesperrt. Keine bestätigte Hochschulidentität"
        " und keine organisatorische Gesamtfreigabe."
    )
    st.dataframe(
        [
            {
                "Bereich": "Datenschutz-/Embargogrenzen",
                "Status": "Implementiert; automatisierte Regressionen separat in CI nachweisen",
            },
            {
                "Bereich": "Externe KI und öffentliche Dokumentrecherche",
                "Status": "Backendseitig gesperrt",
            },
            {
                "Bereich": "Zielinfrastruktur / Netzwerkabnahme",
                "Status": security.get("network", "Nicht verifiziert"),
            },
            {"Bereich": "Telemetrie", "Status": security.get("telemetry", "Unbekannt")},
            {"Bereich": "Hochschulanmeldung", "Status": security.get("identity", "Unbekannt")},
            {
                "Bereich": "Aufbewahrung im Backend",
                "Status": str(security.get("retention_seconds")) + " Sekunden; flüchtiger Speicher",
            },
        ],
        hide_index=True,
        width="stretch",
    )
    with st.expander("Ausstehende Freigaben und Nachweise", expanded=True):
        for blocker in security.get("blockers", []):
            st.text(blocker)
    details(security, title="Vom Backend gemeldeter Sicherheitsstatus")
    st.caption(
        "Verdachtsfälle sind nur im zugehörigen, autorisierten Review "
        "sichtbar. Sie begründen keine automatische fachliche Abwertung. "
        "Keine Konformitäts- oder Sicherheitsgarantie."
    )


def system_status():
    page_header(
        "Systemstatus",
        "Aktuelle Verbindung und Ressourcen aus der Sicht des Backends.",
        area="Technik",
    )
    health = api_client.request_backend("GET", "/health")
    resources = api_client.request_backend("GET", "/api/v1/system/resources")
    cols = st.columns(3)
    cols[0].metric("Backend", "Erreichbar" if health.get("status") == "ok" else "Unbekannt")
    cols[1].metric("CPU · OS-Sicht", f"{resources['cpu_percent']:.1f} %")
    cols[2].metric(
        "RAM verfügbar · OS-Sicht", f"{resources['ram_available_bytes'] / 1024**3:.1f} GiB"
    )
    st.caption(
        "Momentaufnahme, keine modellbezogene Spitzenmessung. Fehlende "
        "VRAM-Werte bleiben unbekannt."
    )
    details(resources, title="Ressourcen-Messumfang und geladene Modelle")
    st.button("Status aktualisieren", on_click=lambda: None)


def settings():
    page_header("Einstellungen", "Darstellung und flüchtige Sitzungsdaten.", area="Technik")
    st.radio(
        "Arbeitsbereich-Layout",
        ["Registerkarten", "Drei Spalten"],
        key="workspace_layout",
        help="Registerkarten eignen sich für schmale Bildschirme. Drei Spalten "
        "zeigen Orientierung, Dokument und Befund nebeneinander.",
    )
    st.caption(
        "Keine Browserpersistenz, keine lokalen Schrift-Downloads und "
        "keine Modellfreigaben über diese Ansicht."
    )
    confirmed = st.checkbox("Sitzungsentwürfe und die aktuelle Auswahl verwerfen")
    if st.button("Sitzungsspeicher leeren", disabled=not confirmed):
        st.session_state.clear()
        st.rerun()
    st.info(
        "Das leert nur diese Browsersitzung. Begutachtungen im gemeinsamen"
        " Backend werden separat gelöscht oder nach Ablauf bereinigt."
    )
