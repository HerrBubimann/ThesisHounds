# Gutachterwerkzeuge: Lieferstand und lokale Prüfung

## Nachprüfung der vorhandenen Werkzeuge, 28.11.2026

Die folgende Ergänzung erweitert die bereits vorhandenen Komponenten nach der
Frontend- und Dokumentationsiteration; der ursprüngliche Bericht darunter bleibt
historisch erhalten. Ausgangspunkt dieser Nachprüfung sind 940 Tests.

Konkret korrigiert:

- teilweise gelesene numerische Schreibweisen werden mit Originalspanne angezeigt
  und von Vergleichen ausgeschlossen; negierte/hypothetische Werte verlangen
  Interpretation, bekannte Einheiten und Rundungsregeln bleiben erhalten;
- methodengebundene Checklisten markieren Negations-/Unsicherheits- und Zitatkontext;
  lange Originalkontexte zeigen die tatsächliche Fundstelle;
- Dublettenprüfung v2 erhält unterschiedliche Claims, Beziehungen, Stärken,
  Evidenz-/Gegenprüfzustände und Gegenbelege auch bei gleichem Kurztext;
- rechnerische Prozentabweichungen erzeugen gezielte beleggebundene Rückfragen;
- die bestehende Capability-Matrix enthält zusätzliche aggregierte Messwerte,
  Stichprobenzahlen, Mock-/Providerherkunft und explizite unbekannte Werte;
- der veraltete Pilot-Verweis in `.env.example` zeigt auf das vorhandene Setup.

Die Regressionen bestätigten zunächst 13 konkrete Fehlerfälle. Nach Korrektur
bestanden **64 gezielte Tests**, einschließlich vorhandener Freigabe-, ACL-,
Notiz-/Entwurfs- und Oberflächentests. Ruff lint/Format bestanden für die Änderungen.
Die fachlichen Daten sind synthetisch; daraus folgen weder bestätigte wissenschaftliche
Güte noch echte Modellleistung oder Gutachterakzeptanz.

Der anschließende vollständige Lauf bestand mit **956 Tests, keinen Fehlern/Skips,
87,06 % kombinierter Coverage und 100,79 s Laufzeit**. Das 80-%-Gate bleibt erhalten.
JUnit-/Coverage-Belege: `reports/junit-reviewer-refinement.xml`,
`reports/coverage-reviewer-refinement.json` und `.xml`.
Ruff lint/Format (221 Dateien), `pip check`, die sieben statischen Composevarianten
und Artifact-Privacy-Gate bestanden. Git-Whitespace-Prüfung berücksichtigt die
vorhandenen CRLF-Zeilenenden.
Bandit bestand am unveränderten MEDIUM-/MEDIUM-Gate: 17.755 Codezeilen,
0 blockierende Befunde, 0 Scanfehler (`reports/bandit-reviewer-refinement.json`).
Es wurden weder neue Abhängigkeiten noch Scanner-Ausnahmen ergänzt.

Der separate Mock-Lab-Lauf (`reports/reviewer-refinement-model-mock.json`) bearbeitete
33 Fälle für Qwen-/Mistral-/Llama-Konfigurationen und elf Dimensionen mit ausschließlich
gültigen Antwortschemata. Zwei angefragte parallele Jobs blieben auf einen bestehenden
Gateway-Modellslot begrenzt. Lade-/Token-/VRAM-Messungen blieben mangels echter Inferenz
unbekannt; die Matrix meldet dafür `null` und 0 Stichproben.
Neue Image-Builds, reale Parser-/Modelläufe und eine erneute Container-/Browserabnahme
wurden in dieser Nachprüfung nicht durchgeführt.

Die offiziellen Mosbacher Bibliotheksseiten sowie GROBID-/PP-StructureV3-Dokumentation
wurden erneut geprüft. Kontrollierte lokale RIS-/CSL-Importe bleiben der implementierte
Weg; keine Hochschuleinwahl, lizenzierte Massendownloads oder neue externe Verarbeitung.
Die konfigurierten Modellkandidaten haben weiterhin keine freigegebenen Artefakte
für eine echte lokale Pilotmessung. PP-StructureV3 bleibt optional und inaktiv.
Ursprüngliche Projektfolien, primäres Professorenfeedback und ein institutionell
bestätigter Detailkatalog liegen weiterhin nicht als neue Belege vor.

## Ursprünglicher Werkzeugdurchlauf

Stand 28.11.2026, Europe/Berlin, vor der anschließend angeforderten vollständigen
Frontend-Neugestaltung. Ausgangspunkt: 878 bestandene Tests. Aktueller Nachweis
dieses Backend-/Werkzeugdurchlaufs: **934 bestanden, keine Fehler/Skips,
87,09 % kombinierte Zeilen-/Branch-Coverage**, unverändertes 80-%-Gate.

Implementiert im vorhandenen Assessmentpfad:

- methodengebundene Dokumentationschecklisten mit Originalbelegen; keine Experimentausführung;
- kontextgebundene numerische Kandidaten, Einheiten-/Rundungsprüfung, Seeds/Runs/Folds,
  unsichere Tabellen-/Extraktionsbefunde und konservative Ergebnis-/Fazitvergleiche;
- lokale Dublettengruppen ohne Löschen oder Modellmehrheitsentscheidung; exakte ausgewählte
  Duplikate werden im Entwurf einmal mit nachvollziehbarer zusätzlicher Original-ID ausgegeben;
