# Risk register

## Erneutes Hardening, 27.11.2026

Vorgeschlagene Verantwortlichkeiten, keine erklärte Risikoannahme. Die konkreten
Scans und Testgrenzen stehen im [Hardening-Bericht](hardening_results.md).

| ID / Risiko | Wahrscheinlichkeit / Schaden | Maßnahme / Nachweis | Restrisiko / vorgeschlagener Owner |
|---|---|---|---|
| SEC-R1: Frontend-DNS-/Redirect-Abfluss | M/H | numerisches IP-Pinning, keine Redirects/Proxyumgebung; Unit und echte lokale Positivkontrolle | Host/Browser/privilegierter Code bleiben Vertrauensgrenze / IT+Security |
| SEC-R2: Online-Provisioning öffnet Verarbeitungsnetz | M/H | eigenständiges Projekt ohne Processing, Volume-Aktivitätsprüfung, Cleanup bei Fehler; Compose-/Lifecycletests | gleichzeitiger Operatorstart, kompromittierter Downloadserver; tatsächliche Modellbereitstellung offen / Modellsteward+IT |
| SEC-R3: Modelltag wird nach Review verändert | M/H | volle Manifest-Digests und Freigaben vor Download/Routing/Chat | Server kann falsche Digests melden; Wechsel zwischen Prüfung/Inferenz möglich; echte Gewichtsbytes/Signaturen offen / Modellsteward |
| SEC-R4: Bibliografie verliert Klassifizierung/Scope | M/H | immutable Eintragsklasse, IDs, Maximumregel, Fremdscope-Deny; acht neue Regressionen | künftige Adapter und berechtigte Fehlklassifizierung / Backend+Datenschutz |
| SEC-R5: große/langsame API-/Modellnachricht | H/M | vor Handler 1-MiB-/15-s-Grenze; Antworten 8 MB, Modellgesamtdeadline | viele parallele Verbindungen und Zielhostlast unvermessen / Backend+IT |
| SEC-R6: bekannte OS-Image-Schwachstellen | M/H | vollständiger Offline-Trivy-Scan; pip entfernt; keine Fixable-HIGH/CRITICAL-Ausnahme | je App-Image 100 HIGH und 2 CRITICAL ohne gemeldete Korrektur; kein Exploitability-Nachweis, Produktion weiterhin gesperrt / DevOps+Security |


## Mosbach-/Quellen-Folgeaudit, 27.11.2026

Qualitative Einschätzung, keine statistische Eintrittswahrscheinlichkeit oder
unterzeichnete Risikoannahme. Verantwortlichkeiten sind vorgeschlagene Rollen.
Ergebnisse beziehen sich auf lokale synthetische Tests, siehe
[aktueller Ergebnisbericht](../evaluation/mosbach_results.md).

| Risiko-ID / Daten | Angriffsfläche / Wahrscheinlichkeit / Schaden | Technische Gegenmaßnahme | Organisatorisch / vorgeschlagener Owner | Test / tatsächlicher Befund | Restrisiko / Status |
|---|---|---|---|---|---|
| MOS-R1: falsche Prüfungsanforderungen | falsche Jahrgangs-/Standortregel; M/H | exakte Auswahl, Hierarchie, Kandidatengate, Hashfreigabe, Konfliktsperre | Originale/Gültigkeit bestätigen / Studiengang+Prüfungsamt | Regel-/Versions-/Konflikttests lokal bestanden | menschliche Fehlfreigabe; Originale/Freigabe offen |
| MOS-R2: DOI-/Bibliografie-Abfluss | Rechercheprovider; H/H | kein HTTP-Research-Client, lokale Public-Importe, IFC | getrennte öffentliche Beschaffung / Datenschutz+Research | sieben Provider-Denytests bestanden | Host-/Operatorfehlverhalten; Produktion gesperrt |
| MOS-R3: Arbeitsinhalt durch GROBID-Konsolidierung | Parserdienst/impliziter Crossref-Zugriff; M/H | Konsolidierung 0, Loopback-Konfig, IP-Pinning, internes Netz | Image-/Hostabnahme / IT+Security | Parameter-/DNS-/Redirect-/XML-Mocks, Compose-Prüfung bestanden | echtes GROBID nicht gestartet/vermessen; offen |
| MOS-R4: Parserexploit / Bibliotheksdaten | PDF/Office/XML/Archive; M/H | Größen-/Expansionslimits, Entities aus, keine Makros/externen Ressourcen | Sandbox/Malwareprozess / IT+Security | negative Importfixtures lokal bestanden | native Parserlücken; private Eingänge gesperrt |
| MOS-R5: falsche Quellenkritik durch Snapshots | Cachedateien/Metadaten; M/H | Originalhash beim Import/Start, Provenienz und Prüfumfang | Kurator/Lizenz-/Aktualitätsprüfung / Research | Digest-/Provenance-/Mismatchtests bestanden | veraltete/unvollständige Originaldaten; laufend |
| MOS-R6: unberechtigte Kritik / Prüfungsleistung | NOT_FOUND, interne Quelle, falscher DOI-/Semantikschluss; H/H | differenzierte Status, keine automatische Note, menschliche Bestätigung | Expertenreferenzen / Gutachter | interne/fehlende/falsche Metadatenfälle bestanden | tatsächliche Modellqualität ungemessen; offen |
| MOS-R7: Beeinflussung der Erstbewertung | API/UI-Resultate; M/H | gemeinsames Embargo, versionierte Entscheidungen | Bias-/Bedienungsstudie / Prüfungsverantwortliche | API-/UI-/Docker-E2E lokal bestanden | technische Unabhängigkeit beweist keine Biasfreiheit; offen |
| MOS-R8: unverwaltete Analyse / Kontexte | globale Taskreferenzlöschung; M/M | DELETE entfernt nur eigenen Task; TTL/Shutdown | Betrieb/Restoreprozess / Backend+IT | gezielter API-Regressionstest bestanden | Crash/Backups/Swap außerhalb Appgarantie; Codefehler behoben |

