# Datenschutz- und Sicherheits-Gap-Analysis

## Erneutes Security-Hardening, 27.11.2026

Die erneute Prüfung des vorhandenen Codes ergab folgende zusätzliche Lücken.
Die Änderungen erhalten die bestehenden Default-Deny-, Embargo- und Freigabesperren.
Siehe [ausgeführte Prüfungen und offene Grenzen](hardening_results.md).

| Gefundene Lücke | Priorität / umgesetzte Maßnahme | Nachweis / verbleibende Grenze |
|---|---|---|
| Frontend prüfte den Backendnamen, verband sich aber ohne IP-Pinning | P0: Auflösung vollständig prüfen, Verbindung an freigegebene numerische IP binden; keine Redirects/Proxys oder frei übergebenen Requestoptionen | DNS-/IPv6-/Redirecttests und echte Frontend-Positivkontrolle im Docker-E2E; Hostabnahme offen |
| Online-Provisioning konnte das Inferenznetz des Verarbeitungsstacks öffnen | P0: eigenständiges Compose-Projekt mit nur einem Provisioner, ohne Verarbeitungsknoten/-netze; aktives Modell-Volume vor Änderungen ablehnen | gerenderte Einzel-/Fehlkombination, Lifecycle-/Fehlertests; kein Modell tatsächlich heruntergeladen |
| Modellfreigaben waren nicht an volle installierte Ollama-Digests gebunden | P0: Version, Herkunft, voller Digest und Lizenz-/Securityfreigabe verlangen; Router und Provider prüfen Digest vor Promptversand | Tagwechsel-/Approvaltests; Servermanifest-Digest ist kein unabhängiger Gewichtsdateibeweis |
| DOI-/Bibliografie-Zwischenergebnisse trugen nur teilweise eigene IFC-Metadaten | P0: unveränderliche Eintragsklasse, Analyse-/Dokumentkennung an Kandidaten, Maximumregel für Ergebnisse und Quellenreview; fremden Scope ablehnen | vier Schutzklassen, fehlende/ungültige Labels, Mischklassen und Fremdscope getestet; kein externer Research-Client vorhanden |
| Requestkörper konnte vor Pydantic-Validierung unbeschränkt eingelesen werden | P1: ASGI-Limit 1 MiB vor Handler/Zustandsänderung, echte Chunkzählung, 15-s-Lesefrist und generische 400/408/413 | negative Header-/Chunk-/Timeouttests; kein Ersatz für Hostquoten und Mehrprozess-Lasttest |
| Modell-/Backendantworten ohne Gesamtmengenlimit | P1: Streamlimit 8 MB, Gesamtdeadline für Modellaufrufe, keine Upstreamtexte in Fehlerausgaben | Übergrößen-/Timeout-/Sanitisierungstests; echte Modellressourcen nicht vermessen |
| Silbentrennung konnte Sperrvermerk-Indikatoren verbergen; Detailhinweise fehlten | P1: lokale Trennungsnormalisierung und konservative Kandidaten für explizit bezeichnete Firma/Frist/Adressaten/Genehmigung | synthetische Tests einschließlich abgelaufener Frist; keine automatische juristische Auslegung/Entklassifizierung |
| GROBID-XML-Fehler konnten Parserdetails weiterreichen | P1: feste Fehlercodes für ungültiges/XML-Entity-Material | lokale negative Parsertests; echtes GROBID-Image nicht abgenommen |
| Image-Paketinstaller enthielt bekannte Schwachstellen | P1: pip nach hashgebundener Installation aus beiden App-Laufzeitimages entfernen | erneuter Offline-Imagescan; verbleibende OS-Befunde separat dokumentiert, keine Scanner-Ausnahme ergänzt |

Netzwerkfähige Komponenten bleiben ausdrücklich begrenzt: Backend→gepinntes
lokales Ollama/GROBID (optional), Frontend→gepinntes Backend, getrennte Beschaffung
von Modellen/Paketen und manueller öffentlicher Quellenbezug. ResearchProvider haben
keinen HTTP-Client. Private Dokumenteingänge bleiben gesperrt. Host, Administrator,
Browser, DNS/IPv6 und Fremdbibliotheken benötigen weiterhin institutionelle Abnahme.

## Folgeaudit: Mosbach-Wissensbasis und Quellenprüfung, 27.11.2026

Die nachfolgende Ursprungstabelle beschreibt den früheren Ausgangszustand. Das
Folgeaudit hat die inzwischen vorhandenen Policy-/IFC-/ACL-/DLP-Sperren erhalten
und die neuen Datenpfade gesondert geprüft. Keine echte Arbeit wurde geöffnet.

