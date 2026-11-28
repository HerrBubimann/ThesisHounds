# Erneutes Privacy-/Security-Hardening: lokale Ergebnisse

> Historischer Nachweis dieser Iteration. Testzahlen, Werkzeugverfügbarkeit und
> offene Infrastrukturprüfungen beziehen sich auf den unten genannten Prüfzeitpunkt.
> Aktueller konsolidierter Stand: [Validierung](../validation.md).

Dieser Bericht beschreibt die vorherige Sicherheitsiteration. Der anschließende
[Advanced-Review-Stand](../evaluation/advanced_review_results.md) enthält aktuelle
Gesamttestzahlen, weitere Privacyregressionen und Scans der neuen App-Images.

Nachweisstand: **27.11.2026, Europe/Berlin**. Technische Arbeitsgrundlage, keine
rechtliche, fachliche oder organisatorische Hochschulfreigabe. Ausschließlich
Quellcode, synthetische Fixtures und geprüfte öffentliche Unterlagen; keine echte
Arbeit wurde geöffnet oder an einen Dienst übertragen. UNIVERSITY_SECURE und echte
Dokumenteingänge bleiben technisch gesperrt.

## Gefundene Lücken und Umsetzung

Die [Gap Analysis](gap_analysis.md) dokumentiert Priorität, Maßnahme und Grenze je
Fund. Ergänzt wurden Backend-IP-Pinning im Frontend, ein eigenständiges Online-
Provisioning ohne Processing-Netze, erforderliche Modellprovenienz und volle
Ollama-Manifest-Digests, IFC-Metadaten an Bibliografie-/DOI-Zwischenergebnissen,
Request-/Antwortlimits und Deadlines sowie konservative lokale Sperrvermerkdetails.
GROBID-XML-Fehler werden generisch ausgegeben. Der zur Laufzeit unnötige, von Trivy
beanstandete pip-Installer wurde nach der Hashinstallation aus beiden App-Images
entfernt. Keine institutionelle Modellfreigabe oder Digestwerte wurden erfunden.

46 zusätzliche Regressionen gegenüber dem Mosbach-Basisstand prüfen insbesondere
DNS-Rebinding, Redirects, Requestoptionen, Übergrößen vor Zustandsänderungen,
Modelltagwechsel vor Promptversand, Provisioning-Freigaben/Lifecycle und
Klassifizierungs-/Scope-Erhalt. Bestehende Schwellen und Scannerregeln bleiben erhalten.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Beobachtung | Aussagegrenze |
|---|---|---|
| Vollständiges pytest mit JUnit/Coverage | **568 bestanden, 0 Fehler, 0 übersprungen** | deterministische technische Regressionen, überwiegend Mocks |
| Kombinierte Statement-/Branch-Coverage | **88,59 %**, unveränderte Mindestschwelle 80 % | kein Sicherheitsbeweis |
| Ruff Lint/Format, Compileall, pip check | bestanden | statische Qualität/Syntax bzw. Konsistenz |
| Bandit | mindestens MEDIUM Severity/Confidence: 0 gefilterte Befunde, 0 Analysefehler | bestehende LOW-Befunde nicht pauschal freigegeben |
| pip-audit über alle vier Hash-Lockdateien | keine bekannten Schwachstellen gemeldet, Exit 0 | Paketmetadatenabfrage zum Prüfzeitpunkt; OS-Pakete separat gescannt |
| Compose-Validator | CPU, GPU, eigenständiges Provisioning, CI-Mock, University, optional GROBID bestanden | Konfigurationsprüfung, keine Hochschul-/GROBID-Abnahme |
| Backend-/Frontend-Build und Runtime | endgültige Images ohne pip gebaut, alle drei Services gesund | Ollama-Service ist der kontrollierte HTTP-Mock |
| Docker-E2E | Legacy D, Kriterium E, Mosbach-Kandidaten/Embargo, menschliche Entscheidung und Finalisierung bestanden; echter gepinnter Frontendclient positiv geprüft | keine reale Modell-/GPU-/Biasstudie |
| Docker-Netzprobe | erlaubte gepinnte lokale Mock-Inferenz; kontrollierter separater Listener aus **3** privaten Namespaces nicht erreichbar | IPv4/TCP zum Testlistener; kein vollständiger Internet-/Hochschul-DNS-/IPv6-Nachweis |
| Gitleaks 8.30.1, Git-History | 5 lokale Commits, keine Leaks gemeldet, Exit 0 | keine Garantie gegen unbekannte/semantische Geheimnisse |
| Gitleaks, aktueller Arbeitsbaum | nur per Git/DLP zugelassene Quelldateien, keine Leaks gemeldet, Exit 0 | ignorierte/private Pfade nicht geöffnet; kein Komplettscan der Festplatte |
| Git-Index-DLP / Artefakt-Canaries | 0 verbotene indizierte Pfade; Report-Canary-Prüfung bestanden | Pfad-/Markerprüfung ist keine vollständige Inhaltsklassifikation |
| Git diff --check | mit Windows-CRLF-Berücksichtigung bestanden | keine Commit-/Push-/Remoteänderung erfolgt |
| Trivy 0.76.2, beide endgültigen App-Images | vollständige Offlineberichte; Gate für **behebbare HIGH/CRITICAL** jeweils Exit 0 | erhebliche offene OS-Befunde, siehe unten; upstream Ollama/GROBID nicht gescannt |

