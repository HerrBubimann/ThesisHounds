# Komponenten und Zuständigkeiten

| Modul | Komponenten / Zweck |
|---|---|
| `app.py` | Seitenkonfiguration, Verbindung, gemeinsame Fehlergrenze, Seitenauswahl |
| `design.py` | Tokens, CSS, Seitenkopf/Breadcrumb, Statussprache, Leerzustand, Detailbereich, Workflowphasen |
| `navigation.py` | fachliche / technische Navigation, fallbezogene Auswahl und Scopewechsel |
| `viewmodels.py` | typisierte Fallprojektion, Filter und aus Statusdaten abgeleitete Zähler |
| `pages.py` | Dashboard, Fallliste, Anlageassistent, Richtlinien, Modell-/Evaluations-/Sicherheits-/Statusseiten, Einstellungen |
| `evidence.py` | Dokumentleser, geschützter Original-PDF-Viewer, Originalzitat/Offsets, Vergleich und Befundkarten |
| `sources.py` | lokale Quellen, Snapshotnachweise, Statusfilter, verifizierter Rücksprung zum Literaturverzeichnis |
| `assessment_review.py` | Erstbewertung, Freigaben, Befundfeedback, Diskussion, Kriterienentscheidungen, Notizen, Entwurf und Export |
| `control_center.py` | ausdrücklich als Legacy bezeichnete A–D-Läufe und echte Laufgraphen |
| `api_client.py`, `egress.py` | zentrale HTTP-/PDF-Anbindung, Limits, sichere Fehler, DNS-Pinning |

Native Streamlit-Formulare, Tabellen, Expander, Tabs und Spalten bleiben erhalten.
Detaildaten verwenden `st.text`/`st.json`; ausschließlich konstantes CSS und mit
`html.escape` behandelte Status-/Leerzustandslabels gelangen in eigenes HTML.
Keine Modelltexte in CSS, Graphviz-Syntax oder HTML.

Bestätigungen sind ausdrückliche Checkbox-/Button-Aktionen: Anlage, unabhängige
Erstfreigabe, Abbruch, Löschung und Leeren des Sitzungsspeichers. Backendaktionen
werden niemals allein durch Navigation, einen Refresh oder Fragment-Polling ausgelöst.
Fehlende Daten führen zu Leer-/Sperrzuständen; technische Metadaten sind aufklappbar.
