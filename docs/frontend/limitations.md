# Grenzen und Abnahme

Stand: 28.11.2026. Der Umbau erhält Streamlit/FastAPI und die bestehenden Schutzgrenzen.

- Ausschließlich synthetische / operatorgeprüfte öffentliche Testdateien; keine
  allgemeine PDF-Einlieferung und kein produktives Hochschulidentitätssystem.
- Keine offiziellen DHBW-Bewertungskriterien aus bloßen Kandidaten. Fehlende/
  widersprüchliche Mosbacher Freigaben müssen fachlich geklärt werden.
- Kein originales PDF für synthetische Textfixtures. Original-PDF-Vorschau nur für
  integritätsgeprüfte registrierte Dateien ohne Sicherheitsindikatoren. Kein
  OCR-Nachweis und keine erfundenen visuellen Koordinaten/Markierungen.
- Kapitel-/Seitenbezug basiert auf extrahiertem Text. PDF-Seite und Zitat werden
  getrennt navigiert; Layoutkoordinaten sind nicht automatisch synchronisiert.
- Erstentwürfe sind ausdrücklich in der Sitzung speicherbar, nicht dauerhaft.
  Gutachten- und Backenddaten können bei Neustart/Ablauf verloren gehen.
- RESTRICTED-Diskussion bleibt für nicht autorisierte Modelle gesperrt. Menschliche
  Prüfung erzeugt keine vorgetäuschte Discussion-Agent-Antwort.
- Assessment-Teilagenten haben noch keinen separaten Live-Event-Endpunkt. Sichtbar
  sind echte Workflowzustände und freigegebene Ergebnisprovenance. Der separate
  Legacy-Graph wird ausdrücklich als Legacy markiert.
- Keine Benchmark-Report-HTTP-API. Die vorhandene CLI bleibt der Auswertungsweg;
  die Modellmatrix zeigt nur tatsächlich vorhandene Registrierungsnachweise.
- TXT und Markdown sind lokale Exporte. PDF-/DOCX-Gutachtenexport ist nicht angebunden.
- WCAG 2.2 AA ist Ziel, keine bestätigte Vollkonformität. Screenreader und umfassende
  Zoom-/Kontrast-/Langdokumenttests stehen aus.
- Keine organisatorische Freigabe, abgeschlossene Zielhostabnahme oder garantierte
  DSGVO-Konformität. Keine automatisch berechnete Note oder automatische Abgabe.

## Ausgeführte lokale Abnahme

- Vollständiges pytest: **940 bestanden**, keine Fehler/Skips, **88,31 s**.
- Kombinierte Zeilen-/Branch-Coverage: **87,05 %**, unverändertes Minimum 80 %.
- Ruff, Formatprüfung, compileall und `pip check`: bestanden.
- Bandit: **0** Befunde oberhalb der bestehenden MEDIUM-/MEDIUM-Grenze.
- pip-audit: **101** Abhängigkeiten aus vier Hash-Locks, **0** bekannte Schwachstellen.
- Gitleaks 8.30.1: **13 Commits** ohne Secretfund. Zusätzlich aktueller Quell-/
  Konfigurations-/Dokumentationsstand mit **351 Dateien** offline gescannt; keine
  Secretfunde nach punktueller Erklärung zweier synthetischer öffentlicher DBLP-IDs.
  Nur diese zwei XML-Fixturezeilen tragen eine begründete Inlinekennzeichnung;
  keine globalen Regeln oder Schwellen wurden geändert. Die zugehörigen **30 Tests**
  bestanden nach der ausschließlich kommentierenden Fixtureänderung erneut.
- Trivy 0.76.2: beide gebauten Images gescannt. Die tatsächlich ausgeführte bestehende
  Schwelle `--ignore-unfixed --severity HIGH,CRITICAL --exit-code 1` besteht für beide
  mit Exit 0. Es wurden keine CVE-Ausnahmen hinzugefügt.
