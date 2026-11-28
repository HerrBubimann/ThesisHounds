# Frontendsicherheit und Datenschutz

FastAPI ist die Autorität für Zugriff, Embargo, Klassifikation, Sperrvermerke,
Werkzeugnutzung und Produktionssperren. Eine versteckte oder deaktivierte UI-Aktion
ersetzt keine Backendprüfung. Der neue Listenpfad liefert nur erlaubte Metadaten;
Quellen-/Vergleichs-/Belegpfade behalten die unabhängige Erstfreigabe.

Die Browseransicht verwendet keine externen Fonts, Analyse-Tracker, Cloud-PDF-Dienste,
Modellprovider oder dokumentabhängigen öffentlichen Suchlinks. Der optionale offizielle
`streamlit-pdf==2.1.0`-Viewer wird mit gehashten Locks eingebunden; Worker, Zeichentabellen
und Standardfonts liegen im Wheel. Übergeben werden geprüfte Bytes, keine fremden URLs.
Original-PDFs mit Sicherheitsindikatoren erhalten nur die separate Textansicht.

Dokumente, Fragen und Befunde werden als Text dargestellt. Eigenes HTML verwendet
escaped Labels. Graphviz verwendet feste Rollen-/Statuslabels statt modellverfasster
Namen. Keine Browserpersistenz für Dokumente, Prompts, Bewertungen oder Zugangsdaten.
Keine automatische Wiederholung schreibender Requests, kein automatisches Absenden
an Hochschulsysteme und kein Frontendschalter für Modellfreigaben.

Statuscodes werden in sichere lokale Fehler übersetzt. Rohes Provider-HTML,
Stacktraces und Antwortpayloads werden nicht angezeigt. Backendantworten tragen
`no-store` und `no-referrer`; Telemetrie bleibt abgeschaltet.

DEVELOPMENT verwendet eine gemeinsame Demo-Identität. Hochschul-SSO, produktive
Benutzertrennung, Infrastrukturabnahme und organisatorische Freigabe bleiben offen.
Ein lokaler Test ist keine Netzwerkabnahme oder DSGVO-Gesamtprüfung. Der Security
Center kennzeichnet diese Grenzen; Verdachtsfälle verändern nicht automatisch
die wissenschaftliche Bewertung.
