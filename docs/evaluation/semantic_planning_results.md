# Semantische adaptive Planung Prüfstand vom 27. November 2026

Die [semantische Zusatzplanung](../architecture/semantic_adaptive_planning.md)
ist im bestehenden Assessment-, Factory-, Router- und Labpfad integriert.
**Geprüft ist die Software mit kontrollierten Modellantworten, nicht die fachliche
Überlegenheit eines realen Modells.** Es wurden keine Modellfreigaben, Gewichte,
Expertenreferenzen oder Hochschulabnahmen erzeugt. Historische Audit- und
Remediationberichte werden in diesem Schritt nicht bearbeitet. Bei der abschließenden
Dateiprüfung waren `docs/audit/` und `docs/remediation/` im aktuellen Checkout nicht
vorhanden; ihre frühere Bytegleichheit kann hier deshalb nicht erneut bestätigt
werden. Vorhandene historische Verweise in älteren Dokumentabschnitten werden
nicht durch erfundene Ersatzberichte aufgefüllt.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis | Reichweite |
|---|---|---|
| Vollständiges pytest | **699 bestanden**, 0 Failure, 0 Fehler, 0 übersprungen, **69,76 s** | 294 Unit-, 81 Integrations-, 324 Securityfälle |
| Kombinierte Coverage | **87,37 %**, 5.880 Statements / 1.688 Branches | Pflichtminimum 80 % und bestehende Omitliste unverändert |
| Planungsmodulcoverage | 94,6 % kombiniert | nur abgedeckte Kontrollpfade, keine semantische Genauigkeit |
| Ruff check und format check | bestanden | tatsächlicher finaler Format-/Lintcheck |
| Bandit | MEDIUM-/Confidence-Gate Exit 0; 0 MEDIUM/HIGH, 28 LOW, vier bestehende unterdrückte Checks | keine neue Scannerunterdrückung, keine behauptete Schwachstellenfreiheit |
| Hash-Lock-pip-audit | Exit 0, keine bekannten Paketbefunde | vier vorhandene Lockdateien unverändert; keine OS-/Modellprüfung |
| pip check | bestanden | installierte Paketkonsistenz |
| Compose-Validator | alle sechs Varianten bestanden | statische Prüfung, keine Containerabnahme |
| Artefakt-Privacy | ARTIFACT_PRIVACY_PASSED | definierte Testcanaries, kein neuer Gitleaks-Vollscan |
| Mock-Lab-CLI A/B/C | sechs vollständige Durchläufe, 22 simulierte Aufrufe, mocked=true | Standardfixture × drei Varianten × zwei Wiederholungen; keine Inferenzkosten |
| Erweiterte Korpus-CLI | acht Fälle, sieben registrierte tatsächliche PDFs, eine gesperrte Vertraulichkeitskontrolle | lokal extrahiert, expert_validated=false |
| Zwei-Dokument-A/B/C-Integration | zwölf vollständige Softwaredurchläufe; sechs getrennte Konsistenzgruppen mit je einem Wiederholungspaar | tatsächliche PDFs, ausdrücklich vorgegebene Mockantworten |

Die Erweiterung ergänzt 27 Testfälle gegenüber dem letzten 672-Test-Remediationstand.
Die vorhandenen Tests bleiben erhalten. Zwei Tests für Fehler/Quoten der früheren
Templateauswahl wählen jetzt ausdrücklich `regex_baseline`. Das vorhandene
API-Gesamtszenario erwartet sieben Aufrufe: drei Pflichtprüfungen, eine semantische
Mockplanung mit leerem Agentenplan und drei unabhängige Verifikationen. Es prüft
weiterhin beide Reihenfolgen menschlicher/KI-Erstbewertung, alle Embargogrenzen,
Nichtübertragung der menschlichen Texte und den menschlichen Abschluss.

