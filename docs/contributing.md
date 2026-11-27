# Entwicklungsregeln für das ThesisHounds-Team

Diese Regeln sind verbindlich. Sie schützen die Codequalität und die vertraulichen Arbeiten, die ThesisHounds später verarbeitet.

## Grundsätze

1. **Kein direkter Push auf `main`.** Jede Änderung läuft über einen Pull Request. Das [Ruleset](ci-cd.md#github-ruleset-für-main) erzwingt das, sobald es aktiviert ist.
2. **Merge nur bei grünem `thesishounds-ci-gate`** und mindestens einer Freigabe durch ein anderes Teammitglied. Offene Review-Kommentare werden vor dem Merge aufgelöst.
3. **Nur synthetische Daten.** Keine echten wissenschaftlichen Arbeiten, Gutachten, Prompts mit echten Inhalten, Modellantworten zu echten Arbeiten oder personenbezogenen Daten im Repository. Das gilt auch für Tests, Issues, PR-Beschreibungen, Screenshots und CI-Logs.
4. **Keine Secrets im Repository.** Konfiguration gehört in `.env` (ignoriert), Beispiele in `.env.example` ohne echte Werte. Wurde ein Secret versehentlich committet, wird es sofort widerrufen und das Team informiert.
5. **Keine externen KI-APIs.** LLM-Zugriffe laufen ausschließlich über `LLMGateway` und den lokalen Ollama-Provider. In Tests werden LLMs immer gemockt.
6. **Qualitätsgrenzen werden nicht abgesenkt**, um eine Pipeline grün zu bekommen. Das betrifft Coverage-Grenzwert, Scanner-Schwellen, Skips und `continue-on-error`. Ausnahmen folgen dem [Ausnahmeverfahren](ci-cd.md#ausnahmen).

## Arbeitsablauf

```bash
git switch main && git pull
git switch -c feature/<kurzbeschreibung>   # auch: fix/…, docs/…, ci/…, test/…
# entwickeln, Tests ergänzen
make format          # Ruff-Autofix und Formatierung
make ci              # alle lokal ausführbaren Pflichtprüfungen
git push -u origin feature/<kurzbeschreibung>
gh pr create --base main   # Template ausfüllen
```

Windows ohne `make`: `.\.venv\Scripts\python.exe infrastructure/scripts/run_ci.py ci` (gleiche Ziele wie das Makefile).

- Kleine, thematisch geschlossene PRs. Große Umbauten vorher im Team abstimmen.
- Commit-Nachrichten im Imperativ, z. B. `Add evidence validator for absence claims`.
- Ist `main` weitergelaufen, den eigenen Branch aktualisieren (`git rebase origin/main` oder „Update branch“). Der Status Check muss auf dem aktuellen Stand grün sein.
- Nach neuen Commits müssen bestehende Approvals erneut eingeholt werden.

## Tests

| Verzeichnis | Inhalt |
| --- | --- |
| `tests/unit/` | einzelne Komponenten, keine Netzwerk- oder Docker-Abhängigkeit |
| `tests/integration/` | Zusammenspiel: API, Frontend ↔ Backend, vollständige Workflows, Mock-Ollama über HTTP, Compose-Konfiguration |
| `tests/security/` | Datenschutz- und Agenten-Grenzen (LOCAL_ONLY, Tools, AgentSpecs, Limits) |
| `tests/fixtures/` | gemeinsame synthetische Daten und Mocks (`WorkflowProvider`, `mock_ollama`) |

- Neue Funktionen brauchen Tests. Bugfixes brauchen einen Test, der den Fehler vorher reproduziert.
- Neue Sicherheitsgrenzen bekommen einen Test in `tests/security/`.
- Testmodule importieren sich nicht gegenseitig. Gemeinsames gehört nach `tests/fixtures/`.
- `Settings(_env_file=None, …)` verwenden, damit keine lokale `.env` in Tests einfließt.
- Keine Tests, die nur unter bestimmten Bedingungen laufen und sonst stillschweigend übersprungen werden. In der CI lassen übersprungene Tests das Gate fehlschlagen.
- Der Coverage-Grenzwert (aktuell 80 %) darf durch einen PR nicht unterschritten werden.

## Code

- Python 3.12, Ruff-Regeln aus `pyproject.toml`, Zeilenlänge 100.
- Fehlermeldungen und Logs enthalten keine Dokumentinhalte, Prompts oder Modellantworten.
- Neue Abhängigkeiten nur nach Abstimmung. Danach `requirements.txt` pflegen und den Lock mit Hashes neu erzeugen (Befehl im Kopf der Lock-Datei), Lizenz und Wartungsstand prüfen.
- Fachlogik nicht in API-Routen. Agenten nutzen den zentralen Gateway und keine eigenen Clients.
- Änderungen an `config/policies.yaml`, Limits in `config/execution.yaml`, `.github/` oder Compose-Netzen brauchen eine Begründung im PR. Sie werden von einer zweiten Person besonders sorgfältig geprüft.

## Reviews

Reviewer prüfen:

- Funktion und Tests,
- Verständlichkeit und Dokumentation,
- Datenschutz: keine echten Daten, keine Inhaltslogs, kein externer Datenabfluss,
- Sicherheit: Policies, Tool-Freigaben, Limits,
- Auswirkungen auf API-Verträge und Frontend.

Ein Approval bestätigt, dass der Reviewer die Änderung verstanden hat. Es ist kein Durchwinken.

## Dokumentation

Betroffene Doku im selben PR aktualisieren: [README](../README.md), [Architektur](architecture.md), [Setup](setup.md), [Sicherheit](security.md), [CI/CD](ci-cd.md). Tatsächlich durchgeführte Abnahmen kommen mit Datum in [validation.md](validation.md). Es werden keine Ergebnisse behauptet, die nicht ausgeführt wurden.
## Vertrauliche Daten und Entwicklungswerkzeuge

Keine echten Arbeiten, Unternehmensinformationen, Gutachten, privaten Chatverläufe,
Embeddings oder vertraulichen Screenshots in Git, GitHub Actions, Issues, PRs,
IDE-/Coding-Assistenten oder externe Debugdienste übernehmen. Das gilt auch für
private Repositories und zusammengefasste/pseudonymisierte Inhalte. Nur serverseitige
synthetische Fixtures oder nachweislich öffentliche Daten verwenden.

`.gitignore` schützt weder bereits indexierte Dateien noch Kopieren/Uploads.
Der lokale Pre-Commit-DLP-Hook prüft den gesamten Index einschließlich ignorierter,
erzwungen hinzugefügter Dateien. Mit vorhandenem `pre-commit`:
`pre-commit install`; unabhängig davon vor Commit:
`python infrastructure/scripts/privacy_dlp.py`. CI führt dieselbe verpflichtende
Prüfung aus; Hooks können lokal umgangen werden und ersetzen keinen Review.
Pfad-DLP erkennt keine beliebigen Geheimnisse in Quelltext. Vor Push den Index
prüfen, vorhandenes Secret Scanning beachten und `.dockerignore`-Allowlist erhalten.

Bereits eingecheckte vertrauliche Dateien sind ein Sicherheitsvorfall, keine normale
Ignore-Korrektur: [Incident Response](security/incident_response.md). Dokumentablage
außerhalb des Repositorys; keine vertraulichen Daten in Testberichten oder Logs.
