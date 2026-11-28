# Frontend-Architektur und Gap Analysis

Stand: 28.11.2026, Beginn der vollständigen UX-Neugestaltung nach dem
[geprüften Ausbau der Gutachterwerkzeuge](../evaluation/reviewer_productivity_results.md).
Diese erste Tabelle dokumentiert die Ausgangslage, keine bereits erfolgte Abnahme.

| Bereich | Befund | Priorität / konkrete Maßnahme |
|---|---|---|
| Einstieg | ein dunkler langer Bildschirm mit Status, Chatprobe, Assessment und Legacy-Control-Center | P0: helle App-Shell, dunkle Navigation, eigenes Dashboard und klarer Arbeitsbereich |
| Komponenten | `app.py`, `assessment_review.py`, `control_center.py`; wiederholte Roh-JSON-/Statusdarstellung | P0: zentrale Tokens, Karten, Statussprache, Leer-/Fehlerzustände und modulare Seiten |
| Navigation | technische und fachliche Abläufe gleichzeitig gerendert | P0: Gutachterbereich vorne; technische Seiten ausdrücklich aufrufbar |
| Übersicht | kein API-Listing für Assessments, keine datengestützte Übersicht | P0: geschützte Metadatenprojektion und Dashboard ohne Befundinhalte vor Freigabe |
| Anlage | kompakte Arbeitstyp-/Studiengangswahl; feste Beispielprofile, kontrollierte Pilotliste | P0: geführte Anlage mit tatsächlichen Dokument-/Katalog-/Datenschutzvoraussetzungen |
| Begutachtung | unabhängige Erstbewertung und Backend-Embargo funktional | P0: erhalten, verständliche Phasen, Sitzungsspeicher für Entwürfe und ruhiger Vergleich |
| Evidence | Text, Originaloffsets und Quellenprüfung vorhanden; kein PDF-Originalendpunkt | P0: geprüfte Quellenansicht, Seitensuche, sichere Originalbereitstellung soweit möglich; keine erfundenen Pixelkoordinaten |
| Finalisierung | menschliche Entscheidungen und Notizen bestimmen deterministischen Entwurf | P0: strukturiert bearbeiten, Vorschau, lokale TXT-/Markdown-Downloads, ausdrückliche Schlussfreigabe |
| API-Client | zentrale gepinnte HTTP-Verbindung mit Timeout, Antwortlimit und generischen Fehlern | P0: erhalten; typisierte Ansichtsverträge und erlaubte sichere Sperrgründe ergänzen |
| Session | aktuelle Assessment-ID, Widgetstate und flüchtige Backendrecords | P0: nachvollziehbare Rückkehr zu eigenen Fällen, sauberer Scopewechsel; keine Browserpersistenz |
| Quellen/Wissen | lokale Checks und versionierte Kandidaten bereits im Backend | P1: eigene Quellen-/Mosbach-Seite, Status/Gültigkeit und fehlende Freigaben sichtbar |
| Technik | echtes Legacy-Agentenmonitoring und Modell-/Sicherheitsdaten vorhanden | P1: getrennte Zentren, tatsächliche Metadaten, Mock-/Legacy-Kennzeichnung |
| Evaluation | CLI-Lab und lokale Reports, keine freigegebene Benchmark-Report-API | P1: diese Abhängigkeit sichtbar halten, keine UI-Kennzahlen erfinden |
| Polling | bisher gesamtes Control Center alle fünf Sekunden | P1: nur aktive Aufträge kontrolliert aktualisieren; keine automatische doppelte Joberstellung |
| Accessibility | native Streamlit-Labels, aber keine systematische neue Sichtprüfung | P0: klare Fokus-/Kontrasttokens, Tastaturtests und Screenreaderziele dokumentieren |
| Responsive | bestehende Spalten, sehr lange Detailansichten | P0: übersichtliche Karten, Desktopspalten und alternative Registerkarten für kleine Anzeigen |

## Architekturentscheidung

**Variante A: Streamlit beibehalten.** Version 1.67.0 und vorhandene FastAPI-,
Formular-, Fragment-, Dialog- und AppTest-Pfade decken den unterstützten Ablauf ab.
Eine React-Migration würde einen zweiten Zustands-/Test-/Buildpfad und neue
Abhängigkeiten erzeugen, ohne aktuelle organisatorische und fehlende Backendfreigaben
zu lösen. FastAPI bleibt Sicherheitsinstanz. Es gibt kein dauerhaftes zweites Frontend.

Die Produktansicht wird in App-Shell/Designkomponenten, Navigation, fachliche Seiten
und Review-/Evidenzkomponenten aufgeteilt. Vorhandene Entscheidungs- und API-Pfade
werden weiterverwendet. Statische Assets und Fonts bleiben lokal; Benutzerdaten
werden als Text oder sicher escaped ausgegeben. Keine neue Browserpersistenz.

## Implementierungsreihenfolge

1. Design-Tokens, App-Shell und Navigation festlegen; bestehende Sicherheitsbanner erhalten.
2. Dashboard, ACL-gefilterte Assessmentliste und geführte Anlage anbinden.
3. Unabhängige Erstbewertung, Vergleich, Belegnavigation und menschlichen Abschluss überarbeiten.
4. Quellen-, Mosbach-, Modell-, Agenten-, Sicherheits- und Statusseiten konsolidieren.
5. Fehlende Backendfunktionen ausdrücklich ausweisen; begrenztes Polling und Zustandswechsel prüfen.
6. AppTest/API-/Securityregressionen, lokale Desktop-/Tabletansicht und nach Möglichkeit
   echte Browserscreenshots mit ausschließlich synthetischen Daten prüfen.