| Gefundene Lücke | Priorität / konkrete Maßnahme | Nachweis / verbleibende Grenze |
|---|---|---|
| Keine quellen-/jahrgangsgebundene Mosbach-Basis | P0: lokales Quellenregister, exakte Programm/Kohorten/Arbeitstyp-Auswahl, Kandidatenstatus und separate hashgebundene Freigabe | Regel-/Versions-/Konflikttests; Originale/StuPrO-Freigabe noch offen |
| Vermischung mit allgemeinen oder fremden Standortregeln | P0: explizite Hierarchie, Prüfungsrechtsrahmen, keine automatische Konfliktentscheidung | Tests für fremde Standorte, Delegation und Gesetzesvorrang |
| Neue Bibliografie-/DOI-Daten könnten Egresswege eröffnen | P0: lokale Importadapter, ResearchGateway geschlossen; kein Key/Billing/HTTP-Provider | Privacytests aller sieben Providernamen; keine externen Abfragen |
| GROBID könnte implizit Crossref-Konsolidierung nutzen | P0: standardmäßig aus; Konsolidierung 0, Loopback-Konfiguration, internes Netz, IP-Pinning | Transport-/Parameter-/XML-Tests; echtes Image und Zielhost nicht abgenommen |
| Unbekannte Clearance könnte zu hoher Leseberechtigung werden | P0: nicht öffentliche/unklare Bibliotheks-Clearance in DEVELOPMENT vollständig ablehnen | Private-library-Tests; keine vertraulichen Imports |
| Parserfehler könnten Inhalt oder Dateinamen ausgeben | P1: generische Importcodes, keine Rohtracebacks; Pypdf-Logger stumm; Entities/aktive PDF-Inhalte abweisen | Import-/CLI-/Archivtests; native Parser-Sandbox bleibt offen |
| Manipulierte öffentliche Snapshots | P1: Herkunftsprüfung, exklusive Ablage außerhalb Repo, Originalhash/Prüfung beim Start, Mengenlimits | Tamper-/Pfad-/Public-Provenance-Tests; Operator/Host bleibt Vertrauensgrenze |
| DOTX/XLTX nicht ausdrücklich durch Ignores/DLP gesperrt | P1: beide Vorlagentypen ergänzen; öffentliche Vorlagen nur lokal untersuchen | DLP-Regressionen und indexbezogene Prüfung |
| Löschen einer Begutachtung entfernte sämtliche Taskreferenzen | P1: nur zugehörigen Task entfernen, andere Analysen verwaltet lassen | API-Regression `test_delete_one_assessment_keeps_other_task_managed` |
| Formalien-/Quellenergebnisse könnten Erstbewertung vorprägen | P1: gemeinsames Embargo; eigene Bestätigung/Ablehnung versionieren | API-/UI-/Docker-E2E; empirische Biaswirkung offen |

Offene Produktionsblocker: Hochschulidentität, echte Autorisierung, Speicher-/
Backupverschlüsselung, TLS-Dienstidentität, Modellartefakte, Parser-Sandbox,
Host-DNS/IPv6/Egress, Rechts-/Prüfungsfreigabe und offizieller Lösch-/Archivprozess.
Kein neuer Modus erhält dadurch Produktivzugang. Tatsächliche Ergebnisse stehen in
[Mosbach-Ergebnisse](../evaluation/mosbach_results.md).

## Historischer Ausgangszustand der vorherigen Sicherheitsiteration

Bestandsaufnahme: 2026-11-26, vor dieser Erweiterung. Grundlage ausschließlich
Quellcode, Konfiguration und synthetische Fixtures. Keine wissenschaftlichen
Originalarbeiten wurden geöffnet. Dies ist keine rechtliche Freigabe.

