# Privacy test results

**Aktueller Sicherheitsstand:** [Hardening-Nachweise vom 27.11.2026](hardening_results.md).
Die folgenden Zahlen sind historisch und keine aktuelle Hochschulabnahme.

Die nachstehenden Zähler dokumentieren die Privacy-Basis vor der wissenschaftlichen
Erweiterung. Deren aktuelle Routing-/Verifier-/Evidence-Explorer-/Evaluationstests
und erneute Infrastrukturprüfungen stehen in [Evaluation results](../evaluation/results.md).
Keine neue Freigabe echter Arbeiten wird daraus abgeleitet.

Stand: 2026-11-26. Ausschließlich synthetische Fixtures und kontrollierte Mocks.
Zwischenläufe wurden zur Fehlerkorrektur benutzt; unten stehen die beobachteten
Ergebnisse des abschließenden lokalen Teststands. Keine Hochschulfreigabe.

## Nachweisgrenzen

- Unit-/API-/UI-/Canarytests prüfen Anwendungsgrenzen und Mock-Transporte.
- DNS-/Redirecttests benutzen kontrollierte Antworten; sie sind kein Paketmitschnitt
  aus einer Hochschule. Der Defaultmock ist separat auf fehlende HTTP-Aufrufe geprüft.
- Docker-Compose wurde lokal gerendert. Docker Desktop war zunächst gestoppt und
  wurde mit erteilter Berechtigung gestartet. Backend/Frontend wurden anschließend
  gebaut und im getrennten Projekt `thesishounds-privacy-ci` ausschließlich mit
  synthetischen Daten geprüft. Die echte Inferenz blieb ein Mock, ohne Modellgewichte.
- Hochschulnetz, TLS-/SSO-Betrieb, verschlüsselte Speicher/Backups, Parserisolation,
  reale Modellqualität und organisatorische Freigaben wurden nicht geprüft.
- Git-CLI war im initialen Windows-PATH nicht verfügbar; die CLI lehnte zunächst
  korrekt ab. Der Indexscan wurde anschließend in einem getrennten lokalen
  Git-Prüfcontainer ohne Netzwerk und mit schreibgeschütztem Repository bestanden.
  Das ist kein Inhalts-/History-Secret-Scan.
- Der ursprüngliche Sandboxlauf konnte Pytest-Tempverzeichnisse nicht öffnen.
  Tests werden mit erteilter Ausführungsberechtigung und isolierter `.venv` wiederholt.

Die Pipeline erhält einen verpflichtenden `privacy-security`-Job. Missing/empty/
failed/skipped Reports und fehlgeschlagene oder übersprungene Jobs lassen den
bestehenden `thesishounds-ci-gate` scheitern. Keine `continue-on-error`-Ausnahme.
Branch Protection / Rulesets wurden nicht verändert oder remote verifiziert.
Ein Merge wird nur bei tatsächlich aktivem erforderlichem GitHub-Status blockiert.

## Abschließende lokale Ausführung

| Prüfung | Beobachtetes Ergebnis | Grenze |
|---|---|---|
| Vollständige Pytest-Suite, Python 3.12, Windows | 414 bestanden, keine Fehler oder Skips | synthetische Dokumente, kontrollierte Provider/API/UI-Mocks |
| Kombinierte Line-/Branch-Coverage | 89,60 %, unveränderte Pflichtschwelle 80 % erfüllt | keine Aussage über fachliche Modellqualität |
| Ruff lint / Format | bestanden | Sourceprüfung |
| compileall | bestanden | Syntaxprüfung |
| Docker-Compose-Validator | CPU, GPU, Provisioning, CI-Mock, Universität: alle 5 Konfigurationen bestanden | Universität nur statische Konfiguration; Start bleibt gesperrt |
| Backend-/Frontend-Imagebuild | bestanden, hashgeprüfte Abhängigkeiten | echtes Ollama-Image und GPU nicht lokal gebaut/getestet |
| Image-Inhaltsprüfung `/app` | keine PDF-/Office-/CSV-Dokumente oder Modellgewichte, keine Git-Historie; Backend enthält keine Tests | Prüfung der aktuellen finalen Dateibäume, keine forensische Layerprüfung |
| Drei Container-Healthchecks | bestanden | separates synthetisches Testprojekt |
| Container-End-to-End | bestanden: Frontend→API, festes Chatsignal, Modus D mit 2 Befunden und 2 dynamischen Agenten | In-Process-Mock; keine reale fachliche Bewertung |
| Positivkontrolle Inferenznetz | echter IP-gepinnter Ollama-Adapter erreicht ausschließlich internen HTTP-Mock mit PUBLIC-Testsignal | keine universitäre TLS-/GPU-/Modellabnahme |
| Egress-Negativkontrolle | Frontend, Backend und Ollama-Netzwerknamespace erreichen kontrollierten öffentlichen Mocklistener nicht | ein kontrolliertes IPv4/TCP-Ziel; kein vollständiger Host-/DNS-/IPv6-Paketnachweis |
| Gitindex-DLP | 0 gesperrte indexierte Pfade; Scan ohne Netzwerk, Repository read-only | Pfadprüfung; ungetrackte Dateien und Inhalte/History nicht dadurch freigegeben |
| Artefakt-Canaryscan | aktuelle lokale Reports markerfrei; Plain/Base64/Hex und Chunkgrenzen getestet | nur bekannte synthetische Marker, keine universelle DLP |
| Bandit, MEDIUM-Schweregrad und -Konfidenz als Blockierschwelle | keine blockierenden Befunde | LOW-Befunde sind damit nicht ausgeschlossen |
| pip-audit über alle 4 Lockfiles | keine bekannten Schwachstellen gemeldet | Datenbankstand zum Prüflauf; keine Garantie gegen unbekannte Lücken |
| pip check | keine verletzten Paketabhängigkeiten | lokale Testumgebung |
| Gitleaks-Historyscan, Trivy, GitHub Actions und aktives Ruleset | nicht lokal/remote ausgeführt bzw. verifiziert | vorhandene CI-Scanner bleiben verpflichtend; kein grünes Remote-Gate behauptet |

Reproduktion: `python -m pytest -q -p no:cacheprovider --junitxml=reports/junit-local.xml
--cov --cov-report=term --cov-report=xml:reports/coverage.xml`; `ruff check .`;
`ruff format --check .`; `python infrastructure/scripts/validate_docker.py`;
`python infrastructure/scripts/privacy_dlp.py artifacts`.

Container: Backend/Frontend bauen, `compose.yaml` + `compose.ci.yaml` mit eigenem
Projekt starten; danach `ci_e2e.py` und `network_acceptance.py` mit identischem
`COMPOSE_PROJECT_NAME` ausführen. Keine privaten Bestände mounten. Der temporäre
Teststack wird nach der Prüfung entfernt; keine produktiven Volumes wurden benutzt.
Berichte liegen ignoriert unter `reports/`, keine Veröffentlichung/kein Push erfolgt.