- Statische Sicherheits-/Konfigurationsprüfung aller **7** Compose-Varianten bestanden.
- Dockerfile-BuildKit-Prüfung aller drei vorhandenen Dockerfiles bestanden.
- Backend- und Frontend-Images tatsächlich gebaut. Getrennte temporäre Compose-
  Instanz mit Mock-LLM gesund gestartet; vorhandenes `ci_e2e.py` bis zur menschlichen
  Schlussfreigabe bestanden. Testcontainer und Projektnetzwerke danach entfernt.
- Echte Chrome-Sichtprüfung: Desktop 1440 px, Tablet 820 px, Mobilbreite 390 px;
  Dashboard ohne horizontales Überlaufen. Aktive Navigation und mobiler Titel korrigiert.
- Navigation, Assistent, Mosbach-Wissen, Security Center und freigegebener synthetischer
  Review mit drei Spalten wurden als Screenshots geprüft. Tab erzeugt sichtbaren Fokus.
- Im aufgezeichneten Browserlauf ausschließlich `http://127.0.0.1:8501` als
  HTTP-/WebSocket-Origin beobachtet; keine Browseranfrage an externe Dienste oder FastAPI.
  Dies ist ein lokaler Laufnachweis, keine vollständige Host-Egress-Abnahme.
- Zusätzlicher Original-PDF-Browserlauf mit generierter Testdatei und ausschließlich
  temporären Testfreigaben: ein tatsächlich gerenderter PDF-Canvas, Originalseite
  visuell bestätigt; ebenfalls ausschließlich lokaler Streamlit-Origin beobachtet.

Artefakte: `reports/junit-frontend.xml`, `reports/coverage-frontend.{xml,json}`,
`reports/frontend/full-tests.txt`, `reports/frontend/{before,after}-*.png`,
`reports/frontend/after-browser-checks.json`,
`reports/security/{bandit,pip-audit}-frontend.json`.

Containerartefakte: `reports/frontend/docker-{build,smoke,e2e,cleanup}.txt`;
PDF-Browsernachweis unter `reports/frontend/pdf-smoke/`.

Docker Desktop wurde für die lokalen Containerprüfungen gestartet. Der vollständige
GitHub-Workflow und der Lauf mit dem unveränderten realen Ollama-Upstreamimage wurden
für diesen Umbau nicht ausgeführt. Deshalb wird kein bestandener Gesamt-CI-/Merge-
Check behauptet. Die Ergebnisse der ergänzenden Image-/Secret-Scans werden separat
ausgewiesen.
Das verpflichtende `thesishounds-ci-gate` wurde nicht geändert.

## Offene Imagebefunde

Das unveränderte Debian-12.15-Basisimage meldet in **jedem** der zwei Images
**2 CRITICAL** und **95 HIGH** ohne verfügbaren Fix im ausgewerteten Datenbestand.
Die kritischen Scannerzuordnungen betreffen `CVE-2025-7458` / `libsqlite3-0`
(`affected`) und `CVE-2023-45853` / `zlib1g` (`will_not_fix`). Diese Rohzuordnung
ist keine Bestätigung der Erreichbarkeit im ThesisHounds-Workflow. Sie wird auch
nicht als vollständige Sicherheitsfreigabe behandelt. Unfixierte Befunde sind in
der bereits bestehenden CI-Imagepolitik nicht blockierend; die Produktionssperren
und ausstehenden organisatorischen/Hostnachweise bleiben bestehen.

Vollberichte: `reports/security/trivy-frontend-{backend,frontend}.json` und die
zugehörigen `trivy-{backend,frontend}-frontend-gate.txt`.
Secretberichte: `reports/security/gitleaks-frontend{,-working-tree}.json`.

## Lokale Vorschau

Nach Abschluss wurde eine getrennte lokale **Mock-Vorschau** über die vorhandene
CI-Composekonfiguration gestartet: Projekt `thesishounds-frontend-preview`,
Adresse `http://localhost:8501`. Keine realen Modelle oder privaten Arbeiten.
Startnachweis: `reports/frontend/docker-preview.txt`.
Beenden, ohne andere Projekte zu berühren:

```powershell
docker compose -p thesishounds-frontend-preview -f compose.yaml -f compose.ci.yaml down
```

Historische Zwischenergebnisse vor dem UI-Umbau stehen im
[Gutachterwerkzeug-Checkpoint](../evaluation/reviewer_productivity_results.md).
