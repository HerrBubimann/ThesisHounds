# Öffentliche Forschungsdaten Implementierung und Prüfergebnisse

> Historischer Nachweis dieser Iteration. Testzahlen, Werkzeugverfügbarkeit und
> offene Infrastrukturprüfungen beziehen sich auf den unten genannten Prüfzeitpunkt.
> Aktueller konsolidierter Stand: [Validierung](../validation.md).

Fortsetzung vom 28.11.2026: [Parallele Prüfungen und gemeinsames Ergebnis](parallel_review_results.md).
Die folgenden Zahlen dokumentieren weiterhin den früheren Stand vom 27.11.2026.

Stand **27.11.2026, Europe/Berlin**. Erweiterung des vorhandenen ThesisHounds-
Assessmentpfads, keine Produktions- oder Modellfreigabe. Die offizielle Projekt-
PowerPoint liegt weiterhin nicht vor; die OFF-1–5-Zuordnung folgt der vorhandenen
Traceability und dem dokumentierten Professorenfeedback. Vorrang haben kontrollierter
PDF-Import, lokale Inferenzgrenzen und nachvollziehbare menschliche Begutachtung für
DHBW Mosbach Data Science und KI.

## Tatsächlich implementiert

| Anforderung | Bestehende Komponenten / Änderung | Nachweis und Grenze |
|---|---|---|
| P0 Bestandsaufnahme / OFF-2/3/5 | Research Gateway, Provider Registry, Local Verification, Snapshot Store, GROBID, Knowledge Base, Context/Planning, Gateway, Evaluation und Privacy geprüft | [Bestandsmatrix und Betrieb](../research/local_scientific_infrastructure.md); kein paralleler Orchestrator |
| P0 Quellenkonsolidierung / OFF-3/5 | `research/provider_registry.py`, `citations.py`, `isbn.py`: gemeinsame DOI-/ISBN-Identität, SourceType-Präferenzen, Provider-/Feldkonflikte und partielle Metadaten | Exakte verglichene Felder, Quellenstatus und fachliche Relevanz getrennt; kein fachlicher Wahrheitsnachweis |
| P0 Auditfehler / OFF-3/4 | Unscharfe Titel konnten zuvor als VERIFIED_METADATA gelten; ähnliche Titel und partielle Namen bleiben jetzt Kandidaten | Regression mit fast identischem Titel; Metadatenkonflikt kann keine Bestätigung erhalten |
| P0 DBLP / OFF-2/3 | `research/dblp.py`: Streaming-XML, Titel/Autoren/Jahr/Venue/DOI/Typ/Key, Größen-/Komplexitätslimits und Entityschutz | Synthetische Parser-, XXE-, Limit- und Abbruchtests; echter Probeabruf HTTP 202, kein bestätigter Realimport |
| P1 Wissensbasis / OFF-2/3/5 | vorhandener LocalResearchCache nutzt wahlweise SQLite/FTS5; `sqlite_store.py` hält unveränderliche Versionen, Hashes und atomaren CURRENT-Wechsel | DOI-/ISBN-/Titel-/Autorensuche, Version-/Notice-/Jahr-/Typfelder; gepinnte Leser, Rollback und Manipulationsabwehr geprüft |
| P1 öffentliche Syncvorbereitung / OFF-2/3 | `sync_scientific.py`, eigene Compose-Variante: ein festes DBLP-Beispiel, keine freie Query/URL/Keys; TLS/IP-Pinning, Rate/Retry-After, Range/If-Range, Prüfsumme, Speicherlimits und Manifest | HTTP-Mocks prüfen Resume/Redirect/Rate/Digest; kein Zielhost-Netztest und keine erfolgreiche echte Datensynchronisierung |
| P1 Books-/Data-/Softwaremetadaten / OFF-3/5 | begrenzte lokale Open-Library-, DataCite- und Zenodo-JSON-Adapter im bestehenden Registrymodul | synthetische ISBN-only-, Daten-/Softwareversions- und Konfliktfälle; keine Onlineprovider aktiviert |
| P1 LanguageTool / OFF-2/3 | `services/language_tool.py`, `AcademicReviewServices`, Profile/Workflow: optionaler Loopbackadapter, explizites formales Kriterium, Originaloffsets und geschütztes Ergebnis | Mock-HTTP, UTF-16, Zitat-/Code-/Formel-/Literaturschutz, Redirect-/Private-Deny und Embargo geprüft; kein echter Java-Server getestet |
| P1 Retrievalmessung / OFF-3/5 | `LocalContextIndex.search_fulltext` und `evaluation/retrieval.py`: bestehende Suche gegen flüchtiges FTS5, identische Originalchunks/Queries, deterministische P@k/R@k/MRR@k/nDCG@k | Handrechenbare synthetische Qrels und Scopeabwehr; Demo ohne menschliche Referenzen hat Qualitätswerte null |
| OFF-2/3/5 Provenance/UI-Quelle | Workflow protokolliert Bibliotheksversion und verwendet denselben Citation-Engine-Bericht für Sourcechecks, Coverage und akademische Checks | API-Regression weist Version/Alter und Embargo nach; alter leerer Vergleichs-Sourcecheck wurde entfernt |

