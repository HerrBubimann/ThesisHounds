# Threat model and trust boundaries

## Folgeaudit: Transport und Bereitstellung (27.11.2026)

| STRIDE | Konkreter Pfad | Ergänzte Kontrolle | Offene Grenze |
|---|---|---|---|
| Spoofing / Disclosure | manipulierte Backend-DNS-Antwort im Frontend | alle IPs prüfen, einmal numerisch verbinden; keine Redirects/Proxys | Browser-/Hostabnahme |
| Tampering | mutable Ollama-Tags/fehlende Modellprovenienz | volle Servermanifest-Digests und Freigaben vor Download und Promptversand | Gewichtsbytes/Serverintegrität, Race mit privilegiertem Operator |
| Disclosure / Privilege | Provisioning erbt Inferenznetz/-Volume einer aktiven Anwendung | eigenes Projekt/Netz, nur Modell-Volume, aktive Nutzung ablehnen | kein verteilter Operatorlock |
| Disclosure | Bibliografie-Derivat verliert Taint/Analysebereich | Eintragsklasse und Scope, Maximumregel, Fremdscope-Deny vor Modellaufruf | künftige Adapter prüfen |
| Denial of service | große/langsame Bodies oder unbeschränkte Antwort | vor Handler begrenzen, 15-s-Bodydeadline, 8-MB-Antworten, Modellgesamtdeadline | Zielhostquoten/Mehrbenutzerlast |
| Repudiation | Scannergate wird mit Schwachstellenfreiheit verwechselt | vollständiger Befundbericht mit DBzeitpunkt und getrenntem Gateergebnis | Risikoannahme und Patchprozess institutionell offen |


## Ergänzung: Hochschulwissen und Bibliografie (27.11.2026)

| STRIDE | Neuer Angriffspfad | Technische Kontrolle | Verbleibende Grenze |
|---|---|---|---|
| Spoofing | importierte Datei behauptet amtliche Freigabe | Import setzt CANDIDATE, separate hashgebundene Freigabe; keine Approval-API | Operator-/SSO-/Rollennachweis noch offen |
| Tampering | Snapshot/Regelversion wird nach Review verändert | Originalhash, Profilfingerprint, erneute Cacheprüfung, exklusive Dateiablage | Host-/Kuratorrechte und Signaturprozess organisatorisch sichern |
| Repudiation | unklarer Regel-/Quellenstand | Original-URL, Abrufzeit, Prüfumfang, Reviewerbeleg/Revision | manipulationsgeschütztes Produktionsaudit fehlt |
| Information disclosure | DOI-Muster oder GROBID-Consolidation verraten private Forschung | lokaler Cache, geschlossener ResearchGateway, Parser-Pinning/Konsolidierung aus | tatsächlicher GROBID-/Host-DNS-/IPv6-Test offen |
| Denial of service | ZIP/XML/PDF-Bombe oder riesiger Metadatenbestand | Dateityp-/Expansions-/Recordlimits, Entities aus, Ressourcenlimits | native Parser-Sandbox/Malwareprüfung für echte Dateien offen |
| Elevation of privilege | Dokument fordert neue Quellen-/Agentenrechte oder andere Kohorte | serverseitige Scope-/Rechteprüfung, nicht öffentliche Bibliothek gesperrt | kompromittierter Prozess/Root bleibt außerhalb Appgarantie |

Bibliografische Metadaten können fehlerhaft oder manipuliert sein; ein bestätigter
DOI-Treffer ist kein Wahrheitsbeweis. Ergebnisse sind menschlich zu prüfen. Weitere
Vertrauensgrenzen und Datenfluss siehe [Research Privacy](../research/research_privacy.md).

Stand: 2026-11-26. Assets: Unternehmensgeheimnisse, Arbeiten, Identitäten,
Bewertungen, Gutachten, Kontexte, Zugangsdaten und geschützte technische Audits.
Aktuell existieren ausschließlich synthetische Dokumenteingänge und Mock-Inferenz.
Datenflüsse: [Diagramm mit Vertrauensgrenzen](data_flow.md).

