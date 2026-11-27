# Semantische adaptive Prüfplanung vom 27. November 2026

Die Zusatzplanung im bestehenden AssessmentWorkflow verwendet jetzt strukturierte
LLM-Vorschläge statt thematischer Regex-Treffer als Standardentscheidung. Das ist
eine implementierte technische Integration mit kontrollierten Mocknachweisen.
**Eine tatsächlich ausgeführte, freigegebene lokale Modellinferenz und ein fachlicher
Qualitätsgewinn sind nicht nachgewiesen.** Modellartefakte, bestätigter
PA1-Experimentkatalog und Referenzbewertungen fehlen weiterhin. Die bestehenden
[Produktionssperren](../security/production_readiness.md) bleiben gültig.

## Bestehender Ausführungspfad

`AISecondReviewer.review` bearbeitet und validiert zuerst sämtliche Pflichtkriterien.
Erst danach ergänzt `agents/adaptive_assessment.py::plan_specialists` die Planung
für Architektur D/E. Es entsteht kein weiterer Orchestrator. Die Legacy-LangGraph-
Demo bleibt ein eigener historischer Forschungs-/Demopfad und wird dadurch nicht
zum primären Assessment umgebaut. Der lokale Pilot sperrt ihre Run-Erstellung weiter.

Bei E kann die vorhandene Evidenzeskalation bereits feststellen, dass kein weiterer
Spezialist gebraucht wird. Dann gilt NOT_NEEDED_BY_REVIEW; ein zusätzlicher LLM-Aufruf
entfällt. Andernfalls plant das über `config/agents.yaml::orchestrator_model`
bevorzugte, durch Router und Policy tatsächlich zugelassene Modell. Ein leerer
Agentenplan mit Begründung ist ebenfalls ein gültiges Ergebnis.

Der vorhandene LocalContextIndex liefert ein budgetbegrenztes, gekennzeichnetes
Teildokument. Der Planner bekommt Katalog-IDs/Beschreibungen und untrusted Spans
mit eindeutigen IDs. Er erhält keine menschliche Erstbewertung, Kommentare,
Entscheidungen, freie Toolauswahl oder Referenz auf den Humanreview-Speicher.
Der Kontextindex bleibt eine lokale Heuristik und wird nicht als semantisches
Embeddingmodell ausgegeben. Vollständiges Verständnis langer Arbeiten wird nicht
aus einem begrenzten Kontextfenster abgeleitet.

## Strukturierte Methodeneinordnung und Vorschläge

`SemanticPlan` enthält `understanding`, `agents` und eine Begründung. Die Einordnung
umfasst Forschungsfrage, Zielsetzung, Fachgebiet, Methodik, Verfahren mit
APPLIED/MENTIONED/UNCLEAR, Datengrundlage, Versuchsaufbau, Herausforderungen und
relevante Kriterien-IDs. Nicht verfügbare Angaben bleiben UNKNOWN. Es werden keine
neuen amtlichen DHBW-Kriterien aus Modellantworten erzeugt.

Jeder `SpecialistProposal` enthält eine freie fachliche Bezeichnung, konkrete Aufgabe,
Notwendigkeitsbegründung, Kriterien-ID, Methoden-ID, Textreferenzen, erwartetes
Ergebnis, benötigte Router-Aufgabentypen, Werkzeuge und Ressourcenbudget. Die
fachliche Bezeichnung kann beispielsweise eine konkrete Vergleichbarkeitsprüfung
beschreiben, ohne dass dieses Fachgebiet in einer Templateenum existieren muss.
Die ausführbare Sicherheitsrolle bleibt `specialist`, die Kategorie stammt aus
dem tatsächlichen Kriterienkatalog.

Ein Modell darf weder Modell-ID, Supervisor, Pythoncode, Toolschema, Netzziel noch
Delegationsrecht in diesen Vorschlag einfügen. Unbekannte Felder werden abgelehnt.
Der Server baut daraus den bestehenden `AgentSpec`: kurzer serverabgeleiteter ID,
Name, begrenzter Task, Kategorie, geroutetes Modell, passender Parent und Budget.
Factory und Registry prüfen ihn erneut. Der Parent gibt ausschließlich das vom
Server ausgewählte Modell und das gebundene Dokument frei. Blätter können nicht
delegieren. Die Registry hält Quoten und Parent-/Kind-Scope ein.

## Serverseitige Kontrollen

