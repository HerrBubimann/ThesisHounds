# Capability benchmark protocol and matrix

Beitrag: OFF-2/3/5, ENG-1. `app.evaluation.model_benchmark` erweitert die vorhandenen
Probes auf elf Dimensionen. Registry-Schätzungen sind keine Benchmarkergebnisse.

| Dimension | Automatische technische Beobachtung | Erforderlicher fachlicher Nachweis |
|---|---|---|
| wissenschaftliches Textverständnis | gültiges Antwortschema | Expertenurteil über Forschungsfrage/Fazit |
| Methodik | strukturiertes Urteil auf synthetischem Text | richtige Grenzen der Methode, keine unberechtigte Kritik |
| Argumentation | konsistenter Output auf Widerspruchsfixture | tatsächliche argumentative Tragfähigkeit |
| Formalia | sichtbarer Text-/Strukturbezug | freigegebener Katalog, gegebenenfalls überprüfte PDF-Extraktion |
| Quellen | kein behaupteter Online-Nachweis | Quellen-/Versions-/Inhaltsprüfung mit geprüften Daten |
| Deutsch | Antwort im strukturierten Format | fachliche und sprachliche Bewertung durch Experten |
| Structured Output | Schemaerfolg/-fehler | nicht gleich inhaltliche Richtigkeit |
| Tool Calling | unerlaubte Toolausführung bleibt gesperrt | legitime Tool-Calling-Fähigkeit UNMEASURED, kein Executor freigegeben |
| Prompt Injection | eingehaltene Struktur und technische Toolgrenze | fachliche/inferenzspezifische Robustheit auf unabhängigen Angriffen |
| Evidenz | exakte Zitat-/Textübereinstimmung | fachliche Begründung und Gegenkontext |
| Ressourcen | Laufzeit, gemeldete Tokens, Backend-Samples | Inferenzhost-RAM/VRAM/Leistung separat messen |

Ausgelieferte Capability-Matrix für Qwen/Mistral/Llama: **keine realen Qualitäts-
oder Ressourcenscores vorhanden**. Die drei Tags sind manuelle Konfigurationswerte.
Mock-Probes dürfen keine Rangfolge dieser Modellfamilien erzeugen.

Beispiel für die synthetische technische Prüfung:

```powershell
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m app.evaluation.model_benchmark --provider mock --models qwen mistral llama --repeats 2 --output reports/model-capabilities-mock.json
```

Der getrennte lokale Aufruf `--provider ollama` nutzt ausschließlich bereits lokal
vorhandene Modelle und den IP-gepinnten, freigegebenen Endpoint; keine Downloads,
keine externe API und kein Umgehen des Production Gates für echte Arbeiten.
Vorher Lizenzen, Artefakte, Modell-Digests und Hardware abnehmen. Stabile Gewichte,
quantisierte Variante, Dataset-/Prompthash, Softwarestand und Betriebseinstellungen
dokumentieren. Gemessene Qualität erst nach menschlichem Review in die Capability-
Records übernehmen; die Software erfindet diese Scores nicht automatisch.
