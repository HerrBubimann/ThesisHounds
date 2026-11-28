# Mosbach-/Quellen-Ergebnisse und Sicherheitsgrenzen

> Historischer Nachweis dieser Iteration. Testzahlen, Werkzeugverfügbarkeit und
> offene Infrastrukturprüfungen beziehen sich auf den unten genannten Prüfzeitpunkt.
> Aktueller konsolidierter Stand: [Validierung](../validation.md).

**Historischer Basisstand vor dem erneuten Security-Hardening.** Aktuelle Gesamtzahlen,
Gitleaks-/Trivy-Nachweise und weitere Korrekturen stehen im
[Hardening-Bericht](../security/hardening_results.md). Die folgenden 522 Tests und
damaligen Scanlücken beschreiben ausschließlich diese frühere Iteration.

Lokaler Nachweisstand: **27.11.2026, Europe/Berlin**. Ausschließlich synthetische
Fixtures, Quellcode und überprüfte öffentliche Hochschulunterlagen. Keine echte
wissenschaftliche Arbeit wurde geöffnet, an einen Dienst übertragen oder in CI verwendet.
Dies ist keine fachliche, rechtliche oder organisatorische Hochschulfreigabe.

## Implementiertes Ergebnis

Quellenregister und versionierte Kandidaten für PA1/DS25, PA2/DS24 und BA/DS23;
Mosbach-Hierarchie mit Prüfungsrechtsrahmen, Versions-/Freigabebindung und sichtbaren
Konflikten. Lokale öffentliche Bibliotheksimporte für PDF, DOCX/DOTX, XLSX,
Markdown, HTML, YAML und JSON. Keine erfundenen fehlenden Gewichte.

Deterministische Formalien mit konservativen Messgrenzen, lokale Zitations-/Referenz-
und Metadatenprüfung, kleine Crossref/OpenAlex/RW-Snapshots mit Provenienz/Hashes,
optional begrenzter Quellenqualitätsreview im bestehenden Gateway. Der öffentliche
ResearchGateway bleibt geschlossen. Andere Provider sind dokumentierte Registerkandidaten.

UI-/API-Auswahl von Studiengang/Jahrgang, Richtlinienherkunft/-versionen,
Ergebnisembargo auch für lokale Checks, Quellenstellen-Navigation und explizite
versionierte menschliche Prüfentscheidungen. Tasklöschung betrifft nur die eigene
Begutachtung. Importfehler, Vorlage-Dateitypen und neue Parserpfade wurden gehärtet.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Beobachtung | Aussagegrenze |
|---|---|---|
| Gesamte pytest-Suite | **522 bestanden, 0 Fehler, 0 übersprungen** | deterministische/mockbasierte technische Regressionen |
| Kombinierte Statement-/Branch-Coverage | **88,49 %**, unveränderte Mindestschwelle 80 % | keine Gleichsetzung von Coverage und Sicherheit |
| Ruff Lint/Format, Compileall | bestanden | statische Qualität/Syntax |
| Bandit | bestehende Schwelle mindestens MEDIUM Severity/Confidence bestanden | LOW-Befunde nicht als pauschal unbedenklich ausgeben; bestehende Regeln nicht abgesenkt |
| pip-audit, vier Hash-Lockdateien | keine bekannten Schwachstellen gefunden; erfolgreicher Exit | zeitpunktbezogene Datenbankabfrage, keine Garantie unbekannter Lücken |
| pip check | keine inkonsistenten Abhängigkeiten | keine fachliche Parserqualitätsprüfung |
| Compose-Validator | CPU, GPU, Provisioning, CI-Mock, University und optional GROBID statisch bestanden | University- und GROBID-Varianten nicht als echte Zielinfrastruktur ausgeführt |
| Backend-/Frontend-Dockerbuild | mit hashgebundenen Parserabhängigkeiten bestanden | keine produktive Image-/Hostabnahme |
| Docker Runtime/E2E | alle drei Healthchecks; Legacy D und Kriterium E bis menschliche Schlussfreigabe; Mosbach-Kandidaten/Embargo/Prüfentscheidung bestanden | In-Process-/Ollama-Mocks, keine echte Modellgüte |
| Kontrollierte Netzprobe | erlaubter gepinnter lokaler Mockaufruf; separater Testlistener aus Frontend-, Backend- und Ollama-Namespace nicht erreichbar | gezielter IPv4/TCP-Nachweis, kein vollständiger Hochschul-DNS-/IPv6-/Telemetrienachweis |
| Git-Index-DLP | 0 verbotene indizierte Pfade; Dateinamen/Inhalte unterdrückt | kein vollständiger semantischer Geheimnisscan freier Texte |
| Artefakt-Canary-Scan | bestanden | kein vollständiger Nachweis gegen paraphrasierte Lecks |
| Git diff --check | bestanden | keine Commit-/Push-/Mergeaktion erfolgt |

