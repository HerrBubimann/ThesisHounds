# Parallele wissenschaftliche Prüfungen und gemeinsames Ergebnis

Stand: 28.11.2026, Europe/Berlin. Erweiterung des bestehenden Assessment-Workflows.
Keine neue Agentenplattform, keine automatische Benotung und keine Produktionsfreigabe.

## Ablauf und Grenzen

`AcademicReviewServices.run_checks` startet inzwischen sechs begrenzte unabhängige
Teilprüfungen (der ursprüngliche 878-Test-Checkpoint hatte fünf):

| Prüfung | Tatsächliche Ausführung | Ergebnis |
|---|---|---|
| Wissenschaftliche Zweitbewertung | vorhandener `AISecondReviewer`, Gateway, Gegenprüfung und Budgets | Kriterienbefunde; standardmäßig Mock-Inferenz |
| Formalien und Quellen | vorhandene Regeln und lokale Citation Engine, begrenzter Hintergrundthread | lokale Fakten, Metadatenstatus und Konflikte |
| Sprache | vorhandener optionaler Loopback-LanguageTool-Adapter | Vorschläge nur bei ausdrücklich konfiguriertem formalen Kriterium |
| Retrievalvergleich | Feature-Hash-Suche, wiederverwendetes SQLite FTS5 und optional freigegebene lokale Encoder | Fundstellen je Verfahren und gemeinsame RRF-Auswahl |
| Zitierformat | optionaler lokaler citeproc-js-Prozess mit geprüftem CSL und lokalen Sprachdateien | Formatkandidaten mit Originalspannen und menschlicher Prüfpflicht |
| Numerische Konsistenz | begrenzte deterministische Dezimal-/Einheiten-/Kontextprüfung | Prüfkandidaten mit Originalstellen; keine automatische fachliche Fehlerbestätigung |

Eine geteilte Semaphore begrenzt die parallel laufenden Teilprüfungen auch über mehrere
Assessmentläufe hinweg auf `max_parallel_agents` (aktuell 2). Lokale Encoder nutzen
zusätzlich denselben Modellslot wie der bestehende LLM-Gateway und eine eigene
Semaphore von 1. Modellprozesse werden nacheinander geladen; das neue Retrieval
ersetzt nicht ungeprüft die Kontextauswahl des wissenschaftlichen Reviewers.

Die Teilprüfungen erhalten Dokument-/Profilkopien ohne menschliche Erstbewertung.
Ein Ausfall einer verpflichtenden wissenschaftlichen oder akademischen Prüfung
bricht die Gruppe ab. Fehler optionaler Prüfungen bleiben im Bericht sichtbar.
TaskGroup wartet auf das Ende abgebrochener asynchroner Geschwister. Begrenzte,
rein lesende Python-Hintergrundthreads lassen sich nicht hart abbrechen; sie besitzen
nur die Kopie des Eingangs und schreiben keine späteren Assessmentergebnisse.
Encoder-/CSL-Kindprozesse werden bei Zeitlimit oder Abbruch beendet und abgewartet.

`combined_result` erscheint nach derselben menschlichen Freigabe wie der bisherige
Vergleich, außerdem im Provenienzbericht und beim Gutachtenentwurf. Der Bericht
enthält Teilstatus, Laufzeiten, Dokument-/Profilhash, Quellenstatus, widersprüchliche
Befunde, nicht bewertbare Kriterien und fehlende Artefakte. Tasks haben zusätzlich
einen `result_status`, der etwa `DISABLED` oder `NOT_APPLICABLE` sichtbar macht.
`configured_checks_complete` unterscheidet konfigurierte Prüfungen von lediglich
vorgemerkten, noch nicht bereitgestellten Encodern. Technisch abgeschlossene Tasks
belegen keine vollständige fachliche Analyse. Die vorhandene Coverageansicht
bleibt maßgeblich für fehlende Kriterien und offene menschliche Entscheidungen.
Eine Übereinstimmung mehrerer Verfahren wird nicht als wissenschaftliche Bestätigung
gezählt. Der Gutachtentext verwendet weiterhin nur menschlich entschiedene Inhalte.

Bei unverändertem Dokument verwenden akademische Ansichten den gespeicherten
Quellenprüfbericht. Eine nachträgliche Änderung an Dokument oder Profil markiert das
gemeinsame Ergebnis als `STALE_REQUIRES_NEW_REVIEW` und sperrt die Finalisierung.
Für echte Pilot-PDFs bleibt die strengere bestehende Dokumentversionssperre erhalten.

## Lokaler Embeddingvergleich