| Kontrolle | Tatsächlicher Vertrag |
|---|---|
| Methodengebrauch | Ein Agent muss auf ein vorhandenes APPLIED-Verfahren verweisen; MENTIONED/UNCLEAR rechtfertigen keinen Zusatzagenten |
| Kriterienbindung | Vorschlagskriterium muss im verwendeten Profil stehen; Kategorie wird daraus abgeleitet |
| Quellenbindung | Referenzspanne muss im tatsächlich ausgewählten Kontext liegen, zuverlässig sein und ein eindeutiges, exaktes Originalzitat enthalten |
| Nachvollziehbare Position | Seite, Start/Ende und Analyse-/Dokument-ID werden aus Originaltext und Kontextindex abgeleitet; keine erfundenen Modelloffsets |
| Notwendigkeit | rationale und expected_result erforderlich; identische Kriterien-/Methoden-/Aufgabenpaare werden auch bei anderen IDs abgelehnt |
| Rechte | Nur document.read, bestehende lokale Modellpolicy; keine Programmausführung oder Netzwerkerweiterung |
| Ressourcen | Höchstens zwei Planvorschläge standardmäßig; Gesamtquote unverändert; individuelle Calls, Ausgabetokens, Kontextbytes und Laufzeit dürfen Servergrenzen nur unterschreiten |
| Gemeinsame Kosten | Planung, Zusatzprüfungen, Retries und Gegenprüfungen verwenden dasselbe CallBudget; kein Budgetreset |
| Modelle | Vorhandener Router/Gateway; gemessene Zuordnung nur bei passenden Digests und Nachweisen für alle angeforderten Aufgabentypen, sonst MANUAL_DEFAULT |
| Fehlversuche | Schema-/Beleg-/Budgetfehler werden mit generischem Status abgelegt; keine rohe ungültige Modellantwort in Logs/Provenance |
| Prompt Injection | Erkannte Dokumentangriffe blockieren Zusatzplanung in beiden Varianten; verdächtige erzeugte Aufträge werden abgelehnt; keine Rechtegewährung aus Dokumentanweisungen |
| Humanreview | Pflichtbefunde bleiben erhalten; Planungsfehler erfordern menschliche Klärung; Freigabe/Finalisierung und Embargo bleiben serverseitig |

APPLIED ist weiterhin eine Modellbehauptung. Ein echtes Zitat kann falsch als
angewendete Methode interpretiert sein und belegt keine fachliche Notwendigkeit.
Injection-Erkennung und Instruktionstrennung geben keine Garantie gegen alle
semantischen Angriffe. Die harten Rechte-, Tool-, Scope- und Ausführungsgrenzen
bleiben deshalb auch bei einem überzeugend formulierten Plan verbindlich.

Ein Spezialist bekommt einen strukturierten Zusatzauftrag und den dazu begrenzten
Dokumentkontext. Eine exakte Quelle in der Planung garantiert keinen korrekten
späteren Befund: dessen Evidenz wird erneut mit den bestehenden Kontrollen geprüft.
Supplemente hängen getrennt am zugehörigen Pflichtbefund. Sie ersetzen keine
Pflichtkriterien und führen keine automatische Note ein.

## Konfiguration und Betriebszustände

In `config/execution.yaml`:

```yaml
adaptive_planning_mode: semantic
adaptive_planning_fallback: none
max_planned_specialists: 2
```

Alternativen sind `off` und `regex_baseline`. Ein optionaler Fallback
`adaptive_planning_fallback: regex_baseline` gilt nur bei Nichtverfügbarkeit/Timeout
(503/504). Er wird EXPLICIT_REGEX_FALLBACK_NOT_SEMANTIC genannt. Ein abgelehnter
Plan, ein Privacy-/Scopefehler oder ein ausgeschöpftes Budget führen nicht zu einem
verdeckten Ersatzplan. In der Evaluation erfüllt dieser Fallback den semantischen
C-Arm nicht.

Weitere Zustände sind VALIDATED_PROPOSAL, REJECTED_REQUIRES_HUMAN,
UNAVAILABLE_REQUIRES_HUMAN, NO_CONTEXT_REQUIRES_HUMAN und
BLOCKED_INJECTION_REQUIRES_HUMAN. Ein konfigurierter semantischer Modus bedeutet
keine erfolgreiche Planung. `mocked` kennzeichnet Provider-Simulation; die Demo
liefert ausdrücklich ein leeres Verständnis mit Mockbegründung.

Der Plan mitsamt Modellrouting, Kontextwahl, Kosten, Vorschlägen und ausgeführten
AgentSpecs steht nach Freigabe in der geschützten Provenance. Die bestehende
Reviewansicht zeigt unter „Analyseherkunft und Ressourcen“ nach dem Abruf auch
Methodengebrauch, Begründungen und exakte Originalspannen. Vor Freigabe sind diese
Daten weder in Status noch in generischen Agentenlisten sichtbar. Die Ablage bleibt
flüchtig mit den bisherigen Retention-/Neustartgrenzen.

## A/B/C Vergleich im bestehenden Lab

Die neuen **Planungsvarianten** sind von den bereits vorhandenen Architekturarmen
A–E zu unterscheiden:

| planning_variant | Gemeinsamer fester Kern | Zusatzplanung |
|---|---|---|
| A | vorhandener kriteriumsweiser D-Kern und identischer Katalog | off: keine adaptiven Spezialisten |
| B | gleicher Kern, Dokumente, Kriterien und Zuordnung | ausdrücklich regex_baseline |
| C | gleicher Kern, Dokumente, Kriterien und Zuordnung | semantic über bestehenden lokalen Provider |