Die erste Paket-Audit-Ausführung konnte den Bericht wegen eines fehlenden
Berichtsverzeichnisses nicht schreiben; nach Anlage wurde der vollständige Lauf
mit erfolgreichem Exit wiederholt. Zu Beginn erforderte pytest Zugriff auf sein
temporäres OS-Verzeichnis; die Wiederholung in der freigegebenen lokalen Umgebung
bestand. Zwischenfehler werden nicht als fachliche Ergebnisse ausgegeben.

## Reproduzierbare synthetische Benchmarks

`python -m app.evaluation.academic_benchmark`: **6 Quellenfälle + 4 Formalienfälle**
bestanden, keine externen Anfragen. In den engen synthetischen Quellenfixtures
Reference-/Citation-Extraction jeweils Precision/Recall/F1 = 1,0. Keine repräsentative
Genauigkeit echter DHBW-Arbeiten, keine GROBID-/OCR-/Experten-/Modellqualitätsstudie.
Siehe [Quellenbenchmark](citation_benchmark.md) und [Formalienbenchmark](formal_compliance_benchmark.md).

`python -m app.evaluation.privacy_lab`: **12 Szenarien je Architektur, 48 Durchläufe**,
nur kontrollierte Memory-Sinks:

| Variante | Blockierte Aktionen | Unerlaubt zugelassene Aktionen | Einordnung |
|---|---:|---:|---|
| A: ungeschützter Testadapter | 0 | 11 | absichtlich unsicher, kein Runtimeprovider |
| B: deterministisch ignorierter Promptmock | 0 | 11 | kein empirischer Modelltest |
| C: Privacy Policy | 9 | 2 | isolierte Abstraktion ohne IFC/Zielprüfung |
| D: Policy + IFC + Zielprüfung | 11 | 0 | ein erlaubter PUBLIC-Lokalaufruf bleibt zugelassen |

Diese Ablation verwendet echte Prüffunktionen, simuliert aber Aktionen und
fehlende Kontrollen. Sie misst weder echte LLM-Gehorsamkeit noch reale Netzisolation,
Subagentensandboxen oder sämtliche Logging-/Telemetriepfade. Diese Komponenten
werden zusätzlich durch eigene Regressionen beziehungsweise die kontrollierte
Docker-Netzprobe geprüft. Canarywerte werden nicht in den Ergebnisbericht exportiert.

## Nicht ausgeführte oder noch fehlende Nachweise

- Kein GitHub-Actions-Lauf ausgelöst; kein Remote-Ruleset-/Mergeschutznachweis verändert.
  Die lokale Prüfung ersetzt keine tatsächliche erfolgreiche Remote-Pipeline.
- Kein lokaler vollständiger Gitleaks-History- oder Trivy-Imagescan in dieser Iteration.
  Die bestehenden verpflichtenden CI-Scans bleiben aktiv.
- Kein konkretes freigegebenes GROBID-Image gestartet; Extraktionsqualität, restriktive
  UID-/Scratch-Konfiguration und echte Prozess-Egresssperre bleiben abzunehmen.
- Keine realen lokalen LLM-/GPU-Benchmarks, Expertenreferenzen, Nutzungs-/Biasstudie
  oder fachliche Validierung der neuen Quellenqualitätsvorschläge.
- Box-/Palleduhn-Original nicht verfügbar. Neuere/jahrgangsgebundene Fakultätsfassung,
  StuPrO-Übergangsrecht und erkannte Seitenzähl-/Abstractkonflikte nicht freigegeben.
- Hochschul-SSO, echte Mandantenrechte, Verschlüsselung/Backups/Swap, TLS-Identität,
  Host-DNS/IPv6, Parser-Sandbox, offizielle Aufbewahrung sowie Rechts-/DSFA-/KI-VO-
  und organisatorische Freigabe weiterhin offen.

Echte Dokumente, private Katalogimporte und UNIVERSITY_SECURE-Verarbeitung bleiben
technisch gesperrt. Bekannte Restrisiken stehen im [Risikoregister](../security/risk_register.md),
die erforderlichen Freigaben in der [Checkliste](../security/security_release_checklist.md).
