# Parallele Prüfungen: Implementierung und überprüfte Ergebnisse

> Historischer Nachweis dieser Iteration. Testzahlen, Werkzeugverfügbarkeit und
> offene Infrastrukturprüfungen beziehen sich auf den unten genannten Prüfzeitpunkt.
> Aktueller konsolidierter Stand: [Validierung](../validation.md).

Stand: **28.11.2026, Europe/Berlin**. Lokaler Entwicklungsstand; keine
Produktions-, Datenschutz-, Modell- oder fachliche Freigabe.

Der bestehende Assessment-Workflow führt wissenschaftliche Bewertung, lokale
Formalien-/Quellenprüfung, Sprache, Retrievalvergleich und optionales Zitierformat
unter gemeinsamen Limits aus. Nach Abschluss entsteht ein gemeinsamer Bericht
im Vergleich, im Provenienzbericht und im menschlichen Gutachtenentwurf.
Widersprüche und nicht verfügbare Prüfungen bleiben erhalten. Menschliche
Erstbewertung, Befundfreigabe und Finalentscheidung bleiben maßgeblich.

## Geänderte Komponenten und Anforderungsbezug

| Änderung | Komponenten | Beitrag zu den bestehenden Anforderungen |
|---|---|---|
| Begrenzte parallele Teilprüfungen; Fehler-, Zeitlimit- und Abbruchbehandlung | `agents/academic_review.py`, `workflows/assessment_workflow.py` | OFF-2/3/5: kontrollierter vorhandener Workflow und nachvollziehbarer Ressourceneinsatz |
| Gemeinsamer Bericht mit getrenntem Ausführungs-/Ergebnisstatus; veraltete Versionen sperren Finalisierung | Workflow, `frontend/assessment_review.py` | OFF-3/5 und ENG-6/10: menschliche Validierung, unverdeckte Einschränkungen, Provenienz |
| Einmaliger FTS-Aufbau und RRF mit dokumentgebundenen Originalspannen | `services/context_management.py`, `evaluation/retrieval.py` | OFF-3/5 und ENG-8: kontrollierter Retrievalvergleich, Qualität ohne Labels unbekannt |
| Optionale lokale Qwen3-/E5-/BGE-M3-Anbindung mit freigegebenen Artefakten | `services/local_embeddings.py`, `embedding_worker.py`, Settings | OFF-2/3/5: vorhandene Modellslots, lokale Schnittstelle und explizite Ressourcenlimits |
| Optionaler lokaler citeproc-js-Adapter und gesperrte Stilaktivierung | `services/citation_style.py`, `infrastructure/citeproc`, Settings und CI | OFF-3/5: reproduzierbare Formatkandidaten, keine erfundene Hochschulregel |
| DBLP-Release-/Subset-Auswahl im vorhandenen Snapshot Store | `research/dblp.py`, Provider Registry, Snapshot-/SQLite-Store | OFF-3/5 und ENG-7: begrenzte lokale Verifikation mit Versionsbezug |

Die Zuordnung übernimmt die vorhandene Traceability. Ein vollständiger offizieller
Detailkatalog und fachlich bestätigte Referenzbewertungen fehlen weiterhin; aus
Softwaretests folgt keine vollständige Erfüllung wissenschaftlicher Qualitätsziele.

## Tatsächlich ausgeführte Prüfungen

Abschließender vollständiger Lauf:

```powershell
.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --cov `
  --cov-report=xml:reports/coverage-parallel.xml `
  --cov-report=json:reports/coverage-parallel.json `
  --cov-report=term:skip-covered --junitxml=reports/junit-parallel-review.xml
