# Tatsächlich ausgeführte Validierung

Stand: **26. November 2026**, Multi-LLM-Erweiterung 0.2.

## Implementiert und lokal geprüft

| Prüfung | Ergebnis |
| --- | --- |
| Python | Projektlokal CPython 3.12.16 |
| Abhängigkeiten | Backend-/Entwicklungs-Locks mit Versionen und SHA256-Hashes aktualisiert und installiert |
| Ruff | `ruff check .` erfolgreich |
| Formatierung | `ruff format --check .`: alle erfassten Dateien korrekt formatiert |
| Pytest | **154 Tests bestanden** (75 Unit, 42 Integration, 37 Security), keine übersprungenen Tests |
| Coverage | 85,1 % kombiniert (Zeilen + Branches), Grenzwert 80 % |
| Bandit / pip-audit | keine Befunde ≥ MEDIUM; keine bekannten Schwachstellen in allen vier Lock-Dateien |
| CPU-Compose | Konfiguration mit Compose 5.8.0 validiert |
| GPU-Compose | Zusammengeführte Konfiguration validiert; kein GPU-Lauf behauptet |
| Provisionierungs-Compose | Zusammengeführte Konfiguration validiert |

Die Entwicklung erfolgte in überprüfbaren Schritten: Gateway-/Bestands-API-Prüfungen, Registry-/Factory-Prüfungen, Evidenz-/Abhängigkeitsprüfungen, vollständige LangGraph-Durchläufe und abschließende API-/Frontend-/Sicherheitsprüfungen. Der gemeinsame Abschlusslauf ersetzt frühere Teilzählungen.

Die Tests weisen unter anderem nach:

- Ollama-Providervertrag einschließlich Structured Output, Discovery, Capability- und Ressourcenmetadaten.
- Drei konfigurierbare Modellhersteller, unbekannte Modelle und Rollenfreigaben.
- Blockierung externer Provider, Behandlung unbekannter Klassifizierung als vertraulich und Ablehnung von EXPERIMENTAL im lokalen Prozess.
- Validierte AgentSpecs, Parent-Child-Beziehungen, sechs Subagenten als Standardlimit, Ablehnung weiterer Delegation und unerlaubter Tools.
- Zyklusfreie Task-Abhängigkeiten, begrenzte Agentenparallelität, Agenten-/Run-Timeouts, Aufruf-/Tokenbudgets und begrenzte Wiederholungen.
- Vollständige synthetische LangGraph-Durchläufe in **A, B, C und D**, einschließlich dynamischer Agenten im Modus D.
- Herstellerunabhängige Reviews, sichtbar fehlende Reviewer, konservative Konflikterkennung und ein begrenztes drittes Review ohne Löschen des Konflikts.
- Wörtliche Belegprüfung sowie gesonderte Behandlung von Abwesenheitsbehauptungen.
- Abbruch vor und während eines Laufes, Retention-Cleanup und geschützte finale Ausgabe erst nach menschlichen Entscheidungen.
- Erhalt ursprünglicher Befunde und überholter Reviews bei menschlicher Bearbeitung.
- Neue Run-/Agenten-/Review-/Ressourcen-API und bestehende Health-/Chat-/Modell-Endpunkte.
- Streamlit-Dashboard, Control Center, Mock-Kennzeichnung und Graphviz-Agentenbaum.
- Abweisung einer vom Mock-Modell vorgeschlagenen Shell-Berechtigung, ohne einen solchen Agenten zu erzeugen.

**Alle LLM-Antworten in diesen Tests sind Mock-Daten.** Die Tests führen den echten Kontrollfluss und die tatsächlichen Schema-/Policy-/Budgetprüfungen aus, messen jedoch keine reale Modellqualität und keine tatsächliche Inferenzleistung. Der Produktivpfad enthält keinen Mock-Provider oder simulierte Erfolgsergebnisse.

Temporäre Dateizugriffe der Tests waren innerhalb der Ausführungssandbox eingeschränkt. Der erfolgreiche Abschlusslauf erfolgte mit der dafür erteilten Freigabe außerhalb der Sandbox.

## CI-Pipeline und Merge-Schutz

Stand 26.11.2026. Details: [ci-cd.md](ci-cd.md).

