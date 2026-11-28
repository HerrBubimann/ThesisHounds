# Document Security: ausgeführte Prüfungen am 27.11.2026

> Historischer Nachweis dieser Iteration. Testzahlen, Werkzeugverfügbarkeit und
> offene Infrastrukturprüfungen beziehen sich auf den unten genannten Prüfzeitpunkt.
> Aktueller konsolidierter Stand: [Validierung](../validation.md).

Geprüft wurde der lokale Arbeitsbaum unter Windows mit Python 3.12.6 und pypdf
7.2.0. Kein Git-Commitbezug: Git steht hier nicht als ausführbares Programm zur
Verfügung. Keine neue Modell-/Hochschul-/Datenschutzfreigabe. Original-PowerPoint
und die früher verlinkten Markdownberichte unter `docs/audit/` beziehungsweise
`docs/remediation/` waren in diesem Checkout nicht verfügbar. Die vorhandene
Traceability und ignorierte lokale Altberichte ersetzen diese Originale nicht.
Es wurde keine erneute vollständige Prüfung unbekannter Originalanforderungen
oder eine erfolgreiche Remote-CI fingiert.

## Abschlussnachweis

| Prüfung | Tatsächliches Ergebnis | Lokaler Rohbeleg / Umfang |
|---|---|---|
| gesamte pytest-Suite | **737 bestanden, 0 fehlgeschlagen, 0 Fehler, 0 übersprungen**, 64,782 s laut JUnit | `reports/document-security-2026-11-27/junit-final.xml`: 294 Unit, 86 Integration, 357 Security |
| kombinierte Statement-/Branch-Coverage | **87,0169 %**, 80-%-Pflichtgrenze erreicht | `coverage-final.json`: 5.652/6.331 Statements und 1.486/1.872 Branches abgedeckt; Statement-only 89,27 % |
| Ruff check + format --check | bestanden | tatsächliche CLI-Ausführung; kein Typchecker-/Pentestnachweis |
| Bandit | Gate MEDIUM+ bei mindestens MEDIUM Confidence bestanden; Bericht 28 LOW, 0 MEDIUM/HIGH, vier bestehende ausgelassene Tests | `bandit.json`; keine neuen Ausnahmen |
| pip-audit | keine bekannten gemeldeten Schwachstellen, Exit 0 | `pip-audit.json`, vier bestehende Hashlocks; keine Dependencyergänzung |
| pip check | bestanden | Konsistenz der installierten Pythonabhängigkeiten; kein Lizenz-/Supply-Chain-Vollnachweis |
| statischer Docker-Konfigurationsvalidator | sechs Varianten bestanden | `infrastructure/scripts/validate_docker.py`; kein Build-/Runtimebeweis |
| Artefakt-Canarycheck | bestanden | `infrastructure/scripts/privacy_dlp.py artifacts`; kein allgemeiner Geheimnisdetektor |
| Injection-CLI | 125 synthetische Ergebniszeilen, Pflichtkontrolle bestanden | `injection-benchmark.json`; Mock-/Memory-Control-Ablation, reale Modellwerte null |
| Academic-CLI | sechs Zitat-/vier Formalienfälle bestanden, externe Requests 0 | `academic-benchmark.json`; synthetisch, keine Expertenvalidierung |
| Planungs-CLI A/B/C, jeweils zwei Wiederholungen | sechs Mockläufe, 22 simulierte Calls, vollständiger Softwarelauf | `planning-cli/`; keine reale Modellqualität |

Der isoliert gestartete `pdf_worker.py` wird von der Parent-Coveragemessung nicht
instrumentiert und erscheint mit 0 %; der echte Kindprozess wird durch die
genannten Funktions-/Denytests ausgeführt. Daraus wird keine vollständige
Branchabdeckung des Workers abgeleitet. Linux und native Exploits bleiben ungeprüft.

Die Rohberichte sind absichtlich ignorierte lokale Dateien und keine eingecheckten
Gutachterdaten. Ihre Erzeugung benötigt nur synthetische Fixtures; einzelne Tests
nutzen lokale HTTP-/Socket-Testserver mit kontrollierten Antworten. Die neue
PDF-/Security-Implementierung wurde nicht mit echten vertraulichen Arbeiten getestet.

### Reproduktion des vollständigen Laufs

```powershell
$env:COVERAGE_FILE='reports/document-security-2026-11-27/.coverage'
.venv/Scripts/python.exe -m pytest --cov --cov-report=json:reports/document-security-2026-11-27/coverage-final.json --cov-report=term:skip-covered --junitxml=reports/document-security-2026-11-27/junit-final.xml -q --tb=short -p no:cacheprovider
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m bandit -c pyproject.toml -r backend/app frontend infrastructure/scripts infrastructure/security/scripts --severity-level medium --confidence-level medium
.venv/Scripts/python.exe -m pip_audit --strict --disable-pip --require-hashes --progress-spinner off -f json -r backend/requirements.lock -r frontend/requirements.lock -r requirements-dev.lock -r requirements-security.lock
.venv/Scripts/python.exe infrastructure/scripts/validate_docker.py
.venv/Scripts/python.exe infrastructure/scripts/privacy_dlp.py artifacts
```

