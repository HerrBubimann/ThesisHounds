# Navigation und Sitzungszustand

Der Einstieg ist das Dashboard. Der Arbeitsbereich enthält **Neue Begutachtung**,
**Meine Begutachtungen**, **Quellenprüfung** und **DHBW-Richtlinien**. Technik bleibt
unter einem eigenen aufklappbaren Bereich: Agent Control Center, Model Center,
Evaluation Lab, Security Center, Systemstatus, Einstellungen.

Die Navigation verwendet benannte native Buttons und `st.session_state.page`.
Keine Dokument-IDs, Notizen oder Modellprompts werden in Queryparameter geschrieben.
Der Backendfall wird über `assessment_id` gewählt. Beim Fallwechsel werden die
ausgewählte Beleg-ID und der Kriterienfilter zurückgesetzt. Formular-/Dokumentkeys
sind mit dem Fallpfad gebunden; eine Erstfreigabe-Checkbox gehört genau zu einem Fall.

Das Dashboard enthält ausschließlich ACL-gefilterte Backendmetadaten. Die Bezeichnung
„Meine“ bedeutet in DEVELOPMENT keine echte Benutzertrennung: Alle Browser verwenden
die gemeinsame synthetische Demo-Identität. Dies steht auch in der Sidebar.
Ergebnisinhalte sind vor Vergleichsfreigabe weder im Dashboard noch in der Quellenwahl.

Sitzungsentwürfe werden ausdrücklich gespeichert und bleiben nur im Arbeitsspeicher
der Streamlit-Sitzung. Kein localStorage, IndexedDB, zusätzlicher Dokumentcache oder
Dateispeicher. Einstellungen können diesen Sitzungsspeicher nach Bestätigung leeren;
das löscht keinen Backendfall. Die Falllöschung ist eine separate, bestätigte Aktion.