| Bestandteil | Implementiert | Lokal geprüft | Auf GitHub verifiziert |
| --- | --- | --- | --- |
| Workflow mit 7 Jobs + `thesishounds-ci-gate` | ja | YAML-Struktur und Policies per Test (`test_ci_workflow.py`) | **nein**, noch nie auf GitHub gelaufen |
| Gate-Logik (failure/cancelled/skipped/fehlende Berichte) | ja | ja, Unit-Tests | nein |
| Lint, Format, Syntax, Tests, Coverage über `run_ci.py ci` | ja | ja, vollständig grün | nein |
| Bandit, pip-audit | ja | ja | nein |
| Gitleaks | ja | **nein**, lokale Ausführung nicht freigegeben | nein |
| Trivy-Image-Scan | ja | nein, keine Docker-Engine | nein |
| Compose-Validierung aller 4 Varianten | ja | ja, Compose-CLI 5.8.0 ohne Daemon | nein |
| `docker buildx build --check`, Image-Builds | ja | nein, keine Docker-Engine | nein |
| Mock-Ollama | ja | ja, Backend ↔ Mock über echtes HTTP inkl. Lauf D | nein |
| Container-E2E mit Mock (`compose.ci.yaml`, `ci_e2e.py`) | ja | nein, keine Docker-Engine | nein |
| GitHub Ruleset `main-protection` | JSON + Anleitung | – | **nicht aktiviert** (`gh` nicht angemeldet) |
| Abnahmetest Merge-Schutz | Anleitung | – | **nicht durchgeführt** |

Der Merge-Schutz ist erst wirksam, wenn ein Admin das Ruleset angelegt und der Abnahmetest bestanden ist.

## Offen: reale Container- und Modellabnahme

Auf diesem Rechner steht keine Docker-Engine für Containerstarts zur Verfügung. Die vorhandene offizielle Compose-Standalone-CLI validiert die Konfiguration ohne Daemon. Folgende Prüfungen wurden **nicht** ausgeführt:

- Image-Builds und tatsächlicher Start der drei Container mit den konfigurierten Sicherheits- und Ressourcenlimits.
- Download und tatsächliche Inferenz von Qwen3:8b, Mistral:7b und Llama3.1:8b.
- Reale Multi-Agent-Ausgaben oder reale JSON-Schema-Zuverlässigkeit dieser drei Modelle.
- GPU-Gerätezugriff, tatsächliches Entladen, VRAM-Verhalten und Zielhardware-Lasttests.
- Browserzugriff auf das containerisierte Dashboard und realer Offline-Durchlauf.
- Erneute Inferenz nach Container-Neuerstellung als Nachweis der Modellpersistenz.
- Ausführung der GitHub-Actions-Pipeline auf GitHub.
- Produktiver DHBW-Serverbetrieb und wissenschaftliche Evaluation gegen menschliche Referenzen.

CI ist für Mock-Tests, Builds, Compose-Validierung und modellfreien Containerstart vorbereitet. Reale Abnahmebefehle nach Installation/Start von Docker:

```powershell
# Im vorbereiteten Windows-Checkout; .env nur kopieren, falls noch nicht vorhanden:
Copy-Item .env.example .env
.\.venv\Scripts\python.exe infrastructure/scripts/provision.py
docker compose up -d --no-build --pull never --wait --wait-timeout 180
.\.venv\Scripts\python.exe infrastructure/scripts/smoke.py --chat
.\.venv\Scripts\python.exe infrastructure/scripts/smoke.py --analysis --mode D

# Lokale Prüfungen:
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

Für den eigentlichen Offline-Nachweis nach der Modellbereitstellung Internet trennen und Start sowie Analyse wiederholen. Der Smoke-Test liefert nur bei tatsächlich abgeschlossener Inferenz mit nicht leeren Befunden einen Erfolg; er kennzeichnet einen Mock-Lauf nicht als echte Inferenz. Vollständige Anleitung: [Setup](setup.md).

Die Implementierung ist damit lokal funktional gegen Mock-Provider geprüft. Die Definition of Done ist hinsichtlich realer lokaler Modelle, Docker-Laufzeit und Offline-/GPU-Betrieb noch nicht vollständig nachgewiesen.