Der erste Gesamtlauf hatte **2 Failure, 696 bestandene Fälle**. Beide Fehlschläge
betrafen die alten festen Aufrufzahlen im API-Test; es war kein bestandener Lauf.
Nach Anpassung an das explizit geprüfte Null-Agenten-Ergebnis und zusätzlicher
Agenten-ID-Grenzfallregression ist der oben genannte 699-Test-Lauf maßgeblich.
Eine neue Regression fand außerdem während der Implementierung einen Fehler bei
reduziertem Retrylimit: nach dem letzten erlaubten Fehlversuch durfte keine
uninitialisierte Antwort gelesen werden. Der Fehler ist korrigiert; die Prüfung
verlangt weiterhin Einhaltung des engeren Budgets und menschliche Klärung.

## Konkrete Testreferenzen

| Vertrag | Nachweis |
|---|---|
| Angewendetes Verfahren ohne Templateschlüsselwort → frei definierter Spezialist | `tests/unit/test_semantic_planning.py::test_applied_procedure_without_template_keywords_creates_dynamic_grounded_specialist` |
| Beiläufig erwähntes Buzzword → gültiger Null-Agenten-Plan | `test_incidental_buzzwords_do_not_force_a_semantic_agent_and_zero_is_valid` |
| MENTIONED/UNCLEAR, fremdes Kriterium/Methode, erfundenes Zitat, fremde Spanne, Zusatztools/-modelle und Budgetüberschreitung werden abgelehnt | parametrisierter `test_untrusted_plans_cannot_expand_scope_or_authority_and_keep_mandatory_coverage` |
| Zu viele/doppelte Aufträge und maximale Vorschlags-ID | `test_excessive_semantic_plan_is_rejected_as_a_whole`, `test_duplicate_semantic_tasks_are_not_created_under_different_names`, `test_a_maximum_length_proposal_key_is_mapped_to_a_valid_server_agent_id` |
| Erkennbare Injection verhindert Zusatzplanung und versteckten Baselinebypass | `test_recognized_document_injection_blocks_both_adaptive_variants_without_planner_call` |
| Gemeinsames Budget, begrenzte Retries und tatsächlicher engerer Timeout | `test_global_budget_and_proposed_retry_cap_are_both_enforced`, `test_agent_runtime_uses_the_proposed_stricter_deadline` |
| Private/fremde Kontexte abgelehnt, Fallback ausdrücklich markiert | `test_planning_cannot_read_private_or_foreign_context`, `test_unavailable_semantic_planner_never_silently_becomes_a_regex_result` |
| Empirischer Router braucht Daten zu allen angeforderten Fähigkeiten | neue zwei Multiskilltests in `tests/unit/test_model_routing.py`; synthetische Testrecords, keine echten Benchmarks |
| Planung hinter Embargo, echte PDF-Quelle und Humanreview bleibt aus Plannerprompt | `tests/integration/test_semantic_planning.py::test_planning_is_embargoed_and_bound_to_a_registered_pdf` |
| Gleiche Dokumente/Kriterien A/B/C, wiederholte Bedingungen getrennt | `test_a_b_c_planning_comparison_uses_same_documents_criteria_and_separate_repeat_groups` |
| Unverfügbarer C-Arm zählt nicht als erfolgreicher Vergleich | `test_unavailable_semantic_arm_does_not_count_as_a_successful_comparison` |
| Fachliche Planungsmetriken nur mit expliziten Referenzen | `test_planning_quality_requires_explicit_human_adjudication` |
| Bestehende Reviewansicht zeigt Aufgabe, Mockhinweis und Originalspanne | `test_existing_review_view_can_explain_dynamic_tasks_and_their_original_spans` |

Die beiden Gegenfälle verwenden im Test ausdrücklich geskriptete Antworten. Der
Testprovider liest bekannte Fixturetexte und liefert vorgegebene Methodenzustände.
Das ist ein positiver Kontrollpfad für strukturierte LLM-Antworten, kein Ersatz für
einen echten semantischen Klassifikationstest oder eine Expertenstudie.

## Reproduktionsbefehle und Rohbelege

PowerShell im Repositoryroot mit vorhandener Python-3.12-Umgebung:

