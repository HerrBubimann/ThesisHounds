"""Drive the actual guided document/catalog/privacy flow in Streamlit tests."""


def create_case_ui(ui, *, document_id="synthetic-demo", cohort="DS23"):
    def click(title):
        next(b for b in ui.button if b.label == title).click().run()
        assert not ui.exception

    next(s for s in ui.selectbox if s.label == "Jahrgang").select(cohort).run()
    click("Weiter")
    next(s for s in ui.selectbox if s.label == "Zulässiges Dokument").select(document_id).run()
    click("Weiter")
    ui.checkbox[0].check().run()
    click("Weiter")
    click("Weiter")
    ui.checkbox[0].check().run()
    click("Begutachtung anlegen")