Auf diesem verwalteten Windows-Arbeitsplatz benötigt pytest Zugriff auf
temporäre Testverzeichnisse und lokale Testserver. Ein erster eingeschränkter
Nachlauf scheiterte an `WinError 5` bei pytest-/Streamlit-Temporärdateien
(8 bestanden, 1 fehlgeschlagen, 4 Setupfehler). Nach zulässiger Ausführung mit
Tempzugriff bestanden die 13 betroffenen Tests und anschließend die gesamte
Suite. Dies wurde durch keine Abschwächung von Tests oder Produktionsgrenzen gelöst.

### Fehler während der Implementierung

Frühe gezielte Läufe waren rot: zunächst wurden bestehende leere interne
Probe-Nachrichten und der serverseitige Delegationszweck abgelehnt; danach ging
eine stabile technische Fehlerkennung bei der Übertragung aus dem PDF-Prozess
verloren. Der gemeinsame PDF-Pfad lehnte außerdem bestehende Blank-PDF-
Knowledge-Kandidaten ab. Korrekturen: exakte feste Probe-/Delegationsverträge,
Whitelist ausschließlich stabiler ACTIVE_CONTENT-/ENCRYPTED-Fehlercodes und
ein fester Candidate-only-Parameter. Blank-Pilotbewertungen bleiben verboten,
rohe Parserfehler bleiben verborgen. Vollständige Regressionen waren danach grün.

Der erste vollständige neue Lauf hatte 722 bestandene Tests/86,19 %, ein
Zwischenlauf 730/86,65 %, der nächste 734/86,95 %, danach 736/87,02 %.
Leserechts-/Scanlimitkorrektur sowie eine explizite Klassifizierungsprüfung beim
Toolzugriff und die erneute Prüfung älterer Freigaben bei neuen Findings ergeben
den oben belegten Endstand. Diese Zähler
sind Softwaretests, keine wissenschaftliche Verbesserung der Bewertungsgüte.

### Neue konkrete Regressionen

* `tests/security/test_secure_document_gateway.py`: echter Worker mit
  verschlüsselten, eingebetteten, aktiven/nested-Action-PDFs, kaputten Signaturen,
  201 Seiten; normale/weiße/kleine/transparente/unsichtbare/abgeschnittene/
  außerhalb liegende Texte; Metadaten, Originalbytes/Versionen; echte
  Python-Socket-/Subprozess-/Schreibablehnung; Tool-/Owner-/Scopes.
* `tests/security/test_injection_controls.py`: Gateway ohne Akteur/Leserecht,
  Modell-/Dokumentscope, rohe verbotene Aktionsfelder trotz laxem Schema,
  optionaler lokaler Klassifikator mit/ohne simulierte Freigaben,
  positive Befunde im verdächtigen Kontext und Mockablation.
* `tests/integration/test_security_review.py`: Quarantäne/Embargo, exakte
  Finding-IDs, kein Privacybypass, explizite UI-Entscheidung/Plaintext,
  legitime Sicherheitsarbeit, kombinierter Scanüberlauf,
  klassifikatorbedingte Pause und kontrollierte Wiederaufnahme.

Keine Scan-/Gate-Ausnahmen, keine gelockerten Coveragegrenzen und keine
übersprungenen Pflichtfälle wurden hinzugefügt. Der neue Benchmark läuft im
bestehenden obligatorischen Privacyjob; Dockerbuild bleibt Pflicht.

### Bewusst nicht nachgewiesen

Dockerdaemon/Build/Trivy/Runtime-Netztest und Remote-GitHub-Actions wurden in
dieser Iteration nicht ausgeführt. Frühere Image-/Netzberichte sind keine neue
Abnahme. Auch Gitleaks-Historienprüfung ist ohne Git hier nicht reproduziert.
Ollama/reale Modellartefakte, PA1-Experimentkatalog und Expertenreferenzen fehlen.

Keine Raster-/OCR-Ausführung, Bildinjektionserkennung, Malwareprüfung,
native Klassifikatorinferenz, Linux-Resource-Limit-Ausführung, vollständige
OS-Workerisolation oder Zielhost-SSO-/ACL-/Backup-/Firewallabnahme. Kein Peak-
RAM/VRAM-/Energie- oder realer Modelllatenznachweis. Übereinstimmung zweier
Mocks ist keine fachliche Validierung. Der gesamte Sicherheits-Definition-of-Done
ist deshalb **noch nicht erreicht**; private Produktion bleibt **BLOCKED**.

Die [Benchmarkauswertung](prompt_injection_benchmark.md) enthält ausdrücklich
die beiden erfolgreichen Heuristikumgehungen. Die [Risiken und Reihenfolge](../security/risk_register.md)
priorisieren einen abgesicherten, wissenschaftlich messbaren PUBLIC-End-to-End-Lauf.
