# Lokale wissenschaftliche Daten und Werkzeuge

Implementierungsabgleich 28.11.2026; datierte externe Recherche vom 27.11.2026. Bestehender AssessmentWorkflow, Citation Engine, Snapshot Store,
LocalResearchCache, Evidence Validator und Model Gateway bleiben die Integrationspunkte.
Keine zweite Providerhierarchie, kein zweiter Orchestrator und kein neuer
Datenbankdienst. [Anbieterprüfung](scientific_sources_2026-11-27.md) und
[Test-/Abnahmebericht](../evaluation/public_research_results.md) grenzen den Umfang ab.

## Bestandsaufnahme

| Bestehende Komponente | Befund und Erweiterung |
|---|---|
| Scientific Research / Research Gateway | PUBLIC-Gateway absichtlich gesperrt, kein produktiver Recherche-HTTP-Pfad; bleibt gesperrt |
| Provider Registry | lokale Crossref/OpenAlex/RW-Adapter; ergänzt um DBLP, Open Library, DataCite, Zenodo und rechtegeprüften RIS-/CSL-Export; weitere Anbieter nur Kandidaten |
| Citation Verification / Local Verification | lokale Zitat-/DOI-/Snapshotprüfungen vorhanden; ISBN, Providerkonflikte, partielle/unscharfe Metadaten ergänzt; alte ResearchEvidence-Schnittstelle bleibt kompatibel |
| Snapshot Store | Rohbytes/Hashprüfung für kleine Importe vorhanden; zusätzlich immutable SQLite/FTS5-Versionen, atomare Aktivierung und Rollback |
| GROBID | gepinnter optionaler Adapter, externe Konsolidierung aus; keine neue Parserfreigabe oder tatsächliche GROBID-Abnahme |
| DHBW Mosbach Knowledge Base | versions-/quellengebundene Regelkandidaten vorhanden; kein fachlich bestätigter CSL-Stil und keine neue Freigabe |
| Context Management | Feature-Hash/Hybridranking und Originaloffsets vorhanden; SQLite-FTS5-Vergleich über dieselben Chunks ergänzt |
| Adaptive Agent Planning | semantische APPLIED-Verfahren, bestehende Kriterien und Factory; unverändert, kein Agent erhält freie neue Werkzeuge |
| Model Gateway / Privacy Policy | lokale, klassifizierte, budgetierte Modellpfade; keine Embedding-API, kein externes Fallback aktiviert |
| Evaluation Lab | A–E-Ablationen vorhanden; separates lokales Retrievalmessmodul ergänzt, ohne erfundene Referenzlabels |

## Kontrollierter Import

Im PRIVATE-Runtime findet ausschließlich Offlinezugriff statt. Originale öffentliche
Quelldateien werden separat aufbewahrt; der versionierte Suchbestand speichert
normalisierte Metadaten, Quelldigests und einen eigenen Datenbankdigest. Er ersetzt
keine revisionssichere, signierte Archivierung der Originaldateien.

Beispiel für einen **vorher geprüften**, kleinen DBLP-XML-Teilbestand außerhalb des
Repositorys; keine Studentendatei als öffentliche Quelle umdeklarieren:

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.research.snapshot_store C:\ReviewedPublicData\dblp-subset.xml `
  --provider dblp --store C:\ReviewedPublicData\library `
  --version dblp-reviewed-v1 --license-id CC0-1.0 `
  --reviewer authorized-reviewer --provenance reviewed-public-subset `
  --public-provenance-reviewed --dblp-release-selection C:\ReviewedPublicData\selection.json
