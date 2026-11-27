# Datenschutz und Sicherheitsgrenzen

Aktueller Stand 2026-11-26: [verbindliche Privacy-Architektur](security/privacy_architecture.md)
und [Production Gate](security/production_readiness.md). Standard ausschließlich
In-Process-Mock, echte Inhalte und KI-Diskussion gesperrt, Hochschulstack absichtlich
nicht startfähig. Die nachfolgenden ursprünglichen Foundation-Hinweise begründen
keine weitergehende Freigabe. Aktuelle Nachweise: [Testergebnisse](security/privacy_test_results.md).

## Vertrauensbasis und Betriebsmodus

Die Foundation ist für lokalen Entwicklungsbetrieb mit freigegebenen synthetischen Daten vorgesehen. Vertrauliche Arbeiten können personenbezogene Daten, unveröffentlichte Forschung und Geschäftsgeheimnisse enthalten. Solche Dokumente können über die aktuelle Run-API nicht eingereicht werden; sie akzeptiert ausschließlich die serverseitige synthetische Fixture.

Host, Docker-Daemon, Administratoren, Backend und lokaler Browser gehören zur Vertrauensbasis. Interne Netze verhindern keinen Zugriff durch Host-Administratoren. Zwischen Containern gibt es keine Authentifizierung oder TLS. Der lokale Einzelplatzbetrieb ist keine produktive Mehrbenutzerlösung.

`LOCAL_ONLY` ist der Standard und einzige aktivierbare Modus. Jeder Inferenzaufruf läuft durch `LLMGateway` und `PolicyEngine`. Modelle müssen lokal, aktiviert, für die Rolle und Datenklassifizierung freigegeben und dem aktiven Ollama-Provider zugeordnet sein. Unbekannte Klassifizierungen gelten als `CONFIDENTIAL`. API-Clients und AgentSpecs können die Dokumentklassifizierung nicht setzen. Der Dokumentkontext und seine Klassifizierung werden serverseitig zugeordnet; Modellselbstauskünfte sind dafür bedeutungslos.

`EXPERIMENTAL` ist als separate Konfigurationsgrenze definiert und wird in diesem Prozess ausdrücklich abgewiesen. Es existiert keine Cloud-Anbindung und kein externer Fallback. Eine spätere Implementierung benötigt einen getrennten Runner ohne Mounts, Netzwerkzugriff oder Objektzugriff auf den lokalen Dokumentenspeicher bzw. interne Befunde. Nur ausdrücklich freigegebene synthetische/öffentliche Exporte dürften hineingelangen. Ein Schalter im aktuellen Frontend genügt dafür nicht.

## Bereits implementierte Kontrollen

| Schutz | Umsetzung |
| --- | --- |
| Netzwerk | Zwei interne Docker-Netze, keine veröffentlichten Backend-/Ollama-Ports, Frontend nur IPv4-Loopback |
| Provider-Ziele | Ollama-Adresse nur interner Service oder Loopback; HTTP-Proxyvariablen und Redirects werden nicht für Inferenz verwendet |
| Lokale Inferenz | Ein Ollama-Service; `OLLAMA_NO_CLOUD=1`; keine externen Provider implementiert |
| Telemetrie/Tracing | Streamlit-Nutzungsstatistiken aus; `LANGSMITH_TRACING=false`, `LANGCHAIN_TRACING_V2=false`, `OTEL_SDK_DISABLED=true` auch im Backend-Code erzwungen; keine Exporter |
| Modell-/Tool-Allowlist | Bekannte Modell-ID und freigegebene Rolle erforderlich; einziges Dokumentwerkzeug erhält nur den laufbezogenen Kontext |
| Keine Codeausführung | AgentSpecs sind Daten. Keine Python-Dateierzeugung, Shell, freien HTTP-Aufrufe, Dateipfade oder modellgesteuerten Tool-Dispatcher |
| Ressourcen | Agenten-/Aufrufsemaphore, Delegations- und Mengenlimits, globales Zeit-/Token-/Aufrufbudget; konfigurierbare Container-CPU-/RAM-Limits |
| Begrenzte Rechte | UID/GID 10001, schreibgeschütztes Root-Dateisystem, keine Capabilities, `no-new-privileges`, kein Docker-Socket |
| Konfiguration | Nur `config/` als schreibgeschützter Host-Bind-Mount; Modelle als benanntes Volume; temporäre Dokumente im tmpfs |
| Logging | Kein explizites Logging von Dokumenten, Prompts oder Antworten; bereinigte Fehler; Uvicorn-Accesslogs aus; rotierte lokale Betriebslogs |
| Build/Git | `.env`, Dokumentformate, Daten-/Report-/Uploadverzeichnisse ausgeschlossen; Build-Kontext mit Allowlist inklusive vier ausdrücklich freigegebener Konfigurationsdateien |
| Modellbeschaffung | Anwendung wird vor Online-Bereitstellung gestoppt; nur Ollama wird internetfähig gestartet; Online-Netz danach entfernt |

