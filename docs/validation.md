# Tatsächlich ausgeführte Validierung

Nachweisstand: **28.11.2026, Europe/Berlin**. Die folgende Übersicht trennt
ausgeführte lokale Prüfungen, frühere Nachweise und offene Abnahmen. Auf die
abgeschlossene Markdown-Pflege folgte eine Implementierungsnachprüfung der
Gutachterwerkzeuge mit neuen lokalen Tests.

## Nachprüfung der Gutachterwerkzeuge

Die vollständige Suite besteht mit **956 Tests, 0 Fehlern, 0 Fehlschlägen und 0 Skips**.
Laufzeit: **100,79 s**; kombinierte Zeilen-/Branch-Coverage: **87,06 %**.
Das Coverage-Minimum bleibt **80 %**, `thesishounds-ci-gate` unverändert.
Die 16 zusätzlichen Regressionen prüfen insbesondere unvollständige Zahlen,
Negation/Unsicherheit, Originalkontext, unterschiedliche Befundperspektiven,
rechnerische Rückfragen und aggregierte Infrastrukturmetriken.

Lokale Belege: `reports/junit-reviewer-refinement.xml`,
`reports/coverage-reviewer-refinement.json` und
`reports/coverage-reviewer-refinement.xml`. Ruff lint und Formatprüfung
(221 Python-Dateien), `pip check`, die sieben statischen Composevarianten,
Git-Whitespace-Prüfung und Artifact-Privacy-Gate bestanden.
Bandit prüfte 17.755 Codezeilen in Backend, Frontend und Infrastruktur mit
**0 Befunden am MEDIUM-Severity-/MEDIUM-Confidence-Gate und 0 Scanfehlern**;
Beleg: `reports/bandit-reviewer-refinement.json`. Dependency-Locks blieben
unverändert; die früheren pip-audit-/Imagescanergebnisse wurden nicht neu erzeugt.

Ein separater Mock-Lab-Lauf enthält **33 Fälle**, drei Modellkonfigurationen
(Qwen/Mistral/Llama) und elf Capability-Dimensionen. Alle Antwortschemata waren
gültig. Bei zwei angefragten parallelen Jobs blieb der beobachtete Modelldispatch
wie konfiguriert bei eins. Beleg: `reports/reviewer-refinement-model-mock.json`.
Die neue Matrix hält unbekannte Modellmessungen auf `null`, mit Stichprobenzahl 0;
es wurden keine realen Gewichte, exakte TTFT oder fachliche Modellgüte vermessen.

Diese Nachprüfung enthält keine neuen Image-Builds, keine neue Container-/Browser-
oder Zielhostabnahme und keinen Remote-CI-Lauf. Die vorhandenen entsprechenden
Nachweise beziehen sich auf die vorherige Frontenditeration.
Änderungen und fachliche Grenzen: [Werkzeugbericht](evaluation/reviewer_productivity_results.md).

## Frontendnachweis vor der Werkzeugnachprüfung

Die Quellbasis entspricht Version 0.2.0. Der vorhandene JUnit-Bericht
`reports/junit-frontend.xml` weist **940 Tests, 0 Fehler, 0 Fehlschläge und 0 Skips**
aus; `reports/coverage-frontend.json` enthält **87,05 %** kombinierte Zeilen-/
Branch-Coverage. Host-Python: **3.12.6**; Docker/CI pinnen **3.12.16**.
Das unveränderte Coverage-Minimum beträgt **80 %**.

| Prüfung vom 28.11.2026 | Vorhandener Nachweis / Ergebnis |
|---|---|
| Gesamte pytest-Suite | 940 bestanden; Konsolenlauf 88,31 s; JUnit und Coverage unter `reports/` |
| Ruff, Format, compileall, pip check | bestanden; zuletzt für den Frontendstand protokolliert |
| Bandit / vier Hash-Locks | 0 blockierende MEDIUM-/MEDIUM-Befunde; pip-audit: 101 Pakete, 0 bekannte Schwachstellen |
| Gitleaks 8.30.1 | 13 Commits ohne Fund; zusätzlich 351 aktuelle Quell-/Konfigurations-/Dokumentationsdateien offline geprüft |
| DBLP-Fixture-False-Positives | zwei synthetische öffentliche Literatur-IDs punktuell erklärt, keine globalen Regeln geändert; 30 zugehörige Tests danach erneut bestanden |
| Compose-Konfiguration | 7 Varianten statisch geprüft: CPU, GPU, Provisioning, CI-Mock, University, GROBID, öffentlicher Sync |
| Dockerfile-Prüfung | BuildKit-Checks für Backend, Frontend und Ollama-Dockerfile bestanden |
| Tatsächliche Image-Builds | Backend und Frontend gebaut |
| Container-E2E | getrennter Mock-Stack gesund; bestehendes `ci_e2e.py` bis zur menschlichen Finalisierung bestanden; Testinstanz bereinigt |
| Trivy 0.76.2 | beide App-Images gescannt; bestehende Schwelle für behebbare HIGH-/CRITICAL-Befunde jeweils Exit 0 |
| Browserprüfung | Desktop 1440 px, Tablet 820 px, Mobilbreite 390 px; Navigation, Assistent, Reviewspalten und Fokus geprüft |
| Original-PDF-Viewer | generierte öffentliche Testdatei; tatsächlich gerenderter Canvas; nur lokaler Streamlit-Origin im aufgezeichneten Lauf |