## Bestehendes Basis-Risikoregister

Stand: 2026-11-26. Qualitative Engineering-Einschätzung, keine gemessenen
Wahrscheinlichkeiten oder unterzeichnete Risikoannahme. Alle Owners sind vorgeschlagene
Rollen. Tatsächliche lokale Testergebnisse stehen ausschließlich in
[privacy_test_results.md](privacy_test_results.md); die Spalte Test benennt Verfahren,
keine zusätzliche Behauptung bestandener Hochschultests. Hoch = H, Mittel = M.

| Risiko / betroffene Daten | Wahrscheinlichkeit / Schaden | Technische Maßnahme | Organisatorische Maßnahme / Owner | Testverfahren | Restrisiko / Status |
|---|---|---|---|---|---|
| Externe LLM-Exfiltration: Arbeiten, Ableitungen | H / H | Defaultmock; zentraler Deny; kein Fallback; Dispatch-/Endpointbindung | Modell-/Infrastrukturfreigabe / Security+IT | test_external_model_blocking, canaries | Hostkompromiss; Produktion gesperrt |
| Suchanfragen verraten Firmen-/Forschungskontext | H / H | Recherche vollständig geschlossen, kein Client/Store | öffentliche Query unabhängig freigeben / Research+Datenschutz | test_research_gateway | Public-Gateway fehlt; geschlossen |
| Sperrvermerk nicht erkannt | H / H | jeder unbekannte Input RESTRICTED; lokaler Mehrquellendetektor | konkrete NDA-/Sperrprüfung / Prüfungsamt+Unternehmen | test_sperrvermerk | Bilder, OCR-Fehler, andere Formulierungen; echte Uploads gesperrt |
| Klassifizierungsverlust: Texte, Chunks, Gutachten | M / H | Maximumregel, immutable Label, serverseitige Ausgabeklasse | Klassifikationsprozess / Datenschutz+Backend | test_classification | zukünftige Adapterfehler; neue Pfade gesperrt |
| Prompt Injection / kodierte Exfiltration | H / H | keine Shell/Netztools, Schemas, Policy, Heuristik | menschliche Prüfung ohne automatische Notenstrafe / Security | test_agent_guardrails, canaries | semantische Manipulation; echte Modellqualität ungeprüft |
| Unsichere Subagenten / fremde Analysen | M / H | Parent-Teilmengen, gleiche Analyse/Klasse, scoped Dokumente | Agentenänderungen prüfen / Backend+Security | test_agent_permissions | Schadcode im Prozess kann umgehen; Hostgrenze nötig |
| Unautorisierter Benutzer / erratene UUID | H / H | Objekt-ACL, getrennte Berechtigungen, keine Admin-Inhaltsrechte | SSO und Zuweisungsprozess / Identitätsbetrieb | test_access_control, API-ID-Tests | nur Demoidentität, keine echten Mandanten; Produktion gesperrt |
| Unzureichende Netzisolation / DNS / IPv6 | H / H | interne Netze, IP-Pinning, Firewallvorlage, Mockstandard | Zielhost-/VPN-/Resolverabnahme / Hochschul-IT | Mocktransporttests; Dockerlistenerprobe; separate Hostpaketprüfung | Firewall nicht installiert, Zielhost ungeprüft; offen |
| Inhalte in allgemeinen Logs / Crash Reports | M / H | feste Auditfelder, Logger/Tracing aus, generische Fehler | Zugriff/Rotation, keine externen Reports / Betrieb+Datenschutz | test_data_leakage | Fremdcode/Hostlogs; produktive Auditintegrität offen |
| Inhalte in Backups / Snapshots / Swap | H / H | keine produktiven Inhalte, flüchtige Demoablage | verschlüsselte Backups, Fristen/Restore / IT+Archiv | Zielhostrestore und Speicherprüfung ausstehend | nicht durch App gelöscht; offen |
| Vertrauliches in GitHub / CI / Tickets | M / H | Git-/Docker-Ignores, DLP-Hook/CI, Build-Allowlist | Schulung, Code Review, Vorfallprozess / DevOps | DLP-Tests, Gitindexscan, Imageprüfung in CI | Geheimnisse in freiem Code/Text nicht sicher erkannt; offen |
| Unvollständige Löschung: Gutachten, Chats, Kontexte | M / H | TTL, DELETE, Taskabbruch, Orphan-Sweep | verbindliche Fristen und Restore-Löschkonzept / Datenschutz+IT | test_retention, scoped delete | physische Löschung nicht garantiert; offen |
| Unsichere Gewichte / Modell-Supply-Chain | M / H | Reviewmetadaten, kein Download/Remote Code zur Runtime | geprüfte Digest-/Lizenz-/Provenienzbelege / Modellsteward | Registrytests; tatsächliche Artefaktprüfung ausstehend | mutable Tags, unbestätigte Bytes; Produktion gesperrt |
| Dependency-/Image-Supply-Chain | M / H | Hashlocks, SHA-Actions, vorhandene Scanner | SBOM, Update-/Incidentprozess / DevOps | Ruff/Bandit; pip-audit/Trivy/Gitleaks in CI | neue Schwachstellen/Registrykompromiss; laufend |
| Unsicherer Administratorzugriff | M / H | kein rollenbasierter Inhaltsbypass in ACL | Least Privilege, Break-glass, Vieraugenprüfung / IT+Security | ACL-Rollentests; Hostabnahme ausstehend | Root kann Code/Speicher lesen; offen |
| Credentialdiebstahl / Identitätsspoofing | M / H | keine Clientheader vertraut, SecretStr, keine Proxyumgebung | SSO/MFA, Rotation, Secretmanager / Identitätsbetrieb | Konfig-/Fehlertests; SSO-Pentest ausstehend | SSO fehlt; Produktion gesperrt |
| Externe IDE-/Coding-Assistenten | H / H | echte Dokumente aus Repository/Images ausgeschlossen | keine Arbeiten/Logs/Screenshots an Assistenten / Projektleitung | DLP und manueller Arbeitsplatzreview | Benutzerkopien/Plugins nicht technisch vollständig kontrolliert; offen |
| Halluzination / unbegründete Kritik / falsche Quellen | H / H | Belegprüfungen, Unsicherheit, menschliche Finalisierung | Expertenvalidierung / fachliche Prüfungsverantwortliche | Evidence-/Human-gate-Regressionen | echte fachliche Qualität ungemessen; offen |
| Automation-/Identitätsbias | H / H | unabhängige Erstbewertung, spätes Ergebnisembargo, keine KI-Punkte | empirische Evaluation/Schulung / HAI+Prüfungsamt | bestehende Embargo-/UI-Tests | menschliche Übernahme falscher Befunde; Studie offen |
| Ressourcenüberlast / lokales Modell nicht verfügbar | M / M | Quoten/Timeouts/Abbruch; niemals Cloudfallback | Hochschulbetrieb und Wiederanlauf / IT | Budget-/Cancellationtests | Hostquoten/Mehrprozessbetrieb nicht abgenommen |

Keine Risikoakzeptanz ist erteilt. Nach Ownerbenennung pro Risiko einen überprüfbaren
Nachweis, Abnahmedatum, Verantwortlichen und Wiedervorlagetermin ergänzen. Für echte
Arbeiten bleiben die Blocker in `production_readiness.md` maßgeblich.
