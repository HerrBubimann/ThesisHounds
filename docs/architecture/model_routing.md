# Model routing and capability evidence

Beitrag: OFF-2/3/5, ENG-1. Der bestehende LLMGateway stellt `route` bereit; es gibt
keinen zweiten Modelltransport. Policy und Modellfreigaben werden zuerst geprüft,
dann Rolle, tatsächliche Discovery-Verfügbarkeit, Herstellerausschluss und explizite
RAM-/VRAM-Grenzen. Erst danach dürfen gemessene Aufgabenscores eine Auswahl bestimmen.
Die Policy wird unmittelbar vor der Inferenz weiterhin erneut geprüft.

Ein `CapabilityRecord` benötigt Modell-ID und exakten bereitgestellten SHA256-Digest,
Benchmarkversion, Daten-/Prompthash, Hardware-ID, Messzeit und Reviewnachweis.
Mock-, veraltete oder aufgabenfremde Messungen steuern keine Auswahl. Mehrdeutige
Datensätze und Scores außerhalb [0,1] werden abgelehnt. Gleiche Scores werden
reproduzierbar nach Modell-ID entschieden. Das prüft Metadatenkonsistenz und ersetzt
keine unabhängige Prüfung, ob ein Operator tatsächlich fachlich valide Scores importiert.

`config/model_capabilities.yaml` enthält bewusst keine Messwerte. Deshalb wird
`MANUAL_DEFAULT` mit Begründung und ohne empirischen Qualitätsanspruch zurückgegeben.
Die Standardzuordnungen bleiben in `agents.yaml`. Ist das bevorzugte Modell lokal
nicht verfügbar, kommt nur ein anderes durch dieselbe Policy erlaubtes Modell in
Frage; fehlen Kandidaten, endet der Aufruf kontrolliert. Keine externe Fallbackkette.

`inference_ram_limit_gib` und `inference_vram_limit_gib` in den ExecutionLimits sind
optionale Operatorgrenzen. Ohne bestätigte Inferenzhostdaten bleibt die Kapazität
UNMEASURED. Backend-RAM und belegter Ollama-VRAM sind keine freien GPU-Kapazitäten.
Die Model Registry enthält bisher Ressourcenabschätzungen, keine belegten Maxima.
`resources_verified` wird durch Operatorlimits allein nicht wahr.

Die Capability-Probes v2 decken elf Dimensionen ab: Textverständnis, Methodik,
Argumentation, Formalia, Quellen, Deutsch, strukturiertes JSON, Toolanforderungen,
Injection, Textbelege und Ressourcen. Automatisch gemessen werden Schemaerfolg,
Laufzeit, gemeldete Tokens und wörtliche Übereinstimmung. Fachliche Qualität benötigt
menschliche Adjudikation. Da die Runtime keinen Tool Executor freigibt, ist reguläre
Tool-Calling-Leistung ausdrücklich UNMEASURED. Ein verweigerter Shell-Aufruf ist
kein Nachweis umfassender Tool-Calling-Fähigkeit.

Tests: `test_model_routing.py`, `test_adversarial_verification.py`, bestehende
Gateway-/Privacytests. Echte Hersteller-/Modellvergleiche stehen weiterhin aus.
