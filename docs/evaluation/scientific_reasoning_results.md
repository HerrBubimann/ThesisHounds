# Wissenschaftliche Begutachtung Implementierung und Prüfungen

> Historischer Nachweis dieser Iteration. Testzahlen, Werkzeugverfügbarkeit und
> offene Infrastrukturprüfungen beziehen sich auf den unten genannten Prüfzeitpunkt.
> Aktueller konsolidierter Stand: [Validierung](../validation.md).

Stand 27.11.2026, Europe/Berlin. Die Erweiterung verbessert überprüfbare technische
Eigenschaften des vorhandenen Assessmentablaufs. Ein wissenschaftlicher Qualitätsgewinn
ist ohne reale lokale Inferenz und menschlich adjudizierte Referenzbefunde offen.
Es wurden ausschließlich Repositorycode und synthetische Tests verarbeitet.

## Bestandsaufnahme und Priorität

Geprüft wurden die vorhandenen Professorenfeedback-, Traceability- und Auditberichte
vom 27.11.2026 sowie Assessmentworkflow, semantische Planung, Citation Engine,
Evidenzvalidierung, IFC, PDF-Pilot, Evaluation und CI. Bereits vorhanden waren
semantische APPLIED/MENTIONED/UNCLEAR-Planung, Factory/Quoten, adversarielle Runden,
Originalspannen, lokale Quellensnapshots und versioniertes Feedback. Die ursprüngliche
Projekt-PowerPoint und neue institutionelle Freigaben liegen nicht vor. Die OFF-1–5-
Zuordnung folgt der vorhandenen Traceability, nicht einer erneuten Originalprüfung.

Zuerst wurden der vorhandene kontrollierte PDF-Pfad und die menschliche Finalisierung
geprüft: 30 gezielte Tests bestanden, mit echtem lokalen Parser und simulierten
Ollama-HTTP-Antworten. Anschließend bestand die Ausgangsbasis mit 737 Tests. Der erste
Sandboxlauf scheiterte an Temp-Verzeichnisrechten; die Wiederholung mit normalen
lokalen Testrechten bestand. Das ist kein behobener Anwendungsfehler.

Der Docker-Client ist vorhanden, der Docker-Daemon unter
`dockerDesktopLinuxEngine` ist nicht erreichbar. Ein Ollama-Binary wurde in den
geprüften Standardpfaden nicht gefunden. Neue Artefakt-/Modellfreigaben wurden nicht
erteilt; keine Gewichte heruntergeladen und keine Freigabe simuliert. Der echte lokale
LLM/PDF-Gesamtlauf bleibt deshalb Voraussetzung der nächsten fachlichen Abnahme.

## Geänderte bestehende Komponenten

| Komponente | Verhalten / Projektbeitrag |
|---|---|
| `assessments/schemas.py`, `scientific_consistency.py` | sieben Claimkategorien, Original-/Support-/Gegenbelege, Verknüpfung mit vorhandener Citation Engine, fehlende Evidenz getrennt von möglichem Fachfehler; OFF-3/5 |
| `agents/adaptive_assessment.py` | neun Methodenfamilien plus UNKNOWN mit wissenschaftlichen Prüffragen; nur semantische APPLIED-Vorschläge mit Originalbeleg und bestehendem Kriterium; keine zusätzliche verbindliche DHBW-Regel; OFF-2/3 |
| `adversarial_verification.py`, `escalation.py` | Critical-/Counter-Rollen im bisherigen Review, insgesamt begrenzte Dauer, konservativer deterministischer Arbiter und menschliche Konfliktübergabe; OFF-3/4 |
| `scientific_consistency.py`, `provenance.py`, `ai_review.py` | ORIGINAL_DOCUMENT, DETERMINISTIC_CHECK, MODEL_INTERPRETATION, UNVERIFIED_FINDING_PROPOSAL und HUMAN_CONFIRMED; Originalreferenzen erneut geprüft; Workflow `scientific-review.v3`; OFF-2/3/5 |
| `scientific_consistency.py` | JSON-Graph über fünfzehn Aspekte einschließlich Hypothesen, Quellen, Datensätzen und Experimenten; jede Kante CANDIDATE mit Belegen und menschlichem Semantikstatus; OFF-3/5 |
| `coverage.py`, `assessment_workflow.py`, Streamlit | Pflicht-/optionale Kriterien, Nichtbewertbarkeit, Teilfehler, Textlücken, Quellen-/Ressourcenlücken und offene menschliche Entscheidungen; deterministische Intervallvereinigung statt LLM-Prozentwert; OFF-2/3/5 |
| `schemas.py`, `assessment_workflow.py`, `evaluation/metrics.py`, Streamlit | normalisierte Feedbackzustände/-gründe und lokale Auswertung nach Modell/Agent/Kriterium/Fehler; letzte Version pro Befund, manuelle Prüfung sperrt Übernahme; OFF-1/4/5 |
| `evaluation/metrics.py`, `lab.py` | optionale menschliche Qualitätsannotation, Annotationsnenner, stärkere Befundfingerprints, Hashbindung für Ablationspaare; OFF-3/5 |
| `schemas/domain.py` | kompakte Ausgabeschemata entfernen ausschließlich Titelannotationen; alle Validierungsconstraints und konservativen Tokenbudgets bleiben erhalten |

