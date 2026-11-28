"""Small typed projections of the backend contract; never a second workflow engine."""

from typing import TypedDict


class AssessmentSummary(TypedDict):
    id: str
    state: str
    work_type: str
    program: str
    cohort: str | None
    created_at: str
    updated_at: str
    document_id: str
    human_completed: bool
    ai_state: str
    ai_released: bool
    classification: str


def filter_assessments(rows: list[AssessmentSummary], search: str, state: str, work_type: str):
    query = search.casefold().strip()
    return [
        r
        for r in rows
        if (
            not query
            or query
            in " ".join(
                str(r.get(k) or "") for k in ("id", "work_type", "cohort", "document_id")
            ).casefold()
        )
        and (state == "Alle" or r["state"] == state)
        and (work_type == "Alle" or r["work_type"] == work_type)
    ]


def dashboard_counts(rows):
    terminal = {"FINALIZED", "CANCELLED", "FAILED"}
    return {
        "Aktive Begutachtungen": sum(r["state"] not in terminal for r in rows),
        "Erstbewertungen offen": sum(
            not r["human_completed"] and r["state"] not in terminal for r in rows
        ),
        "Vergleiche freigegeben": sum(
            r["ai_released"] and r["state"] not in terminal for r in rows
        ),
        "Menschlich abgeschlossen": sum(r["state"] == "FINALIZED" for r in rows),
    }
