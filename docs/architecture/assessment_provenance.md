# Herkunft und Konfiguration jeder Begutachtung

OFF-2/3/4/5: provenancegebundene Analyse und nachvollziehbare menschliche Entscheidungen.
`GET /api/v1/assessments/{id}/provenance` verlangt dieselbe Zuweisung und gemeinsame
Freigabe wie Vergleich und Evidence Explorer. Statuslisten zeigen keine Modell-
oder menschlichen Inhalte. Neue Datensätze übernehmen die höchste Schutzklasse.

Beim Anlegen wird ein unabhängiger Snapshot erzeugt: Dokument-ID und Seitenhash als
Dokumentversion, Katalog-ID/Version/Status/Hash, DHBW-Richtlinienstand samt Herkunft,
Appversion, Workflowversion, Agentenkonfiguration und Limits. Je Befund folgen
Modell-ID/-Digest, Quantisierung soweit belegt, Promptversion, Parameter, Routing,
Kontextauswahl, Ressourcen und Verifikationsstatus/-runden. Lokale tatsächlich
ausgeführte Metadatenchecks erfassen Provider, Snapshotdigest, Abruf-/Prüfzeit und
Prüfumfang. Noch nicht ausgeführte Recherche wird nicht als benutzt aufgeführt.
Menschliche Entscheidungen und Feedback bleiben versioniert daneben erhalten.

Git-SHA kann durch den kontrollierten Build-/Betriebsprozess als
`THESISHOUNDS_GIT_SHA` bereitgestellt werden. Nur vollständige 40-/64-stellige
Hexwerte werden übernommen und ausdrücklich als operatorgemeldet gekennzeichnet.
Ohne Nachweis steht `null/UNKNOWN`; der Agent erfindet keinen Commit für den
uncommitteten Arbeitsbaum. Dessen Zustand bleibt UNKNOWN. Quantisierung und reale
Gewichtsdigests fehlen entsprechend bei Mock-/nicht freigegebenen Artefakten.

Konfigurationsnachvollziehbarkeit ist keine bitgenaue Reproduzierbarkeit. Hardware,
Kernels, Quantisierung, Scheduler und Modellserver können Ergebnisse verändern.
Eine Temperatur von 0 garantiert keine identischen Antworten. Modellmanifest-
Digests beweisen zudem keine Integrität eines kompromittierten Inferenzservers.

Provenance und Feedback bleiben im zugewiesenen Assessment-RAM, erhalten dieselbe
TTL-/Cancel-/Delete-/Shutdownbehandlung und werden nicht automatisch exportiert,
trainiert oder für Fine-Tuning benutzt. Neustart bedeutet Verlust der Demoanalyse;
es gibt keine behauptete verschlüsselte Recovery-Datenbank oder Auditunveränderlichkeit.
Produktive dauerhafte Aufbewahrung verlangt gesonderte Hochschulabnahme.
