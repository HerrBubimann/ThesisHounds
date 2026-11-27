# Network isolation

Security-Folgeaudit: Auch der synchrone Frontendclient prüft alle DNS-Antworten und
verbindet sich anschließend mit der geprüften numerischen Backend-IP. Nur feste
lokale Hosts/Ports sind erlaubt; Redirects, Proxyumgebung, Query-/Fragment-Tricks
und beliebige Clientoptionen werden abgewiesen. Das eigenständige Online-Projekt
`compose.provision.yaml` enthält keine Verarbeitungsdienste/-netze. Es darf nur mit
einem nicht aktiven Modell-Volume verwendet werden. Die tatsächliche lokale
Prüfung und deren Grenzen stehen im [Hardening-Bericht](hardening_results.md).

Ergänzung 27.11.2026: `compose.grobid.yaml` definiert ein zusätzliches internes
Parsernetz ohne IPv6, öffentliche DNS-Auflösung, Hostports oder Dokumentenmount.
Der optionale Adapter ist IP-/Port-/Pfad-gepinnt. Die sechste Compose-Variante wird
statisch geprüft; ein echtes GROBID-Image wurde nicht betrieben. Dessen Host-/Egress-
Abnahme bleibt offen. Die bestandene Drei-Namespace-Probe betrifft ausschließlich
den Backend-/Frontend-/Ollama-Mockstack.

## Gelieferte Konfiguration

`compose.yaml` verbindet Frontend und API über das interne Netz 172.30.10.0/24,
API und Ollama über das interne Netz 172.30.20.0/24. Feste Adressen: Frontend
172.30.10.3, Backend 172.30.10.2 / 172.30.20.2, Ollama 172.30.20.3. Nur die UI
ist an Host-Loopback gebunden. Backend und Ollama veröffentlichen keine Ports.
Die Netze haben kein IPv6; Backend/Frontend nutzen explizite Hosteinträge.
Upstream-DNS zeigt auf Container-Loopback ohne Resolver. Docker-interne
Namensauflösung, Host-/Gatewaypfade und IPv6 sind trotzdem bei der Abnahme zu prüfen.

Container laufen ohne Capabilities, schreibgeschützt und ohne Docker-Socket.
Ollama hat Cloud/History/Debug deaktiviert. Die Standard-App nutzt ausschließlich
den In-Process-Mock; sie kontaktiert auch Ollama nicht. Der separate Ollama-Adapter
erlaubt nur fest eingetragene lokale Ziele/Ports und feste API-Pfade. DNS-Ergebnisse
müssen vollständig in der erlaubten IP-Menge liegen; die Verbindung wird auf die
geprüfte IP umgeschrieben. Keine zweite DNS-Auflösung, Proxy-Umgebung oder Redirects.
Das ist kein Schutz gegen beliebigen Schadcode auf dem Host.

## Hostmaßnahmen: Vorlage, nicht angewendet

`infrastructure/security/firewall/private-zone.nft` beschreibt Default-Deny für
ausgehenden Verkehr beider privater Subnetze. Hochschul-IT muss vor Anwendung
Interfaces, Docker-Firewallbackend, Bridgefilter, Host INPUT/OUTPUT, VPN, etablierte
Verbindungen, IPv6/Link-local, DNS und Verwaltungszugänge prüfen. Mit `nft --check`
validieren; vorhandene Regeln niemals pauschal flushen. Die Vorlage enthält keine
Host-INPUT-/OUTPUT-/Docker-Resolver-Vollabsicherung und ersetzt keine Standortregeln.
Linux-Hostregeln wirken bei Docker Desktop gegebenenfalls nur in der VM.

`compose.university.yaml` benutzt weiterhin ein extern administriertes Netz. Sein
Netzname ist **kein** Isolationsbeweis. SECURITY_MODE=UNIVERSITY_SECURE verweigert
bis zur Implementierung und Abnahme der fehlenden Adapter den Start.

## Nachweisverfahren

1. CI startet ausschließlich synthetische Services und einen kontrollierten
   öffentlichen Mocklistener. `infrastructure/security/scripts/network_acceptance.py`
   prüft dessen Erreichbarkeit positiv und erwartet danach Verbindungsablehnung
   aus allen drei privaten Netzwerk-Namespaces. Eine zusätzliche Positivkontrolle
   führt den echten IP-gepinnten Ollama-Adapter nur gegen den internen HTTP-Mock
   mit dem festen PUBLIC-Verbindungssignal aus. Jeder nicht interne Runtimeanschluss,
   fehlende Service oder erfolgreiche Verbindung lässt die Prüfung fehlschlagen.
2. Unit-/Securitytests prüfen DNS-Manipulation, IP-/Port-/Protokollwechsel,
   Proxyumgebung, Redirects und direkte Providerumgehung mit kontrollierten Mocks.
3. **Separat auf dem Zielhost:** paketbasierter Nachweis für TCP/UDP, DNS-Tunnel,
   direkte IPs, IPv6, Webhooks, alternative Ports, Container→Host, externe Proxys,
   Ollama-Cloud und Telemetrie; Positivkontrolle der erlaubten Verbindungen.
   Nur kontrollierte Testziele und synthetische Marker verwenden. UI-Browser
   einschließlich Webfonts, WebSocket und Cache im echten Browser untersuchen.

Aktueller Status und tatsächliche Ausführung stehen in `privacy_test_results.md`.
Eine Config-Prüfung oder CI-Probe ersetzt keine Hochschulnetzabnahme.