LangGraph bringt LangSmith als transitive Abhängigkeit mit. Das bedeutet keine aktivierte Verbindung: Tracing wird abgeschaltet, es wird kein Client oder Exporter eingerichtet und die Laufzeitnetze sind isoliert. Host- und Docker-Desktop-Telemetrie liegen außerhalb der Anwendung und müssen separat bewertet werden.

## Prompt Injection und Evidenz

Dokumenttexte, Aufgaben, Agentenvorschläge und Befunde werden als JSON in der User-Nachricht übergeben. Systemanweisungen benennen sie ausdrücklich als nicht vertrauenswürdige Daten. Eine Anweisung im Dokument kann weder neue Tools freischalten noch Konfiguration ändern; Factory, Gateway und Policy prüfen unabhängig vom Modelltext. Providerantworten mit unerwarteten Tool-Aufrufen werden abgewiesen. Die Graphviz-Darstellung verwendet nur serverseitig erzeugte Knoten-IDs und erlaubte Rollen/Statuswerte, keine Modelltexte als DOT-Code.

Diese Kontrollen begrenzen die Auswirkungen von Prompt Injection. Sie garantieren nicht, dass ein Modell inhaltlich jeder bösartigen Anweisung widersteht. Auch synthetische Eingaben können zu falschen Befunden führen. Wörtliche Belegprüfung, Herstellerwechsel und menschliche Freigabe sind getrennte Prüfungen; keine davon ist allein ein Wahrheitsnachweis.

## Speicherung und Aufbewahrung

Dokumentinhalt, Befunde, Prompts und Antworten werden während der Verarbeitung im RAM gehalten. Synthetische Dokumentseiten werden zusätzlich im Backend-tmpfs gespeichert, bei nativer Entwicklung unter `.runtime/documents`. Befunde und menschliche Entscheidungen bleiben ausschließlich im Prozessspeicher und sind über die lokale API/UI einsehbar, nicht in allgemeinen Logs. API-Antworten mit fachlichem Inhalt sind keine öffentlich zugänglichen Monitoring-Logs.

Abgeschlossene Ausführungen werden standardmäßig nach einer Stunde bereinigt; dies umfasst auch Läufe mit noch ausstehender menschlicher Prüfung. Bei voller Aufbewahrungsgrenze können ältere abgeschlossene Ausführungen für neue Läufe entfernt werden. Ein Backend-Neustart verliert den gesamten Run-Zustand. Es gibt keine dauerhafte Auditakte und keine Recovery laufender Analysen.

Das Modell-Volume bleibt erhalten und kann neben Modellen lokale Ollama-Schlüssel-/Konfigurationsdateien enthalten. Es ist unverschlüsselt. tmpfs und RAM sind keine garantierte sichere Löschung: Host-Swap, Crashdumps, Backups und Browserfunktionen können Daten erhalten. Ein hart beendeter nativer Entwicklungsprozess kann synthetische Restdateien hinterlassen.

## Vor produktivem Einsatz noch erforderlich

- Authentifizierung, Rollen und dokumentierte Identität der menschlich freigebenden Person. Der aktuelle Review-Endpunkt ist eine technische Freigabesperre, kein nachweisbares Professoren-Sign-off.
- TLS und abgesicherter Zugang für zentralen Mehrbenutzerbetrieb. Eine öffentliche Portbindung ist im Standard nicht vorgesehen.
- Freigabe der zulässigen Datenbestände, Rechtsgrundlage, Verantwortlichkeiten, Datenschutzbewertung und gegebenenfalls Datenschutz-Folgenabschätzung mit zuständigen Stellen.
- Verschlüsselung, Swap-/Crashdump-Regeln, Lösch-/Backupkonzept, revisionsfähige Freigabehistorie und geeignete Persistenz.
- Sichere PDF-Ingestion, Dateityp-/Größenprüfung, isolierter Parser, kontrollierte Dokumentberechtigungen und Bereinigung vor echten Uploads.
- Zielhardware-Tests für CPU/GPU, Speicherdruck, Abbruch, Netzwerk-Egress und Offline-Betrieb. Modell-Ladeverhalten wird derzeit nicht durch einen VRAM-Scheduler garantiert.
- Sicherheitsupdates, Schwachstellenscans, Modell-/Lizenzfreigabe, Image-Digests und Actions-Commit-SHAs. Versions-Tags und Hash-geprüfte Pakete ersetzen keine Herkunftsprüfung.
- Domänenspezifische Evaluation gegen menschlich annotierte Referenzen, einschließlich Prompt-Injection-Angriffen und unbelegten Abwesenheitsbehauptungen.

**Lokale KI ist nicht automatisch DSGVO-konform.** Diese Foundation ersetzt keine Datenschutz- oder IT-Sicherheitsfreigabe. Keine vertraulichen Inhalte in Issues, Commit-Nachrichten, Screenshots, Testfixtures oder CI-Logs übernehmen.

Offizielle Hinweise: [Ollama lokaler Betrieb](https://docs.ollama.com/faq), [Streamlit Telemetrie-Konfiguration](https://docs.streamlit.io/develop/concepts/configuration/options), [interne Compose-Netze](https://docs.docker.com/reference/compose-file/networks/).
