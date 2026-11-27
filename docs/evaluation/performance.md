# Ressourcen und robuste Verarbeitung

OFF-2/3/5: Kosten werden im bestehenden Gateway/Assessment statt in einer parallelen
Laufzeit erfasst. Je Kriteriumsaufruf: Laufzeit, tatsächliche Modellaufrufe inklusive
Retries, gemeldete Tokens, Retries, Kontextbytes, konservative Inputreservierung und
Backend-RSS vorher/nachher. Gesamtbudgets behalten beobachtete/unklare Tokens und
Reservierungen; fehlende Usage ist keine gemessene Null. Provenance zählt zusätzlich
dynamische Agenten und Verifikationsrunden. Backend-RSS ist kein Inferenz-RAM.

Zusammengeführte Kriteriumsmetriken zählen Pflicht-, Zusatz- und Verifikationsaufrufe
sowie gescheiterte Zusatzversuche. `criterion_active_seconds` summiert die erfassten
Retrieval-/Modell-/Verifikationsphasen; es ist keine Gesamtwallzeit einschließlich
Wartezeiten, Indexaufbau oder optionalem Monitoring. A nutzt einen gemeinsamen
Batchaufruf: individuelle Kriteriumskosten bleiben dort `null`, gemeinsame
Batchkosten werden ausdrücklich markiert und nicht mehrfach als Aufrufe gezählt.
Ein Texttreffer aus einem ungeprüften Tabellen-/Bild-/Formelobjekt genügt nicht als
direkte fachliche Evidenz; diese Extraktionsgrenze führt zu menschlicher Klärung.

Ollamas gemeldete `load_duration` wird aus Nanosekunden in Sekunden umgerechnet.
Die Einheit ist durch die [Ollama-Chat-API](https://docs.ollama.com/api/chat) dokumentiert;
geladene Modelle/VRAM durch die [PS-API](https://docs.ollama.com/api/ps), geprüft 27.11.2026.
Wenn nicht gemeldet, bleibt sie `null`; Mockzeiten sind keine Modellladebenchmarks.
Optional aktiviert `capture_inference_resources` den vorhandenen gepinnten `/api/ps`-
Adapter nach Kriteriumsaufrufen. Geladene Modellbytes und VRAM sind ausdrücklich
**Post-Call-Snapshots**, keine physischen RAM-/VRAM-Peaks; bei sequenziellem Entladen
kann der Snapshot bereits leer sein. Fehlender Dienst ergibt UNAVAILABLE, keine
falsche Messung oder gescheiterte fachliche Bewertung. Standard ist aus, um unnötige
Statusaufrufe zu vermeiden. Reale Peaks brauchen einen separat abgenommenen lokalen Sampler.

Grenzen: `max_context_bytes`, `max_model_calls`, `max_tokens`, `max_retries`,
Agenten-/Run-Timeouts, Semaphore und `max_dynamic_agents`. Pflichtkriterien laufen
vor Zusatzagenten; E fordert solche nur bei Befundbedarf plus Thema an. Eine direkt
belegte Stärke benötigt nicht automatisch Zusatzaufrufe. Kein globaler vertraulicher
Ergebniscache; der Kontextindex lebt nur im einzelnen Review. Keine neuen Abhängigkeiten.

Nur transiente Schema-/Provider-/Timeoutfehler 502/503/504 werden begrenzt am selben
lokalen Ziel wiederholt. Policy-/Scope-/Budgetfehler werden nicht durch Retry oder
Providerwechsel umgangen. Jeder gestartete Versuch zählt. Ungültige Rohantworten
gehen nicht in Diagnosefelder ein. Eine dauerhaft gescheiterte Pflichtaufgabe
führt zur fehlgeschlagenen Analyse; optionale Fehler bleiben mit menschlichem
Klärungsbedarf sichtbar. Cancel/TTL/Delete/Shutdown behandeln weiterhin den ganzen
Assessmentdatensatz. Nach Neustart ist die RAM-Demoanalyse verloren, nicht erfolgreich
fortgesetzt; durable verschlüsselte Wiederaufnahme bleibt Produktionsarbeit.

Tatsächliche neue Messungen und Grenzen: [Advanced-Ergebnisse](advanced_review_results.md).
Es liegen keine reale Inferenzlast-, GPU-, Mehrbenutzer-, Zeitersparnis- oder
Kosten-/Nutzenmessung mit Gutachtern vor.