Die Modellkandidaten sind [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
(Apache-2.0, 1024 Dimensionen),
[multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small)
(MIT, 384) und [BGE-M3](https://huggingface.co/BAAI/bge-m3) (MIT, 1024).
Die Anbindung verwendet die dokumentierte lokale
[SentenceTransformer-Schnittstelle](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html).
Es wurden keine Gewichte und keine Torch-/SentenceTransformers-Laufzeit installiert.

`LOCAL_EMBEDDING_MANIFEST_DIR` bezeichnet ein externes, administrativ verwaltetes
Verzeichnis mit höchstens drei JSON-Manifests. `EmbeddingArtifact` verlangt:

- passende Modell-ID, Repository, Dimensionen und Lizenz;
- eine konkrete 40-stellige Revision und SHA-256 für jede lokale Artefaktdatei;
- einen externen Modellpfad ohne Symlinks, höchstens 200 Dateien und 4 GB;
- `approved_by`, `license_reviewed`, `security_reviewed`, `runtime_reviewed`;
- Safetensors statt Pickle-Gewichten; keine Modellskripte oder Remote-Code-Freigabe.

Die Felder sind dokumentierte menschliche Freigaben, keine digitale Signatur und
kein Ersatz für administrativ geschützte Dateien. Ohne tatsächlichen Artefakt- und
Laufzeitreview darf kein Manifest aktiviert werden. Die optionalen Laufzeitpakete
müssen vor Aktivierung separat versioniert, sicherheitsgeprüft und reproduzierbar
bereitgestellt werden; sie gehören derzeit nicht zum freigegebenen Backend-Lock.

Der feste Worker läuft mit CPU, Offlineflags, `local_files_only=True`,
`trust_remote_code=False`, `token=False` und `use_safetensors=True`.
Host-Zugangstokens werden nicht in die Prozessumgebung übernommen. Python-Audithooks
weisen Socket-/Kindprozessereignisse ab. Das ist zusätzliche Abwehr, kein Ersatz
für eine Betriebssystem-Netzwerksperre gegenüber nativen Bibliotheken. Verarbeitung
bleibt auf PUBLIC-Dokumente beschränkt; kein neuer privater Verarbeitungsweg.

Der Vergleich verwendet höchstens 256 Dokumentchunks und ein gemeinsames Fenster von
512 Tokens. Teilmengenauswahl und mögliche Tokenkürzung sind ausgewiesen. Qwen erhält
die Query-Instruktion, E5 die Query-/Passage-Präfixe. Gemessen wird eine Dauer inklusive
Warten und Integritätsprüfung; nativer Peak-RAM bleibt unbekannt. Ohne reale Inferenz
und menschliche Referenzpassagen ist kein Qualitätsvorteil nachgewiesen.

`review_retrieval(..., references=[RetrievalReference(...)])` erlaubt abgegrenzte
Experimente mit expliziten Relevanzlabels derselben Dokumentversion und Originalchunks.
P@k/R@k/MRR@k/nDCG@k werden je Verfahren und RRF-Auswahl berechnet. Ohne Labels bleiben
sie `null`. Die allgemeine synthetische A/B-Demo bleibt reproduzierbar:

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.evaluation.retrieval --output reports/retrieval-public-demo.json
```

Ein FTS-Index wird pro Dokument lazily einmal im RAM angelegt, für weitere Queries
wiederverwendet, threadgeschützt gelesen und am Ende geschlossen. Die erste
FTS-Suchdauer enthält den Aufbau; spätere Aufrufe nicht. RRF verwendet die
[veröffentlichte Formel mit k=60](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)
und verbindet ausschließlich Fundstellen. Fremde und doppelte Chunkreferenzen
werden abgewiesen.

## citeproc-js und freigegebene Stile

Die optionale Host-Laufzeit liegt unter `infrastructure/citeproc`. Installation:

```powershell
npm ci --prefix infrastructure/citeproc --ignore-scripts --no-audit --no-fund
npm audit --prefix infrastructure/citeproc --package-lock-only --omit=dev --audit-level=low
```

`citeproc` ist auf 2.4.63 mit npm-Integrität im Lock festgelegt. Der Pythonadapter
prüft zusätzlich den SHA-256 der direkt geladenen CommonJS-Datei. Die
[Paketmetadaten](https://registry.npmjs.org/citeproc/2.4.63) deklarieren
**CPAL-1.0 OR AGPL-1.0**, keine MIT-Lizenz. Lizenzpflichten und etwaige Distribution
müssen vor Nutzung geprüft werden. Der Adapter verlangt dafür
`processor_license_reviewed`; die Testinstallation ist keine Produktfreigabe.

`CITATION_STYLE_DIR` liegt außerhalb des Repositorys. Für Profil `pa1-example`
werden `pa1-example.json`, `pa1-example.csl` und die im Manifest aufgeführten
`locales-<Sprachtag>.xml` benötigt. Der Manifestvertrag `CitationStyleBundle` enthält
Profilhash, erlaubte Kriterium-IDs, Quellenangabe, Reviewer, Stilstatus, Stilhash,
Locale-Hashes und die Processor-Lizenzprüfung. Nur formale Kriterien mit
`local_checks: [citation_style]` lösen die Prüfung aus. Ein APPROVED-Profil
verlangt einen APPROVED-Stil. Beispielkataloge wurden nicht stillschweigend geändert.

XML-Entitäten/DTDs, fremde Pfade und veränderte Dateien werden abgewiesen. Items und
Locales werden nach der [citeproc-Dokumentation](https://citeproc-js.readthedocs.io/en/latest/running.html)
ausschließlich lokal bereitgestellt. Der Kindprozess hat 128 MB V8-Heap und zehn
Sekunden Zeitlimit; Netzwerk-/Prozessfunktionen werden zusätzlich gesperrt.
Diese JavaScript-Abwehr ersetzt ebenfalls keine Betriebssystemisolierung.

Es gibt noch keinen bestätigten offiziellen DHBW-Mosbach-CSL-Stil. Der reale Test
rendert einen selbst definierten synthetischen Titelstil. Autoren-/Metadatenextraktion
ist heuristisch; fehlende Verlag-/Band-/Seitenangaben sowie die grobe Book-/Article-
Zuordnung begrenzen fachliche Formatprüfungen. Abweichungen bleiben Kandidaten,
keine automatisch festgestellten Verstöße. Node und citeproc sind nicht Bestandteil
des standardmäßigen Python-Dockerimages; die Anbindung ist derzeit ein Host-Opt-in.

## DBLP-Release und kontrollierte Auswahl

DBLP veröffentlicht persistente monatliche Releases, etwa
[10.4230/dblp.xml.2026-11-01](https://doi.org/10.4230/dblp.xml.2026-11-01).
Die [Sammlung](https://drops.dagstuhl.de/entities/collection/10.4230/dblp.xml)
weist CC0 aus. Der Import erweitert den bestehenden Snapshot Store, nicht den
privaten Recherchepfad. Ein optionales externes Auswahlmanifest hat diese Form:

```json
{
  "release_doi": "10.4230/dblp.xml.2026-11-01",
  "subset_sha256": "<SHA-256 DES TATSAECHLICH GEPRUEFTEN XML-TEILBESTANDS>",
  "keys": ["conf/nips/VaswaniSPUJGKP17"],
  "reviewed_by": "<VERANTWORTLICHER REVIEWER>",
  "public_provenance_reviewed": false
}
```

Nach unabhängiger Prüfung der Herkunft und tatsächlichem Setzen der Freigabe:

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.research.snapshot_store C:\PublicStaging\subset.xml `
  --provider dblp --store C:\PublicLibrary --version dblp-reviewed-v1 `
  --reviewer '<Reviewer>' --provenance '<nachgeprüfte Herkunft>' --license-id CC0-1.0 `
  --public-provenance-reviewed --dblp-release-selection C:\PublicStaging\selection.json
```

Release-DOI und Auswahlhash bleiben in den einzelnen Datensätzen und im
Versionsmanifest erhalten. Eingangschecksumme, doppelte Schlüssel, ungültige
Datumsangaben oder fehlende angeforderte Einträge verhindern die Aktivierung.
Die Provenienzbehauptung zur Ableitung aus dem Release wird menschlich geprüft;
die Subset-Checksumme beweist diese Ableitung nicht selbstständig.

Weiterhin gelten 64 MB XML und 100.000 Eingangsdatensätze. Der Import verarbeitet
bereits begrenzte öffentliche Teilbestände; er lädt oder konvertiert keinen gesamten
DBLP-Dump und löst keine DTD-Entities auf. Es wurde kein aktueller realer Release
heruntergeladen oder aktiviert. Vertrauliche Literaturverzeichnisse dürfen keine
öffentlichen Download-/SPARQL-Abfragen auslösen.

## Zurückgestellte Ergänzungen

Der bestehende konservative `SequenceMatcher` bleibt für unscharfe Quellenkandidaten
aktiv. RapidFuzz kann nach einem repräsentativen Laufzeit-/Treffervergleich folgen;
eine neue Vergleichsmetrik wird nicht ohne diesen Nachweis zum Bestätigungskriterium.
Docling bleibt ein möglicher Zusatz für Tabellen und Layout. Es fehlen geprüfte
Modellartefakte, Laufzeitbudget und ein Referenzkorpus gegenüber GROBID/aktuellem Parser.
Diese beiden Werkzeuge sind in diesem Änderungsschritt nicht integriert.

Tatsächlich durchgeführte Prüfungen und offene Freigaben stehen im
[Ergebnisbericht](../evaluation/parallel_review_results.md).
