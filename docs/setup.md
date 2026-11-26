# Einrichtung, API und Serverbetrieb

## Betriebssysteme

Windows benötigt Python 3.12, Git und Docker Desktop mit Linux-Containern, WSL2-Backend und aktivierter Virtualisierung. Prüfen: `py -3.12 --version`, `docker version`, `docker compose version`. In einer WSL-Distribution eine eigene Linux-Umgebung verwenden, nicht die Windows-`.venv`.

Linux benötigt Python 3.12 inklusive venv-Unterstützung, Git, laufende Docker Engine und Compose-Plugin. Die Installation ist distributionsabhängig; die [offizielle Docker-Anleitung](https://docs.docker.com/engine/install/) verwenden. Docker-Socket- oder Docker-Gruppenzugriff verleiht weitreichende Hostrechte.

macOS benötigt Python 3.12, Git und Docker Desktop. Der Stack nutzt unter Apple Silicon Linux-arm64-Images; im vorliegenden Containeraufbau erfolgt Inferenz auf der CPU. Die NVIDIA-Konfiguration ist dafür nicht geeignet.

## Erste Installation und Aktualisierung eines bestehenden Checkouts

Alle Befehle aus dem Repository-Stamm ausführen. `.env` einmal aus `.env.example` kopieren. Bei einer vorhandenen Foundation die Datei erhalten und die neuen Ressourcenvariablen bei Bedarf ergänzen; Compose besitzt Standardwerte.

Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
.\.venv\Scripts\python.exe infrastructure/scripts/provision.py
docker compose up -d --no-build --pull never --wait --wait-timeout 180
.\.venv\Scripts\python.exe infrastructure/scripts/smoke.py --analysis --mode D
```

Linux/macOS:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock
.venv/bin/python infrastructure/scripts/provision.py
docker compose up -d --no-build --pull never --wait --wait-timeout 180
.venv/bin/python infrastructure/scripts/smoke.py --analysis --mode D
```

Die Bereitstellung lädt alle aktivierten lokalen Ollama-Modelle der Registry, baut alle Images und entfernt abschließend das temporäre Online-Netz. Der Einzelchat-Tag `LLM_MODEL` muss ebenfalls in der Registry freigegeben sein. Das vorhandene Modell-Volume wird unverändert weiterverwendet. Keine automatische Migration fremder Root-Volumes; Berechtigungen vor Übernahme gezielt prüfen.

### Unterbrochene Bereitstellung

Nach hartem Abbruch oder fehlgeschlagenem Cleanup:

```bash
docker compose -f compose.yaml -f compose.provision.yaml down --remove-orphans
docker compose up -d --no-build --pull never --wait --wait-timeout 180
```

Kein `-v` verwenden: Das Modell-Volume muss bestehen bleiben. Fehlt ein Modell, die Bereitstellung erneut starten. Niemals den kompletten Analyse-Stack mit dem Provisionierungs-Override für vertrauliche Daten betreiben.

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
| GET | `/models/status` | Alle Registry-Einträge, Hersteller, Rollen, lokale Verfügbarkeit und Digest |
| POST | `/chat` | Einzelchat, Body `{ "prompt": "Hallo" }` |
| GET | `/agents` | Konfigurierte statische Definitionen und erstellte Agenteninstanzen |
| GET | `/agents/{agent_id}` | Laufzeitstatus eines Agenten |
| GET / POST | `/runs` | Läufe auflisten / neue synthetische Analyse starten |
| GET | `/runs/{run_id}` | Status, Fortschritt, Metriken, Snapshots und Ausgabe |
| GET | `/runs/{run_id}/graph` | Agentenknoten und Parent-Child-Kanten |
| GET | `/runs/{run_id}/findings` | Befunde, Belege, Reviews, Konflikte und Human-Status |
| POST | `/runs/{run_id}/cancel` | Lauf kontrolliert abbrechen |
| POST | `/findings/{finding_id}/review` | Menschliche Entscheidung und optionale Bearbeitung |
| GET | `/system/resources` | Lokale Ressourcen und aktive Ausführungen |

Zusätzlich `GET /health` für Backend-Liveness. Fehlender Modellbestand macht den Backend-Prozess nicht unhealthy. Ein verfügbarer Modelltag bestätigt noch keine erfolgreiche Inferenz.

Run-Body: `{ "document_id": "synthetic-demo", "mode": "D", "task": "Prüfe die Arbeit", "criteria": ["Methodik", "Forschungsfrage"] }`. Klassifizierung, beliebige Dokumentpfade und Provider lassen sich nicht über den Body setzen. Review-Body: `{ "decision": "ACCEPTED", "note": "Beleg geprüft", "edited_statement": "Optional bearbeiteter Befund" }`; `REJECTED` ist ebenfalls möglich. Ohne Bearbeitung `edited_statement` weglassen.

Fehler enthalten `detail` und bei zentral behandelten Fehlern zusätzlich `code`. 403 bedeutet Policy-Sperre, 404 fehlendes/bereinigtes Objekt, 409 unpassenden Zustand, 422 Schema-/Planfehler, 429 Budget-/Kapazitätslimit, 502 fehlerhafte Providerantwort, 503 fehlenden Provider/Modell, 504 Zeitlimit. Kein Fehler spiegelt vertrauliche Eingabewerte zurück. Hintergrundfehler stehen im Run-Status statt als nachträglicher HTTP-Fehler des Startaufrufs.

Backend und Ollama bleiben intern. Ohne zusätzliche Portfreigaben in PowerShell oder POSIX-Shell prüfen:

```bash
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/models/status').read().decode())"
docker compose exec backend python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/v1/runs').read().decode())"
```

Für Start, Review und Abbruch das Dashboard oder den Smoke-Test nutzen. Im nativen Backend-Entwicklungsmodus stehen OpenAPI und interaktive API-Tests unter `http://localhost:8000/docs` bereit.

## Native Entwicklung

Nur für freigegebene Testdaten; native Prozesse besitzen keine Docker-Netzisolation. Lokales Ollama separat auf Loopback starten, Cloudfunktionen deaktivieren und Modelle bereitstellen. Windows, je ein Terminal:

```powershell
$env:OLLAMA_HOST='127.0.0.1:11434'
$env:OLLAMA_NO_CLOUD='1'
ollama serve
```

```powershell
$env:OLLAMA_BASE_URL='http://localhost:11434'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload --no-access-log
```

```powershell
$env:BACKEND_URL='http://localhost:8000'
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py --server.address=127.0.0.1 --browser.gatherUsageStats=false --theme.base=dark --theme.primaryColor='#dc2626'
```

Linux/macOS verwenden `.venv/bin/python` und vorangestellte Umgebungsvariablen, etwa `OLLAMA_BASE_URL=http://localhost:11434 .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload --no-access-log`. In `.runtime/` nur synthetische Daten erwarten. Das vollständige Streamlit-Theme liegt in `frontend/.streamlit/config.toml`; Docker kopiert es an den Arbeitsort.

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
| Keine VRAM-Daten | Ollama `/api/ps` kann nicht verfügbar sein; CPU-Betrieb oder bereits entladene Modelle können 0 liefern. |
| RAM/OOM oder Zeitlimit | Containergrenzen, Docker-Desktop-RAM, Modellgröße und sequentielles Laden prüfen; CPU kann lange dauern. |
| Lauf verschwunden | Backend-Neustart oder Aufbewahrungs-/Kapazitätsbereinigung; diese Version hat keine dauerhafte Run-Datenbank. |
| Port belegt | `FRONTEND_PORT` anpassen, `up -d` ausführen und Browser-Port ändern. |

Offline-Abnahme: Bereitstellung vollständig abschließen, `docker compose down` ausführen, Internet trennen, mit `--no-build --pull never --wait` starten und `smoke.py --analysis --mode D` ausführen. Dashboard und Browser-Netzwerkrequests prüfen. Dann Container neu erstellen, Modell-Digests vergleichen und Analyse erneut ausführen. Das prüft Modellpersistenz und reale Inferenz, nicht Persistenz der absichtlich flüchtigen Runs.

Abhängigkeiten kontrolliert über direkte Pins ändern und mit `uv==0.13.10` auflösen:

```bash
uv pip compile backend/requirements.txt --python-version 3.12 --universal --generate-hashes --output-file backend/requirements.lock
uv pip compile frontend/requirements.txt --python-version 3.12 --universal --generate-hashes --output-file frontend/requirements.lock
uv pip compile requirements-dev.txt --python-version 3.12 --universal --generate-hashes --output-file requirements-dev.lock
```

Danach Entwicklungsinstallation, Tests, Images und echte Smoke-Tests aktualisieren. Image- und Actions-Versionen sind konkrete Tags, keine unveränderlichen Digests/Commit-SHAs.