```

`--updated-at` nimmt ein bekanntes ISO-8601-Quelldatum mit Zeitzone entgegen.
Ohne einen unabhängig geprüften DBLP-Release-Selektor wird ein versionierter DBLP-Import
abgewiesen. `selection.json` bindet Release-DOI, exakten Teilbestand-SHA-256,
ausgewählte öffentliche DBLP-Schlüssel, Reviewer und Herkunftsprüfung.
[Schema und Beispiel](parallel_scientific_checks.md#dblp-release-und-kontrollierte-auswahl).
Ohne bekanntes Quelldatum bleibt Aktualität UNKNOWN. Importzeit wird nie als Beleg einer
aktuellen Datenquelle ausgegeben. Alter über 90 Tage wird als STALE ausgewiesen;
die Schwelle ist eine technische Diagnose, keine DHBW-Vorgabe.

Für vorhandenes Crossref/OpenAlex/RW-JSON/CSV sowie Open-Library-Books-API-, DataCite-
oder Zenodo-Records-JSON denselben Import mit entsprechendem `--provider` verwenden.
`--include-current` übernimmt den bestehenden geprüften Datenbestand in eine neue
Version; Quelldigests bleiben erhalten. Die Lizenzangabe muss den gesamten gewählten
Bestand korrekt beschreiben. Bestehende Legacy-Rohsnapshots bleiben lesbar.

Grenzen: 8 MB je JSON/CSV-Rohimport, 64 MB unkomprimiertes DBLP-XML,
100.000 normalisierte Einträge pro neuer Version, 96 MB Datenbanklimit,
256 MB Storebudget mit freier Reserve für den nächsten Import und höchstens acht
Versionen. Streaming begrenzt XML-Baum/Recordgröße und verwirft unvollständige Daten;
die Liste des Gesamtdumps wird nicht in den RAM geladen. Nicht freigegebene externe
Entities/DTD-Abhängigkeiten werden nicht nachgeladen. Vollständige DBLP-Dumps sind
damit ausdrücklich kein unterstützter Pilotumfang.
Das [offizielle XML-Verzeichnis](https://dblp.org/xml/) listete am Prüftag für
`dblp.xml.gz` rund **1,0 GB komprimiert**, Stand 25.11.2026. Entpacktes XML,
Suchindizes und parallele Versionen benötigen zusätzlichen, hier nicht vermessenen
Speicher. Ein Gesamtdownload überschreitet bereits komprimiert die Pilotlimits und
wurde nicht begonnen.

Aktivierung geschieht nach erfolgreichem Import über atomaren `CURRENT.json`-Wechsel.
Fehlerhafte Importdaten verändern die aktive Version nicht. Ein bereits geöffnetes
Cacheobjekt bleibt an die bisherige Version gebunden. Für einen bewusst geprüften
Rollback kann ein Operator die vorhandene Funktion aufrufen:

```python
from pathlib import Path
from app.research.sqlite_store import activate_version

activate_version(Path(r"C:\ReviewedPublicData\library"), "dblp-reviewed-v1")
```

Mit `PUBLIC_METADATA_DIR` und einem gezielten **read-only**-Mount wird der Bestand
dem vorhandenen Backend zur Verfügung gestellt. Neue Begutachtungen protokollieren
die verwendete Bibliotheksversion in Provenance; tatsächliche Metadatenprüfungen
tragen zusätzlich Provider-, Quellhash- und Snapshotversionsangaben. Kein automatischer
Hot-Swap unter laufenden Bewertungen. Nach einem bewusst gewählten Datenwechsel den
lokalen Dienst kontrolliert neu starten.

## Getrennter öffentlicher Sync

`infrastructure/scripts/sync_scientific.py` importiert keine Backend-, Dokument-,
Gutachten- oder Agentenmodule. Es akzeptiert genau einen festen öffentlichen
DBLP-Beispieldatensatz, keine freie URL, DOI oder Suchbegriffe. TLS, öffentliche
DNS-Adressen, IP-Pinning, keine Redirects/Proxyübernahme, mindestens drei Sekunden
zwischen Requests, persistiertes Retry-After, Größen-/Speicherlimits und ein vorab
geprüfter SHA-256 begrenzen den Abruf. Range/If-Range setzt nur identische
Repräsentationen mit starkem ETag fort. Fehler lassen keine aktivierte Datenbank
entstehen. Downloadzeit und gegebenenfalls Last-Modified werden getrennt erfasst.

`compose.scientific-sync.yaml` bildet eine eigene Umgebung ohne private Netze,
Dokumentmounts, Secrets oder Modellzugriff. Nur Downloaderdatei und öffentliches
Stagingvolume werden eingebunden; keine Images werden automatisch heruntergeladen.
Der bestehende Compose-CI-Validator prüft diese siebte Variante. Die Zielhost-
Netzisolation des öffentlichen Sync wurde nicht abgenommen; die späteren lokalen
App-Build-/Mock-E2E-Nachweise ersetzen diese separate Abnahme nicht.

Auf freigegebener Infrastruktur mit vorhandenem lokalem Backendimage:

```powershell
docker compose -f compose.scientific-sync.yaml run --rm public-sync `
  --dataset dblp-attention-example --output /public-staging `
  --sha256 '<independently-reviewed-64-character-sha256>' `
  --version reviewed-public-example-v1 --public-provenance-reviewed
```

Die Zeilen gehören zu einem Befehl; Platzhalter erst nach Herkunftsprüfung ersetzen.
Eine optionale Betriebssystem-Zeitsteuerung kann denselben fest freigegebenen
Abruf auslösen. Sie wurde nicht eingerichtet. Geänderte Bytes, Prüfsumme oder
Version erfordern erneute öffentliche Bestandsprüfung; keine Auswahl anhand einer
vertraulichen Arbeit. Die Übergabe an den Offlineimport bleibt ein separater
Operatorvorgang. Der reale Einzelprobeabruf am 27.11.2026 lieferte HTTP 202, deshalb
liegen weder ein bestätigter XML-Download noch ein importierter öffentlicher
Probe-Snapshot als Realnachweis vor.

