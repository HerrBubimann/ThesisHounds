# Prompt Injection und Bewertungsintegrität

## Aktueller Stand, 27.11.2026

Der bestehende PDF-/Assessmentpfad, die Agent Factory, die ExecutionEngine und das
LLM-Gateway wurden erweitert. Es gibt keinen zweiten Orchestrator und keine neue
privilegierte Toolausführung. Die Verarbeitung echter vertraulicher Arbeiten bleibt
gesperrt. Ein kompromittiertes Modell erhält durch seine Antwort keine zusätzlichen
Rechte; eine fachlich manipulierte, formal gültige Antwort bleibt trotzdem möglich.

Implementierung: `backend/app/security/document_security.py`,
`injection_detection.py`, `tool_permissions.py`, `backend/app/llm/gateway.py`,
`backend/app/workflows/assessment_workflow.py`. [PDF-Grenzen](pdf_security.md),
[Agentengrenzen](agent_security.md), [Benchmarks](../evaluation/prompt_injection_benchmark.md),
[tatsächliche Prüfergebnisse](../evaluation/security_results.md).

### Erkennung und Entscheidung

Der Scanner prüft deutsche/englische Instruktions-, Rollen-, Kriterien-, Noten-,
Modell-, Tool- und Exfiltrationsmuster. NFKC und Entfernung von Unicode-Cf-Zeichen
gelten nur für die Erkennung; Originaltext und Belegoffsets bleiben erhalten.
Kodierte Inhalte werden markiert, nicht beliebig dekodiert/ausgeführt. Eine
wissenschaftliche Beispielkennzeichnung senkt den Verdacht, gewährt aber keine
Rechte. Der synthetische Benchmark zeigt ausdrücklich, dass diese Kennzeichnung
zur Umgehung der Quarantäneheuristik missbraucht werden kann.

`SecurityFinding` bindet ID, Dokument-ID/-Hash, Seite/Abschnitt, Erkennungsmethode,
Originalauszug/Offsets, Kontext, Risiko, Klassifizierung und Handlungsempfehlung.
Verdacht, technisch blockierter Aufruf und bestätigter Vorfall sind getrennte
Felder. Automatisch erzeugte Befunde haben `INDICATOR_ONLY` und
`confirmed_incident=false`; sie beweisen weder Angriff noch Täuschungsversuch.
PDF-Metadaten-/Layoutbelege besitzen gegebenenfalls keine Textoffsets; ihr Abschnitt
und der Original-PDF-Hash bleiben nachvollziehbar.

Zustände: `NO_INDICATOR_FOUND`, `SUSPICIOUS`, `MANUAL_REVIEW_REQUIRED`,
`QUARANTINED`, `BLOCKED`, `HUMAN_REVIEWED`. Kein Indikator bedeutet keine
Sicherheitsgarantie. Quarantäne/Prüfbedarf pausieren KI-Start, Ergebnisfreigabe und
Finalisierung. Bei überschrittenem Scanlimit ist das Dokument `BLOCKED`; ein
abgeschnittener Bericht kann nicht zur Weiterverarbeitung freigegeben werden.
Maximal 199 Dokumentbefunde reservieren einen der 200 Reviewplätze für einen
optionalen Klassifikatorbefund.

### Menschliche Prüfung ohne automatische Notenwirkung

`GET /api/v1/assessments/{id}/document-security` liefert Details erst nach der
unabhängigen menschlichen Erstbewertung. Technische Importfehler erscheinen sofort;
ein pausierter KI-Start liefert vorher nur den generischen Prüfbedarf. Die UI
`frontend/assessment_review.py` zeigt Auszüge als Text, Ursache und alternative
Erklärung. Eine explizite Entscheidung mit Begründung/Bestätigung gilt exakt für
die aktuellen Finding-IDs. Neue Befunde erfordern eine erneute Prüfung.