```

- **878 bestanden, 0 fehlgeschlagen, 0 übersprungen**; darunter **370 Sicherheitsfälle**.
- **87,12 % kombinierte Zeilen-/Branch-Coverage**; bestehendes Gate unverändert **80 %**.
- Ruff lint und Formatprüfung bestanden; Python-Syntaxprüfung bestanden.
- Bandit-Gate bestanden: keine MEDIUM-/HIGH-Funde; LOW-Statistik im Bericht vorhanden.
- `pip-audit` über alle vier bestehenden Python-Locks: keine bekannten Schwachstellen.
- `npm audit` für das gesperrte citeproc-Paket: keine bekannten Schwachstellen.
- Statische Docker-/Composevalidierung für alle **sieben** bestehenden Varianten bestanden.
- Artefakt-Datenschutzprüfung bestanden (`ARTIFACT_PRIVACY_PASSED`).

Lokale Nachweise: `reports/junit-parallel-review.xml`, `coverage-parallel.json/.xml`,
`reports/security/bandit-parallel.json`, `pip-audit-parallel.json` und
`reports/parallel-public-demo.json`. Die Reports sind generierte lokale Artefakte,
keine eingecheckten unabhängigen Zertifikate. Der letzte Komplettlauf dauerte 74,70 s
auf diesem Entwicklungsrechner; das ist kein repräsentativer Performancebenchmark.

Der Demoablauf verwendet ausschließlich eingebaute synthetische Seiten und einen
Mock-Provider. Er erzeugt einen freigegebenen gemeinsamen Bericht für alle fünf
Teilprüfungen. Nicht aktivierte Stil-/Sprachprüfungen erscheinen als solche; fehlende
Embedding-Artefakte sind explizit gesperrt. Die fachliche Qualität wird nicht bewertet.

Die gezielten neuen Regressionen prüfen:

- tatsächliche Überlappung unabhängiger Prüfungen und das gemeinsame Limit über zwei Läufe;
- Pflichtfehler, optionale Fehler, Zeitlimits, Abbruch und Ende asynchroner Geschwister;
- Freigabesperre für den gemeinsamen Bericht und Finalisierungssperre bei Versionswechsel;
- denselben gespeicherten Quellenbericht für unveränderte Dokumente;
- einmaligen FTS-Aufbau bei mehreren Threads, Originaloffsets und fremde/doppelte RRF-Chunks;
- fehlende, veränderte oder unfreigegebene Encoderartefakte, ungültige Vektoren und Modellslotbindung;
- Worker-Protokoll, gefilterte Umgebung sowie Beenden/Abwarten bei Timeout oder Abbruch;
- freigegebene/gesperrte CSL-Bundles, Profil-/Dateihashes, XML-Entities, Privatdatensperre;
- DBLP-Auswahl, Releasebezug, fehlerhafte Checksummen und atomar abgewiesene unvollständige Versionen.

**Realer Teiltest:** Die installierte citeproc-js-Version 2.4.63 hat im lokalen
Node-Prozess einen selbst definierten synthetischen Titelstil tatsächlich gerendert.
Dieser Test verwendet keine Modellinferenz und bestätigt keinen offiziellen DHBW-Stil.
CI installiert den gesperrten citeproc-Testprozessor ohne Lifecycle-Skripte und prüft
ihn zusätzlich mit npm audit. Das bestehende `thesishounds-ci-gate` bleibt erhalten.

**Mock-Teile:** Encodervektoren und SentenceTransformer-Objekte werden in den
Regressionstests gezielt simuliert. Kein Qwen3-/E5-/BGE-M3-Gewicht wurde geladen,
keine reale semantische Retrievalqualität oder RAM-/GPU-Belegung gemessen.
Das bestehende LanguageTool wurde weiterhin nur mit Mock-HTTP getestet.

## Verbleibende Freigaben und Einschränkungen

Lokale Embeddings benötigen geprüfte Artefakte, Revisionen, Lizenzen und eine separat
reproduzierbar bereitgestellte Torch-/SentenceTransformers-Laufzeit. Die Anbindung
ist ein Host-Opt-in; sie wird nicht durch die neue Einstellung automatisch freigegeben
oder in das normale Backend-Dockerimage installiert. Neue private Dokumentpfade,
öffentliche Dokumentabfragen, kostenpflichtige APIs und KI-Benotung bleiben gesperrt.

citeproc deklariert CPAL-1.0 OR AGPL-1.0. Die Produkt-/Distributionslizenzprüfung,
ein bestätigter offizieller CSL-Stil und geprüfte zugehörige Locales sind offen.
Heuristisch extrahierte Autoren, Quellentypen und fehlende bibliografische Felder
begrenzen Formatvergleiche. Abweichungen bleiben menschlich zu prüfende Kandidaten.

DBLP-Tests verwenden synthetisches XML. Ein aktueller realer Monatsrelease wurde
nicht heruntergeladen oder aktiviert. Die Auswahl nimmt bereits begrenzte,
menschlich geprüfte öffentliche XML-Teilbestände entgegen, keine vollständigen
Dump-/Gzip-/DTD-Imports. Provenienz einer Ableitung bleibt operatorgeprüft.

Docling und RapidFuzz sind in diesem Schritt nicht integriert. Für Docling fehlen
Artefakt-/Ressourcenfreigabe und ein Extraktionsvergleich; für RapidFuzz ein belegter
Vorteil gegenüber dem vorhandenen konservativen Fuzzy-Kandidatenverfahren.
Für Retrieval fehlen repräsentative fachlich bestätigte Qrels. Übereinstimmung,
Texttreffer und nicht gefundene Quellen belegen weder Wahrheit noch Inhaltsabwesenheit.

Docker-Daemon, echte Containerstarts, reale lokale LLM-Inferenz und Remote-GitHub-CI
wurden hier nicht ausgeführt. Die lokale statische Composevalidierung ersetzt sie
nicht. Der vollständige Lauf wurde unter Windows/Python 3.12.6 durchgeführt.
Node war für den synthetischen lokalen Processor-Test vorhanden; dessen Test ist
keine Freigabe dieser Host-Laufzeit für den Produktivbetrieb.

Konfigurationsverträge, Quellen und reproduzierbare Operatorbefehle:
[Betrieb und Grenzen](../research/parallel_scientific_checks.md).
