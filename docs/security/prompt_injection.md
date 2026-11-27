# Prompt Injection und unerlaubte Kritik

Dokument, Metadaten, Bibliografie und importierte Publikationen sind nicht
vertrauenswürdige Daten. Systeminstruktionen bleiben getrennt, Tools/Shell/Netzwerk-
Aufrufe entstehen nicht aus Dokumenttext. AgentSpecs, Rechte, Modelle, Dokument-IDs
und Budgets werden serverseitig geprüft. Unteragenten erben höchstens die Rechte
ihres Parents. Privacy/IFC und Netzgrenzen gelten unabhängig vom Modellgehorsam.

Der lokale Detektor meldet unter anderem Instruktions-/Notenmanipulation, externe
Übertragung, Klassifizierungsänderung und unsichtbare Unicode-Zeichen. Er ist eine
Heuristik mit False Positives/Negatives. Gefundene Signale werden als Sicherheitsbefund
erst nach dem Bewertungs-Embargo sichtbar; sie erzeugen keine automatische schlechtere Note.
Die vollständige visuelle Erkennung versteckter PDF-Texte ist nicht implementiert.

Der Quellenqualitätsreview sieht nur die zugewiesene Passage, den zugehörigen Eintrag,
lokales Material und eine aktive Regel. Er erhält keine menschliche Erstbewertung und
keine Recherchewerkzeuge. Quellenzitate werden nach dem Modellaufruf lokal abgeglichen.
Ein passendes Zitat validiert weder Interpretation noch wissenschaftliche Qualität.

`app.evaluation.privacy_lab` vergleicht 12 synthetische Szenarien in vier kontrollierten
Memory-Sink-Adaptern. A/B enthalten bewusst keine technisch wirksame Schranke;
der B-Mock ignoriert Instruktionen deterministisch. C/D testen echte Policy-/IFC-/Ziel-
Prüffunktionen. Das ist eine Control-Ablation, **kein** empirischer LLM-Robustheitsbenchmark.
Paraphrasierte/kodierte Lecks sind durch einen bloßen Canary-Stringtest nicht vollständig abgedeckt.
Tatsächliche Host-/Modelltests und ein vielfältiger Angriffskorpus bleiben erforderlich.

Fachliche Grundlage: [BSI, Generative KI-Modelle](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/KI/Generative_KI-Modelle.pdf?__blob=publicationFile&v=7),
abgerufen 27.11.2026; Empfehlungen sind kein projektspezifischer Sicherheitsnachweis.