| Datenfluss / Komponente | Tatsächlicher Ausgangszustand | Lücke / Priorität |
|---|---|---|
| FastAPI `/chat` | Freie Prompts, fester lokaler Gateway, generische Fehlermeldungen | Vertrauliche Eingaben trotz Demo möglich; verbindliche Freigabe fehlt / P0 |
| `/runs`, Aufgaben, Bewertungen | Festes synthetisches Dokument, freie Aufgaben/Kriterien/Kommentare | Abgeleitete Kontexte nicht durchgängig klassifiziert / P0 |
| Assessment, Discussion, Synthesis | Unabhängige Bewertung, serverseitige Ergebnisembargos, menschliche Finalisierung | `SYNTHETIC` fest einprogrammiert, keine Herkunftsprüfung freier Kommentare / P0 |
| DocumentStore | UUID-Pfade, JSON, zeitlich begrenzte synthetische Dateien | Default CONFIDENTIAL, Repository-Unterverzeichnis, kein Neustart-Cleanup / P0 |
| LLM-Gateway / Ollama | Nur Ollama, keine externen Fallbacks, Budgets; TLS, keine Proxy-Umgebung/Redirects im App-Client | `local=true` und Modell-Privacy sind keine technische Endpunktfreigabe / P0 |
| Model Registry | Hersteller, Fähigkeiten, Ressourcen, HF-Reviewmetadaten | Betriebsort, Endpunktbindung, Telemetrie-/Cloudfreigabe fehlen / P0 |
| Policy Engine | LOCAL_ONLY und feste Toolliste | Kein vierstufiges IFC, kein Production Gate, unvollständige Entscheidungskontexte / P0 |
| AgentFactory / Registry | Schemas, Parent-Zuordnung, Quoten, feste Tools, keine Shell | Keine explizit vererbten Sicherheitskontexte / P1 |
| ResearchGateway | Kein HTTP-Client, jede Suche abgelehnt | Sicher geschlossen; nicht als implementierte öffentliche Recherche ausgeben / erhalten |
| API / Benutzerzugriff | Keine Authentifizierung; lokale Demo | UUIDs sind keine Autorisierung; Mandanten-/ACL-Prüfung fehlt / P0 |
| Streamlit | Telemetrie aus, Upload deaktiviert, Ausgabe als Text | Freier Chat, fehlender vollständiger Sicherheitsstatus; Browser-/Downloadregeln / P1 |
| Netzwerk | Lokale interne Docker-Netze; Universität externes Netzwerk | Kein nachgewiesenes Host-Egress, DNS-/IPv6-Kontrolle, mTLS oder Live-Isolationstest / P0 |
| Provisioning | Separate Online-Compose-Überlagerung; HF-Kandidaten gesperrt | Online-Overlay kann missbraucht werden; isolierter Lifecycle und Hashbeleg erforderlich / P1 |
| Monitoring / Fehler | Ressourcenmetrik, generische Validierungsfehler, keine Uvicorn-Accesslogs; Backend erzwingt LangSmith-/OTel-Deaktivierung bereits beim Import | weitere Fremdbibliothekslogs/HF-Flags und geschütztes Audit fehlen / P1 |
| Löschung | Laufzeit-TTL und Shutdown-Cleanup; Assessment im RAM | Kein explizites Delete, verwaiste Dateien nach Crash; Backups/Swap ungeprüft / P1 |
| Git / Docker / CI | Umfangreiche Ignores, Build-Allowlist, synthetische Tests, Security-Scanner, CI-Gate | Kein eigenständiger verpflichtender Privacy-Job, kein Pfad-DLP/Canary-Gate / P1 |
| PDF / OCR / Embeddings | Nicht implementiert; keine echte Uploadroute | Parser-Sandbox, Malwareprüfung, OCR-/Embedding-IFC erst vor Freigabe implementieren / Sperre erhalten |

## Priorisierter Implementierungsplan

1. P0: vier Schutzklassen mit RESTRICTED-Default, unveränderliche IFC-Metadaten,
   lokaler Sperrvermerkdetektor; zentraler Default-Deny-Entscheidungsweg.
2. P0: Servermodi und nicht umgehbares Production Gate; freie Eingaben dürfen
   ohne Freigabe keinen Modellaufruf auslösen. Keine erfundenen Freigaben.
3. P0: Modell-/Endpointbindung, keine Redirects/Proxys/externen Provider;
   Berechtigungen unabhängig von Rollen, objektbezogene Zugriffskontrolle.
4. P1: vererbte Agentenkontexte, geschlossene Recherche, inhaltsarme Audits,
   explizite Löschung, sichere temporäre Ablage außerhalb des Repositorys.
5. P1: Netzsegmentierung und Firewall-Vorlage mit separatem Host-Abnahmetest,
   DLP-Hook, Canary-Tests und verpflichtender Privacy-Security-CI-Job.
6. Dokumentation: Threat Model, Risikoregister, TOMs und offene Freigaben.
   Tests berichten nur tatsächlich beobachtete Ergebnisse. Hochschulnetz,
   SSO, Verschlüsselung und rechtliche Zulässigkeit bleiben Freigabeblocker,
   solange sie nicht auf der Zielinfrastruktur geprüft wurden.