Angreifer: unberechtigter Benutzer, Dokumentautor mit Prompt Injection,
kompromittiertes Modell/Dependency, fehlerhaft konfigurierte Infrastruktur und
privilegierter Innentäter. Ein kompromittierter Host/Betreiber kann Quellcode und
Speicher verändern; die App behauptet keinen Schutz gegen Root oder beliebigen
Python-Code im selben Prozess. Abhilfe braucht unabhängige Infrastrukturkontrollen.

| Grenze / Bedrohung | Gelieferte Kontrolle | Restaufgabe |
|---|---|---|
| Browser → API: Identitätsspoofing, fremde IDs | keine Identitäts-/Rollenheader vertraut; Objekt-ACL; no-store; strikte Schemas | Hochschul-SSO und echte Benutzersitzungen; Demoidentität ist nicht mandantenfähig |
| Dokument → Steuerung: Prompt Injection | Dokumente als Daten; keine Tools/Gradefreigaben; Hinweise ohne automatische Notenstrafe | echter PDF-/OCR-Angriffskorpus und Parser-Sandbox; Detektionsheuristik nicht vollständig |
| Quelle → Ableitung: Taintverlust | RESTRICTED-Default, Maximumregel, immutable Label, serverseitige Outputs | neue Persistenz-/Embedding-/Exportpfade vor Einführung anbinden |
| Parent → Child: Privilegienerweiterung | Factory und Registry prüfen gleiche Analyse, Klasse und Teilmengen; feste Toolliste | unabhängige Prozess-/Hostkontrollen gegen kompromittierten Code |
| Workflow → Inferenz: Providerwechsel | obligatorischer Gateway, kein Fallback, Provider-Dispatchkontext; Defaultmock ohne I/O | Hochschule muss sichere echte Inferenz erst implementieren/abnehmen |
| DNS/HTTP → Netzwerk: Rebinding, Proxy, Redirect, IP/Port/IPv6 | feste Ziele/IP-Mengen, IP-Pinning, keine Redirects/Umgebungsproxies | Hostfirewall inkl. Dockerresolver, UDP, IPv6/Link-local, Container→Host abnehmen |
| Privater Kontext → Recherche | ResearchGateway ohne Client/Store verweigert alle Anfragen | isolierter Public-Service fehlt; keine aus Dokumenten abgeleitete Query freigeben |
| Menschlicher Review → KI-Kontext | unabhängige Zweitbewertung bekommt keinen Erstreview; freie Kommentare RESTRICTED | KI-Diskussion bis Produktivfreigabe blockiert; menschlicher Ablauf verfügbar |
| Verdecktes Ergebnis → Client | serverseitiges Erstbewertungs- und Freigabeembargo; explizite Projektionen | weiterhin keine Identitätstrennung zwischen echten Personen in der Demo |
| Anwendung → Logs/Git/CI | inhaltsarme Audits, generische Fehler, Logger/Tracing aus; Ignores/DLP/Canaries | manipulationsgeschützte Auditablage, manuelle Prüfung; Pfad-DLP erkennt keine Geheimnisse in beliebigem Quelltext |
| Speicher → Löschung/Backup | UUID-Pfade, exklusive Dateien, TTL/Delete/Orphan-Sweep | Verschlüsselung, Swap, Snapshots, Backuprestore und offizielle Archivierung offen |
| Gewichte/Dependencies → Runtime | hashfixierte Python-Locks, HF-Reviewmetadaten, kein Runtime-Download/Remote Code | Gewichte tatsächlich gegen Hash/Digest prüfen, Signatur/Provenienz und Modelllizenz abnehmen |

Sicherheitsentscheidungen sind keine akademischen Entscheidungen. Ein erkannter
Manipulationshinweis darf nur zur menschlichen Sicherheitsprüfung führen. Freigaben
für Datenzweck, Verarbeitung, Infrastruktur und konkrete Sperrvermerke bleiben
getrennte organisatorische Nachweise. Tests und offene Punkte siehe
[Ergebnisse](privacy_test_results.md) und [Readiness](production_readiness.md).
