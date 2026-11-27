# Benchmark: Quellenextraktion und Verifikation

Reproduzierbarer Einstieg:

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.evaluation.academic_benchmark --output reports/academic-benchmark.json
```

Sechs synthetische Fälle: PA1, PA2 und BA jeweils mit numerischen Einzelzitaten und
einfachen Autor-Jahr-Zitaten. Gleiche handgeschriebene Ground Truth: zwei Referenzen,
eine interne Quelle, ein fehlender Referenzkandidat, passende und gezielt veränderte
Metadaten. Dies sind **keine API-Ergebnisse** und keine realen Prüfungsleistungen.

Das Skript führt den tatsächlichen lokalen Parser und Verifikator aus. Pro Fall
werden genaue Tupel aus Eintrag-ID/Autor/Jahr/DOI und normalisierte Zitaterwähnungen
gegen bekannte synthetische Sollmengen verglichen. Berichtet werden TP/FP/FN,
Precision, Recall und F1; zusätzlich positive/negative Metadaten- und interne Quellenfälle.
Die Fall- und Implementierungsgrenzen stehen im JSON; CI führt denselben Benchmark offline aus.

Beobachteter lokaler Lauf 27.11.2026: alle sechs Fälle bestanden; in diesen engen
Fixtures Reference-/Citation-Extraction jeweils Precision/Recall/F1 = 1,0.
Das ist **keine** repräsentative Genauigkeit für DHBW-Arbeiten. Layout, mehrzeilige
Literatur, Mehrfachautoren, Fußnoten, Zitatbereiche, Bücher ohne DOI, OCR und GROBID
sind damit nicht bewertet. Die Güte echter lokaler LLMs und semantische Aussagenstützung
bleiben ungemessen.

Nächster empirischer Nachweis vor Produktionsfreigabe: unabhängig annotierter,
rechtmäßig verfügbarer synthetischer/public Korpus mit unterschiedlichen Zitierstilen;
auf Dokumentebene gesplittete Entwicklung/Testdaten; getrennte Auswertung von Parser,
Metadatenmatch und fachlichem Urteil; Konfidenzintervalle und Fehlertypen berichten.
Keine vertraulichen Arbeiten in GitHub Actions.
