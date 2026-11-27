# Privacy architecture

Erneutes Security-Folgeaudit: [Maßnahmen, Scans und Nachweisgrenzen](hardening_results.md).
Frontend-IP-Pinning, eigenständige Bereitstellungszone, volle Modellmanifest-Digests,
Bibliografie-IFC und Request-/Antwortlimits ergänzen die nachstehenden Kontrollen.

Ergänzung 27.11.2026: Die [Mosbach-Wissensbasis](../dhbw/assessment_profiles.md)
und [lokale Quellenprüfung](../research/research_privacy.md) erweitern ausschließlich
die öffentliche/synthetische Entwicklungsbasis. Neue Parser-/Importpfade sind kein
Realdokumenteingang. Interne Kataloge und private GROBID-Aufrufe bleiben gesperrt.
Keine neue Netzwerkroute zu Rechercheprovidern wurde geöffnet.

Stand: 2026-11-26. Einstieg: [Gap Analysis und Plan](gap_analysis.md),
[Produktionssperren](production_readiness.md), [Testnachweise](privacy_test_results.md).

## Verbindliche Grenze

Wissenschaftliche Arbeiten und alle Ableitungen verlassen niemals die autorisierte
Verarbeitungsumgebung. Benutzer, LLMs und Agenten können diese Regel nicht aufheben.
Öffentliche Herkunft muss unabhängig feststehen; Anonymisierung ist keine Freigabe.
Auch INTERNAL darf nicht extern verarbeitet werden. In diesem Repository bleibt
zusätzlich jede öffentliche externe Modellverarbeitung deaktiviert.

## Implementierter Zustand

- `Settings.security_mode`: nur DEVELOPMENT startet. UNIVERSITY_SECURE,
  PUBLIC_RESEARCH und EXPERIMENTAL_PUBLIC werden serverseitig abgelehnt.
- Die App verwendet einen deterministischen `DemoProvider` ohne Netzwerk-/Datei-I/O.
  Dieser simuliert Abläufe, keine fachliche Modellleistung. Kein Modellfallback.
- Nur das serverseitige synthetische Dokument ist adressierbar; keine Uploadroute,
  kein privater PDF-/OCR-/persistenter Vektordatenbankpfad. Freier `/chat` ist gesperrt;
  ausschließlich das feste Signal `Test` ist zugelassen.
- Lokale Textchunks und Feature-Hash-Vektoren bleiben im analyse-/dokumentbezogenen
  Reviewkontext. Kein externer Embedder oder globaler Index. Feedback/Provenance
  unterliegen ACL, Erstbewertungs-/Ergebnisembargo, höchster Klasse und Parent-TTL.
  Keine automatische Trainingsnutzung oder Feedbackaggregation.
- `Classification`: PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED; unbekannt/fehlend
  ergibt RESTRICTED. SYNTHETIC ist Herkunft, keine zusätzliche Schutzklasse.
- `InformationLabel` ist unveränderlich, verbindet Quellen nur innerhalb einer
  Analyse und übernimmt deren höchste Klasse. Gateway und Agentenkontexte setzen
  die Klasse serverseitig; Modellantworten können sie nicht ändern.
- `PolicyEngine` ist der obligatorische Modelladapter der `PrivacyPolicyEngine`.
  Der aktuelle Adapter erlaubt nur freigegebene PUBLIC-Demonstrationen. Die
  zusätzliche Entscheidung REQUIRE_AUTHORIZED_APPROVAL ist keine Benutzerfreigabe.
- `OllamaProvider` verlangt einen Gateway-Dispatchkontext. Externe Ziele,
  unbekannte Ports/Downloads, Redirects und manipulierte Client-Basisadressen
  werden blockiert. Der produktive App-Client verwendet IP-Pinning ohne Proxy-Umgebung.
- Agenten erben Datenklasse, Analyse, Dokument-, Modell-, Tool- und Zielmengen.
  Die Registry prüft Parentgrenzen zusätzlich zur Factory; keine Shell/Code-/Netztools.
- Objekt-ACLs prüfen Identität, Zuweisung und einzelne Berechtigungen. Rollen
  verleihen keine Inhaltsrechte. Die Demoidentität ist ausdrücklich **kein SSO**.
- Freie menschliche Kommentare/Fragen sind RESTRICTED. Ihre Weitergabe an Modelle
  bleibt gesperrt. Eine ausdrücklich bestätigte menschliche Prüfung ohne Modell
  erhält den anschließenden Begutachtungsablauf.
- Inferenz-/Create-/Delete-Audit enthält nur erlaubte technische Metadaten.
  Allgemeine HTTP-/Tracinglogs sind unterdrückt, Fehler generisch, API-Antworten no-store.
- Speicherung außerhalb des Source-Repositorys, exklusive UUID-Dateien, TTL,
  Shutdown-Cleanup, Orphan-Sweep und explizite Delete-Endpunkte.
- Vor jedem CI-Artefaktupload werden Reports auf die synthetischen Canary-Marker
  einschließlich Base64/Hex und Chunkgrenzen geprüft. Bei Treffer oder fehlender
  Prüfbarkeit scheitert der Job und der Upload wird gesperrt.

## Vertrauensmodell und Grenzen

Benutzer-HTTP-Header, Dokumenttexte, Modellantworten und Agentenspezifikationen
begründen keine Autorität. Quellcode, Betreiberkonfiguration und Hostadministration
sind vertrauenswürdig vorausgesetzt. Python im selben Prozess ist keine Sandbox:
ein kompromittierter Host oder beliebiger Schadcode könnte Prüfungen manipulieren.
Daher bleiben Betriebssystemisolation, Default-Deny-Egress, verschlüsselte Speicher,
TLS-Serviceidentitäten, SSO und organisatorische Freigaben verpflichtend.

Die nftables-Datei ist eine **nicht installierte Vorlage**. Ein Docker-Netzwerkname,
ein grünes CI oder `deployment_type=LOCAL` beweist keine Hochschulfreigabe.
Der Hochschulstack verweigert deshalb zurzeit den Start. Ein echtes SSO, sichere
Parserprozesse, durable Mandantenspeicher und produktive Schlüsselverwaltung sind
geplant und nicht als implementiert ausgewiesen.
