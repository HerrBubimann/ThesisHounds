# Einrichtung, API und Serverbetrieb

Stand: 28.11.2026. Standard: `SECURITY_MODE=DEVELOPMENT`, `INFERENCE_MODE=mock`.

Neue Begutachtungsoberfläche:
[Navigation, Anlageassistent und Reviewablauf](frontend/review_workflow.md),
[Architektur und Gap Analysis](frontend/architecture.md),
[Tests und Grenzen](frontend/limitations.md).
Die bestehenden Start-/Sicherheitsvorgaben bleiben erhalten. Nach Änderungen am
Frontend inklusive PDF-Viewer die Images mit `docker compose up --build` neu bauen;
hierfür muss die Docker-Engine laufen. Kein Modell-Download für die Mock-Demo nötig.

Zusätzliche Gutachterwerkzeuge, Mosbacher Exportwege und lokale Messungen:
[Betrieb, wissenschaftlicher Prüfumfang und Grenzen](research/reviewer_productivity_tools_2026-11-28.md),
[Checkpoint vor dem Frontendumbau](evaluation/reviewer_productivity_results.md).

Parallele Prüfungen, gemeinsames Ergebnis sowie optionale Embedding-/CSL-Manifests:
[Betrieb und Grenzen](research/parallel_scientific_checks.md),
[Prüfergebnisse vom 28.11.2026](evaluation/parallel_review_results.md).

Öffentliche wissenschaftliche Metadaten und lokale Zusatzwerkzeuge:
[kontrollierter Import, SQLite-Versionen, Sync und Retrieval](research/local_scientific_infrastructure.md).
Der [Prüfbericht vom 27.11.2026](evaluation/public_research_results.md) trennt
implementierte Adapter von noch fehlenden echten Modell-/Serviceabnahmen.

Sicherheitsänderung 2026-11-26: `docker compose up` startet ausschließlich die
synthetische Mock-Demo. Modell-Provisioning ist dafür nicht erforderlich.
`compose.university.yaml` verweigert derzeit den Start (UNIVERSITY_SECURE).
Freier Chat ist gesperrt, der Testprompt lautet exakt `Test`. Maßgeblich sind
[Produktionsblocker](security/production_readiness.md) und
[Privacy-Architektur](security/privacy_architecture.md). Folgende ältere
Inferenz-/Hochschulbeispiele sind keine Freigabe echter Arbeiten.

## Betriebssysteme

Windows benötigt für native Entwicklung Python 3.12 und Git; der Containerbetrieb benötigt Docker Desktop mit Linux-Containern, WSL2-Backend und aktivierter Virtualisierung. Prüfen: `py -3.12 --version`, `docker version`, `docker compose version`. In einer WSL-Distribution eine eigene Linux-Umgebung verwenden, nicht die Windows-`.venv`.

