# Wissenschaftliche Gutachterwerkzeuge: Betrieb, Quellen und Grenzen

Stand: 28.11.2026, Europe/Berlin. Alle Funktionen erweitern den vorhandenen
Assessment-/Evaluationpfad. Die ursprüngliche Projekt-PowerPoint und primäres
Professorenfeedback wurden im Repository nicht gefunden; maßgeblich bleiben die
vorhandene Traceability und die übergebene Aufgabenbeschreibung, keine behauptete
offizielle Hochschulabnahme. Beispielkriterien sind weiterhin keine amtlichen Regeln.

## Gutachter-Arbeitsbereich

Nach unabhängiger menschlicher Erstbewertung und KI-Zweitbewertung werden beide
Ergebnisse über die bestehende Freigabe geöffnet. Der Vergleich bietet jetzt einen
Kriterienfilter und den Abschnitt **Gutachter-Arbeitsbereich** mit Bearbeitungsstand,
Dublettenkandidaten, Dokumentationscheckliste, Zahlenhinweisen, extrahierten Tabellen-
und Abbildungstexten, fachlichen Rückfragen und eigenen Anmerkungen.

Es wird keine künstliche Zahl positiver oder negativer Befunde verlangt. Stärken
und Schwächen benötigen gleichermaßen Originalevidenz. `METHOD_CONCERN` und
`IMPROVEMENT_SUGGESTION` ergänzen die bestehenden Befundarten. Ein Texttreffer
bestätigt keine wissenschaftliche Interpretation; Verbesserungspotenzial wird
nicht als nachgewiesener Fehler ausgegeben.

Die Rückfragen entstehen lokal aus offenem Kriterium, unzureichender Evidenz,
methodischer Unsicherheit, Konflikt oder einem vergleichbaren Zahlenpaar. Sie
enthalten Kriterien- und Befundbezug beziehungsweise Originalpassagen. Es gibt
keine automatische mündliche Prüfung und keinen Modellaufruf mit Gutachternotizen.
Höchstens 40 Fragen werden angezeigt; dadurch ist keine Vollständigkeit zugesichert.

Eigene Notizen und Antworten werden versioniert gespeichert. Nur ausdrücklich mit
**Diese Anmerkung für den Gutachtenentwurf freigeben** ausgewählte Inhalte erscheinen
im Entwurf. Überarbeiten einer Notiz erhält die Historie; nur ihre letzte Version
gilt für die aktuelle Anzeige und Übernahme. Die ursprüngliche Erstbewertung bleibt
unverändert. Nach Finalisierung sind Änderungen gesperrt.

Die optional gestartete Gutachtersitzung erfasst serverseitig monotone verstrichene
Zeit nach Ergebnisfreigabe. Stoppen oder Finalisierung schließt sie. Die Messung
umfasst gegebenenfalls Pausen; sie misst weder Aufmerksamkeit noch die unabhängige
Erstbewertung oder Zeitersparnis gegenüber einem Vergleichsverfahren.

Alle Schreibaktionen nutzen vorhandene Assessment-ACLs, Freigabe, Schreibsperre
und Klassifikationsanhebung auf RESTRICTED. Rohnotizen, Antworten und Sitzungsdaten
werden nicht in öffentliche Forschung, Modellkontexte, Statusprojektionen oder
automatisches Training übernommen. Speicherung bleibt flüchtiger Server-RAM mit
vorhandener Retention und Löschung, kein neues Archiv oder Wiederanlaufversprechen.

## Dokumentierte Reproduzierbarkeit

Die Checkliste übernimmt nur APPLIED-Methodenkandidaten aus dem vorhandenen validierten
semantischen Plan mit erneut abgeglichenen Originalchunks oder eine ausdrückliche
menschliche Methodenbestätigung mit eindeutigem Originalzitat. MENTIONED/UNCLEAR und
unbekannte Familien lösen keine ML-Anforderungsliste aus. Ohne ausreichenden Kontext
lautet das Ergebnis `NOT_ASSESSABLE_METHOD_CONTEXT`.