```powershell
$env:COVERAGE_FILE='reports/semantic-planning-2026-11-27/.coverage'
.venv/Scripts/python.exe -m pytest --cov --cov-report=json:reports/semantic-planning-2026-11-27/coverage-final.json --cov-report=term:skip-covered --junitxml=reports/semantic-planning-2026-11-27/junit-final.xml -q
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
.venv/Scripts/python.exe -m bandit -c pyproject.toml -r backend/app frontend infrastructure/scripts infrastructure/security/scripts --severity-level medium --confidence-level medium
.venv/Scripts/python.exe -m pip_audit --strict --disable-pip --require-hashes --progress-spinner off -r backend/requirements.lock -r frontend/requirements.lock -r requirements-dev.lock -r requirements-security.lock -f json -o reports/semantic-planning-2026-11-27/pip-audit.json
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe infrastructure/scripts/validate_docker.py
.venv/Scripts/python.exe infrastructure/scripts/privacy_dlp.py artifacts
$env:PYTHONPATH='backend'
.venv/Scripts/python.exe -m app.evaluation.lab --provider mock --planning-variants A B C --repeats 2 --output-dir reports/semantic-planning-2026-11-27/mock-cli
```

Korpusreproduktion und notwendige Vorbedingungen für reale Aufrufe stehen in der
[Architekturbeschreibung](../architecture/semantic_adaptive_planning.md#reproduktion-mit-synthetischen-daten).
Dateirechte für Windows-Temp-/Parser-Unterprozesse und den Dependencyabgleich waren
außerhalb der eingeschränkten Sandbox erforderlich. Es wurden keine
Sicherheitsgrenzen herabgesetzt, um die Tests auszuführen.

Lokale ignorierte Belege: `reports/semantic-planning-2026-11-27/junit.xml` und
`coverage-first-failed.json` dokumentieren den ersten fehlgeschlagenen Stand;
`junit-final.xml` und `coverage-final.json` den Abschlusslauf. `bandit.json`,
`pip-audit.json`, `mock-cli/evaluation.json`, `mock-cli/evaluation.csv`, `corpus.json`
und `corpus-location.json` enthalten die jeweils bezeichneten Kontrollen und
synthetischen Testartefakte. Keine echten Arbeiten oder Gutachtertexte wurden
dorthin exportiert. Der PDF-Worker bleibt in einem isoliert gestarteten Unterprozess
außerhalb des Eltern-Coveragetracers; seine Dateicoverage 0 % ist kein behaupteter
Vollnachweis und wurde nicht durch eine neue Ausnahme ausgeblendet.

## Klassifikation und offene Abnahmen

| Umfang | Status |
|---|---|
| Strukturierter Plan, Abgrenzung Methodenstatus, Originalbelege, dynamische AgentSpecs, Router-/Factoryintegration | IMPLEMENTED_AND_TESTED für Software mit kontrollierten Antworten |
| Regexvergleich und ausdrücklich gewählter Fallback | IMPLEMENTED_AND_TESTED als deterministische Baseline |
| Semantische Leistung des Standard-DemoProviders | MOCK_ONLY; er liefert ausdrücklich keinen behaupteten realen Methodenbefund |
| Tatsächliche lokale Planner-/Spezialisteninferenz | IMPLEMENTED_NOT_VERIFIED; freigegebene Modellartefakte und reale Läufe fehlen |
| Fachliche Notwendigkeit und Qualität gegenüber Regex | BLOCKED_BY_EXTERNAL_REQUIREMENTS; unabhängige Referenzen und reale Experimente fehlen |
| Amtlicher DHBW-Katalog und Palleduhn-/Projektoriginale | BLOCKED_BY_EXTERNAL_REQUIREMENTS; bestehende Beispiele werden nicht zu amtlichen Kriterien erklärt |
| Zielhardwarekosten, RAM-/VRAM-Peaks, neuer Docker-/Hochschul-/Remote-CI-Lauf | IMPLEMENTED_NOT_VERIFIED; in dieser Änderung nicht ausgeführt |

Die Änderungen führen keine zusätzliche Provider-/Orchestrator-/Datenbankarchitektur
ein. Privacy-/Produktionssperren, vertrauliche Humanreview-Klassifizierung, Scope,
80-%-Coverage und `thesishounds-ci-gate` bleiben bestehen. Die frühere Dockerfile-
Paketkorrektur wird nicht als hier neu bestandener Image-/Trivy-Lauf ausgegeben.