## Implementierter Stand nach dem Umbau

Die vorherige Einzelseite ist durch eine gemeinsame Shell mit fachlichen und
technischen Seiten ersetzt. Die bestehende API-Anbindung bleibt zentral.
Dashboard/Fallliste, fünfstufige Anlage, unabhängige Erstbewertung mit ausdrücklichem
Sitzungsentwurf, neutraler Vergleich, Beleg-/Originalansicht, Quelleninspektor,
Richtlinienvorschau und menschlicher Kriterieneditor sind angebunden. Neue lesende
API-Projektionen ergänzen Fallliste, Modellmatrix und Richtlinienvorschau; eine
geschützte Binärroute liefert nur registrierte, erneut geprüfte PDF-Originale.

Streamlit bleibt das einzige Frontend. Die alten direkten Anlagefelder und der
Chat-Verbindungstest wurden aus dem Produktworkflow entfernt. Das Legacy Control
Center bleibt eine ausdrücklich benannte technische Seite. Daten-/Formularzustand
ist an die Begutachtungs-ID gebunden; persistenter Browser-/Dokumentcache wurde
nicht eingeführt. Nur aktive Jobs lösen Statuspolling aus.

Die neue PDF-Abhängigkeit `streamlit-pdf==2.1.0` ergänzt den offiziellen nativen
`st.pdf`-Pfad. Worker und Fonts sind im Wheel enthalten. Beide betroffenen
Python-Locks enthalten die PyPI-Artefakthashes; Docker kopiert die neuen Module
über eine explizit erweiterte Allowlist. Keine React-/Node-Buildkette für das Frontend.

Es wurden keine neuen Modellfreigaben, offiziellen Hochschulkriterien oder
gemessenen Modellfähigkeiten erzeugt. Fehlende Evaluations-Report-API, fehlende
Assessment-Teilagenten-Liveereignisse und nicht bestätigte PDF-Geometrie bleiben
ausdrücklich als Abhängigkeiten sichtbar.

## Weitere Dokumentation

- [Designsystem](design_system.md), [Komponenten](components.md), [Navigation](navigation.md)
- [Begutachtungsworkflow](review_workflow.md), [API-Anbindung](api_integration.md)
- [Barrierefreiheit](accessibility.md), [Sicherheit](security.md)
- [Tests und Browserprüfung](testing.md), [Abnahme und Grenzen](limitations.md)

WCAG-2.2-AA ist Entwicklungsziel, keine vorweggenommene Konformitätsbehauptung.

## Vorher / nachher und geänderte Dateien

| Vorher | Nachher |
|---|---|
| dunkle lange Seite mit Modelltest und Legacy-Graph | helle App-Shell, fachlicher Einstieg, getrennte technische Navigation |
| direkte kompakte Anlagefelder | fünfstufiger Assistent mit tatsächlichem Dokument-/Katalogangebot und Datenschutzbestätigung |
| lineare JSON-Vergleichsblöcke | neutraler Mensch-/KI-Vergleich, such-/filterbare Befundkarten, Tabs oder drei Spalten |
| ausschließlich Seitentext | Textleser, geschützte Original-PDF-Vorschau, Originalzitat mit Textoffsets und Versionshash |
| kein eigener Fallbestand im Frontend | ACL-gefilterte Metadatenliste mit echten Workflowzählern und Änderungszeitpunkten |
| immer aktives Legacy-Polling | Statusfragmente nur bei aktiven Jobs |
| kein expliziter Erstentwurfsspeicher | ausdrücklich gespeicherter fallbezogener Sitzungsentwurf mit Verlusthinweis |
| technische Status-/Quelleninformationen verteilt | eigene Quellen-, Richtlinien-, Modell-, Sicherheits- und Statusansichten |

Geänderte Produktdateien dieser Frontenditeration:

- `frontend/{app,api_client,assessment_review,control_center}.py`
- neue `frontend/{design,navigation,pages,viewmodels,evidence,sources}.py`
- `frontend/.streamlit/config.toml`, `frontend/requirements.{txt,lock}`,
  `requirements-dev.lock`, `.dockerignore`
- `backend/app/api/{assessments,control}.py`,
  `backend/app/workflows/assessment_workflow.py`
- `scripts/frontend_browser_qa.py`, neue UI-/Read-API-Regressionen und angepasste
  bestehende Anlage-/Evidence-/Pilot-/Gutachtertests unter `tests/integration`
- zwei synthetische DBLP-XML-Testfixtures unter `tests/unit`: ausschließlich
  punktuelle False-Positive-Kennzeichnung öffentlicher bibliografischer IDs
- diese zehn Frontenddokumente sowie README, Setup und Requirements-Traceability

Die vorherige Gutachterwerkzeug-Iteration ist separat im
[Checkpoint](../evaluation/reviewer_productivity_results.md) und
[Betriebs-/Recherchebericht](../research/reviewer_productivity_tools_2026-11-28.md)
beschrieben. Historische Auditbefunde wurden nicht rückwirkend als damalige
Implementierung umgeschrieben.