- Stärken, Schwächen, methodische Hinweise und Verbesserungsvorschläge mit gleicher Evidenzpflicht;
- kriteriums-/befundgebundene lokale Rückfragen, private versionierte Anmerkungen und
  ausdrücklich ausgewählte letzte Notizversionen im menschlichen Gutachtenentwurf;
- explizite serverseitige Sitzungszeitmessung nach Freigabe, ohne Zeitersparnisbehauptung;
- begrenzter lokaler RIS-/CSL-Metadatenimport im vorhandenen Snapshot Store mit separater
  Herkunfts- und Rechtebestätigung; kein Bibliothekslogin oder automatischer Volltextbezug;
- GROBID-TEI-Objekttexte/-zellen mit unbestätigtem Layout-/Koordinatenbezug;
- optionaler Ollama-NDJSON-Messpfad im selben Gateway, gemeldete Dauern/Tokenraten,
  erster sichtbarer Content-Chunk als Proxy und null für exakte TTFT/nicht gemessene Peaks;
- Infrastrukturwerte in der bestehenden Benchmark-Matrix und zusätzliche optionale
  Capability-Metadaten, ohne automatische Änderung von Routing oder Freigaben;
- zusätzliche Evaluationsvorhersagen und Qualitätsmetriken ausschließlich bei expliziten,
  dokument-/profilgebundenen Expertenadjudikationen.

Das trägt zu OFF-2/3/4/5 der bestehenden Traceability bei. Die ursprüngliche Projekt-
PowerPoint, primäres Professorenfeedback und ein bestätigter offizieller Detailkatalog
liegen hier nicht vor. Daraus wird keine amtliche Erfüllungs- oder Qualitätsabnahme abgeleitet.

## Tatsächlich ausgeführt

```powershell
.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --cov `
  --cov-report=xml:reports/coverage-reviewer-tools.xml `
  --cov-report=json:reports/coverage-reviewer-tools.json `
  --cov-report=term:skip-covered --junitxml=reports/junit-reviewer-tools.xml
```

Der vollständige Lauf dauerte 83,79 s und bestand. Neue Regressionen umfassen
Rechenfälle, abweichende Experimentkontexte und Metrikvarianten, ungesicherte Tabellen,
Methodenabgrenzung, Originalspannen, Dublettenschutz, bewahrte Gegenperspektiven,
Rückfragen, Rechte-/Formatgrenzen von Literaturimporten, Streaming-/Dispatchschutz,
Sitzungszeiten, Anmerkungsrevisionen/-widerruf, Freigabesperre, ACL und UI-Bedienung
über die tatsächliche FastAPI-Testanbindung. Die vollständige bisherige Suite blieb erhalten.

Ruff lint/Format, Compileall und `pip check` bestanden. Bandit meldete keine Befunde
am unveränderten MEDIUM-Severity-/Confidence-Gate. `pip-audit` prüfte alle vier
Hash-Locks ohne bekannte Befunde. Statische Composevalidierung aller sieben Varianten
bestand. Es wurden keine neuen Python-Laufzeitpakete benötigt. JUnit, Coverage und
Scannerbelege stehen unter dem ignorierten lokalen `reports/`.

## Aussagegrenzen und offene Voraussetzungen

Die fachlichen Tests sind synthetisch. HTTP-Streaming und Satz-/Vektormessungen in
Adaptertests sind keine echte Modellinferenz. Fachqualität, repräsentative Präzision/
Recall, tatsächliche Reproduzierbarkeit, Gutachterakzeptanz und Zeitersparnis bleiben
ohne passende reale Studie unbekannt; Referenzschnittstellen ersetzen keine Expertise.

Am Prüfzeitpunkt war der Docker-Linux-Daemon nicht erreichbar. Neue Containerstarts,
GROBID-Läufe, OCR-, GPU- und echte lokale Modellbenchmarks sowie Remote-GitHub-CI
wurden nicht ausgeführt. Freigegebene Modellartefakte, Hochschuleinsatz, offizieller
Bewertungskatalog und Zitierstil bleiben externe Voraussetzungen.

PaddleOCR PP-StructureV3 wurde anhand offizieller Dokumentation untersucht, nicht
installiert/aktiviert. Vollständige Pixelansicht, Diagramm-/Formelinterpretation und
expertisch validiertes Tabellenmapping sind noch keine implementierten Qualitätsnachweise.
Die aktuelle Oberfläche bietet extrahierte Objekttexte und Originalreferenzen.

Die Bibliotheksrecherche belegt Angebote und dokumentierte Zugangsbeschränkungen,
keine institutionsspezifische TDM-/API-Freigabe. Es wurden keine Zugangsdaten benutzt,
keine Bibliothekskontakte angeschrieben und keine kostenpflichtigen Abfragen ausgelöst.

Produktions-, Sperrvermerk-, Local-Only-, Netzwerk-, Modell- und Veröffentlichungsgrenzen
bleiben bestehen. Eigene Notizen und Erstbewertungen werden nicht an Modelle oder
öffentliche Recherche weitergegeben. Speicherung ist weiterhin flüchtig; kein neuer
Archiv-, Authentifizierungs- oder Backupnachweis wurde erzeugt.

Quellen, Bedienung, API-/CLI-Verträge und offene Bibliotheksfragen:
[Betriebs- und Recherchebericht](../research/reviewer_productivity_tools_2026-11-28.md).
