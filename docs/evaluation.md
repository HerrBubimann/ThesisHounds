# Wissenschaftliche Evaluation: Verfahren und Grenzen

Stand: 28.11.2026. Es gibt zwei getrennte Vergleichswege:
Legacy-Runs A–D und das kriteriumsbezogene CLI-Labor A–E. Sie dürfen nicht als
identische Experimente zusammengefasst werden. Vorhandene Resultate sind
technische Mock-/Synthetiknachweise, keine bestätigte fachliche Modellqualität.

## Gemeinsames Kriterienlabor A–E

`backend/app/evaluation/lab.py` verwendet dieselben Dokument-/Katalogdaten und
den vorhandenen `AISecondReviewer`. Architektur, Variation, Wiederholung und
Ablation bleiben im Ergebnis unterscheidbar.

| Architektur | Vergleichsbedingung |
|---|---|
| A | ein begrenzter Batchprompt |
| B | spezialisierter Ablauf mit einem Modell |
| C | feste Zuordnung mehrerer lokaler Modelle |
| D | zusätzliche kontrollierte adaptive Spezialisten |
| E | adaptiver Ablauf mit evidenz-/befundabhängiger unabhängiger Gegenprüfung |

Gemeinsame Privacy-, Budget-, Kontext- und Belegkontrollen bleiben erhalten.
`baseline`, `no_retrieval`, `no_dynamic` und `no_verification` sind explizite
Laborbedingungen, keine Sicherheitsschalter der Benutzeroberfläche.

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.evaluation.lab --provider mock --repeats 1 --output-dir reports/evaluation
```

Unter POSIX `PYTHONPATH=backend .venv/bin/python -m app.evaluation.lab …` verwenden.
Reports enthalten tatsächliche Aufrufe, Fehler, Laufzeit, Tokenmetadaten und
verfügbare Ressourcen-/Evidenzdaten. Das globale Aufrufbudget bleibt begrenzt.
Anleitung: [Ablationen](evaluation/ablation_studies.md),
[Experimentdesign](evaluation/experiment_design.md).

## Legacy-Runs A–D

Der separate LangGraph-Orchestrator hinter `/api/v1/runs` besitzt einen anderen
Versuchsaufbau: A einfacher Prompt, B homogene feste Hierarchie, C heterogene
Hierarchie mit Modellreview, D dynamische AgentSpecs mit Review und Belegprüfung.
Supervisorzahl, Aufrufzahl und aktivierte Prüfungen unterscheiden sich.
Diese Unterschiede isolieren keinen einzelnen kausalen Einflussfaktor.

`validated_count` zählt dort mechanisch bestätigte Zitate, keine fachlich korrekten
Urteile. `unsupported_count` kombiniert ablehnende Beleg-/Modellprüfungen und ist
keine unabhängig erhobene Halluzinationsrate.

## Tatsächlich verfügbare Messungen

- Gateway-Aufrufversuche, begrenzte Wiederholungen und reservierte Tokenbudgets.
- Vom Provider gemeldete Tokens und Dauern; fehlende Werte bleiben unbekannt.
- OS-CPU/RAM, Backend-RSS und gegebenenfalls Ollama-Modell-VRAM-Snapshots.
  Sie sind keine vollständig isolierten Modell-/Containerpeaks.
- Originalbelegzustände, Kriterienabdeckung und offene Konflikt-/Prüfkandidaten.
- Modell-/Prompt-/Dokument-/Katalogherkunft, Routing und Agentenbeziehungen.
- Modellbenchmark v3: begrenzte Dispatchparallelität, optionale Streamingmessung,
  Tokenrate und Zeit bis zum ersten nicht leeren Inhaltsfragment.
  Diese Fragmentzeit ist **keine exakte TTFT**.
- Gutachterwerkzeuge: mechanische Kandidaten-/Gruppenzahlen und Qualitätsmetriken
  ausschließlich bei passenden menschlichen Adjudikationen. Explizite Sitzungszeit
  ist kein Nachweis von Aufmerksamkeit oder Zeitersparnis.

Die Oberfläche **Evaluation Lab** besitzt noch keine Report-HTTP-Schnittstelle.
Sie zeigt deshalb keine erfundenen Benchmarks. Modellfähigkeitseinträge bleiben
leer, solange keine überprüften, digestgebundenen Messungen vorliegen.

## Menschliche Referenzbewertungen

Precision, Recall, F1, unberechtigte Kritik und fachliche Evidenzqualität benötigen
explizite, dokument-/kataloggebundene Referenzurteile mit festgelegten Matchingregeln.
Ein Zitat, eine Modellmehrheit oder ein korrektes JSON-Schema ist kein Goldlabel.
Mindestens zwei unabhängige Fachbewertungen und dokumentierte Konfliktadjudikation
sind im Studienprotokoll vorgesehen, aber nicht als durchgeführte Studie belegt.

Warm-/Cold-Start, Modellrevision/Digest, Quantisierung, Kontext, Hardware, Datensatz,
Prompts und Fehlversuche sind bei echten Vergleichen zu kontrollieren.
Ohne passende Referenzen bleiben Qualitäts- und Zeitersparnismetriken `null`.

[Modellbenchmarks](evaluation/model_benchmarks.md) ·
[Gutachterwerkzeuge](research/reviewer_productivity_tools_2026-11-28.md) ·
[Letzter vorhandener Prüfnachweis](validation.md)
