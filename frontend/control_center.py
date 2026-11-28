import streamlit as st

from frontend.api_client import BackendError, request_backend


def render_tree(nodes: list[dict], edges: list[dict]) -> str:
    # Model-authored names/tasks never enter the DOT language.
    identifiers = {node["agent_id"]: f"n{index}" for index, node in enumerate(nodes)}
    lines = ['digraph agents { rankdir=TB; node [shape=box, color="#dc2626"];']
    roles = {
        "orchestrator",
        "content",
        "methodology",
        "formal",
        "specialist",
        "reviewer",
        "synthesis",
    }
    states = {
        "CREATED",
        "QUEUED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
        "WAITING_FOR_REVIEW",
    }
    for node in nodes:
        role = node["role"] if node.get("role") in roles else "agent"
        status = node.get("status") if node.get("status") in states else ""
        lines.append(f'{identifiers[node["agent_id"]]} [label="{role}\\n{status}"];')
    for edge in edges:
        if edge["parent"] in identifiers and edge["child"] in identifiers:
            lines.append(f"{identifiers[edge['parent']]} -> {identifiers[edge['child']]};")
    return "\n".join([*lines, "}"])


def render_control_center() -> None:
    st.subheader("Multi-Agent Control Center")
    st.caption("Experimentelle A–D-Demo · synthetische Daten · keine unabhängige Erstbewertung")
    try:
        models = request_backend("GET", "/api/v1/models/status")["models"]
        resources = request_backend("GET", "/api/v1/system/resources")
        st.info(f"Datenschutzmodus: {resources['privacy_mode']} · Externe Provider deaktiviert")
        st.dataframe(
            [
                {
                    "ID": m["id"],
                    "Modell": m["name"],
                    "Hersteller": m["manufacturer"],
                    "Verfügbarkeit": m["availability"],
                    "Rollen": ", ".join(m["allowed_roles"]),
                }
                for m in models
            ],
            hide_index=True,
            width="stretch",
        )
        columns = st.columns(4)
        columns[0].metric("CPU (OS-Sicht)", f"{resources['cpu_percent']:.1f} %")
        columns[1].metric(
            "RAM verfügbar (OS-Sicht)", f"{resources['ram_available_bytes'] / 1024**3:.1f} GiB"
        )
        columns[2].metric("Aktive Agenten", resources["active_agents"])
        values = [m.get("vram_bytes") for m in resources.get("loaded_models", [])]
        used = sum(values) if all(type(v) is int and v >= 0 for v in values) else None
        columns[3].metric(
            "VRAM der Ollama-Modelle",
            "Unbekannt"
            if resources.get("vram_unavailable") or used is None
            else f"{used / 1024**3:.1f} GiB",
        )
        st.caption(
            "OS-Metriken sind keine vollständige Messung der einzelnen Container. "
            "VRAM umfasst nur geladene Ollama-Modelle."
        )
        with st.form("synthetic_analysis"):
            mode = st.selectbox(
                "Evaluationsmodus",
                ["D", "C", "B", "A"],
                help="A: Single Prompt · B: homogen · C: heterogen + Review · "
                "D: dynamisch + Review + Evidenz",
            )
            start = st.form_submit_button("Synthetische Beispielanalyse starten", type="primary")
        if start:
            created = request_backend(
                "POST", "/api/v1/runs", json={"mode": mode, "document_id": "synthetic-demo"}
            )
            st.session_state["selected_run"] = created["run_id"]
            st.success("Analyse gestartet. Statusansicht wird bei aktiven Läufen aktualisiert.")
        values = request_backend("GET", "/api/v1/runs")
        if not values:
            st.info(
                "Noch keine Analyse gestartet. Für Modus D alle drei lokalen Modelle bereitstellen."
            )
            return
        ids = [run["run_id"] for run in values]
        previous = st.session_state.get("selected_run")
        selected = st.selectbox(
            "Analyse", ids, index=ids.index(previous) if previous in ids else len(ids) - 1
        )
        run = request_backend("GET", f"/api/v1/runs/{selected}")
        if run["status"] in {"RUNNING", "QUEUED"}:
            render_active_run_status(selected)
        elif st.button("Laufstatus aktualisieren"):
            st.rerun()
        if run.get("mocked"):
            st.warning("MOCK-DATEN: Dieser Lauf verwendet einen simulierten Testprovider.")
        st.progress(run["progress"], text=f"{run['status']} · {run['stage']}")
        st.write(
            {
                "Dauer (s)": round(run["runtime_seconds"], 2),
                "Modellaufrufe": run["model_calls"],
                "Gemeldete Tokens": run["tokens"],
                "Reserviertes Tokenbudget": run["reserved_tokens"],
                "Unvollständig gemessene Aufrufe": run["unknown_token_calls"],
                "Konflikte": run["conflicts_count"],
            }
        )
        if run.get("error"):
            st.error(run["error"])
        for warning in run.get("warnings", []):
            st.warning(warning)
        if run["status"] in {"RUNNING", "QUEUED"} and st.button("Analyse abbrechen"):
            request_backend("POST", f"/api/v1/runs/{selected}/cancel")
            st.rerun()
        graph = request_backend("GET", f"/api/v1/runs/{selected}/graph")
        if graph["nodes"]:
            st.graphviz_chart(render_tree(graph["nodes"], graph["edges"]))
            st.dataframe(
                [
                    {
                        "Agent": n["name"],
                        "Rolle": n["role"],
                        "Modell": n["model_id"],
                        "Hersteller": n["manufacturer"],
                        "Status": n["status"],
                        "Dynamisch": n["dynamic"],
                        "Parent": n["parent_agent"],
                        "Aufrufe": n["model_calls"],
                        "Tokens": n["tokens"],
                    }
                    for n in graph["nodes"]
                ],
                hide_index=True,
                width="stretch",
            )
        if run.get("synthesis_draft"):
            st.write("Syntheseentwurf · nicht final")
            st.text(run["synthesis_draft"])
        for finding in request_backend("GET", f"/api/v1/runs/{selected}/findings"):
            render_finding(finding, run)
        if run.get("final_report"):
            st.success("Finale Zusammenstellung: ausschließlich menschlich freigegebene Befunde.")
            st.text(run["final_report"])
    except (BackendError, KeyError, TypeError):
        st.warning(
            "Control Center momentan nicht vollständig verfügbar. Backend und Modelle prüfen."
        )