Keine zweite Factory, Graphdatenbank, Modelltransportschicht, neue Abhängigkeit oder
externe Recherche. Institutionelle Profile für DHBW Mosbach Data Science und KI
werden nicht verändert oder durch Modellvorschläge freigegeben.

## Ausgeführte Prüfungen

Der endgültige vollständige Lauf bestand mit **779 Tests**, **0 Fehlern**, **0
übersprungenen Tests** und **87,28 %** kombinierter Statement-/Branch-Coverage bei
unveränderter Mindestschwelle **80 %**. Gegenüber der Ausgangsbasis sind das
**42 zusätzliche Regressionstests**. Neue Tests liegen in
`tests/unit/test_scientific_reasoning.py`, `test_scientific_evaluation.py`,
`tests/integration/test_scientific_reasoning.py` und
`tests/security/test_scientific_reasoning_boundaries.py`.
Der Gesamtlauf enthält **363 Securitytests**. JUnit bestätigt die vollständigen
Testzahlen; die bestehenden CI-Parser bestätigen Coverage und pip-audit-Bericht.

Ruff Lint und Format, Compileall und `pip check` bestanden. Bandit bestand mit dem
bestehenden MEDIUM-Severity/-Confidence-Gate. `pip-audit` bestand für alle vier
unveränderten Hash-Lockdateien ohne bekannte Befunde. Der erste eingeschränkte Audit
hatte keinen Netzwerk-/Cachezugriff; erst der abgeschlossene Lauf mit öffentlichen
Paketmetadaten ist der Prüfbeleg. Keine Dokumentdaten wurden dafür verwendet.

Alle sechs Compose-Varianten bestanden die statische Validierung. Der lokale
Artefakt-Canarycheck bestand. `thesishounds-ci-gate`, Pflichtjobs, 80-%-Schwelle und
bestehende Privacy-/Sperrvermerk-/IFC-/Berechtigungsregeln bleiben unverändert.
Git ist hier nicht als ausführbares Programm verfügbar; ein vollständiger Git-Diff-,
History-DLP- oder Gitleaks-Historynachweis wurde nicht erbracht. Keine Commits,
GitHub-Schreibzugriffe, Remote-Actions oder Veröffentlichungen ausgeführt.

## Kontrollierte Mockablation

Ausgeführt wurde `app.evaluation.lab --provider mock --architectures E --all-ablations
--repeats 1 --output-dir reports/scientific-ablation --max-total-model-calls 100`.
Vier Läufe vollständig, 33 Mockaufrufe, drei gepaarte Vergleiche mit identischen
Dokument-/Kataloghashes und genau einem geänderten Komponentenflag je Paar:

| Variante | Modellaufrufe |
|---|---:|
| Basis | 10 |
| Ohne Retrievalranking | 10 |
| Ohne adaptive Zusatzagenten | 9 |
| Ohne Gegenprüfung | 4 |

Die Zahlen sind Softwarebeobachtungen, keine Inferenzbenchmarks. Alle fachlichen
Gütemaße bleiben ohne echte menschliche Referenzen `null`. Die Skriptlabels in
Unit-Tests dienen allein der Metrikprüfung und sind kein Referenzkorpus. Laufzeiten
belegen keine menschliche Zeitersparnis. Einzelablationen nur der Claimextraktion
und des Graphen fehlen noch. Lokale JSON/CSV/JUnit/Coverage-Berichte liegen im
ignorierten `reports/`-Verzeichnis.

## Grenzen und nächste Abnahme

Es fehlt weiterhin ein freigegebener lokaler Modellbestand mit belegten Digests,
Lizenzen und Ressourcen sowie ein erreichbarer autorisierter Inferenzdienst. Darauf
folgen ein kontrollierter PUBLIC-PDF-Lauf und eine Expertenstudie mit identischen
Dokumenten/Kriterien, Wiederholungen und menschlichen Referenzbefunden. Die Modelle
müssen Claimextraktion, Methodeneinordnung und Gegenprüfung tatsächlich beherrschen;
Schema- und Mocktests beweisen das nicht.

Claim- und Quellenlinks bleiben Modellvorschläge; geerdete Zitate bestätigen weder
Argumentation noch Wahrheit. Graphlücken beweisen keine fehlenden wissenschaftlichen
Zusammenhänge. Methodeneinordnung ist semantisch vorgeschlagen, nicht fachlich
zertifiziert. Kontextabdeckung misst ausgewählte Zeichenintervalle, keine Vollständigkeit
von OCR, Bildern, Tabellen oder wissenschaftlichem Verständnis. Bei fehlgeschlagenem
Gesamtworkflow werden Teilbefunde weiterhin nicht freigegeben; erfolgreiche
Zwischenschritte sind dann nicht als vollständig begutachtet nachweisbar.

Gutachterfeedback bleibt RESTRICTED, lokal und am bestehenden TTL/Löschpfad. Keine
automatische Trainingsnutzung, kein Fine-Tuning und keine analyseübergreifende
Auswertung. Authentifizierung, dauerhafte manipulationsgeschützte Speicherung,
Zielhost-Netzabnahme, OCR/OS-Sandbox und rechtlich-organisatorische Freigaben bleiben
die vorhandenen Produktionsblocker. Bestehende Image-CVEs wurden ohne Docker nicht
neu gescannt; historische Scanberichte sind kein aktueller Nachweis.
