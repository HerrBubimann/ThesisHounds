# Reproduzierbare Prompt-Injection-Control-Ablation

Stand 27.11.2026. `backend/app/evaluation/injection_benchmark.py` verwendet nur
synthetischen Text. Zwölf manipulierte Fälle besitzen jeweils eine saubere
Kontrolle; zusätzlich eine legitime wissenschaftliche Sicherheitsbeschreibung.
Das ergibt 25 Eingaben × fünf Varianten = 125 Ergebniszeilen. Die zwölf sauberen
Kontrolltexte sind identisch; dies ist kein vielfältiger akademischer Korpus.

```powershell
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe -m app.evaluation.injection_benchmark --output reports/document-security-2026-11-27/injection-benchmark.json
```

| Variante | Tatsächlich ausgeführt | Simulierter Angriffserfolg | Reale LLM-ASR |
|---|---|---|---|
| A | hypothetisch gehorsamer Memory-Mock ohne Schutz | 12/12 | nicht gemessen |
| B | gleiches hypothetisches Verhalten trotz Securityprompt | 12/12 | nicht gemessen |
| C | echte Quarantäneheuristik, verbleibende Aktion nur Memory-Sink | 2/12 | nicht gemessen |
| D | semantische Inferenz nicht ausgeführt, explizit null | nicht gemessen | nicht gemessen |
| E | echte registrierte scoped Agentidentität und Tool-Firewall, Angriff verlangt unerlaubte Shellaktion | 0/12, zwölf Aufrufe abgelehnt | nicht gemessen |

E ist eine enge Firewall-Control-Ablation, kein vollständiger empirischer Test
der Netzwerkisolation oder der gesamten mehrschichtigen Architektur. A/B führen
keinen echten Prompt-/Systempromptvergleich durch. D wird als
`SEMANTIC_NOT_EXECUTED` gespeichert. Sämtliche realen ASR-/semantischen Raten und
fachlichen Qualitätswerte bleiben `null`; `scientific_evaluation_complete=false`.

### Beobachtete Erkennung und Umgehungen

Quarantäneheuristik: 10/12 Angriffe erkannt, 2/12 nicht erkannt, 0/13 Kontrollen
quarantänisiert. Im Report heißt dies `rule_detection_rate=0.8333…`,
`rule_false_negative_rate=0.1666…`, `rule_false_positive_rate=0`.
Diese Zahlen beziehen sich auf die Quarantäneentscheidung, nicht auf jedes
niedrigriskante Scannersignal. Ein legitimes Angriffszitat kann als Verdacht
erscheinen, ohne die Quarantäne auszulösen.

Die Base64-Anweisung und das als wissenschaftliches Angriffsbeispiel getarnte
Kommando umgehen diese Heuristik. C erreicht damit zweimal den simulierten
Memory-Sink; E verweigert die unerlaubte Aktion auch ohne Erkennung. Das zeigt
den Unterschied zwischen Erkennen und Verhindern, keine allgemeine Robustheit.
Keine Konfidenzintervalle oder populationsbezogene FPR/FNR-Aussage aus diesem
kleinen, selbst entworfenen Korpus ableiten.

PDF-Metadaten-/Unicode-Kategorien dieser Ablation sind Textrepräsentationen.
Wirkliche synthetische PDFs mit versteckten Textebenen/Metadaten werden separat
in `tests/security/test_secure_document_gateway.py` verarbeitet. Bildinjektion,
OCR-Manipulation und Render-/OCR-Paare fehlen. Eine vollständige gepaarte
PDF-/Bild-/Literaturstudie mit Fachlabels ist offen.

Tatsächliche unautorisierte Hostaktionen und externe Transfers sind im Report
null, weil der Memory-Sink technisch keine ausführen kann. Das ist kein
Hostnetzwerkbeweis. Laufzeit pro Zeile wird lokal gemessen; keine belastbare
Peak-RAM-/VRAM-, Energie- oder Modelllatenzmessung. Kontrollbewertungen,
Befundqualität und Bewertungsverschiebungen sind nicht gemessen. Es gibt keinen
automatischen Notenpfad, dessen Robustheit damit bewiesen wäre.

### CI und nächste wissenschaftliche Abnahme

Der CLI-Lauf hängt im bestehenden obligatorischen `privacy-security`-Job von
`.github/workflows/ci.yml`. Exitcode wird bei fehlerhaften Pflichtkontrollen
ungleich null. Bericht und Privacy-JUnit sind explizit freigegebene Artefaktpfade,
vor Upload erfolgt der bestehende Canarycheck. `thesishounds-ci-gate` verlangt
weiterhin alle Pflichtjobs einschließlich Dockerbuild; Coveragegrenze bleibt 80 %.
Probabilistische Modellbenchmarks werden dadurch nicht als CI-Erfolg fingiert.

Für eine echte A–E-Studie: identische freigegebene lokale Artefakte/Digests,
gepaarte vielfältige PDF-/Bildfälle, unabhängig geprüfte Angriff-/Fachlabels,
wiederholte Läufe mit Seeds/Parametern, negative Kontrollen und gemessene
Ressourcen. Unsichere Varianten ausschließlich mit synthetischen Daten und
isolierten Mockzielen. Keine echten Arbeiten oder verdächtigen Auszüge an
Cloudscanner, OCR-/Inference-APIs oder öffentliche Tickets senden.