Keine neue Laufzeitabhängigkeit, kein PostgreSQL/Graphdienst und kein beliebiger
Code-, SQL-, Shell- oder Netzwerkzugriff für Agenten. Die bestehenden Toolrechte
bleiben auf `document.read` beschränkt. Unveränderte Produktions-/Sperrvermerk-/IFC-
Grenzen werden nicht durch neue Umgebungsflags freigegeben.

## Recherchierter und bewusst nicht aktivierter Umfang

Die [Quellenprüfung aller fünfzehn angefragten Angebote](../research/scientific_sources_2026-11-27.md)
nennt Quellentypen, Metadaten, dokumentierte Endpunkte, Zugang, Kosten/Limits,
Bulkwege, Lizenzen, Datenschutz und Mosbach-Relevanz. Nicht zuverlässig erreichbare
Angaben sind ausdrücklich unbekannt, nicht aus Drittanbieterlisten ergänzt.
Aktuell bedeutsam: OpenAlex-Ratenmodell ist differenziert; Unpaywall-Suche ist
eingestellt; DOAJ-Dumps benötigen Einzelfallzugang. Bezahlte Anbieterpfade, Keys,
Top-ups, Depot-/Archivierungs-/Publish-Endpunkte sind nicht implementiert.

BGE-M3 wurde anhand offizieller Modellkarte und Publisher-Metadaten untersucht:
MIT, Revision und Dateidigest sind dokumentiert, aber keine lokal geprüften Gewichte.
Keine Modellpakete oder Embeddings wurden heruntergeladen. C/D/E der Retrieval-
Evaluation bleiben BLOCKED_NO_APPROVED_EMBEDDING_OR_RERANKER. Ein deutschsprachiger
Retrievalvorteil und reale RAM/VRAM-Anforderungen sind nicht nachgewiesen.

citeproc-py und CSL wurden untersucht; es fehlt ein bestätigter Mosbach-Originalstil
mit zulässigen Varianten/Referenzbeispielen. Es gibt keinen erfundenen DHBW-CSL-Stil
und keine neue Stilbenotung. ranx wurde untersucht; die kleinen deterministischen
Pilotmetriken benötigen vorerst keine NumPy/Numba-Erweiterung. SymPy/SciPy/Pandera-
Werkzeuge und systematischer Software-Reproducibility-Check bleiben P2, weil konkrete
Rohdaten und bestätigte Prüfaufträge fehlen. DataCite-/Zenodo-Versionstreffer sind
keine erfolgreich reproduzierten Experimente. Software-Heritage-Rohimport, weitere
Provideradapter und große Gesamtdumps sind bewusst nicht vorgetäuscht implementiert.

## Tatsächliche Prüfungen

Ausgangspunkt war der im vorherigen Durchlauf belegte Stand mit 779 Tests. Der
abgeschlossene aktuelle Gesamtlauf ergibt **819 Tests bestanden**, **0 Fehler**,
**0 übersprungen**, **86,73 % kombinierte Statement-/Branch-Coverage**. Die
verbindliche Schwelle bleibt **80 %**, `thesishounds-ci-gate` und Pflichtjobs bleiben
erhalten. Es wurden 40 weitere synthetische Regressionen ergänzt.

| Prüfung | Beobachtetes Ergebnis |
|---|---|
| Vollständiges pytest mit API/UI/PDF/Security | 819 bestanden; JUnit `reports/public-research-tests.xml` |
| Securityumfang innerhalb des Gesamtlaufs | 370 Tests bestanden |
| Ruff Lint / Format | bestanden; ein fehlender Abstand im Markdown-Pythonbeispiel wurde korrigiert und erneut geprüft |
| Compileall / pip check | bestanden |
| Bandit | bestehendes MEDIUM-Severity/-Confidence-Gate bestanden |
| pip-audit | vier unveränderte Hash-Lockdateien geprüft, keine bekannten Befunde; vorhandener CI-Parser bestätigt den JSON-Bericht |
| Compose statisch | alle sieben Varianten bestanden, einschließlich separatem public-sync; kein Containerstart |
| Artefakt-Privacy-Canaries | bestanden |
| Retrieval-Demo | zwei synthetische Queries × fünf Varianten; A/B vier Ausführungen, C/D/E sechs explizite Blockierungen; keine Human-Qrels, alle Qualitätsmetriken null |
| Echter öffentlicher DBLP-Einzelprobeabruf | ausschließlich fest gewählter öffentlicher Export, Antwort HTTP 202; Antwort nicht als XML akzeptiert, kein Snapshot aktiviert |

