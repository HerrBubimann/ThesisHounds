# Kostenlose Rechercheprovider und tatsächlich freigegebener Umfang

Offizielle Dokumentation geprüft am 26.11.2026 UTC. Kein API-Konto angelegt, kein
kostenpflichtiger Aufruf, kein Gesamtdatensatz heruntergeladen. Zugang/Limits können sich ändern.
**Alle Registry-Provider sind in der Anwendung `LOCAL_IMPORT_ONLY`, Netzwerk aus,
Kostenobergrenze 0 USD.** Crossref/OpenAlex/Retraction Watch haben Importadapter;
die übrigen Einträge dokumentieren Kandidaten, keine vorgetäuschte Onlineintegration.

| Provider / Originaldokumentation | Zugang, Limit und Lizenzstand | Verwendung und MVP-Status |
|---|---|---|
| [Crossref REST](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), [Zugang](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication), [Änderung 21.07.2026](https://community.crossref.org/t/refining-rest-api-limits-for-improved-stability-and-reliability/16137) | Public ohne Anmeldung; Polite mit eigener Kontaktadresse. Einzelabfragen 5/s bzw. 10/s, Listen 1/s bzw. 3/s; Antwortheader und 429 maßgeblich. Metadata Plus ist kostenpflichtig und nicht integriert. Abstracts/Publisher-Inhalte haben ggf. eigene Rechte. | DOI, Titel, Autor, Jahr, Typ/Version lokal aus Original-JSON; keine Aussagebelege aus DOI allein. `update-to`-Notice-Zuordnung noch manuell, RW-Import für Rücknahmen/Korrekturen. |
| [OpenAlex API](https://help.openalex.org/api/), [Authentifizierung](https://help.openalex.org/api/authentication/), [Preise](https://help.openalex.org/access/pricing/) | Daten CC0; aktuelles Modell: freies Tagesbudget 1 USD mit kostenlosem Konto, automatische Abrechnung nicht voraussetzen. Ohne Key nur begrenzte Nutzung; für Cursor-Paging Key. Suchart-/Tariflimits und `X-RateLimit-*` aus Dokumentation beachten. Bezahlte Prepaid-/Jahres-/Sync-Optionen existieren. | Import kleiner `results`-Teilbestände, lokale Titelsuche. Keine Keys, Kauf-/Top-up-Route, Volltext-Sync oder Onlineabfragen im MVP. `is_retracted=false` ist kein umfassender Entwarnungsnachweis. |
| [Semantic Scholar API](https://www.semanticscholar.org/product/api), [API-Dokumentation](https://api.semanticscholar.org/api-docs/), [Lizenz](https://api.semanticscholar.org/license/) | Produktseite im Werkzeug 403, API-Doku nur JavaScript-Navigation. Lizenz erreichbar: nutzungsbezogene Einschränkungen, keine pauschale CC0-Annahme. Aktuelles individuelles Key-/Ratenlimit nicht zuverlässig auslesbar und vor Freigabe zu bestätigen. | Registerkandidat für Literatur/Zitationsgraph; kein freigegebener HTTP- oder Importadapter. |
| [DataCite REST](https://support.datacite.org/docs/rest-api), [Rate Limits](https://support.datacite.org/docs/rate-limit) | Öffentliche Metadatenabfrage ohne Authentifizierung, nur findable DOIs. Dokumentierte Klassen je 5 Minuten/IP: unidentifiziert 500, identifiziert 1000, authentifiziert 3000; 429/Backoff. Keine DOI-Registrierung im Projekt. Lizenz der importierten Felder und verknüpften Daten getrennt prüfen. | Kandidat für Forschungsdatensätze/weitere DOI-Typen; noch kein freigegebener Adapter. |
| [Unpaywall API](https://unpaywall.org/api), [offizielle API-Beschreibung](https://data.unpaywall.org/products/api) | Produktseiten überwiegend JavaScript; offizieller Suchindex beschreibt kostenlosen Zugriff mit E-Mail-Parameter und 100.000 Aufrufen/Tag. Diese Angaben vor Onlinefreigabe erneut bestätigen. OA-Link ist keine pauschale Volltext-Nutzungslizenz. | Nur Registerkandidat. Keine automatischen PDF-Downloads oder Übernahme externer URLs in Parser. |
| [Retraction Watch bei Crossref](https://www.crossref.org/documentation/retrieve-metadata/retraction-watch/), [Datensatz](https://gitlab.com/crossref/retraction-watch-data) | Öffentlicher CSV-Bestand, laut Crossref werktäglich aktualisiert; Verteilung/Reusebedingungen vor organisatorischer Freigabe dokumentieren. Korrekturen/Expressions of Concern sind weniger vollständig als Rücknahmen. | Begrenzter lokaler CSV-Import von `OriginalPaperDOI`, `Title`, `RetractionNature`; Semikolonlisten unterstützt. Fehlender Treffer bleibt UNKNOWN. Keine gesamte Datenbank geladen. |
| [arXiv Manual](https://info.arxiv.org/help/api/user-manual.html), [API-Bedingungen](https://info.arxiv.org/help/api/tou.html) | Kostenlos; beschreibende Metadaten CC0, Volltextrechte individuell. Limits aus aktueller Terms-/Rate-Limit-Seite vor Freigabe übernehmen; kein frei erfundener Universaltarif. API-Einstiegslink zeitweise nicht zugänglich, Manual/Terms erreichbar. | Registerkandidat; Preprints werden als eigener Typ geführt, nicht als begutachtete Publikation ausgegeben. Versions-/Neuheitssuche noch manuell. |

Der MVP bezahlt keine APIs: Es gibt im privaten Prozess keinen Recherche-HTTP-Client,
keinen API-Key-Parameter, keine Billingintegration und keinen Onlinefallback.
Damit werden dort auch keine externen Rate-Limits verbraucht. Eine spätere öffentliche
Recherche benötigt einen getrennten Prozess ohne Thesis-Dateien oder private Kontexte,
einen erneut geprüften kostenlosen Zugang und nachweisbare Budget-/Rate-Grenzen.
Ein nachträglicher Kostencheck einer schon bezahlten Antwort wäre kein Kostenschutz.

## Reproduzierbarer lokaler Import

Nur unabhängig bereitgestellte und nachweislich öffentliche kleine Teilbestände:

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.research.snapshot_store crossref-public.json `
  --provider crossref --store C:\ApprovedPublicMetadata --reviewer reviewer-id `
  --provenance public-snapshot-description --public-provenance-reviewed
```

Für OpenAlex `--provider openalex`, für den lokalen CSV-Teilbestand
`--provider retraction_watch`. Derselbe Operator prüft Rechte/Herkunft unabhängig;
der Schalter behauptet keine institutionelle Rollenfreigabe. Rohbytes, SHA-256,
Importzeit und Provenienz werden außerhalb des Repositorys gespeichert. Beim Laden
werden Hash und Dateiname erneut geprüft. Maximal 8 MB je Rohimport, 32 Snapshots,
10.000 normalisierte Cacheeinträge. Kein Massendownload und keine automatische Aktualisierung.

Ein lokaler DEVELOPMENT-Server kann den geprüften Bestand mit
`PUBLIC_METADATA_DIR=C:\ApprovedPublicMetadata` lesen. In Docker ist zusätzlich ein
gezielter read-only Mount außerhalb des Buildkontexts erforderlich. Die Basiskonfiguration
enthält keinen solchen Mount und keinen Bestand. Interne Quellen/Thesis-Auszüge dürfen
niemals als öffentliche Metadaten eingespeist werden.