Diese Varianten dürfen nur mit `architectures=["D"]` und Baselineablation kombiniert
werden. Die CLI setzt D entsprechend; sie benennt die historischen Architekturarme
nicht um. Zusatzmodelle können nach Vorschlagsfähigkeiten geroutet werden; ihre
Identität/Digests und MANUAL_DEFAULT/MEASURED-Zuordnung müssen im Vergleich
berücksichtigt werden. Gemeinsame Budgets begrenzen alle Bedingungen. Ein
unverfügbarer oder abgelehnter C-Plan ergibt PLANNING_INCOMPLETE, kein erfolgreiches
Realexperiment. Konsistenzgruppen trennen Dokument-, Katalog- und Planungsvariante.

Das Lab erfasst Anzahl vorgeschlagener/erstellter/abgeschlossener Spezialisten,
Befunde, Evidenz, Calls, Tokens, Dauer und Backendressourcen. GPU-/Inferenzhostpeaks
bleiben ohne Messung leer. `HumanReferenceSet` kann zusätzlich
`required_specialist_ids` und `specialist_adjudications` mit Vorschlagshash,
Relevanzentscheidung und zugeordneten Referenz-IDs tragen. Fachliche Relevanz,
unnötige und fehlende notwendige Spezialisten bleiben ohne diese Adjudikation null.
Die vorhandenen fachlichen Befundmetriken benötigen weiterhin eigene vollständige
menschliche Adjudikationen. Keine synthetische Falldefinition wird automatisch zum
Expertenlabel.

## Reproduktion mit synthetischen Daten

PowerShell im Repositoryroot, vorhandene Python-3.12-Umgebung:

```powershell
.venv/Scripts/python.exe -m pytest tests/unit/test_semantic_planning.py tests/unit/test_model_routing.py tests/integration/test_semantic_planning.py -q
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe -m app.evaluation.lab --provider mock --planning-variants A B C --repeats 2 --output-dir reports/semantic-planning-2026-11-27/mock-cli
$semanticCorpusPath=Join-Path $env:TEMP ('ThesisHoundsSemanticCorpus-' + [guid]::NewGuid().ToString('N'))
.venv/Scripts/python.exe -m app.evaluation.academic_benchmark --planning-cases --pilot-corpus-dir $semanticCorpusPath --output reports/semantic-planning-2026-11-27/corpus.json
```

Der optionale Korpus v2 ergänzt die ursprünglichen sechs Fälle um beiläufige
Methodenbegriffe und ein ohne typische Templatebegriffe beschriebenes Verfahren.
Er erzeugt sieben analysierbare PDFs; die künstlich vertrauliche achte Kontrolle
bleibt gesperrt. Die bisherige Korpus-CLI ohne `--planning-cases` bleibt unverändert.
Ein Mehrdokumentvergleich über `--document-ids` setzt weiterhin den tatsächlich
bestätigten Experimentkatalog und registrierte Dateien voraus; Testfreigaben werden
nicht als Operatorfreigaben übernommen.

Der Integrationstest vergleicht zwei tatsächliche PDFs × drei Planungsvarianten ×
zwei Wiederholungen. Antworten sind ein expliziter Fixture-Lookup. Unterschiedliche
Agentenzahlen zeigen damit lediglich, dass die drei Pfade technisch getrennt und
bewusst gesteuert ausgeführt werden können. Sie belegen keine bessere semantische
Erkennung, Genauigkeit oder Wirtschaftlichkeit eines realen Modells.

Für einen Realvergleich müssen Modell-/Lizenz-/Digest- und Katalogbelege vorliegen.
`config/models.yaml` verlangt tatsächliche Einsatz-, Lizenz- und Securityentscheidungen,
Version, Herkunft, vollständigen Manifestdigest und passenden lokalen Endpunkt.
Der PA1-Katalog muss PUBLIC/EXPERIMENT mit tatsächlicher fachlicher Bestätigung sein.
Die vorhandenen Pilotsettings sind `INFERENCE_MODE=local_pilot`, `PILOT_MODEL_ID`,
`PILOT_PROFILE_ID`, `PILOT_DOCUMENT_DIR` außerhalb des Repositorys sowie gegebenenfalls
`CONFIG_DIR` für die geprüfte Konfigurationskopie. Der Endpoint muss mit
`OLLAMA_BASE_URL` und Registryfreigabe übereinstimmen. Die aktuelle Konfiguration
enthält diese tatsächlichen Freigaben nicht; Testfixtures sind kein Ersatz.
Danach dieselben Dokumente und Kriterien
einfrieren, Menschen unabhängig referenzieren/adjudizieren lassen und den
bestehenden Aufruf mit `--provider ollama` ausführen. Keine neue Modellfreigabe,
kein Modell-/Hardwaredownload und keine Hochschulfreigabe wurden hier erzeugt.
