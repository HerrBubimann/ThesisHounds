# Lokales, dokumentbezogenes Kontextmanagement

Beitrag zu OFF-2/3/5: sichere Architektur, evidenzbasierte Analyse und überprüfbarer
Ressourceneinsatz. Integration in den vorhandenen `AISecondReviewer` und Challenge-
Pfad; keine zweite RAG-Plattform, Datenbank oder Modellverbindung.

`LocalContextIndex` verwendet die bestehende Document Intelligence. Er packt
zusammengehörige Sätze innerhalb von Absatz-/Kapitelgrenzen; lange Einzelsätze
werden hart begrenzt. Originalspannen, Seiten, Kapitel, Zuverlässigkeit, Analyse-ID,
Dokument-ID und Schutzklasse bleiben an den unveränderlichen Chunks. Kapitelanker
und Begriffsgruppen unterstützen kapitelübergreifende Auswahl. Das ist heuristisches
semantisches Chunking, keine gelernte Segmentierung oder zuverlässige PDF-Struktur.

Hybrides Ranking kombiniert Stichwortüberdeckung mit Cosinusähnlichkeit lokaler
128-dimensionaler Feature-Hash-Embeddings und einem kleinen DE/EN-Begriffslexikon.
Deterministisches Reranking bevorzugt Kapiteldiversität. Keine Gewichtsdownloads,
Cloudembeddings, Persistenz, Telemetrie oder externen Indizes. Diese Vektoren sind
**keine vortrainierten semantischen Embeddings**; Suchqualität, Lexikonabdeckung und
Hashkollisionen müssen mit freigegebenen Referenzpassagen geprüft werden. Der optionale lokale Encoderpfad ist inzwischen implementiert, benötigt aber
Artefakt-/Lizenz-/Privacyfreigabe und eigene Qualitäts-/Laufzeitnachweise. Ohne diese
bleiben gelernte Encoder explizit blockiert; Feature-Hash ist weiterhin die Baseline.

Jeder Index gehört genau einer Analyse und einem Dokument; fremder Scope wird
abgewiesen. Serverseitige `allowed_pages` schränken auch die erweiterte Suche ein.
Kriterium, erwartete Evidenz und kontrollierter fachlicher Fokus bilden die Anfrage;
keine menschliche Erstbewertung wird hineinkopiert. Es gibt keinen globalen Cache.
Dokumente über 2 MB oder mehr als 4096 Chunks werden kontrolliert abgewiesen.
Diese interne Grenze öffnet keinen echten Dokumenteingang.

`max_context_bytes` begrenzt die Auswahl. Zusätzlich wird der tatsächlich serialisierte
Prompt einschließlich JSON-Schema, UTF-8, Rollen, Gatewayreserve und Ausgabe gegen
das registrierte Modellfenster geprüft. Niedriger priorisierte Chunks werden entfernt;
passt schon der feste Prompt nicht, endet die Teilaufgabe mit Fehler. Leerer Kontext
ergibt explizit NOT_ASSESSABLE ohne semantischen Modellaufruf. Trace enthält IDs,
Spannen, Rankinggründe, geschätzte Tokens und Auswahlgröße; keinen globalen Inhaltsexport.
Das konservative Byteverfahren ist kein verifizierter modellspezifischer Tokenizer.

Ein Originalzitat außerhalb des ausgewählten Modellkontexts ist unzureichend belegt,
selbst wenn es im Dokument existiert. Keine Treffer beweisen keine Abwesenheit.
ABSENCE-Kandidaten lösen eine erweiterte lokale Suche aus und bleiben menschlich
zu klären; auch vollständiger Text beweist die semantische Abwesenheit nicht.
Challenge erhält gesondert ausgewählte Gegenkontexte und die gleiche Budgetgrenze.
Die einfache A-Baseline ist bewusst ein einzelner begrenzter Batchprompt.

Identitätsheader auf der ersten Seite können lokal längenerhaltend maskiert werden.
Bewertungsrelevante Firmen-/Methodeninformationen im Fließtext bleiben erhalten.
Keine allgemeine Anonymisierung oder Deidentifizierung wird behauptet. Originalzitate
werden weiterhin gegen das lokale Original geprüft. Siehe [Fairness](../evaluation/fairness.md).

## Ergänzung vom 28.11.2026

FTS5 verwendet jetzt eine threadgeschützte, wiederverwendete RAM-Verbindung je
Dokument mit explizitem Lebenszyklus. Ein zusätzlicher Vergleichspfad kann nach
Artefakt-/Laufzeitfreigabe lokale Qwen3-/E5-/BGE-M3-Encoder hinzunehmen. Er verbindet
Fundstellen mit RRF, ohne den bestehenden Standardretriever oder fachliche Urteile
automatisch zu ersetzen. [Konfiguration, Limits und offene Nachweise](../research/parallel_scientific_checks.md).
