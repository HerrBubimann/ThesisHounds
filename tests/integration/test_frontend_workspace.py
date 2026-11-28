"""Exercise navigation, wizard, saved human drafts and safe unavailable states."""

from unittest.mock import patch

import httpx
import pytest
from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from frontend.api_client import BackendError, request_pdf
from tests.fixtures import CONFIG, ROOT
from tests.fixtures.assessments import AssessmentProvider


def button(ui, title):
    next(b for b in ui.button if b.label == title).click().run()
    assert not ui.exception


def select(ui, title, value):
    next(s for s in ui.selectbox if s.label == title).select(value).run()
    assert not ui.exception


def test_wizard_session_draft_navigation_and_actual_case_list(tmp_path):
    app = create_app(Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path))
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider()),
        TestClient(app) as client,
    ):
        calls = []

        def backend(method, path, **kwargs):
            calls.append((method, path))
            response = client.request(method, path, **kwargs)
            if response.is_error:
                raise BackendError("Aktion nicht freigegeben")
            return response.json()

        with (
            patch("frontend.api_client.request_backend", side_effect=backend),
            patch("frontend.assessment_review.request_backend", side_effect=backend),
        ):
            ui = AppTest.from_file(ROOT / "frontend/app.py", default_timeout=15).run()
            next(b for b in ui.button if b.key == "nav_Neue Begutachtung").click().run()
            assert next(b for b in ui.button if b.label == "Weiter").disabled
            select(ui, "Jahrgang", "DS23")
            button(ui, "Weiter")
            assert (
                next(s for s in ui.selectbox if s.label == "Zulässiges Dokument").value
                == "synthetic-demo"
            )
            button(ui, "Weiter")
            assert next(b for b in ui.button if b.label == "Weiter").disabled
            ui.checkbox[0].check().run()
            button(ui, "Weiter")
            assert (
                next(s for s in ui.selectbox if s.label == "Bewertungskatalog").value
                == "pa1-example"
            )
            button(ui, "Weiter")
            ui.checkbox[0].check().run()
            button(ui, "Begutachtung anlegen")
            key = ui.session_state.assessment_id
            assert len(app.state.runtime.assessments.records) == 1
            assert not any(path.endswith("/comparison") for _, path in calls)
            next(a for a in ui.text_area if a.label == "Beobachtungen").set_value(
                "SESSION_DRAFT_ONLY"
            )
            button(ui, "Entwurf in Sitzung speichern")
            assert client.get("/api/v1/assessments/" + key).json()["human_completed"] is False
            button(ui, "Dashboard")
            assert any(m.value == "1" for m in ui.metric)
            button(ui, "Öffnen")
            assert (
                next(a for a in ui.text_area if a.label == "Beobachtungen").value
                == "SESSION_DRAFT_ONLY"
            )
            assert not any(
                method == "POST" and path.endswith("/human-review") for method, path in calls
            )
            assert not any(
                method == "POST" and path.endswith("/ai-review") for method, path in calls
            )
            # Knowledge, models, empty source and evaluation views use real read contracts.
            for page in (
                "Quellenprüfung",
                "DHBW-Richtlinien",
                "Model Center",
                "Evaluation Lab",
                "Security Center",
                "Systemstatus",
                "Einstellungen",
            ):
                button(ui, page)
            assert not ui.exception
            ui.checkbox[0].check().run()
            button(ui, "Sitzungsspeicher leeren")
            assert "assessment_id" not in ui.session_state
            assert len(app.state.runtime.assessments.records) == 1


def test_pdf_client_reuses_pinned_transport_and_rejects_wrong_content():
    with patch(
        "httpx.Client.send",
        return_value=httpx.Response(
            200, content=b"%PDF-verified", headers={"content-type": "application/pdf"}
        ),
    ):
        assert request_pdf("/api/v1/assessments/id/original-pdf") == b"%PDF-verified"
    for content_type, content in (
        ("text/html", b"PRIVATE_HTML"),
        ("application/pdf", b"PRIVATE_NOT_PDF"),
    ):
        with patch(
            "httpx.Client.send",
            return_value=httpx.Response(
                200, content=content, headers={"content-type": content_type}
            ),
        ):
            with pytest.raises(BackendError) as error:
                request_pdf("/api/v1/assessments/id/original-pdf")
            assert "PRIVATE" not in str(error.value)
    with pytest.raises(BackendError):
        request_pdf("https://evil.example/original-pdf")
    with pytest.raises(BackendError):
        request_pdf("/api/v1/assessments/id/document")


def test_source_inspector_shows_snapshot_scope_and_verifies_original_before_display():
    from app.research.citations import verify_citations
    from app.research.provider_registry import LocalResearchCache

    from tests.unit.test_citation_engine import doc, record

    document = doc()
    report = verify_citations(document, LocalResearchCache([record()]))
    calls = []

    def backend(method, path, **kwargs):
        calls.append((method, path))
        if path.endswith("/academic-checks"):
            return {"citations": report}
        assert path.endswith("/document") and method == "GET"
        return document.model_dump(mode="json")

    with patch("frontend.api_client.request_backend", side_effect=backend):
        ui = AppTest.from_string(
            "from frontend.sources import render_source_inspector\n"
            "render_source_inspector('/api/v1/assessments/synthetic')"
        ).run()
        assert not ui.exception
        assert any("10.5555/test" in t.value for t in ui.text)
        assert any("crossref" in t.value for t in ui.text)
        button(ui, "Originalstelle der Quelle öffnen")
        assert any(t.value == document.pages[2] for t in ui.text)
        document.pages[2] = "Changed original; cannot match stored offsets"
        button(ui, "Originalstelle der Quelle öffnen")
        assert any("nicht mehr eindeutig" in w.value for w in ui.warning)
        assert all(method == "GET" for method, _ in calls)
        assert not ui.get("link_button")
