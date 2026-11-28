# Data classification and information flow

| Klasse | Beispiele | Grenze |
|---|---|---|
| PUBLIC | ausdrücklich freigegebene Paper, bibliografische Metadaten, serverseitige synthetische Fixtures | nur ausdrücklich zugelassene Dienste; externe Verarbeitung hier deaktiviert |
| INTERNAL | unveröffentlichte Hochschulrichtlinien/Bewertungsraster | ausschließlich autorisierte interne Umgebung |
| CONFIDENTIAL | Unternehmensarbeiten, personenbezogene Daten, Gutachten | ausschließlich autorisierte interne Umgebung |
| RESTRICTED | neue/unbekannte Arbeiten, Sperrvermerk, NDA, Geschäftsgeheimnisse | ausdrücklich dafür freigegebene Sicherheitsumgebung und zugewiesene Personen |

Implementiert in `backend/app/security/classification.py`. Unbekannte Werte,
falsche Groß-/Kleinschreibung, fehlende Werte und das frühere Label SYNTHETIC
werden RESTRICTED. Für die serverseitige synthetische Fixture wird PUBLIC
explizit gesetzt; das ist keine pauschale Anerkennung einer Clientbehauptung.

`combine` bildet das Maximum. `InformationLabel.derive` bewahrt Analyse-ID,
Quell-Dokumente und höchste Klasse; unterschiedliche Analyse-IDs werden abgelehnt.
Es gibt keine automatische Herabstufung oder Entklassifizierung nach Fristablauf.
Die Policy erlaubt keine externe Verarbeitung durch Zustimmung im UI.

Die Metadaten gelten für Dokument, Prompt, Antwort, Befund, Agent und Export.
Auch DOI-Kandidaten, Zitationsnennungen und Bibliografieeinträge tragen Klasse,
Analyse-ID und Dokument-ID. Bibliografieeinträge sind unveränderlich; fehlende oder
ungültige Labels werden RESTRICTED. Metadatenprüfungen bilden das Maximum aller
Eingangsklassen, Quellenreviews prüfen zusätzlich den Scope des Eintrags und
verwenden dessen Klasse auch beim Modellrouting. Öffentliche Quellenmetadaten
stufen eine vertrauliche Bibliografie nicht herab.
Menschliche freie Eingaben erhalten RESTRICTED, auch in einer synthetischen Analyse.
Dokumentbasierte KI-Zweitbewertung erhält keine menschlichen Inhalte und kann
deshalb nur das zugelassene PUBLIC-Dokument sehen: synthetische Fixture oder
registrierte öffentliche Pilotdatei. Diskussion und gemischte
Berichte übernehmen dagegen RESTRICTED. Strukturierte Modelloutputs enthalten
keine autoritative Klassifizierung; der Server ergänzt sie nach der Validierung.

Lokale Textchunks und Feature-Hash-Embeddings tragen jetzt unveränderliche Klasse,
Analyse-ID und Dokument-ID. Der Index lebt ausschließlich im einzelnen Review;
kein globaler Cache und keine externe Embedding-API. Fremde Analysen/Dokumente
und nicht freigegebene Seiten werden auch bei erweiterter Suche ausgeschlossen.
OCR, persistente Vektorspeicher und private Dokumentparser sind weiterhin nicht
freigegeben. Vor deren Einführung bleibt dieselbe Label-/Scopeprüfung verpflichtend.
Siehe [Kontextmanagement](../architecture/context_management.md).