Für ML/DL werden Datenbeschreibung, Herkunft, Vorverarbeitung, Architektur,
Softwareversionen, Hyperparameter, Seeds, Train-/Testtrennung, Metriken, Baselines,
Hardware, Bedingungen und Limitationen als optionale wissenschaftliche Prüfaspekte
geführt. Andere Methoden verwenden kleinere passende Teilmengen; Interviews
erhalten beispielsweise keine Seed-/GPU-Liste. Die Anwendbarkeit bleibt individuell
zu prüfen, etwa bei deterministischen Verfahren.

Nachprüfung desselben Tages: Negations-/Unsicherheitsmarker im nahen Textkontext
und zitierte Angaben erhalten `DOCUMENTATION_UNCERTAINTY_REQUIRES_HUMAN` samt
`review_reasons`. Das ist eine konservative Textheuristik, keine verifizierte
Negationsanalyse. Solche Aspekte erzeugen wie nicht lokalisierte Angaben eine
beleggebundene Rückfrage. Auch bei langen Methodenblöcken enthält der maximal
800 Zeichen lange Originalkontext jetzt die tatsächliche Fundstelle.

Die Suche bleibt auf die eindeutig belegten Methodenblöcke beschränkt. Ein gefundener
Begriff ist eine Textnennung, kein Vollständigkeitsnachweis; insbesondere kann ein
Satz gerade das Fehlen der Information beschreiben. Nicht gefundene Angaben sind
`NOT_LOCATED_IN_METHOD_CONTEXT`, kein bewiesenes Fehlen im ganzen Dokument.
Jeder Kandidat zeigt Quelle und Kontext. `experiment_reproduced` bleibt immer false:
Es werden weder Experimentcode noch Trainingsläufe oder untrusted Formeln ausgeführt.

## Zahlen, Tabellen und wissenschaftlicher Kontext

Der zusätzliche numerische Check läuft als sechste begrenzte Teilprüfung parallel
zu den bisherigen Diensten. Er arbeitet ausschließlich mit extrahiertem Originaltext,
Decimal-Arithmetik und bekannten Metrik-/Einheitenmustern. Prozentverhältnisse wie
`80 von 100 entsprechen 90 %` können als rechnerische Abweichungskandidaten markiert
werden. Rundung wird konservativ mit einer halben letzten angezeigten Dezimalstelle
berücksichtigt; eine abweichende Rundungs-/Trunkierungsregel bleibt menschlich zu prüfen.

Für Vergleiche von Metrikwerten müssen vier ausdrücklich abgegrenzte Kontextangaben
übereinstimmen, beispielsweise:

```text
Experiment E1; Modell M1; Datensatz D1; Split test: Accuracy = 90,0 %.
```

Zusätzlich erkannte Runs, Seeds, Folds und Macro-/Micro-/Weighted-Varianten dürfen
nicht abweichen. Mehrdeutige oder unvollständige Kontexte werden nicht verglichen.
Bekannte Einheiten werden normalisiert; Rundungsintervalle werden berücksichtigt.
Unsicherheitsangaben wie ±/Konfidenzintervalle verhindern die Ausgabe eines festen
Zahlenkonflikts. Diese Regeln decken keine beliebige wissenschaftliche Notation ab;
insbesondere sind nicht dokumentierte Versuchsbedingungen weiterhin unbekannt.

Zahlenpräfixe aus nicht unterstützten Exponenten, Intervallen, Quotienten oder
angehängten unbekannten Zeichen werden nicht als feste Metrikwerte verglichen.
`unparsed_candidates` bewahrt dafür Originalstelle und Prüfhinweis; die Oberfläche
zeigt diese Unsicherheit. Erkannte und nicht auswertbare Kandidaten teilen sich
das Limit von 200. Bekannte direkt angehängte Einheiten bleiben unterstützt.
Negierte oder hypothetische Angaben verlangen Interpretation statt eines festen
Konfliktbefunds. Für sichere rechnerische Abweichungskandidaten erzeugt die
vorhandene Rückfragenfunktion `NUMERICAL_ARITHMETIC` mit Originalbeleg und
berechnetem Prozentwert; ohne passendes Inhaltskriterium wird keine Zuordnung erfunden.