`POST .../document-security/review` benötigt Objektzugriff und Reviewrecht.
Private Klassifizierung, Sperrvermerk und `BLOCKED` sind nicht übersteuerbar.
Entscheidungen enthalten Akteur/Zeitpunkt und sind selbst `RESTRICTED`.
Sie verändern keine Kriterienurteile, Punkte oder Noten. Maximal 20 Revisionen;
die Analyseablage bleibt flüchtig und ist kein revisionssicheres Produktionsaudit.
Einheitlich positive KI-Befunde bei Sicherheitsindikatoren verlangen zusätzliche
Verifikation und menschliche Klärung; auch übereinstimmende Modelle beweisen nichts.

### Sämtliche derzeitigen Übergänge nicht vertrauenswürdiger Inhalte

| Eingang → Entscheidung/Prompt | Konkreter Pfad | Kontrolle / verbleibende Grenze |
|---|---|---|
| PDF → Text/Metadaten/Layout | `backend/app/services/pdf_security.py`, `pdf_worker.py`, `document_store.py`; `knowledge/importer.py` | gemeinsamer begrenzter Kindprozess, Original-/Texthash; keine aktive Ausführung/URL-Auflösung; kein vollständiger OS-Sandboxnachweis |
| Seiten → Struktur/Chunks/Kriteriumskontext | `services/document_intelligence.py`, `context_management.py` | begrenzte, dokumentgebundene Ausschnitte; abgeleitete Struktur ist weiter nicht vertrauenswürdig; kein OCR |
| Ausschnitte → semantischer Plan → AgentSpec | `agents/adaptive_assessment.py`, `agent_factory.py`, `agent_registry.py` | strukturierte Vorschläge, Originalreferenzen, feste Rechte/Quoten/Parent, Quarantäneprüfung; Fachnotwendigkeit nicht wissenschaftlich validiert |
| Dokument/Kriterien → Pflichtreview/Spezialisten | `assessments/ai_review.py`, `agents/academic_review.py`, `core/execution_engine.py` | feste Systemrollen, untrusted Datenfelder, Gateway/Firewall, serverseitige Pflichtcoverage und Evidenzprüfung |
| Modellbefund/Vorrunden → unabhängige Gegenprüfung | `validation/cross_model_review.py`, `assessments/ai_review.py` | Schemata, Originalbelege und Kriteriumsbindung; Modellkonsens ist keine Wahrheit |
| Bibliografie/Import/Paper → Quellenreview | `research/citations.py`, `snapshot_store.py`, `local_verification.py`, `agents/research_quality.py` | Klasse/Scope bleiben gebunden; Quellenmaterial im Datenfeld, Zitatabgleich; Metadaten beweisen keine Publikationsqualität |
| Externe Recherche → Kontext | `research/gateway.py`, `provider_registry.py` | Runtime-Recherche bleibt geschlossen; kein HTTP-Research-Client; statische lokale Public-Snapshots bleiben untrusted |
| Legacy-Plan/Delegation/Analyse/Synthese | `core/execution_engine.py` | feste serverseitige Zwecke und Ausführungsmechanismen, aktueller Agent/Owner/Scope, validierte Antworten; kein aus JSON ausführbarer Code |
| Menschlicher Kommentar → Diskussion | `workflows/assessment_workflow.py` | freie Texte RESTRICTED, KI-Diskussion weiterhin gesperrt; keine Verwertung als Systemanweisung |
| Befunde → Gutachtenentwurf | `workflows/assessment_workflow.py`, `assessments/provenance.py` | manuelle Entscheidungen/Finalisierung und Originalbelege; kein automatischer Notenentscheid |
| OCR/Bilder → Prompt | kein aktivierter OCR-/Renderingpfad | NOT_IMPLEMENTED; Bildanweisungen und OCR-Mismatch nicht geprüft |
| GROBID-TEI → Struktur | `services/grobid.py` | bestehender optionaler gepinnter Adapter, Konsolidierung aus; kein echter Dienst-/Image-/Hostnachweis dieser Iteration |

Auch JSON-Felder und Modellantworten bleiben Daten. Stringquotierung allein hält
einen LLM nicht davon ab, Inhalt als Anweisung zu interpretieren. Die technische
Grenze liegt in den fest programmierten, serverseitig erlaubten Operationen.