## Bibliografische Prüfgrenzen

ISBN-10/-13 werden anhand beider Prüfsummen normalisiert, ISBN-10 wird kanonisch
ISBN-13. DOI verwendet die bestehende gemeinsame Normalisierung. SourceType legt
geeignete lokale Provider nahe: Paper/Konferenz über Crossref/DBLP/OpenAlex,
Bücher über Open Library, Daten/Software über DataCite/Zenodo und zukünftig
Software Heritage. Interne Quellen, Interviews und eigene Daten bleiben lokale
oder menschliche Prüfaufgaben. Fehlende lokale Treffer beweisen keine erfundene Quelle.

Existenz eines Identifikators im Snapshot, übereinstimmende Metadaten, Notice-Status
und fachliche Relevanz bleiben getrennt. SequenceMatcher ist der bereits vorhandene
lokale Ähnlichkeitsalgorithmus; RapidFuzz wurde mangels nachgewiesenen Vorteils nicht
zusätzlich installiert. Ähnliche Titel und unvollständige Autorennamen bleiben
Kandidaten. Fehlende Felder sind PARTIAL_METADATA, widersprüchliche Bestände
PROVIDER_CONFLICT. Auch exakte verglichene Metadaten bestätigen weder fachlichen
Inhalt noch die Relevanz eines Zitats. Aktuelle Onlineexistenz wird nicht behauptet.

## LanguageTool