**Alle Modellantworten dieser Nachweise sind MOCK/SYNTHETIC.**
Sie belegen Kontrollfluss, Schema-/Policy-/Budget-/Scopegrenzen und UI-Verhalten,
keine reale Modellgüte, exakte TTFT oder wissenschaftliche Wirksamkeit.

Vollständige Abgrenzung und Artefaktpfade:
[Frontend-Abnahme](frontend/limitations.md),
[Gutachterwerkzeug-Checkpoint](evaluation/reviewer_productivity_results.md).
Die Dateien unter `reports/` sind lokale generierte Nachweise und werden nicht
als dauerhaft verfügbare Repositoryartefakte vorausgesetzt.

## CI, Sicherheit und verbleibende Abnahme

Der Workflow enthält **acht Pflichtjobs plus `thesishounds-ci-gate`**.
`privacy-security` und dessen Berichte gehören dazu. Lokale Einzelprüfungen sind
kein erfolgreicher vollständiger GitHub-Lauf. Die Rulesetdatei und Anleitung sind
vorhanden; die aktuelle Remote-Aktivierung und ein Merge-Schutz-Abnahmetest sind
in dieser Dokumentationspflege nicht überprüft worden.

Beide zuletzt gescannten Debian-12.15-App-Images melden je 2 CRITICAL- und 95 HIGH-
Zuordnungen ohne verfügbaren Fix im ausgewerteten Scannerbestand. Dazu gehören
`CVE-2025-7458` / `libsqlite3-0` und `CVE-2023-45853` / `zlib1g`.
Die unveränderte CI-Schwelle besteht, ist aber keine Aussage zur Erreichbarkeit,
vollständigen Schwachstellenfreiheit oder Produktivfreigabe.
[Restrisiken](frontend/limitations.md#offene-imagebefunde).

Weiter offen:

- freigegebene Modellartefakte/Digests, positiver echter lokaler Modelllauf,
  Zielhardware, GPU-/VRAM-/Offline- und Modellpersistenznachweise;
- reale GROBID-/Encoder-/CSL-/LanguageTool-Abnahme, visuelle Extraktions-/OCRqualität
  und vollständige OS-Parserisolation für private Dokumente;
- genehmigter Detailkatalog, primäres Professorenfeedback, Expertenreferenzen und
  fachliche Nutzen-/Fairness-/Zeitersparnisstudie;
- Hochschulidentität, produktive Zuweisung, TLS-/Netz-/Speicher-/Backup-/Löschabnahme,
  geschütztes Audit und organisatorische Freigaben;
- vollständiger Remote-CI-Lauf einschließlich realem Ollama-Upstreamimage;
- umfassende Screenreader-/Zoom-/Barrierefreiheitsabnahme.

Die lokale Mock-Vorschau wurde als Projekt `thesishounds-frontend-preview` gestartet.
Das ist ein protokollierter Start, keine dauerhaft garantierte Laufzeitadresse.
Start/Stop und aktuelle Betriebsparameter stehen im [Setup](setup.md).

## Historische Prüfstände

Frühere Zahlen werden nicht als heutiger Gesamtnachweis ausgegeben.

| Historischer Stand | Ergebnis / Bericht |
|---|---|
| Foundation, 26.11.2026 | 154 Tests (75 Unit, 42 Integration, 37 Security), 85,1 % Coverage; damalige fehlende Engine-/Scannerabnahme ist überholt |
| Wissenschaftliches Engineering | [448 Tests](evaluation/results.md) |
| Security-Hardening | [568 Tests und damalige Imagebefunde](security/hardening_results.md) |
| Advanced Review | [627 Tests](evaluation/advanced_review_results.md) |
| Semantische Planung | [699 Tests](evaluation/semantic_planning_results.md) |
| Dokumentsicherheit | [737 Tests](evaluation/security_results.md) |
| Parallele Prüfungen | [878 Tests](evaluation/parallel_review_results.md) |
| Gutachterwerkzeuge vor UI-Umbau | [934 Tests](evaluation/reviewer_productivity_results.md) |

Die fehlenden historischen `docs/audit/`- und `docs/remediation/`-Dateien wurden
nicht rekonstruiert oder als neue Belege erfunden. Aktuelle Anleitungen und
Requirements stehen in [Setup](setup.md) und [Traceability](requirements/traceability.md).

## Dokumentationsprüfung vom 28.11.2026

Diese Dokumentationsänderung ist ausschließlich auf Markdown begrenzt. Projektcode,
Konfiguration, Tests, Dependency-Locks und bestehende individuelle Anweisungen
werden nicht verändert. Generierte Dateien, Laufzeitdaten, externe Abhängigkeiten,
Vendor-/Cacheverzeichnisse und Git-Metadaten sind nicht Teil der Dokumentpflege.

Die Prüfung umfasst **113 Markdown-Dateien** in allen relevanten Unterverzeichnissen:
**57 aktualisiert, 56 ohne Änderungsbedarf**. Die Zählung bezieht sich auf den
Dateistand zu Beginn dieser Dokumentationsaufgabe; bereits vorhandene
Benutzeränderungen zählen nicht als neu vorgenommene Änderungen.

### Inhaltliche Korrekturen

- Architektur, Technologien, Versionsangaben, Schnittstellen und Startbefehle
  wurden mit Quellcode, Konfiguration und vorhandenen Prüfarbelegen abgeglichen.
- DemoProvider, kontrollierter PUBLIC-Pilot und noch offene Produktionsfreigabe
  sind getrennt beschrieben. Die Basis-Compose-Datei übernimmt Pilotparameter
  nicht automatisch aus der Host-Konfiguration.
- Sechs parallele Fachprüfungen, acht implementierte Metadatenadapter,
  Gutachteroberfläche und menschlich freigegebene TXT-/Markdown-Exporte sind
  dokumentiert; geplante Funktionen werden als solche gekennzeichnet.
- CI-Jobstruktur, lokale Prüfskripte, aktuelle Sicherheitsbefunde und historische
  Teststände wurden berichtigt. Historische Ergebnisse und individuelle
  Anweisungen bleiben erhalten.
- Zehn Verweise auf fehlende historische Remediation-Dateien wurden korrigiert;
  überholte Pfadangaben, Sprungmarken und beschädigte Sonderzeichen wurden bereinigt.

### Abschließende Prüfungen

- Alle relevanten Markdown-Dateien wurden erneut geparst; relative Links,
  Sprungmarken und überprüfbare Projektpfade haben gültige Ziele.
- **56 Codeblöcke** wurden statisch geprüft, darunter JSON-/Python-Syntax
  und die dokumentierten Optionen von **16 Projekt-CLIs** anhand des Quellcodes.
  Diese Dokumentationsprüfung enthält keinen neuen Laufzeitnachweis.
- Ein vorhandener Markdown-Linter samt Konfiguration wurde nicht gefunden.
  Ersatzweise wurden Markdown-Parsing, Link-/Pfadprüfung, UTF-8 und
  Whitespace-Prüfungen ausgeführt.
- Der Git-Diff wurde kontrolliert. Die Whitespace-Prüfung berücksichtigt die
  vorhandenen Windows-Zeilenenden (`core.whitespace=cr-at-eol`).
  Ein Hashvergleich mit dem Aufgabenbeginn weist keine Änderungen außerhalb
  von Markdown nach. Es wurden keine Dokumentationsdateien neu angelegt oder gelöscht.
- Es wurde weder ein Git-Commit erstellt noch ein Git-Push ausgeführt.

### Offene oder nicht verifizierbare Punkte

Reale Modellqualität und Ressourcenmessungen, produktive Identitäten/SSO,
Freigaben für vertrauliche Dokumente, vollständige PDF-Isolation und
Barrierefreiheitsabnahme bleiben offen. Der aktuelle Remote-CI-/Ruleset-Zustand
und historische externe Quellen wurden nicht erneut unabhängig verifiziert.
Die konkreten Grenzen und vorhandenen lokalen Prüfarbelege stehen in den
vorangehenden Abschnitten dieses Dokuments.

Nicht-Markdown-Dateien wurden entsprechend dem Auftrag unverändert gelassen.
Zum damaligen Dokumentationsabschluss gehörte dazu ein historischer Remediation-Pfad
in `.env.example`. Er wurde im anschließenden Implementierungsauftrag korrigiert;
die Markdown-Verweise waren bereits hier bereinigt.

### Aktualisierte Dateien

- [Erklärungs.md](../Erklärungs.md)
- [README.md](../README.md)
- [docs/architecture.md](architecture.md)
- [docs/architecture/assessment_mvp.md](architecture/assessment_mvp.md)
- [docs/architecture/context_management.md](architecture/context_management.md)
- [docs/architecture/implementation_status.md](architecture/implementation_status.md)
- [docs/architecture/model_routing.md](architecture/model_routing.md)
- [docs/ci-cd.md](ci-cd.md)
- [docs/decisions/001-independent-assessment-mvp.md](decisions/001-independent-assessment-mvp.md)
- [docs/decisions/002-inference-and-research-boundaries.md](decisions/002-inference-and-research-boundaries.md)
- [docs/decisions/004-mandatory-coverage-and-adversarial-review.md](decisions/004-mandatory-coverage-and-adversarial-review.md)
- [docs/decisions/005-source-spans-and-offline-verification.md](decisions/005-source-spans-and-offline-verification.md)
- [docs/decisions/006-comparable-synthetic-experiments.md](decisions/006-comparable-synthetic-experiments.md)
- [docs/dhbw/source_versions.md](dhbw/source_versions.md)
- [docs/evaluation.md](evaluation.md)
- [docs/evaluation/advanced_review_results.md](evaluation/advanced_review_results.md)
- [docs/evaluation/automation_bias.md](evaluation/automation_bias.md)
- [docs/evaluation/benchmark_metrics.md](evaluation/benchmark_metrics.md)
- [docs/evaluation/experiment_design.md](evaluation/experiment_design.md)
- [docs/evaluation/limitations.md](evaluation/limitations.md)
- [docs/evaluation/model_benchmarks.md](evaluation/model_benchmarks.md)
- [docs/evaluation/mosbach_results.md](evaluation/mosbach_results.md)
- [docs/evaluation/parallel_review_results.md](evaluation/parallel_review_results.md)
- [docs/evaluation/performance.md](evaluation/performance.md)
- [docs/evaluation/public_research_results.md](evaluation/public_research_results.md)
- [docs/evaluation/results.md](evaluation/results.md)
- [docs/evaluation/scientific_reasoning_results.md](evaluation/scientific_reasoning_results.md)
- [docs/evaluation/security_evaluation.md](evaluation/security_evaluation.md)
- [docs/evaluation/security_results.md](evaluation/security_results.md)
- [docs/evaluation/semantic_planning_results.md](evaluation/semantic_planning_results.md)
- [docs/evaluation/test_cases.md](evaluation/test_cases.md)
- [docs/requirements/traceability.md](requirements/traceability.md)
- [docs/research/citation_verification.md](research/citation_verification.md)
- [docs/research/existing_solutions.md](research/existing_solutions.md)
- [docs/research/free_api_providers.md](research/free_api_providers.md)
- [docs/research/local_scientific_infrastructure.md](research/local_scientific_infrastructure.md)
- [docs/research/model_evaluation.md](research/model_evaluation.md)
- [docs/research/parallel_scientific_checks.md](research/parallel_scientific_checks.md)
- [docs/research/research_privacy.md](research/research_privacy.md)
- [docs/research/state_of_the_art.md](research/state_of_the_art.md)
- [docs/security.md](security.md)
- [docs/security/data_classification.md](security/data_classification.md)
- [docs/security/data_flow.md](security/data_flow.md)
- [docs/security/data_processing_overview.md](security/data_processing_overview.md)
- [docs/security/gap_analysis.md](security/gap_analysis.md)
- [docs/security/hardening_results.md](security/hardening_results.md)
- [docs/security/network_isolation.md](security/network_isolation.md)
- [docs/security/pdf_security.md](security/pdf_security.md)
- [docs/security/privacy_architecture.md](security/privacy_architecture.md)
- [docs/security/privacy_test_results.md](security/privacy_test_results.md)
- [docs/security/production_readiness.md](security/production_readiness.md)
- [docs/security/risk_register.md](security/risk_register.md)
- [docs/security/sperrvermerk_policy.md](security/sperrvermerk_policy.md)
- [docs/security/toms_draft.md](security/toms_draft.md)
- [docs/setup.md](setup.md)
- [docs/stakeholders/open_questions.md](stakeholders/open_questions.md)
- [docs/validation.md](validation.md)
