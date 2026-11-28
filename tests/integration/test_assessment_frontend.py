"""Exercise the complete human workflow through Streamlit and the actual HTTP API."""

from unittest.mock import patch

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from frontend.api_client import BackendError
from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider
from tests.fixtures.frontend import create_case_ui


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    assert not app.exception


def test_synthetic_human_first_review_through_ui(tmp_path):
    api = create_app(Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path))
    with (
        patch("app.main.create_provider", return_value=AssessmentProvider()),
        TestClient(api) as client,
    ):

        def backend(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            if response.is_error:
                raise BackendError("Aktion nicht freigegeben")
            if path.endswith("/ai-review"):

                async def wait():
                    for task in api.state.runtime.assessments.tasks.values():
                        await task

                client.portal.call(wait)
            return response.json()

        with (
            patch("frontend.assessment_review.request_backend", side_effect=backend),
            patch("frontend.api_client.request_backend", side_effect=backend),
        ):
            app = AppTest.from_string(
                "from frontend.assessment_review import render_assessment_review\n"
                "render_assessment_review()",
                default_timeout=10,
            ).run()
            create_case_ui(app)
            judgments = [box for box in app.selectbox if box.label == "Einschätzung"]
            assert len(judgments) == 3
            assert all(box.value is None for box in judgments)
            assert not any("AI_EMBARGO_MARKER" in text.value for text in app.text)
            # Submitting without explicit release remains a UI warning.
            click(app, "Erstbewertung unveränderlich freigeben")
            assert app.warning
            for box in app.selectbox:
                if box.label != "Einschätzung":
                    continue
                box.select("MIXED")
            for area in app.text_area:
                if area.label in {"Beobachtungen", "Begründung"}:
                    area.set_value("Unabhängige menschliche Beobachtung")
            next(box for box in app.checkbox if box.label.startswith("Ich schließe")).check()
            click(app, "Erstbewertung unveränderlich freigeben")
            click(app, "Unabhängige KI-Bewertung starten")
            assert not any("AI_EMBARGO_MARKER" in text.value for text in app.text)
            click(app, "Beide Bewertungen zum Vergleich öffnen")
            assert any("AI_EMBARGO_MARKER" in text.value for text in app.text)
            app.text_area[0].set_value("Welche Gegenargumente sprechen gegen den Befund?")
            click(app, "Diskutieren")
            assert app.error  # Confidential discussion cannot reach an unapproved model.
            click(app, "Ohne KI-Diskussion menschlich prüfen")
            include = next(box for box in app.selectbox if box.label == "KI-Befund übernehmen?")
            assert include.value is None
            click(app, "Entscheidung versioniert speichern")
            assert app.warning
            for criterion in ["literature", "methodology", "structure"]:
                next(
                    box for box in app.selectbox if box.label == "Menschliche Entscheidung für"
                ).select(criterion)
                next(box for box in app.selectbox if box.label == "KI-Befund übernehmen?").select(
                    "Nein"
                )
                next(
                    area for area in app.text_area if area.label == "Menschliche Schlussfolgerung"
                ).set_value("Menschliche Schlussfolgerung")
                next(
                    area for area in app.text_area if area.label == "Begründung der Entscheidung"
                ).set_value("Eigenständige Begründung")
                click(app, "Entscheidung versioniert speichern")
            assert any("Gutachtenentwurf" in text.value for text in app.text)
            click(app, "Gutachtenentwurf abschließend menschlich freigeben")
            assert any("Menschlich freigegeben" in text.value for text in app.text)
            click(app, "Weitere synthetische Begutachtung")
            assert "assessment_id" not in app.session_state