Die [offizielle Anleitung](https://dev.languagetool.org/http-server.html) beschreibt
einen lokalen Java-HTTP-Server; lokale Basisregeln sind von Cloud-KI-Regeln getrennt.
Der [Quellcode](https://github.com/languagetool-org/languagetool) verwendet LGPL-2.1;
konkrete Distributionen/Regelressourcen sind vor Betrieb zusätzlich zu prüfen.
Keine Distribution wurde heruntergeladen oder freigegeben.

Der neue Adapter verwendet ausschließlich `http://127.0.0.1:8081/v2/check`, POST,
keine Redirects, keinen öffentlichen LanguageTool-Host und keine Cloudalternativen.
Standardmäßig deaktiviert. `ENABLE_LOCAL_LANGUAGE_TOOL=true` aktiviert nur den
technischen PUBLIC-Testpfad; private Inhalte bleiben gesperrt. Außerdem muss ein
vorhandenes formales Kriterium ausdrücklich `local_checks: [language]` enthalten.
Die vorhandenen Mosbach-/Beispielprofile wurden dafür nicht verändert: Aufbau ist
nicht automatisch ein Grammatikbewertungskriterium.

Deutsch sowie US-/UK-Englisch sind im Adapter möglich; der integrierte Workflow
verwendet derzeit Deutsch als Standard. Maximal 20 Absätze/12.000 Zeichen und
15 Sekunden je Kriterienaufruf. Code, Formeln, Literaturangaben und erkannte
Zitate werden konservativ übersprungen, Terminologiewörter können ausgenommen
werden. UTF-16-Offsets werden auf Originalseitenpositionen abgebildet.
Alle Treffer sind menschlich zu prüfende Vorschläge, keine automatischen
Beanstandungen oder Korrekturen. Das Original bleibt unverändert. Vollständige
Erkennung von Fachbegriffen/Zitaten sowie reale Sprachqualität bleiben offen.

## DHBW-Zitierformate und CSL

[citeproc-py](https://github.com/citeproc-py/citeproc-py) verarbeitet CSL 1.0.2,
unterstützt Python ab 3.11 und benötigt lxml. Die eigene Dokumentation nennt
unvollständige CSL-Konformität, unter anderem bei Disambiguierung. Die
[Lizenz](https://github.com/citeproc-py/citeproc-py/blob/master/LICENSE) ist eine
BSD-artige Zwei-Bedingungen-Lizenz. Eine Bibliografie zu rendern beweist außerdem
nicht, dass unzuverlässig extrahierte Originalzeichen korrekt verglichen wurden.

Die Knowledge Base enthält quellengebundene Zitationskonsistenz-Regelkandidaten,
aber keinen bestätigten CSL-Stil samt akzeptierten Varianten für Mosbach DS/KI.
Deshalb kein erfundener DHBW-Stil, keine automatische Stilbeanstandung und keine
neue citeproc-Abhängigkeit. Vorhandene Verweis-/Literaturlistenprüfungen bleiben
aktiv. Ein fachlich bestätigter Originalstil und konkrete Referenzbeispiele sind
Voraussetzung eines späteren Render-/Vergleichsadapters.

## Lokale Embeddings und Retrievalmessung

Die [BGE-M3-Modellkarte](https://huggingface.co/BAAI/bge-m3) beschreibt ein
mehrsprachiges BAAI-Modell, MIT-Lizenz, 1024 Dimensionen und 8192 Token Kontext.
Die [offizielle Metadatenantwort](https://huggingface.co/api/models/BAAI/bge-m3?blobs=true)
meldete Revision `5617a9f61b028005a4858fdac845db406aefb181` und für
`pytorch_model.bin` 2.271.145.830 Bytes mit LFS-SHA-256
`b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38`.
Das sind **Publisher-Metadaten**, keine lokal nachgemessenen Dateidaten oder
Artefaktfreigaben. Ein ONNX-Artefakt ist ebenfalls gelistet. Keine Gewichte,
Tokenizer oder ausführbaren Modellpakete wurden geladen. Tatsächlicher RAM/VRAM,
Latenz und deutsches Retrieval müssen auf dem Zielhost gemessen werden; die
Gewichtsdateigröße ist keine Hardwareanforderung.

Das vorhandene Feature-Hash-Verfahren bleibt der Anwendungsstandard. Der neue
`LocalContextIndex.search_fulltext` verwendet SQLite FTS5/BM25 im flüchtigen RAM
über dieselben Chunks und Originaloffsets. Das ist eine Vergleichsbaseline, kein
umgebauter Produktions-Retriever. Die [FTS5-Dokumentation](https://sqlite.org/fts5.html)
begründet die ressourcenschonende Wahl ohne zusätzlichen Datenbankserver.

`app.evaluation.retrieval` vergleicht A (bestehende Suche) und B (FTS5). C/D/E
(semantisch/hybrid/lokal rerankt) sind explizit BLOCKED_NO_APPROVED_EMBEDDING_OR_RERANKER.
Originalpassagen, Query und Dokumenthash sind pro Vergleich identisch. Precision@k,
Recall@k, MRR@k und nDCG@k werden nur aus expliziten menschlichen Qrels berechnet.
Fehlende Labels ergeben `null`. Kein automatisch generierter fachlicher Goldstandard.

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.evaluation.retrieval --output reports/retrieval-public-demo.json
```

Die Demo verwendet ausschließlich eingebaute synthetische Seiten. Gemessen werden
Suchdauer und Python-Allokationspeak; nativer SQLite-RAM und Modellressourcen sind
nicht erfasst. Bei B ist die flüchtige FTS-Tabellenerstellung enthalten, bei A werden
vorberechnete Chunks durchsucht: kein fairer allgemeiner Geschwindigkeitsbenchmark.
[ranx](https://github.com/AmenRa/ranx) bietet diese Rankingmetriken und Vergleiche unter
MIT mit NumPy/Numba-basierter Beschleunigung. Für die kleinen Pilottests genügt eine
deterministische Implementierung ohne diese zusätzlichen Abhängigkeiten. Vor einer
Fachstudie Metrikkonventionen mit ranx abgleichen und Referenzpassagen expertisch
bestätigen. Ein semantischer Vorteil ist bisher nicht gemessen.

## Bewusst zurückgestellte Werkzeuge

[SymPy](https://docs.sympy.org/latest/modules/parsing.html),
[SciPy](https://docs.scipy.org/doc/scipy/reference/stats.html),
[NumPy](https://numpy.org/doc/stable/) und [Pandera](https://pandera.readthedocs.io/en/stable/)
sind geeignete Kandidaten für symbolische, statistische, numerische und tabellarische
Prüfungen. Kein allgemeiner Code-/Expression-Interpreter wird freigeschaltet;
insbesondere SymPy-Stringparser dürfen nicht mit untrusted LLM-Ausdrücken verwendet
werden. Es fehlen freigegebene Rohdaten-/Messwerte und fachlich bestätigte konkrete
Prüfaufträge. Daher derzeit keine neuen statistischen Bibliotheken oder dynamischen
Agententools; nur das bestehende `document.read` bleibt zulässig.

Software-/Datenversionen können über die neuen lokalen DataCite-/Zenodo-Metadaten
nachgeschlagen werden. Das ist noch kein systematischer Reproducibility Check.
Software-Heritage-Rohimport, Versionsinventar von Bibliotheken/Modellen,
Experimentkonfiguration und reale Reproduktion sind P2-Backlog. Öffentliche
Unternehmensrepository-Suche oder Archivierung ist nicht implementiert und bleibt
für vertrauliche Referenzen untersagt.
