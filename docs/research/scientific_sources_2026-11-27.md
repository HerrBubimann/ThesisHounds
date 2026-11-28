# Wissenschaftliche Datenquellen Zugang und Auswahl

Offizielle Dokumentation am **27.11.2026** geprüft. Die Angaben beschreiben
Anbieterangebote, keine erteilte Betriebsfreigabe. Im privaten Assessment bleiben
alle Provider `LOCAL_IMPORT_ONLY`, ohne API-Key oder Onlinefallback, Kostenlimit
0 USD. Öffentliche Anfragen dürfen keine aus Arbeiten gewonnenen DOI-, ISBN-,
URL- oder Suchbegriffe enthalten. Lizenzangaben für Metadaten gelten nicht
automatisch für Abstracts, Volltexte, Daten oder Software.

## Crossref

Paper, Konferenzbeiträge, Bücher und weitere DOI-Typen; DOI, Titel, Autoren, Jahr,
Typ, Referenzen und Updates. Öffentliche REST-Abfragen ohne Konto; Polite-Zugang
mit Kontaktadresse. `https://api.crossref.org/works/{doi}` bzw. `/works`.
Public: DOI 5/s, Listen 1/s; Polite 10/s bzw. 3/s; Header und 429 beachten.
Metadata Plus ist kostenpflichtig und ausgeschlossen. Jährliche öffentliche
JSON-Dumps sind eine Bulkoption. Faktenmetadaten weitgehend frei, Abstractrechte
separat. Bestehender lokaler JSON-Adapter bleibt Grundlage für alle DHBW-Fachgebiete.
Risiko: DOI-Abfragen könnten vertrauliche Literaturauswahl verraten.
[REST](https://www.crossref.org/documentation/retrieve-metadata/rest-api/),
[Limits](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/),
[Lizenz](https://www.crossref.org/documentation/retrieve-metadata/).

## OpenAlex

Disziplinübergreifende Werke, Autoren, Quellen und Einrichtungen; DOI, Titel,
Autorschaften, Jahre, Beziehungen und OA-Informationen. `https://api.openalex.org/works`.
Basistests ohne Key; kostenloser verifizierter Key erhöht das Tagesbudget auf
1 USD und ist für Cursor-Paging erforderlich. Dokumentiert sind 10 Requests/s
ohne Key und 30/s mit freiem Key, mit strengeren Speziallimits; ältere Angaben
100/s sind überholt. Bezahlte Konten/Prepaid werden nicht angebunden. Daten CC0,
Snapshots sind für lokale Verarbeitung vorgesehen; Zugangsmodell vor Massennutzung
erneut prüfen. Der bestehende lokale Import genügt zunächst. Hohe Fachrelevanz,
aber Suchbegriffe, DOI und Kontaktadresse sind Offenlegungsrisiken.
[API](https://help.openalex.org/api/),
[Zugang und Limits](https://help.openalex.org/api/authentication/),
[Preise](https://help.openalex.org/access/pricing/).

## DBLP

Informatik, Data Science und KI: Paper, Konferenzen, Zeitschriften, Bücher und
Dissertationen; Schlüssel, Titel, Autoren, Jahr, Venue und vorhandene DOI.
Öffentliche Exporte `/rec/{key}.xml`, Such-API `/search/publ/api` und XML-Dump
unter `https://dblp.org/xml/`; kein API-Konto erforderlich. Offizielle Empfehlung:
mindestens ein bis zwei Sekunden zwischen Requests, 429/Retry-After respektieren.
Metadaten CC0-1.0. Vollständiges XML/gzip plus DTD ist verfügbar; der neue Import
begrenzt bewusst kleine XML-Teilbestände. Originaldumps mit benannten DTD-Entities
brauchen eine separat geprüfte Offlinekonvertierung; externe DTDs werden nie geladen.
Höchste fachliche Priorität. Exportabfragen können Literaturinteressen offenlegen.
[Download](https://dblp.org/faq/How+can+I+download+the+whole+dblp+dataset.html),
[XML](https://dblp.org/faq/How+to+parse+dblp+xml.html),
[Lizenz](https://dblp.org/db/about/copyright.html),
[Raten](https://dblp.org/faq/1474706.html).

## OpenCitations API

Zitationsbeziehungen und bibliografische Metadaten, DOI/OMID/OCI und Provenienz.
`https://api.opencitations.net/index/v2/` und `/meta/v1/`; etwa
`/index/v2/citation-count/doi:{doi}` und `/meta/v1/metadata/{ids}`.
Kostenlos, freier Token empfohlen; 180 Requests/Minute/IP. Daten CC0; Software-
und Dokumentationslizenzen sind davon getrennt. Bulkbestände siehe nächsten Abschnitt.
Registerkandidat, kein neuer HTTP- oder Rohformatadapter. Für DHBW nützlich für
Beziehungsnachweise, nicht für Wahrheits- oder Qualitätsurteile. Risiko: Identifikatoren
und Zitationsinteressen werden beim Remoteabruf offengelegt.
[Index](https://api.opencitations.net/index/v2/),
[Meta](https://api.opencitations.net/meta/v1/),
[Lizenz](https://opencitations.net/).

## OpenCitations Data

Dieselbe Datenfamilie als CSV/RDF/Datenbankdumps mit Snapshotversionen und Provenienz;
öffentliche Downloads über Zenodo, Figshare oder Internet Archive, keine eigene
kostenpflichtige Queryintegration. Die Metadatenseite nennt beispielsweise 8,4 GB
komprimiertes CSV und 56 GB entpackt für Juni 2026. Daten CC0; die Hostingplattform
hat eigene Abruflimits, kein gemeinsames garantiertes Ratenlimit. Solche Vollbestände
überschreiten den hier gewählten Pilotumfang. Kein Download implementiert oder
durchgeführt. Offline fachlich interessant, derzeit kein belegter Vorteil gegenüber
kleinen DOI-Teilmengen. Download-/Queryauswahl muss unabhängig von Arbeiten erfolgen.
[Offizielle Downloads](https://download.opencitations.net/).

## Semantic Scholar

Paper, Autoren, Referenzen und Zitationsgraph; Academic Graph unter
`https://api.semanticscholar.org/graph/v1/`, z. B. `/paper/{paper_id}`;
Dataset-Releases unter `/datasets/v1/release`. Teile öffentlich ohne Key,
einige Endpunkte nur mit Key. Offizielle Produktseite nennt 1000/s als gemeinsam
genutzten anonymen Pool, **kein individuelles Kontingent**; initialer Key 1/s.
Lizenz hat Nutzungs-/Attributionsbedingungen und ist nicht pauschal CC0.
Bulk und Diffs existieren; kein neuer Adapter. Relevant für Literaturbeziehungen,
aber Lizenz und individuelle Nutzung vor Freigabe klären. Risiko: Suchinhalte,
Schlüssel und Identifikatoren. Hauptseite 403, offizielle Produktspiegel/Dataset-
und Lizenzdokumentation erreichbar.
[Produkt](https://webflow.semanticscholar.org/product/api),
[Datasets](https://api.semanticscholar.org/api-docs/datasets),
[Lizenz](https://api.semanticscholar.org/license/).

## DataCite

Datensätze, Software und andere Forschungsoutputs; DOI, Titel, Creator, Jahr,
Typ, Version und Beziehungen. `https://api.datacite.org/dois/{doi}` bzw. `/dois`.
Public ohne Authentifizierung, nur Findable-DOIs; kostenlose Leseabfragen sind
von kostenpflichtigen DOI-Diensten zu unterscheiden. Limits pro fünf Minuten/IP:
500 unidentifiziert, 1000 identifiziert, 3000 authentifiziert. Metadaten CC0;
jahresweise Public Data Files und OAI-PMH für Bulk. Neuer begrenzter JSON-Import,
keine Online- oder Registrierungsfunktion. Hohe Relevanz für DS/KI-Datensätze.
Risiko: DOI-Abfragen könnten vertrauliche Datensatzwahl offenlegen; verknüpfte
Daten haben eigene Rechte.
[API](https://support.datacite.org/docs/rest-api),
[Limits](https://support.datacite.org/docs/rate-limit),
[Bulk/Lizenz](https://support.datacite.org/docs/datacite-public-data-file).

## Unpaywall

OA-Status, bibliografische Metadaten und zugängliche Versionen zu DOI über
`https://api.unpaywall.org/v2/{doi}`. Kostenlos mit echtem E-Mail-Parameter,
100.000 Calls/Tag. **`/v2/search` wurde am 18.09.2026 eingestellt und liefert 410.**
Eigenständige halbjährliche Snapshots werden nicht mehr erstellt; die offizielle
Seite verweist auf OpenAlex. Ein angebotenes Data Feed ist nicht kostenlos
vorauszusetzen und bleibt ausgeschlossen. Die geprüfte API-Seite erteilt keine
pauschale Volltextlizenz; Feld-/Bestandsrechte vor Import dokumentieren. Kein
Adapter wegen Überschneidung mit OpenAlex. Risiko: DOI und E-Mail sowie externe
PDF-Links; kein automatischer PDF-Abruf.
[API](https://data.unpaywall.org/products/api),
[Snapshotänderung](https://unpaywall.org/products/snapshot).

## Retraction Watch

Rücknahmen, Korrekturen und Expressions of Concern; Original-/Notice-DOI,
Titel, Datum und Status. Kostenloser öffentlicher CSV-/Git-Bestand,
werktägliche Updates, CC0 laut Crossref. Kein eigenes garantiertes CSV-Ratenlimit;
wenige kontrollierte Abrufe, keine Crawlserie. Crossref-REST unterliegt dessen
Limits. Bestehender lokaler CSV-Adapter bleibt Statusquelle. Fehlende Notices
beweisen keine Unbedenklichkeit; Korrekturen sind weniger vollständig als Rücknahmen.
Fachübergreifend relevant. Personenbezogene Zuschreibungen und veraltete Notices
sind fachlich sensibel. Kein neuer automatischer Onlinesync; Rechte/Herkunft
bleiben im Snapshot festzuhalten.
[Datensatzbeschreibung](https://gitlab.com/crossref/retraction-watch-data/-/raw/main/README.md),
[Zugang](https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/),
[CC0](https://www.crossref.org/documentation/retrieve-metadata/).

## Open Library

Bücher/Editionen, ISBN, Titel, Autoren, Publikationsdatum und Katalogschlüssel.
`https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data`,
`/isbn/{isbn}.json` und `/search.json`. Öffentliche Leseabfragen ohne Key;
1 Request/s anonym, 3/s identifiziert. Monatsdumps statt API-Massenharvesting.
Internet Archive beansprucht keine neuen Rechte; vorhandene Rechte einzelner
Beiträge können bestehen, keine pauschale juristische Freigabe behaupten.
Neuer lokaler Books-API-JSON-Import plus ISBN-Prüfsummen. Relevant für Lehr-/Fachbücher,
nicht als Qualitätsnachweis. Risiko: ISBN-/Titelsuche verrät private Literaturauswahl;
Cover-/Lese-APIs werden nicht integriert.
[API/Limits](https://openlibrary.org/developers/api),
[Rechte](https://openlibrary.org/developers/licensing).

## DOAJ

OA-Zeitschriften und Artikel; ISSN, Titel, Publisher, Fachgebiet und Artikelmetadaten.
API-Dokumentation unter `https://doaj.org/docs/api/` bzw. `/api/v4/docs` lieferte 403;
deshalb kein konkret freigegebener Endpunkt, Authentifizierungsablauf oder numerisches
Ratenlimit in dieser Implementierung. Offizielle Terms bestätigen CC0 für Journal-
und Artikelmetadaten. Dumps werden nach Einzelfallzugang monatlich, für Premium-
Metadatennutzer täglich erzeugt. Premium ist ausgeschlossen; Zugang nicht beantragt.
Nur Registerkandidat. Fachlich ergänzendes Journalmerkmal, kein Retraktions- oder
Gütesiegel eines einzelnen Papers. Risiko: Publikationsinteressen und mögliche
personenbezogene Zuschreibungen.
[API](https://doaj.org/docs/api/), [Terms](https://doaj.org/terms/),
[Dumpzugang](https://doaj.org/docs/public-data-dump/).

## Zenodo

Daten, Software und weitere Outputs; DOI, Titel, Creator, Version und Lizenzfelder.
`https://zenodo.org/api/records/{id}` bzw. `/api/records`; öffentliche Leseabfragen
ohne Deposit-Token, keine Upload-/Publish-Funktion integriert. Gastlimit 60/Minute
und 2000/Stunde, Suche 30/Minute; Header sind maßgeblich. OAI-PMH-Harvesting als
Bulkweg, ebenfalls begrenzt. Metadaten CC0 außer E-Mail-Adressen; Dateien behalten
ihre eigenen Lizenzen. Neuer lokaler Records-JSON-Import für Daten-/Softwareversionen.
Hohe DS/KI-Relevanz. Risiko: private Repository-/Datensatzreferenzen, Upload und
unbeabsichtigte Veröffentlichung; alle Schreibendpunkte bleiben ausgeschlossen.
[API/Limits](https://developers.zenodo.org/), [Policy](https://about.zenodo.org/policies/).

## Software Heritage

Öffentliche Softwaregeschichte, Content-, Revision-, Release- und Snapshot-IDs.
`https://archive.softwareheritage.org/api/1/`, etwa `/revision/`, `/release/`,
`/known/` und `/origin/search/`; genaue objektbezogene Pfade sind in der
Endpointreferenz beschrieben. Öffentlicher punktweiser Zugriff; Bearer-Zugang
kann Limits anheben. Kein zuverlässig allgemeingültiges numerisches Limit aus
den geprüften Primärseiten übernommen. Quoten/Hostbedingungen vor Nutzung prüfen.
Bulk nicht über Punktabfragen: Anbieter verlangt Abstimmung großer Teilbestände.
Software behält eigene Lizenzen; API-Fakten sind keine Nutzungslizenz des Codes.
Nur Registerkandidat. Hohe Reproduzierbarkeitsrelevanz, aber keinerlei Archivierungs-
oder URL-Suche privater Unternehmensrepositories.
[Endpoints](https://archive.softwareheritage.org/api/1/),
[Bedingungen](https://www.softwareheritage.org/legal/api-terms-of-use/),
[Authentifizierung](https://docs.softwareheritage.org/devel/swh-web-client/index.html).

## arXiv

Preprints mit Titel, Autoren, Abstract, Version und vorhandener DOI.
`https://export.arxiv.org/api/query`, Atomantworten, kein Key für die Legacy-API.
Kostenlose Nutzung; maximal ein Request je drei Sekunden, eine Verbindung über
alle eigenen Maschinen hinweg. Deskriptive Metadaten CC0, e-Print-Rechte separat.
OAI-PMH/Bulkverfahren sind dokumentiert; Speicher-/Transferkosten bei externen
Bulkangeboten nicht als kostenlos voraussetzen. Registerkandidat; kein neuer
Adapter angesichts vorhandener DOI-Quellen. Relevant für KI, aber Preprintstatus
und Version sind keine Peer-Review-Bestätigung. Risiko: Suchbegriffe und private
Publikationsinteressen; keine Volltextdownloads.
[Manual](https://info.arxiv.org/help/api/user-manual.html),
[Bedingungen](https://info.arxiv.org/help/api/tou.html).

## Europe PMC

Vor allem biomedizinische Artikel, Preprints, Bücher und Referenzbeziehungen;
DOI/PMID/PMCID, Titel, Autoren, Journal und verfügbare Abstract-/OA-Felder.
Offizielle REST-Basis `https://www.ebi.ac.uk/europepmc/webservices/rest/`,
z. B. `/search` und `/fields`; öffentliche Lesebeispiele ohne Key. In der
geprüften zentralen Referenz kein belastbares universelles numerisches Limit;
eine Supportauskunft ersetzt keine aktuelle Betriebsfreigabe. REST, OAI-PMH und
Bulkdownloads nach Datentyp. OA-/Abstract-/Dateirechte getrennt prüfen; keine
pauschale CC0-Freigabe. Registerkandidat, geringe direkte Priorität gegenüber DBLP
für Mosbach DS/KI. Risiko: Suchbegriffe können sensible Gesundheits-/Forschungsfragen
offenlegen. Kein Remotezugriff aus Arbeiten.
[Developerressourcen](https://dev.europepmc.org/developers),
[REST](https://dev.europepmc.org/RestfulWebService).

## Implementierungsentscheidung

Aktiv implementiert sind ausschließlich zusätzliche **lokale Importe** für DBLP,
Open Library, DataCite und Zenodo; Crossref/OpenAlex/Retraction Watch bleiben erhalten.
Die übrigen Registryeinträge sind recherchierte Kandidaten, keine freigegebenen
Adapter. Der getrennte Downloader besitzt genau eine feste öffentliche DBLP-Probe,
keine freie Suche und keine kostenpflichtigen Ziele. Der reale Probeabruf lieferte
HTTP 202 und wurde nicht importiert. Die Anwendungsfreigabe bleibt unverändert.
Details: [lokaler Betrieb](local_scientific_infrastructure.md).