### Optionale lokale semantische Erkennung

Der optionale Schlüssel `semantic_injection_model_id` in `config/execution.yaml`
ist nicht gesetzt; `ExecutionLimits` verwendet standardmäßig `None`.
`optional_semantic_check` verwendet ausschließlich den vorhandenen lokalen
Gateway-/Reviewerpfad nach Artefakt-, Herkunfts-, Lizenz-, Digest- und
Sicherheitsfreigabe. PUBLIC-only; keine externen Inference-APIs, Tools oder
Notenbefugnisse. 1.500 Zeichen Ausschnitt, 256 Ausgabetokens, gemeinsames Budget;
der Ausschnitt ist explizit unvollständig. `BENIGN` erteilt keine Freigabe;
`SUSPICIOUS`/`UNKNOWN` beziehungsweise Ausfall erfordern menschliche Prüfung.
Status, Mockkennzeichnung und tatsächlich versuchte Aufrufe bleiben unterscheidbar.

Dies ist ein optionaler generativer Revieweradapter, kein installierter
Prompt-Guard-/DeBERTa-Klassifikator. Es wurden keine Gewichte heruntergeladen oder
freigegeben, keine realen Klassifikatorwahrscheinlichkeiten gemessen.

| Untersuchte Kandidaten | Primärquelle / dokumentierte Eigenschaften | Offene Entscheidung |
|---|---|---|
| Meta Prompt Guard 86M | [Model Card](https://huggingface.co/meta-llama/Prompt-Guard-86M): Llama-3.1-Lizenz, 512 Tokens, mehrsprachige Angaben einschließlich Deutsch | konkrete Revision/Digest, institutionelle Lizenzprüfung, RAM/VRAM/Latenz und lokale DE/EN-FPR/FNR fehlen |
| ProtectAI DeBERTa v2 | [Model Card](https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2): Apache-2.0, Englisch, Beispieltrunkierung auf 512 Tokens; archiviert/nicht mehr gepflegt | Pflegezustand und deutsche Qualität sprechen gegen ungeprüfte Aktivierung; Revision/Digest und Hardwaremessung fehlen |

Modellkartenaussagen sind keine ThesisHounds-Messwerte. Die Kandidaten sind
`BLOCKED_BY_EXTERNAL_REQUIREMENTS`; ein passender nativer Klassifikatoradapter
ist `NOT_IMPLEMENTED`.

### Fachliche Bezugspunkte

Recherchierte Primärquellen, Stand der Prüfung 27.11.2026:
[OWASP Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html),
[OWASP LLM01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/),
[NIST AML-Taxonomie](https://www.nist.gov/publications/adversarial-machine-learning-taxonomy-and-terminology-attacks-and-mitigations),
[MITRE-Zuordnung AML.T0051.002](https://d3fend.mitre.org/offensive-technique/attack/AML.T0051.002/).
Verwendet werden ihre Trennung von Angriffspfad, zusätzlichen Detektoren und
deterministischer Rechtebegrenzung. Daraus folgt keine Zertifizierung oder
vollständige Abdeckung eines Standards.

## Historischer Ausgangsstand

Dokument, Metadaten, Bibliografie und importierte Publikationen sind nicht
vertrauenswürdige Daten. Systeminstruktionen bleiben getrennt, Tools/Shell/Netzwerk-
Aufrufe entstehen nicht aus Dokumenttext. AgentSpecs, Rechte, Modelle, Dokument-IDs
und Budgets werden serverseitig geprüft. Unteragenten erben höchstens die Rechte
ihres Parents. Privacy/IFC und Netzgrenzen gelten unabhängig vom Modellgehorsam.

Der lokale Detektor meldet unter anderem Instruktions-/Notenmanipulation, externe
Übertragung, Klassifizierungsänderung und unsichtbare Unicode-Zeichen. Er ist eine
Heuristik mit False Positives/Negatives. Gefundene Signale werden als Sicherheitsbefund
erst nach der unabhängigen Erstbewertung sichtbar; sie erzeugen keine automatische schlechtere Note.
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