Neue Tests: `tests/unit/test_public_library.py`, `test_local_academic_tools.py`,
`tests/security/test_public_scientific_boundaries.py` und
`tests/integration/test_public_scientific_workflow.py`. Bestehende Zitationstests
wurden nur dort angepasst, wo DataCite nun tatsächlich ein lokaler Adapter ist;
ein weiterhin nicht implementierter Anbieter prüft die unveränderte Denygrenze.
Alle HTTP-Testantworten sind Mocks. Echte Modellinferenz ist kein CI-Test.

Die Windows-Prüfung erkannte außerdem einen echten Implementierungsfehler beim
ersten SQLite-Prototyp: ein SQLite-Contextmanager schließt die Verbindung nicht
automatisch. Explizites `closing()` verhindert offene Dateihandles bei atomarem
Versionswechsel; der erfolgreiche Regressionstest prüft Aktivierung und Rollback.
Unbekannte Quelldatenzeit wird unabhängig von Importzeit als UNKNOWN behandelt.

## Reproduzierbare Befehle

```powershell
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --cov --cov-report=xml `
  --junitxml=reports/public-research-tests.xml
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
.venv\Scripts\python.exe infrastructure/scripts/validate_docker.py
.venv\Scripts\python.exe infrastructure/scripts/privacy_dlp.py artifacts
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.evaluation.retrieval --output reports/retrieval-public-demo.json
```

Import-, Merge-, Rollback- und isolierte Syncbefehle sowie Ressourcenlimits stehen
im [Betriebsnachweis](../research/local_scientific_infrastructure.md). Tests benötigen
normale lokale Temp-Verzeichnisrechte; die eingeschränkte Sandbox dieses Arbeitsplatzes
verhinderte solche Zugriffe, weshalb die Tests mit normalen lokalen Dateirechten
ausgeführt wurden. Das erteilt keine neue Anwendungs-/Produktionsfreigabe.

## Offene Abnahmen und verbleibende Risiken

Docker-Client vorhanden, Docker-Daemon nicht erreichbar. Keine neuen Images gebaut,
keine echten Container-/DNS-/IPv6-/Firewall-/Ressourcenproben; das Backendimage bereitet
lediglich die Eigentümerschaft eines neuen öffentlichen Stagingvolumes vor.
Ein bestehendes Volume benötigt weiterhin korrekte Operatorrechte. Keine aktuelle
Trivy-Abnahme; historische Imagebefunde bleiben offen. Git ist nicht ausführbar,
deshalb kein vollständiger Git-/History-DLP-/Gitleaks-Nachweis. Kein Commit, Push,
GitHub-Actions-Lauf, Remote-Schreibzugriff oder vertraulicher externer Datentransfer.

Der echte lokale LLM/PDF-Gesamtlauf bleibt wegen fehlender erreichbarer/freigegebener
Inferenzinfrastruktur offen. Der DBLP-Export ist an diesem Zugang nicht als XML
bestätigt. LanguageTool-Service, Embeddingartefakte, Original-CSL-Stil, fachlich
bestätigte Retrievalaufgaben und Rohdaten für Statistik fehlen. Die neue öffentliche
Syncumgebung ist konfiguriert und statisch geprüft, nicht auf dem Zielhost isoliert
abgenommen. Keine automatische periodische Aufgabe wurde eingerichtet.

Metadatenquellen können falsch, veraltet, unvollständig oder manipuliert sein. Hashes
erkennen Änderung gegenüber dem lokalen Manifest, ersetzen aber keine signierte
Herkunfts-/Operatorauthentifizierung. Fuzzytreffer, Autorenaliases, Editions-/
Versionsunterschiede, Zitatgrenzen und Sprachregeln brauchen menschliche Klärung.
Kein beobachteter technischer Test belegt einen wissenschaftlichen Qualitätsgewinn,
eine höhere Gutachterakzeptanz, reale Retrievalgüte oder menschliche Zeitersparnis.