JUnit, Coverage, Bandit, pip-audit, Gitleaks und Trivy liegen lokal unter `reports/`
und werden nicht ins Repository aufgenommen. Scannerbinaries/Archive/DB liegen
ebenfalls ausschließlich in ignorierter lokaler Laufzeitablage. Keine realen
Dokumente, Modell-Volumes oder Zugangsdaten wurden an Scanner gemountet.

Die GitHub-Actions-Konfiguration enthält weiterhin den verpflichtenden
`privacy-security`-Job samt Canary-/DLP-/Benchmarkprüfungen. Fehlende, leere,
fehlgeschlagene oder übersprungene Nachweise blockieren das abschließende CI-Gate.
Die neuen Securitytests werden über dessen bestehende Verzeichnisauswahl erfasst.
**Kein Remote-Actions-Lauf und keine Änderung von Branchschutz/Rulesets erfolgte.**

## Containerbefunde und Beschaffungsgrenze

Trivy-DB: UpdatedAt **2026-11-26 19:04:08 UTC**, lokal bezogen **23:55:13 UTC**.
Die öffentlichen DB-Daten wurden in einer getrennten Online-Umgebung ohne
Repository-/Image-/Dokumentenmount bezogen. Beide eigentlichen Imagescans sowie
deren Gates liefen mit `--network none --offline-scan --skip-db-update`.

| Endgültiges Image | LOW | MEDIUM | HIGH | CRITICAL | UNKNOWN | Behebbare HIGH/CRITICAL | Python-Paketbefunde |
|---|---:|---:|---:|---:|---:|---:|---:|
| Backend | 114 | 148 | 100 | 2 | 18 | 0 | 0 |
| Frontend | 114 | 148 | 100 | 2 | 18 | 0 | 0 |

Je Image 382 gemeldete Paket-/CVE-Zuordnungen der Debian-12.15-Basis. Gemeinsame
Pakete werden je Image erneut gezählt. CRITICAL: `CVE-2025-7458` für `libsqlite3-0`
(Status `affected`) und `CVE-2023-45853` für `zlib1g` (Status `will_not_fix`), jeweils
ohne vom Scanner gemeldete FixedVersion. Es wurde weder tatsächliche Ausnutzbarkeit
noch Unbedenklichkeit nachgewiesen. Die Bewertung durch Security und ein geeigneter
Patch-/Basisimageplan bleiben Produktionsblocker. Keine Ignore-Ausnahme wurde ergänzt.

Der erste Scan enthielt zusätzlich sechs pip-Befunde (fünf MEDIUM, ein LOW).
Nach Entfernung des Runtime-Installers und erneutem Build meldete Trivy diese
nicht mehr. Ein bestandenes bestehendes Fixable-Gate bedeutet ausdrücklich keine
Schwachstellenfreiheit. Die vollen Berichte bleiben zur Prüfung erhalten.

Geprüfte endgültige Image-IDs:

- Backend: `sha256:e297df0b4e2a84b9f464e7e2e75ef64460b269c371df609fb61213672bdacc31`
- Frontend: `sha256:9da8ccae0f1520add0c53b72a8d017cff068e7a03baaec0cfc29bb7c1637ce99`

Scannerdownloads wurden gegen die vorhandenen CI-Pins geprüft: Gitleaks
`551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb`, Trivy
`bc0fc726e017b8927a62b2d3531d7a84ee01769daf5c99ed866dced54089fdbf`.

## Tatsächlich blockierte und offene Verbindungen

Die echte lokale Netzprobe ließ den freigegebenen Ollama-Mockaufruf zu und konnte
aus Frontend-, Backend- und Ollama-Namespace keine Verbindung zum vorher positiv
kontrollierten separaten Listener aufbauen. Die Probe sendet keine Arbeitsinhalte.
DNS-/IP-/Port-/IPv6-Manipulation, Redirects und externe Provider wurden zusätzlich
an kontrollierten Transportmocks abgewiesen; das sind keine externen Paketmitschnitte.

