from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from tests.integration.test_finding_feedback import assessment


def test_workspace_note_method_and_time_controls_use_the_authorized_api(tmp_path):
    with assessment(tmp_path) as (_, client, path, _, provider):

        def backend(method, target, **kwargs):
            result = client.request(method, target, **kwargs)
            result.raise_for_status()
            return result.json()

        with (
            patch("frontend.assessment_review.request_backend", side_effect=backend),
            patch("frontend.api_client.request_backend", side_effect=backend),
        ):
            app = AppTest.from_string(
                "from frontend.assessment_review import render_comparison, request_backend\n"
                f"render_comparison({path!r}, request_backend('GET', {path!r}))",
                default_timeout=10,
            ).run()
            assert not app.exception
            next(a for a in app.text_area if a.label == "Gutachteranmerkung / Antwort").set_value(
                "SYNTHETIC_UI_NOTE"
            )
            next(b for b in app.button if b.label == "Gutachteranmerkung speichern").click().run()
            assert not app.exception and any("SYNTHETIC_UI_NOTE" in t.value for t in app.text)
            next(b for b in app.button if b.label == "Gutachtersitzung starten").click().run()
            assert not app.exception
            next(b for b in app.button if b.label == "Gutachtersitzung beenden").click().run()
            assert not app.exception
            next(s for s in app.selectbox if s.label == "Methodenprüfung zu Kriterium").select(
                "methodology"
            )
            next(s for s in app.selectbox if s.label == "Tatsächlich angewandte Methode").select(
                "STATISTICS"
            )
            next(n for n in app.number_input if n.label == "Seite des Methodenbelegs").set_value(2)
            next(
                a
                for a in app.text_area
                if a.label == "Exaktes Originalzitat zur angewandten Methode"
            ).set_value("Es wurden sechs synthetische Arbeiten")
            next(
                b
                for b in app.button
                if b.label == "Angewandte Methode mit Originalbeleg bestätigen"
            ).click().run()
            assert not app.exception
            next(s for s in app.selectbox if s.label == "Kriterium anzeigen").select(
                "methodology"
            ).run()
            assert not app.exception
            assert "SYNTHETIC_UI_NOTE" not in str(provider.contexts)