@st.fragment(run_every="5s")
def render_active_run_status(run_id):
    try:
        run = request_backend("GET", f"/api/v1/runs/{run_id}")
    except BackendError as exc:
        st.error(str(exc))
        return
    if run["status"] not in {"RUNNING", "QUEUED"}:
        st.rerun()
    st.caption("Aktiver Legacy-Lauf · Statusabfrage alle fünf Sekunden")


def render_finding(finding: dict, run: dict) -> None:
    with st.expander(f"{finding['category']} · {finding['kind']} · {finding['human_status']}"):
        st.text(finding["statement"])
        st.text(f"Seite {finding['page']}: {finding['quote']}")
        st.text(finding["rationale"])
        st.write(
            f"Evidenz: {finding['evidence_status']} · Modellprüfung: {finding['review_status']}"
        )
        if finding["conflict"]:
            st.warning("Konflikt: menschliche Prüfung erforderlich; kein automatischer Konsens.")
        for review in finding["reviews"]:
            st.text(
                f"{review['manufacturer']} ({review['model_id']}): "
                f"{review['verdict']} – {review['rationale']}"
            )
        if run["status"] in {"WAITING_FOR_REVIEW", "COMPLETED"}:
            with st.form(f"review_{finding['finding_id']}"):
                edit = st.text_area("Befund prüfen / bearbeiten", value=finding["statement"])
                note = st.text_input("Prüfvermerk", value=finding["human_note"])
                decision = st.selectbox("Entscheidung", ["ACCEPTED", "REJECTED"], index=None)
                if st.form_submit_button("Menschliche Entscheidung speichern"):
                    if decision is None:
                        st.warning("Bitte eine menschliche Entscheidung auswählen.")
                        return
                    request_backend(
                        "POST",
                        f"/api/v1/runs/{run['run_id']}/findings/{finding['finding_id']}/review",
                        json={"decision": decision, "note": note, "edited_statement": edit},
                    )
                    st.rerun()
