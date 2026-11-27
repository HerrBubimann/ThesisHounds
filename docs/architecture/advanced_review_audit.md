# Advanced Review: Audit und priorisierter Verbesserungsdurchlauf

Stand 27.11.2026, vor dieser Erweiterung. Grundlage: vorhandene App-/Agenten-/
Assessment-/LLM-/Knowledge-/Research-/Security-/Evaluation-/UI-/Infrastrukturmodule,
Professorenfeedback und Traceability. Die ursprüngliche Projekt-PowerPoint liegt
nicht vor; OFF-1 bis OFF-5 bezeichnen die dokumentierte übergebene Aufgabenstellung.
Keine institutionelle Freigabe oder gemessene reale Modellqualität wird unterstellt.

| Bereich | Tatsächlicher Ausgangszustand | Lücke / Entscheidung |
|---|---|---|
| FastAPI/Streamlit und LangGraph/Assessment | synthetischer vertikaler Ablauf implementiert, unabhängiger Erstreview, Embargo, menschliche Schlussfreigabe | erhalten; neue Diagnose-/Feedbackdaten erst nach gleichem Embargo |
| Document Intelligence | Seiten-/Absatzspannen, Kapitel und Warnungen implementiert | keine Retrievalindizes; volle Seiten in jedem Kriteriums-/Challengeprompt / P0 |
| Embeddings/RAG | nicht vorhanden | begrenzter lokaler In-Memory-Index, klassifizierte Spannen, ohne Download oder neue Dienste / P0 |
| Wissenschaftliche Konsistenz | Promptaufforderung, keine strukturierte Beziehungsausgabe | Kapitelanker und nachvollziehbare Beziehungskandidaten; keine automatische Kritik aus Leerstellen / P0 |
| AgentFactory/Registry/ExecutionEngine | Rechte, Tiefe, Quoten, Timeout/Retry implementiert | im Assessment thematische Zusatzagenten ohne Befundbedarf; vorhandene Factory weiterverwenden / P0 |
| Multi-LLM/Gateway/Router | lokale Adapter, Kontext-/Tokenbudget, Semaphore und Digestchecks implementiert | Auswahl-/Promptkontext und Kriteriumsmetriken zusammenführen / P0 |
| Evidenz/Challenge | Quoteprüfung, max. zwei unabhängige Herstellerreviews, Konflikte bleiben erhalten | reichere Evidenztypen/-zustände, Gegenbelege und sichtbare Eskalationsgründe / P0 |
| Human Feedback | Kriteriumsentscheidungen und akademische Accept/Reject-Versionen | einzelne Modellbefunde nicht strukturiert korrigierbar; Ablehnungsgründe fehlen / P1 |
| Provenance | verstreute Modell-/Routing-/Regel-/Auditdaten | gemeinsamer snapshotgebundener Herkunftsdatensatz mit expliziten UNKNOWNs / P1 |
| Monitoring | Backend-RSS/CPU, Gesamtbudgets, Lablaufzeit | kriteriumsbezogene Dauer, Kontext, Aufrufe, Wiederholungen; Inferenz-RAM/VRAM unbekannt / P1 |
| Robustheit | Transaktionsgrenze, generische Fehler, Cancel/TTL/Delete, Server-RAM | Teilfehlerdiagnose und menschliche Klärung; kein Restore versprechen / P0 |
| Evaluation | A–E-Mockläufe, Variation/Repeat, HumanReferenceSet, Privacyablation | Gender-/Notenerwartungsvarianten, Einzelkomponentenablation, reichere Paarmetriken / P1 |
| DHBW-Wissen/Formalien/Quellen | lokale Public-Importe, Kandidaten-/Hash-/Versionsgate, lokale Snapshots implementiert | offizielle Gültigkeit und Expertenreferenzen offen; keine Parallelrecherche bauen |
| GROBID/Modelle/Hochschulbetrieb | Adapter/Compose vorhanden, reale Gewichte/Parser/Hochschule nicht abgenommen; Defaultmock | nicht als real getestet ausgeben; Freigabesperren erhalten |
| Privacy/ACL/CI | vier Klassen, IFC, IP-Pinning, DLP/Canaries, verbindliches Gate implementiert | alle neuen Kontexte/Feedbacks ableiten und scopen; bekannte Image-CVEs bleiben offen |

Keine zweite Agent Factory, Datenbank, Modelltransport- oder Bewertungsarchitektur.
Legacy-Orchestrator bleibt die vorhandene Vergleichsbasis; der kriteriumsweise
Assessmentpfad ist der Integrationspunkt. Lokale Citation-/Snapshotprüfungen werden
nicht durch Retrieval oder Modellkonsens ersetzt.

Reihenfolge: (1) Kontext/Scope/Budgets und Regressionen, (2) Evidenz/Konsistenz und
bedarfsgebundene Eskalation, (3) Provenance/Feedback/UI, (4) Fairness/Ablation und
Messgrenzen, (5) vollständige Tests und lokaler Docker-Nachweis. Neue Features sind
bis zum tatsächlichen Test keine bestandenen Abnahmen. Ergebnisse werden im
Advanced-Review-Ergebnisbericht nachgeführt.

Abgeschlossener technischer Durchlauf: [Lieferstand und tatsächliche Nachweise](../evaluation/advanced_review_results.md).
Die Ursprungstabelle ist der Audit vor Umsetzung und keine aktuelle Liste weiterhin
fehlender Module. Fachliche Modellqualität und institutionelle Voraussetzungen
bleiben ausdrücklich offen.