Netzwerkfähige Laufzeitadapter: Frontend→Backend, optional Backend→lokales Ollama
oder GROBID. Ziele sind fest begrenzt/gepinnt. Der Defaultprovider hat kein Netzwerk;
ResearchGateway hat keinen HTTP-Client. Modell-/Paket-/öffentliche Quellenbeschaffung
ist getrennt und darf keine vertraulichen Inhalte erhalten. Provisioning wurde in
dieser Iteration **nicht tatsächlich für Modellgewichte ausgeführt**, weil die
ausgelieferte Registry keine erforderlichen APPROVED-/Digestnachweise enthält.
Dieses negative Gate und Cleanup-/Fehlerfälle wurden getestet.

## Reproduzierbare synthetische Experimente

Die erneut ausgeführten bestehenden CLIs erzeugen ausschließlich synthetische
Berichte; unter PowerShell zuvor `$env:PYTHONPATH='backend'` setzen:

```text
python -m app.evaluation.privacy_lab
python -m app.evaluation.academic_benchmark
python infrastructure/scripts/validate_docker.py
python infrastructure/scripts/ci_e2e.py
python infrastructure/security/scripts/network_acceptance.py
```

Die letzten beiden Befehle benötigen einen gesunden Stack aus `compose.yaml` und
`compose.ci.yaml`; lokal wurde das isolierte Projekt `thesishounds-hardening-ci`
verwendet. Die Testdienste werden nach Abschluss entfernt.

Privacy-Ablation: 12 Szenarien × 4 Varianten = 48 kontrollierte Memory-Sink-Läufe.
A/B ließen je 11 unerlaubte Aktionen zu, C noch 2, D keine; D blockierte 11 Aktionen
und ließ die eine erlaubte PUBLIC-Lokalkontrolle zu. Keine echten Provideranfragen,
keine Canarywerte exportiert, keine empirische Modellrobustheit behauptet.
Academic-Benchmark: 6 Quellen- und 4 Formalienfälle bestanden, 0 externe Anfragen.
Diese engen Fixtures ersetzen keinen repräsentativen Expertenkorpus.

Zwischenprobleme wurden korrigiert: Trivy benötigt pro Dockerarchiv genau ein
Image sowie beschreibbaren privaten Scratch; die Scans wurden getrennt wiederholt.
Ein eingeschränkter Banditlauf wurde beendet und mit freigegebener lokaler
Ausführungsumgebung erfolgreich wiederholt. Linux-Git wertete Windows-CRLF zunächst
als Whitespacefehler; die Wiederholung berücksichtigt ausschließlich CR am Zeilenende,
ohne andere Whitespacekontrollen auszuschalten. Diese Zwischenläufe sind keine
bestandenen Sicherheitstests und ändern keine Scanner-/CI-Schwellen.

## Nicht ausgeführte Nachweise und erforderliche Freigaben

- Keine echte Inferenz, Modellgewichts-/Signaturprüfung, GPU-/Latenz-/Speicherstudie
  oder tatsächliche freigegebene Modellbereitstellung. Das echte Ollama-Image war
  lokal nicht vorhanden und wurde nicht gescannt oder im Betrieb geprüft.
- Kein tatsächlich freigegebenes GROBID-Image, keine OCR-/Parser-Sandbox-/Malware-
  oder reale PDF-Extraktionsqualitätsabnahme. Private Parser bleiben gesperrt.
- Keine Hochschul-SSO-/Mandanten-/TLS-/mTLS-Abnahme, keine Zielhost-Firewallinstallation,
  keine vollständigen DNS-/IPv6-/UDP-/Telemetrie-/Browser-Egressmessungen.
- Keine produktive Speicher-/Schlüssel-/Backup-/Swap-/Crashdump-/Restoreprüfung,
  keine physische Löschgarantie oder manipulationsgeschützter Produktionsaudit.
- Keine repräsentative fachliche/Biasstudie oder amtliche Freigabe von Regelkandidaten.
- Keine DSGVO-/DSFA-/KI-VO-/Prüfungsrechtsentscheidung, konkrete NDA-/Sperrvermerk-
  und Unternehmensautorisierung oder organisatorische Betriebsfreigabe.

Die offiziellen Projektziele werden technisch unterstützt durch lokale agentische
Verarbeitung mit Sperren (Architektur/Datenschutz), Modell-/Supply-Chain-Prüfungen
(Modellauswahl), fortgeführte unabhängige menschliche Prüfung (Human-in-the-Loop)
und reproduzierbare Sicherheitsablation/Regressionen (Evaluation). Diese Zuordnung
und der begrenzte Erfüllungsgrad stehen in der [Traceability](../requirements/traceability.md).
Die Gesamtabnahme echter vertraulicher Arbeiten bleibt **offen und gesperrt**.
Siehe [Risikoregister](risk_register.md), [Freigabecheckliste](security_release_checklist.md)
und [offene organisatorische Fragen](open_organizational_questions.md).