Linux benötigt Python 3.12 inklusive venv-Unterstützung, Git, laufende Docker Engine und Compose-Plugin. Die Installation ist distributionsabhängig; die [offizielle Docker-Anleitung](https://docs.docker.com/engine/install/) verwenden. Docker-Socket- oder Docker-Gruppenzugriff verleiht weitreichende Hostrechte.

macOS benötigt Python 3.12, Git und Docker Desktop. Der Stack nutzt unter Apple Silicon Linux-arm64-Images; im vorliegenden Containeraufbau erfolgt Inferenz auf der CPU. Die NVIDIA-Konfiguration ist dafür nicht geeignet.

## Erste Installation und Aktualisierung eines bestehenden Checkouts

Compose muss die verwendeten
[`!reset`-/`!override`-Tags](https://docs.docker.com/reference/compose-file/merge/) unterstützen.
Python/CI-Basis: 3.12.16; unterstützte native Minorversion: 3.12. Direkte Pins stehen
in `backend/requirements.txt` und `frontend/requirements.txt`, aufgelöste Pakete in
vier Hash-Locks. Aktuell: FastAPI 0.165.0, Streamlit 1.67.0, streamlit-pdf 2.1.0,
LangGraph 1.2.24, HTTPX 0.28.1, Pydantic 2.14.4 und pypdf 7.2.0.


Alle Befehle aus dem Repository-Stamm ausführen. `.env` einmal aus `.env.example` kopieren. Bei einer vorhandenen Foundation die Datei erhalten und die neuen Ressourcenvariablen bei Bedarf ergänzen; Compose besitzt Standardwerte.

Windows:

```powershell
if (-not (Test-Path -LiteralPath '.env')) { Copy-Item .env.example .env }
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
docker compose build
docker compose up -d --no-build --pull never --wait --wait-timeout 180
.\.venv\Scripts\python.exe infrastructure/scripts/smoke.py --analysis --mode D
```

Linux/macOS:

```bash
test -f .env || cp .env.example .env
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock
docker compose build
docker compose up -d --no-build --pull never --wait --wait-timeout 180
.venv/bin/python infrastructure/scripts/smoke.py --analysis --mode D
```

### Kleine Mock-Vorschau ohne Ollama-Imagebau

Alternativ nur die App-Images bauen und den vorhandenen CI-Mock einsetzen:

```powershell
docker compose build backend frontend
docker compose -f compose.yaml -f compose.ci.yaml up -d --no-build --pull never --wait --wait-timeout 180
```

Die Oberfläche startet im Dashboard unter `http://localhost:8501`. Begutachtungen
werden über den Assistenten angelegt; das Legacy-Control-Center liegt unter
**Technik & Verwaltung**. Beenden mit denselben `-f`-Dateien und `down`.
Ein bestehendes Projekt `thesishounds-frontend-preview` zusätzlich mit
`-p thesishounds-frontend-preview` adressieren. Nicht zwei Stacks mit demselben
Port und denselben festen Netzen gleichzeitig betreiben.

Die Mock-Demo benötigt keine Modellgewichte. Optionales Provisioning verweigert die
mitgelieferte DEVELOPMENT_ONLY-Registry: Lizenz-/Sicherheitsfreigabe, Modellversion,
Gewichtsherkunft und vollständiger `expected_digest` müssen vorher bestätigt werden.
Nach dokumentierter Freigabe verwendet `infrastructure/scripts/provision.py` nur
das eigenständige Projekt `compose.provision.yaml`. Ein aktives Modell-Volume wird
nicht geändert; die Anwendung wird nicht automatisch gestoppt. Der volle Digest
wird nach dem Download lokal geprüft. Keine automatische Volume-Migration.

### Unterbrochene Bereitstellung

Nach hartem Abbruch oder fehlgeschlagenem Cleanup:

```bash
docker compose --project-name thesishounds-provisioning -f compose.provision.yaml down --remove-orphans
docker compose up -d --no-build --pull never --wait --wait-timeout 180
```

Kein `-v` verwenden: Das Modell-Volume bleibt bestehen. Vor einem erneuten Versuch
Freigabe und Digest prüfen. Eine fehlgeschlagene Prüfung autorisiert keine Inferenz.
Die Provisioning-Datei ist kein Runtime-Override; Verarbeitungsnetze bleiben intern.

## Konfiguration und Ressourcen

`config/` wird nur lesbar eingebunden. Modelle und Rollen werden in `models.yaml` und `agents.yaml` konfiguriert. `context_length` gilt pro Modell; `LLM_CONTEXT_LENGTH` ist weiterhin Ollamas allgemeiner Default. Analyse- und Chat-Aufrufe verwenden den registrierten Modellkontext. Der Einzelchat verwendet `LLM_MAX_TOKENS`, Agenten verwenden `max_output_tokens` aus `execution.yaml`.

In `.env` lassen sich Frontend-/Backend-/Ollama-CPU und RAM mit `FRONTEND_CPUS`, `FRONTEND_MEMORY`, `BACKEND_CPUS`, `BACKEND_MEMORY`, `OLLAMA_CPUS`, `OLLAMA_MEMORY` begrenzen. Standard: 1 CPU/1 GiB, 2 CPUs/1 GiB, 4 CPUs/12 GiB. Docker Desktop insgesamt ausreichend Speicher zuweisen.

Für sparsame CPU-Nutzung `sequential_model_loading: true`, `max_parallel_model_calls: 1`, `OLLAMA_NUM_PARALLEL=1` und `OLLAMA_MAX_LOADED_MODELS=1` beibehalten. Bewusst größere Parallelität benötigt einen passenden Ollama- und Hardwareausbau; Registry-Ressourcenwerte sind Schätzungen, keine automatische Speicherzuteilung.

HTTP-Variablen: `LLM_CONNECT_TIMEOUT=5`, `LLM_STATUS_TIMEOUT=10`, `LLM_CHAT_TIMEOUT=300`, `FRONTEND_REQUEST_TIMEOUT=320`. Das Frontend muss für den Einzelchat länger als Statusprüfung plus Chat warten. Analyse-Starts sind asynchron und liefern HTTP 202; ihre Gesamtlaufzeit steht separat in `execution.yaml`. HTTPX begrenzt Netzwerkphasen, keine exakte Gesamtfrist. Das Run-/Agentenlimit verwendet zusätzlich `asyncio.timeout`.

YAML-Änderungen benötigen `docker compose restart backend`; laufende Analysen gehen dabei verloren. Geänderte Compose-Umgebungsvariablen mit `docker compose up -d` übernehmen. Codeänderungen benötigen `docker compose build` und anschließendes `up -d`.

## NVIDIA-GPU

Linux: unterstützte Treiber und [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) einrichten. Windows: GPU-fähiger WSL-Treiber und Docker Desktop. Auf dem Host `nvidia-smi` prüfen. Anschließend:

```bash
docker compose -f compose.yaml -f compose.gpu.yaml up -d --no-build --pull never --wait --wait-timeout 180
docker compose -f compose.yaml -f compose.gpu.yaml exec ollama ollama ps
```

Smoke-Test mit `--gpu --analysis --mode D` ausführen. Das gleiche Modell-Volume wird verwendet; der Download selbst braucht keine GPU. `ollama ps` zeigt die tatsächliche CPU-/GPU-Verteilung. GPU-Reservierung allein garantiert nicht, dass ein Modell vollständig in den Grafikspeicher passt.

## API-Verträge

| Methode | Pfad unter `/api/v1` | Zweck |
| --- | --- | --- |
| GET | `/status` | Bestehender Backend-/Ollama-/Standardmodellstatus |
| GET | `/models` | Bestehende lokale Modellliste mit Name, Größe und Digest |
| GET | `/models/status` | Registry-Einträge und Discovery; unter Mock keine echte Artefaktverfügbarkeit |
| GET | `/models/capabilities` | Vorhandene Fähigkeitsnachweise, derzeit leere Matrix |
| GET | `/security/status` | Betriebsmodus, Produktionsblocker und Freigabestatus |
| POST | `/chat` | Fester synthetischer Verbindungstest, ausschließlich `{ "prompt": "Test" }` |
| GET | `/agents` | Konfigurierte statische Definitionen und erstellte Agenteninstanzen |
| GET | `/agents/{agent_id}` | Laufzeitstatus eines Agenten |
| GET / POST | `/runs` | Läufe auflisten / neue synthetische Analyse starten |
| GET | `/runs/{run_id}` | Status, Fortschritt, Metriken, Snapshots und Ausgabe |
| GET | `/runs/{run_id}/graph` | Agentenknoten und Parent-Child-Kanten |
| GET | `/runs/{run_id}/findings` | Befunde, Belege, Reviews, Konflikte und Human-Status |
| POST | `/runs/{run_id}/cancel` | Lauf kontrolliert abbrechen |
| POST | `/runs/{run_id}/findings/{finding_id}/review` | Menschliche Entscheidung und optionale Bearbeitung innerhalb des angegebenen Runs |
| GET | `/system/resources` | Lokale Ressourcen und aktive Ausführungen |

Zusätzlich `GET /health` für Backend-Liveness. Fehlender Modellbestand macht den Backend-Prozess nicht unhealthy. Ein verfügbarer Modelltag bestätigt noch keine erfolgreiche Inferenz.

Zulässiger Run-Body: `{ "document_id": "synthetic-demo", "mode": "D" }`. Freie Aufgaben oder abweichende Kriterien sind im Entwicklungsmodus gesperrt; die Defaults aus `RunRequest` beibehalten. Klassifizierung, beliebige Dokumentpfade und Provider lassen sich nicht über den Body setzen. Review-Body: `{ "decision": "ACCEPTED", "note": "Beleg geprüft", "edited_statement": "Optional bearbeiteter Befund" }`; `REJECTED` ist ebenfalls möglich. Ohne Bearbeitung `edited_statement` weglassen.

Der Review-Endpoint validiert beide IDs und sucht ausschließlich im angegebenen Run. Ein Befund aus einem anderen Run liefert 404; der frühere globale `/findings/{finding_id}/review`-Endpoint ist entfernt. Die Run-ID ist keine Benutzerberechtigung: Objektzuweisung und read/process/review/delete-Prüfungen sind implementiert, aber alle DEVELOPMENT-Anfragen erhalten dieselbe Demo-Identität; eine echte Anmeldung/Mandantentrennung fehlt. Mehrbenutzerbetrieb benötigt Authentifizierung und Autorisierung für alle Run-Endpunkte (Backlog PROD-1).

Fehler enthalten `detail` und bei zentral behandelten Fehlern zusätzlich `code`. 403 bedeutet Policy-Sperre, 404 fehlendes/bereinigtes Objekt, 409 unpassenden Zustand, 422 Schema-/Planfehler, 429 Budget-/Kapazitätslimit, 502 fehlerhafte Providerantwort, 503 fehlenden Provider/Modell, 504 Zeitlimit. Kein Fehler spiegelt vertrauliche Eingabewerte zurück. Hintergrundfehler stehen im Run-Status statt als nachträglicher HTTP-Fehler des Startaufrufs.

Backend und Ollama bleiben intern. Ohne zusätzliche Portfreigaben in PowerShell oder POSIX-Shell prüfen:

```bash
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/models/status').read().decode())"
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/runs').read().decode())"
```

Für Start, Review und Abbruch das Dashboard oder den Smoke-Test nutzen. Im nativen Backend-Entwicklungsmodus stehen OpenAPI und interaktive API-Tests unter `http://localhost:8000/docs` bereit.

### Assessment-API

Alle fallbezogenen Pfade beginnen mit `/api/v1/assessments/{assessment_id}`.
Die genaue OpenAPI-Spezifikation entsteht aus `backend/app/api/assessments.py`;
UUID, Schemata, Scope, Zustand und Freigabe werden serverseitig geprüft.

| Methode / Suffix | Zweck / Grenze |
|---|---|
| GET / POST `/api/v1/assessments` | ACL-gefilterte Metadatenliste / zugelassenen Fall anlegen |
| GET `/api/v1/assessments/profiles`, `/api/v1/assessments/pilot-documents` | tatsächlich angebotene öffentliche Kataloge / registrierte Pilotdateien |
| POST `/api/v1/assessments/rules-preview` | validierte Mosbach-Richtlinienvorschau ohne Freigabe |
| GET `/{id}`, `/{id}/document` | sichere Statusprojektion / zugewiesener Dokumenttext |
| GET `/original-pdf` | erneut geprüftes registriertes PUBLIC-Original; kein Ersatz-PDF für Textfixtures |
| POST `/human-review`, `/ai-review`, `/release` | unabhängige Erstbewertung / KI-Start / ausdrückliche Vergleichsfreigabe |
| GET `/comparison`, `/provenance`, `/findings/{finding_id}/evidence` | freigegebene Ergebnisse, Herkunft und Originalbelege |
| GET `/academic-checks`; POST `/academic-decisions` | lokale Formalien-/Quellenprüfung und menschliche Entscheidungen |
| GET `/document-security`; POST `/document-security/review` | menschliche Klärung von Sicherheitshinweisen nach Erstbewertung |
| POST `/finding-feedback`, `/reviewer-notes`, `/review-methods`, `/reviewer-time` | versioniertes Feedback/Notizen, belegte Methodenbestätigung, explizite Sitzungszeit |
| POST `/discussion` | RESTRICTED-Modellweitergabe aktuell durch Privacy-Gate gesperrt |
| POST `/manual-review`, `/decisions` | menschliche Prüfung ohne KI-Diskussion / Kriterienentscheidung |
| GET `/draft`; POST `/finalize` | menschlich zusammengestellter Entwurf / endgültige Freigabe |
| POST `/cancel`; DELETE Basispfad | abbrechen / zugewiesenen Fall löschen |

Keine HTTP-Schnittstelle importiert beliebige PDFs oder erteilt Modell-/Hochschulfreigaben.
Bewertungen, Diskussionsdaten und Notizen bleiben flüchtig. TXT/Markdown werden im
Frontend aus dem autorisierten Entwurf heruntergeladen; keine automatische externe Abgabe.
Alle übrigen Suffixe der Tabelle sind fallbezogen. Kein Backend-/Ollama-Port wird
im Standard nach außen veröffentlicht.

## Native Entwicklung

Nur für synthetische beziehungsweise unabhängig geprüfte öffentliche Testdaten; native Prozesse besitzen keine Docker-Netzisolation. Im Mockstandard sind weder ein laufender Ollama-Server noch Modellgewichte nötig. Zwei Terminals im Repository-Stamm:

```powershell
$env:SECURITY_MODE='DEVELOPMENT'
$env:INFERENCE_MODE='mock'
$env:OLLAMA_BASE_URL='http://localhost:11434'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload --no-access-log
```

```powershell
$projectRoot = (Get-Location).Path
$env:PYTHONPATH = $projectRoot
$env:BACKEND_URL='http://localhost:8000'
Push-Location frontend
..\.venv\Scripts\python.exe -m streamlit run app.py --server.address=127.0.0.1
Pop-Location
```

Linux/macOS verwenden `.venv/bin/python` und vorangestellte Umgebungsvariablen, etwa `OLLAMA_BASE_URL=http://localhost:11434 .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload --no-access-log`. Der Standardstore liegt nativ unter `tempfile.gettempdir()/thesishounds-demo/documents`; ein Store im Quellrepository wird abgewiesen. Das vollständige Streamlit-Theme liegt in `frontend/.streamlit/config.toml`; Docker kopiert es an den Arbeitsort.

## Kontrollierter PUBLIC-Pilot

Dies ist eine Testgrenze, keine Freigabe echter vertraulicher Arbeiten. Erforderlich:

1. Tatsächlich überprüftes PA1-/DS-KI-`EXPERIMENT`-Profil statt bloßer Umbenennung
   des Beispielkatalogs; Herkunft, Reviewer und Zeitpunkt müssen belegt sein.
2. Modellartefakte mit vollständigem `expected_digest`, tatsächlicher installierter
   Übereinstimmung und Modell-/Lizenz-/Sicherheitsfreigabe. Die ausgelieferte Registry
   erfüllt dies nicht. Keine fingierten Approvals übernehmen.
3. Öffentliche oder synthetische PDF außerhalb des Repositorys; unabhängiger
   Herkunftsbeleg als `PilotApproval` mit `kind` (`SYNTHETIC` oder `REVIEWED_PUBLIC`),
   `reviewed_by`, `reviewed_at` und `provenance`. Aktive Inhalte/Sperrvermerke werden abgewiesen.
4. Registrieren mit dem vorhandenen Offline-CLI; Pfade sind zu ersetzende lokale Beispiele:

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.services.document_store C:\ReviewedPublicData\sample.pdf --store C:\ApprovedPublicPilot --approval C:\ReviewedPublicData\approval.json
```

Nativ benötigt der bestehende Settings-Vertrag `INFERENCE_MODE=local_pilot`,
`PILOT_MODEL_ID`, `PILOT_PROFILE_ID`, `PILOT_DOCUMENT_DIR` und den passenden
Loopback-Ollama-Endpunkt. `PILOT_ARCHITECTURE=A` oder `E`; E braucht zusätzlich
`PILOT_VERIFIER_MODEL_ID`. Ein echter lokaler Ollama-Prozess muss dann laufen.
Nach Konfiguration in derselben Umgebung neu starten und ausschließlich die
registrierte Datei auswählen. Legacy-Runs sind in diesem Modus gesperrt.

**Die ausgelieferte Basis-Compose-Datei reicht diese Pilotvariablen nicht durch.**
Eine Änderung nur in der Host-`.env` aktiviert dort keinen Pilot. Ein neuer
Container-Pilotpfad benötigt eine überprüfte Betreiberkonfiguration einschließlich
schreibgeschützter externer Katalog-/PDF-Mounts; die Doku erfindet dafür keinen
bereits ausgelieferten Override. CLI-/Test-Erfolg ersetzt keine organisatorische Freigabe.

## Vorbereitung eines DHBW-Servers

Ein freigegebener Linux-Server kann denselben Stack mit konfigurierten CPU-/RAM- und optional GPU-Limits betreiben. Voraussetzung sind ein genehmigter Docker-Host, zugriffsbeschränktes Checkout, kontrollierte Modellbeschaffung und freigegebene Modelllizenzen. Anwendung und Modell-Volume auf dem Server bereitstellen; danach den normalen internen Stack ohne Build-/Pull-Zugriff starten. Kein Kubernetes und keine Cloud-Infrastruktur erforderlich.

Den Frontend-Port zunächst auf Server-Loopback belassen. Berechtigte Entwickler können einen SSH-Tunnel verwenden: `ssh -N -L 8501:127.0.0.1:8501 user@dhbw-server`. Ein geteilter Mehrbenutzerzugang benötigt vorher Authentifizierung, Rollen, TLS und eine fachlich-organisatorische Betriebsfreigabe; diese sind nicht vorgetäuscht implementiert.

**Genau einen Backend-Prozess verwenden.** Keine zusätzlichen Uvicorn-Worker oder Backend-Replikate starten: Registry, Abbruch und Human-Freigaben liegen nur im jeweiligen Prozess. Neustarts/Updates im Team abstimmen, weil flüchtige Ergebnisse verloren gehen. Ein institutioneller Betriebsdienst kann später Compose-Start/Stop übernehmen; externe Zugriffe dürfen dabei nicht ungeprüft geöffnet werden.

## Fehlerbehebung und Offline-Abnahme

| Problem | Abhilfe |
| --- | --- |
| Modell fehlt | `docker compose exec ollama ollama list` und `/models/status` vergleichen; Registry und Bereitstellung prüfen. |
| Lauf FAILED bei Schemafehler | Kleine lokale Modelle können ungültige AgentSpecs erzeugen. Run-Fehler prüfen; Limits nicht pauschal aufheben. Modell-/Promptkompatibilität mit synthetischen Daten testen. |
| Kontextbudget überschritten | Aufgaben/Kriterien verkürzen oder registrierten Modellkontext kontrolliert erhöhen; Speicherbedarf berücksichtigen. |
| Budget erreicht | Modellaufrufe und reservierte Tokens im Run prüfen. Bewusstes Anpassen in `execution.yaml`; nicht automatisch nach außen ausweichen. |
| Review fehlt | Unabhängiges lokales Review-Modell prüfen. `MISSING` bleibt sichtbar und darf nicht als Zustimmung interpretiert werden. |
| Keine VRAM-Daten | Nicht verfügbare Messungen bleiben unbekannt/null. Ein tatsächlich gemeldeter Wert 0 ist davon getrennt; Mockwerte belegen keine reale GPU. |
| RAM/OOM oder Zeitlimit | Containergrenzen, Docker-Desktop-RAM, Modellgröße und sequentielles Laden prüfen; CPU kann lange dauern. |
| Lauf verschwunden | Backend-Neustart oder Aufbewahrungs-/Kapazitätsbereinigung; diese Version hat keine dauerhafte Run-Datenbank. |
| Port belegt | `FRONTEND_PORT` anpassen, `up -d` ausführen und Browser-Port ändern. |

Offline-Abnahme: Bereitstellung vollständig abschließen, `docker compose down` ausführen, Internet trennen, mit `--no-build --pull never --wait` starten und `smoke.py --analysis --mode D` ausführen. Dashboard und Browser-Netzwerkrequests prüfen. Dann Container neu erstellen, Modell-Digests vergleichen und Analyse erneut ausführen. Der Mockstandard beweist dabei keine reale Inferenz. Diese muss nach den obigen Pilotvoraussetzungen gesondert mit dem freigegebenen lokalen Provider nachgewiesen werden. Backendbewertungen bleiben absichtlich flüchtig.

Abhängigkeiten kontrolliert über direkte Pins ändern und mit `uv==0.13.10` auflösen:

```bash
uv pip compile backend/requirements.txt --python-version 3.12 --universal --generate-hashes --output-file backend/requirements.lock
uv pip compile frontend/requirements.txt --python-version 3.12 --universal --generate-hashes --output-file frontend/requirements.lock
uv pip compile requirements-dev.txt --python-version 3.12 --universal --generate-hashes --output-file requirements-dev.lock
```

Danach Entwicklungsinstallation, Tests, Images und echte Smoke-Tests aktualisieren. Dockerbasisimages verwenden konkrete Tags; Drittanbieter-Actions im Workflow sind dagegen auf Commit-SHAs gepinnt. Release-/Paketversionen ersetzen keine Herkunfts- und Freigabeprüfung.