Tabellenwerte in einer passenden Textdarstellung können als unbestätigte Kandidaten
erfasst werden. Sie werden bis zur fachlichen Prüfung nicht wie verlässlich gelesene
Fließtextwerte behandelt. Zitate, Code, Formeln und Bibliografie werden nicht als eigene
numerische Ergebnisse interpretiert. Fehlerwarnungen der PDF-Extraktion bleiben wirksam.
Tabellen-/Abbildungsreferenzen ohne auffindbare Textbeschriftung bedeuten
`NOT_LOCATED_IN_EXTRACTED_TEXT`, nicht „Abbildung fehlt im Original“.

Maxima: 2 MB Dokumenttext, 4096 Blöcke, 200 numerische Claims, 200 Vergleiche,
100 Verhältnisrechnungen und 100 ausgegebene komplexe Objekte. Der Workflow
verwendet weiterhin keine ungeprüften Ergebnisse für eine automatische Benotung.

## Lokale Extraktionswerkzeuge

| Werkzeug | Geprüfte Primärquelle / Einordnung | Konkrete Entscheidung |
|---|---|---|
| GROBID | [TEI-Ausgabe](https://grobid.readthedocs.io/en/latest/TEI-encoding-of-results/) strukturiert wissenschaftliche Dokumente; [PDF-Koordinaten](https://grobid.readthedocs.io/en/latest/Coordinates-in-PDF/) dienen der Quellenzuordnung | Vorhandenen lokalen Adapter erweitert: Tabellenzellen, Abbildungs-/Formeltext, IDs und unbestätigte Koordinaten. Keine neue externe Verarbeitung oder Consolidation. |
| PaddleOCR PP-StructureV3 | [Offizielle Pipeline-Dokumentation](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PP-StructureV3.html) beschreibt Layout-, OCR-, Tabellen-, Diagramm- und Formelkomponenten sowie lokale Modellpfade | Optionaler Kandidat, derzeit nicht installiert oder aktiviert. Es fehlen geprüfte Gewichte, reproduzierbare Laufzeit, Ressourcen- und Offlineabnahme gegenüber dem bestehenden Parser. |
| PaddleOCR-Code-Lizenz | [Offizielles Repository](https://github.com/PaddlePaddle/PaddleOCR) deklariert Apache-2.0 | Die Code-Lizenz ersetzt keine Prüfung einzelner Modellartefakte und ihrer Abhängigkeiten. Kein automatischer Modellbezug. |

Die Oberfläche zeigt derzeit extrahierte Objekttexte und Originalreferenzen. Echte
Bild-/Diagrammpixel, OCR-Zahlen und Formelinterpretationen sind nicht verifiziert;
ein vollständiger visueller Evidence Explorer bleibt offen. GROBID-Objektmapping
wurde mit synthetischem TEI getestet, nicht mit einem echten Parserlauf.

Die genannten GROBID- und PP-StructureV3-Primärseiten wurden in dieser Nachprüfung
erneut gelesen. Die Koordinatenparameter und lokalen Modellpfade sind dokumentiert;
das ersetzt weder eine aktivierte OCR-Pipeline noch geprüfte Modellgewichte.

## Offizielle Bibliotheksangebote der DHBW Mosbach

Die [Literatursuche](https://www.mosbach.dhbw.de/service-einrichtungen/bibliothek/literatursuche/)
verweist auf den aDIS-Katalog beider Campusbibliotheken, BOSS, EZB und weitere
Verlagsangebote. Die [Datenbankseite](https://www.mosbach.dhbw.de/service-einrichtungen/bibliothek/datenbanken/)
nennt fachlich relevante Zugänge, darunter IEEE und Inspec, sowie Campus-/VPN-/
Shibboleth-Bedingungen. Ihre rechtlichen Hinweise begrenzen Downloads auf einzelne
Suchergebnisse und untersagen den Gesamtdownload. Aus diesen Hinweisen wurde keine
ausdrückliche ThesisHounds-TDM-/Automationsfreigabe abgeleitet.

Beide offiziellen Hochschulseiten wurden in der Nachprüfung erneut gelesen.
Katalog/BOSS, DBIS und die dokumentierten Zugangs-/Downloadgrenzen sind weiter
belegt. Die Seiten liefern keine ausdrückliche projektspezifische API- oder
TDM-Freigabe; lizenzierte Bestände bleiben daher beim kontrollierten lokalen Import.

Der öffentliche Katalog war lesbar; BOSS lieferte eine Schutzseite, die nicht umgangen
wurde. Eine für uns freigegebene Mosbach-spezifische API konnte nicht bestätigt werden.
Die [BSZ-BOSS-Roadmap](https://wiki.bsz-bw.de/spaces/BOSS/pages/4882890/Roadmap)
dokumentiert historisch Citavi-/RIS-Export. Das bestätigt weder jede aktuelle
Mosbacher Exportoption noch Rechte an allen dort eingebundenen Datenquellen.
CSL-JSON ist ein zusätzlich unterstütztes lokales Austauschformat, kein behauptetes
Exportmerkmal der Mosbacher Instanz.

SRU/unAPI wurden als mögliche Verbund-Metadatenwege untersucht. Die konsultierten
K10plus-Wikiseiten waren nicht abrufbar; der Kooperationsauftritt antwortete mit 429.
Daher kein neuer Onlineadapter, keine erfundenen Endpunkte, Limits oder Nutzungsrechte.
Die [SLUB-Quellendokumentation](https://data.slub-dresden.de/doc/data_sources/) nennt
CC0 für ihren K10plus-Teilbestand; daraus folgt keine pauschale Freigabe lizenzierter
Mosbacher Volltexte oder aggregierter Fremddaten. Allgemeine
[Open-Access-Informationen](https://www.mosbach.dhbw.de/service-einrichtungen/bibliothek/wissenschaftliches-schreiben/)
ersetzen ebenfalls keine Prüfung des konkreten Datensatzes.

Implementiert ist ein lokaler, metadatenbeschränkter RIS-/CSL-JSON-Import im bestehenden
Snapshot Store (`library_export`). Er verlangt getrennte Bestätigungen öffentlicher
Herkunft und geprüfter Export-/Nutzungsrechte. Die Flags dokumentieren menschliche
Prüfung; sie sind kein Nachweis einer Bibliotheksvereinbarung. Keine Zugangsdaten,
Logins, Proxyumgehung, Volltexte, Abstracts oder Dateianhänge werden importiert;
Export-URLs werden nicht aufgerufen. Unbekannte Metadatenrechte bleiben UNKNOWN.

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.research.snapshot_store C:\PublicStaging\reviewed.ris `
  --provider library_export --store C:\PublicLibrary --version library-reviewed-v1 `
  --reviewer '<tatsächlicher Reviewer>' --provenance '<geprüfte Quelle und Rechtebeleg>' `
  --license-id '<tatsächlich geprüfte Metadatenrechte>' `
  --public-provenance-reviewed --export-rights-reviewed
```

Bis 2 MB, 1000 Datensätze, 4000 Zeichen pro RIS-Feld; nur der dokumentierte sichere
Feldumfang wird akzeptiert. Titel/Autoren, Jahr, DOI/ISBN, Typ, ID und Venue gelangen
in die bestehende lokale Verifikation. Kein vollständiger RIS-/CSL-/BibTeX-/MARC-
Konverter und keine pauschale Quellenexistenzbestätigung werden behauptet.

Offene Fragen an die Bibliothek, **nicht automatisch versendet**:

- Welche Metadatenbestände und Exportformate sind für diese lokale Anwendung nutzbar?
- Welche dokumentierte API, Rate-/Mengenlimits und Authentifizierung wären ausdrücklich erlaubt?
- Welche Bestände dürfen für TDM und lokale KI-Auswertung verwendet werden, mit welchen Auflagen?
- Welche Speicherung, Weitergabe, Löschfristen und Lizenzangaben gelten je Anbieter?
- Ist ein institutionell freigegebener DHBW-Mosbach-CSL-Stil verfügbar?

## Performance-Lab und wissenschaftliche Evaluation

Der vorhandene Ollama-Adapter übernimmt die in der
[offiziellen Chat-API](https://docs.ollama.com/api/chat) beschriebenen Tokenzahlen und
Nanosekunden für Laden, Promptverarbeitung, Generierung und Gesamtverarbeitung.
Tokens/s werden aus Ausgabetokens und Generierungsdauer berechnet. Optionales NDJSON-
Streaming nutzt denselben Gateway mit denselben Ziel-, Digest-, Budget- und Egresschecks.
Gemessen wird die Zeit ab Chatrequest bis zum ersten nicht leeren Antwortfragment.
Da ein Fragment mehrere Tokens enthalten kann und Reasoning getrennt ankommen kann,
ist dies ausdrücklich ein Proxy; exaktes `ttft_seconds` bleibt null.

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.evaluation.model_benchmark --models qwen mistral `
  --provider mock --parallelism 2 --output reports/reviewer-tools-model-mock.json
```

Reale Messungen benötigen den vorhandenen freigegebenen `local_pilot`; dann kann
`--provider ollama --stream-metrics` gewählt werden. `--context-length` senkt das
gemeinsame Kontextbudget innerhalb der registrierten Grenzen. Quantisierungen werden
über unterschiedliche geprüfte Modellartefakte/Digests verglichen, nicht automatisch
heruntergeladen. Gleiche Cases und Prompthashes bleiben dokumentiert.

Jobparallelität erhöht nie den bestehenden Gateway-Modellslot. Das Lab protokolliert
beobachtete Dispatchparallelität, Aufrufversuche, Fehlerrate, Kontext und bekannte
Quantisierung sowie Backend-/Host-RAM-Snapshots. Ollama-VRAM/Modellgrößen nach dem
Aufruf sind Snapshots, keine physischen RAM- oder Peakmessungen; fehlende Werte sind
null. Die Capability-Matrix erhält Infrastrukturwerte. Das bestehende CapabilityRecord
akzeptiert nach menschlichem Review zusätzliche nichtnegative endliche Infrastruktur-
Messwerte; Konfiguration und Routing werden nicht automatisch verändert.

Die Matrix aggregiert zusätzlich gemeldete Lade-, Provider-, Generierungs- und
Promptlaufzeiten, den First-Content-Proxy sowie vorhandene RAM-/VRAM-Snapshots.
Jeder Metrik stehen ihre tatsächliche Stichprobenanzahl und die Herkunft
`MOCK`/`LOCAL_PROVIDER` gegenüber. Fehlende Messwerte werden nicht als null Sekunden
oder null Bytes gemittelt: ihr Ergebnis ist JSON `null`, die Stichprobenanzahl 0.
`mean_ttft_seconds` bleibt ausdrücklich `null`; es gibt keine Messung exakter
Tokengrenzen oder physischer Modell-RAM-/GPU-Peaks.

Das bestehende Evaluation Lab ergänzt mechanische Vorher-/Gruppenzahlen sowie
Vorhersage-IDs für numerische Hinweise, Reproduzierbarkeitsfragen, Dublettengruppen
und positive/negative Evidenz. Fachliche Qualitätswerte erfordern explizite, passende
`HumanReferenceSet.review_tool_adjudications`. Ohne vollständige Labels je Kategorie
bleibt der jeweilige Wert null. Gruppenreduktion ist kein Qualitätsgewinn; Recall,
repräsentative Fachgüte, Gutachterakzeptanz und tatsächliche Zeitersparnis sind ohne
geeignete Referenzstudie nicht belegt.

Tatsächliche Tests, offene Hardware-/Katalogfreigaben und Restrisiken:
[Ergebnisbericht](../evaluation/reviewer_productivity_results.md).
