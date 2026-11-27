# Requirements traceability and engineering gap analysis

## Document Security, 27.11.2026 – aktueller Arbeitsstand

Die OFF-1–5-Zuordnung ist aus vorhandener Dokumentation rekonstruiert, keine
erneute Prüfung der fehlenden Original-PowerPoint/Professorenfreigabe. Historisch
verlinkte `docs/audit/`-/`docs/remediation/`-Dateien fehlen derzeit im Checkout.
Die G-IDs werden als bestehende Zuordnung übernommen, nicht als neu bestätigter
Wortlaut. Status gelten jeweils für den abgegrenzten Umfang; ein grüner
Softwaretest erteilt keine fachliche oder produktive Freigabe.

| ID / Bezug | Anforderung / konkrete Implementierung | Testreferenz | Status / Grenze |
|---|---|---|---|
| DOC-01 / OFF-2,3 / G03,G05 | lokaler begrenzter PDF-Preflight: `backend/app/services/pdf_security.py`, `pdf_worker.py`, `knowledge/importer.py` | `tests/security/test_secure_document_gateway.py::test_active_or_encrypted_pdf_is_rejected_in_the_real_worker`, `test_page_limit_is_checked_before_text_extraction`; Knowledge-Importtests | IMPLEMENTED_AND_TESTED für kontrollierte synthetische/PUBLIC-PDFs; sichere private Gesamtverarbeitung PARTIALLY_IMPLEMENTED |
| DOC-02 / OFF-2 / G05,G19 | Python-Socket-/Prozess-/Schreib-Deny, Windows JobObject, Timeout: `services/pdf_worker.py` | `test_worker_python_network_process_and_write_operations_are_denied`, bestehende Workergrenztests | IMPLEMENTED_AND_TESTED für Python-/Windows-Grenzen; vollständige OS-Netzsandbox NOT_IMPLEMENTED, POSIX-Ausführung IMPLEMENTED_NOT_VERIFIED |
| DOC-03 / OFF-2,5 / G22 | Originalbytes/Hash/Importzeit/Parser-/Inspektionsversion: `services/document_store.py`, `assessments/provenance.py` | `test_import_preserves_original_pdf_and_records_versions`, `tests/security/test_pilot_boundaries.py` | IMPLEMENTED_AND_TESTED; signierte Attestation/revisionssichere Produktionsablage NOT_IMPLEMENTED |
| DOC-04 / OFF-3,5 / G05,G26 | Hidden-Text-/Unicode-/Metadatenindikatoren: `services/pdf_security.py`, `security/injection_detection.py` | `test_hidden_text_indicators_are_detected_without_rewriting_original_text`, `test_metadata_is_untrusted_and_normal_font_is_not_a_hidden_text_indicator` | PARTIALLY_IMPLEMENTED: getestete Heuristiken, keine Hintergrund-/OCR-/Bildgarantie |
| DOC-05 / OFF-2,3 | Raster-/OCR-Dual-Extraction und Bildinjektion | kein implementierter Pfad/kein ausgeführter Test | NOT_IMPLEMENTED; Rendering/OCR-Binaries fehlen |
| DOC-06 / OFF-2,3 / G19 | optionale semantische Indikatoren: `security/document_security.py::optional_semantic_check`, `backend/app/core/configuration.py::ExecutionLimits` | `tests/security/test_injection_controls.py::test_optional_local_classifier_requires_artifact_approval_and_cannot_grant_rights` | PARTIALLY_IMPLEMENTED: Software mit Mocks getestet; reale lokale Modelle BLOCKED_BY_EXTERNAL_REQUIREMENTS; Prompt-Guard-/DeBERTa-Adapter NOT_IMPLEMENTED |
| DOC-07 / OFF-2,3 / G21 | serverseitige Parent-/Owner-/Rechte-/Scopebindung: `agents/agent_factory.py`, `agent_registry.py`, `core/execution_engine.py` | `test_another_actor_cannot_delegate_from_a_registered_parent`, `tests/security/test_agent_guardrails.py`, semantische Planungstests | IMPLEMENTED_AND_TESTED innerhalb der Anwendung; OS-/SSO-Vertrauensgrenze offen |
| DOC-08 / OFF-2 / G19,G21 | obligatorische Toolprüfung: `security/tool_permissions.py`; festes Modell/Dokumentlabel im `llm/gateway.py` | `test_tool_firewall_checks_every_grant_before_execution`, `test_model_dispatch_is_bound_to_the_current_agent_even_for_valid_local_models`, `test_document_inference_requires_read_permission_before_budget_or_dispatch` | IMPLEMENTED_AND_TESTED für vorhandene Callpfade; kein Schutz gegen beliebigen Backend-Schadcode |
| DOC-09 / OFF-3,4 / G17 | rohe/typisierte Outputs, Kriterien/Evidenz/Coverage: `llm/gateway.py`, `assessments/ai_review.py`, `coverage.py` | `test_lax_output_schema_cannot_silently_drop_a_tool_or_grade_request`, bestehende Coverage-/Evidenztests | IMPLEMENTED_AND_TESTED für Struktur/Invarianten; wissenschaftliche Aussagegüte BLOCKED_BY_EXTERNAL_REQUIREMENTS |
| DOC-10 / OFF-4 / G03,G22 | Befunde/Zustände, Review/Embargo, kein Noteneffekt: `security/document_security.py`, `workflows/assessment_workflow.py`, `api/assessments.py`, `frontend/assessment_review.py` | `tests/integration/test_security_review.py` einschließlich exakter IDs, Privacy-Deny, UI und kombiniertem Überlauf | IMPLEMENTED_AND_TESTED mit synthetischen Daten; produktive auditierbare Mehrbenutzerfreigaben PARTIALLY_IMPLEMENTED |
| DOC-11 / OFF-3,4 | auffällig positive Befunde lösen Gegenprüfung/Humanklärung aus: `assessments/ai_review.py`, `escalation.py` | `test_uniform_positive_model_output_in_suspicious_context_still_requires_human_review` | IMPLEMENTED_AND_TESTED mit kontrollierten Mockantworten; echte Modellunabhängigkeit/-qualität IMPLEMENTED_NOT_VERIFIED |
| DOC-12 / OFF-2,3 | indirekte Rechercheinjektion: `research/gateway.py`, `agents/research_quality.py`, `security/information_flow.py` | `tests/security/test_academic_privacy.py`, `test_citation_information_flow.py`, vorhandene Quellenreviewtests | IMPLEMENTED_AND_TESTED für lokale Scope-/Denygrenzen; öffentliche Runtime-Rechercheschnittstelle NOT_IMPLEMENTED |
| DOC-13 / OFF-5 / G26 | reproduzierbare A–E-Control-Ablation: `evaluation/injection_benchmark.py` | `test_synthetic_ablation_distinguishes_detection_prevention_and_missing_semantics`, ausgeführte CLI | IMPLEMENTED_AND_TESTED als deterministisches Experiment; A/B-Modellverhalten MOCK_ONLY, D-Realinferenz BLOCKED_BY_EXTERNAL_REQUIREMENTS; vollständige PDF-/Modellstudie PARTIALLY_IMPLEMENTED |
| DOC-14 / OFF-2,5 | Mandatory-CI/80-%-Grenze: `.github/workflows/ci.yml`, `pyproject.toml`, `infrastructure/scripts/ci_summary.py` | `tests/unit/test_ci_workflow.py`, `tests/security/test_privacy_ci_gate.py`, gesamte lokale Suite | IMPLEMENTED_AND_TESTED lokal; aktuelle Remote-CI/Dockerbuild IMPLEMENTED_NOT_VERIFIED |

[Abschlussnachweis](../evaluation/security_results.md): 737 bestandene Tests,
87,02 % kombinierte Coverage, keine Skips. [Benchmarkgrenzen](../evaluation/prompt_injection_benchmark.md)
und [priorisierte Schritte bis 15.12.2026/25.01.2027](../security/risk_register.md).
Das vollständige Sicherheits-Definition-of-Done ist noch nicht erfüllt.

## Semantische adaptive Planung, 27.11.2026

Die fünf OFF-Anforderungen bleiben rekonstruierte Anforderungen. Fachkatalog und
Modellfreigaben fehlen weiterhin; es wird keine amtliche DHBW-Abnahme abgeleitet.
[Architektur und Reproduktion](../architecture/semantic_adaptive_planning.md),
[Prüfergebnisse und Grenzen](../evaluation/semantic_planning_results.md).

| ID / Bezug | Umsetzung | Testreferenz | Status und Grenze |
|---|---|---|---|
| SEM-1 / OFF-2,3, G02,G04 | `backend/app/agents/adaptive_assessment.py`: strukturiertes ThesisUnderstanding, APPLIED/MENTIONED/UNCLEAR, null Agenten erlaubt; lokales Gateway | `tests/unit/test_semantic_planning.py`, `tests/integration/test_semantic_planning.py` | IMPLEMENTED_AND_TESTED als Software; reale Inferenz IMPLEMENTED_NOT_VERIFIED |
| SEM-2 / OFF-2,3, G21 | dynamische Fachnamen/Tasks → bestehender AgentSpec, Factory, Registry und ExecutionEngine; feste Rechte/Scope, kein neuer Orchestrator | Factory-/Guardrail-/Securitytests, Planungsregressionen | IMPLEMENTED_AND_TESTED; Vorschläge sind keine fachlich bewiesene Notwendigkeit |
| SEM-3 / OFF-2,3,5, G20,G27 | `backend/app/llm/model_router.py`, `gateway.py`: gemessen nur mit passendem Digest und allen geforderten Aufgabenscores; sonst MANUAL_DEFAULT | zwei Multiskillregressionen in `tests/unit/test_model_routing.py` | IMPLEMENTED_AND_TESTED für Routingvertrag; empirische Modellfähigkeiten fehlen |
| SEM-4 / OFF-3,4, G15,G17,G22 | `assessments/ai_review.py`, geschützte Workflow-Provenance und `frontend/assessment_review.py`: Pflichtcoverage zuerst, exakte Planbelege, Embargo und menschliche Klärung | PDF-/Humanreview-/UI-Integration und alle bisherigen Embargotests | IMPLEMENTED_AND_TESTED mit synthetischen Daten; Ablage weiter flüchtig |
| SEM-5 / OFF-5, G07,G26,G27 | `evaluation/lab.py`, `metrics.py`, `academic_benchmark.py`: fair getrennte A/B/C-Planungsbedingungen, acht Korpusfälle, Referenzschnittstelle für Planrelevanz | Zwei-PDF-Vergleich mit zwölf Mockdurchläufen; Referenz-/Incomplete-Tests | technische Evaluation IMPLEMENTED_AND_TESTED; Fachqualität BLOCKED_BY_EXTERNAL_REQUIREMENTS |

Abschlusslauf: **699 Tests, 87,37 % kombinierte Coverage**, unveränderte 80-%-Grenze.
Frühere Tabellen/Testzahlen sind historische Stände der dort verlinkten Erweiterungen.

## Post-Audit Remediation, 27.11.2026

Maßgeblicher neuer Arbeitsstand: [Phasenbericht und Abnahmegrenzen](../remediation/2026-11-27-remediation.md),
[alle G01–G30 mit Abnahmekriterien](../remediation/2026-11-27-backlog.md),
[tatsächlich ausgeführte Prüfungen](../remediation/2026-11-27-verification.md) und
[Pilotanleitung](../remediation/2026-11-27-pilot-runbook.md).
Die fünf Auditdateien bleiben historische Ausgangsbelege. Die folgenden Abschnitte
zu früheren Erweiterungen sind weiterhin deren jeweilige historische Nachweise.
Die originale DHBW-Projekt-PowerPoint und primäres Professorenfeedback fehlen;
OFF-1 bis OFF-5 bleiben rekonstruierte Anforderungen. Der Nutzer bestätigt weiterhin
fehlenden PA1-Experimentkatalog und fehlende freigegebene Modellartefakte.

| OFF / Gap | Konkreter neuer Implementierungsumfang | Dateipfad | Testreferenz | Ausführungsnachweis / Klassifikation und Grenze |
|---|---|---|---|---|
| OFF-1 / G01,G04 | Katalogzustände EXAMPLE/CANDIDATE/EXPERIMENT/APPROVED getrennt; keine neue Fachfreigabe | `backend/app/assessments/profile_registry.py`, `config/assessment_profiles/pa1.yaml` | `tests/integration/test_pilot_workflow.py::test_local_pilot_needs_actual_artifact_and_catalog_evidence` | `junit-final.xml`; technische Prüfung IMPLEMENTED_AND_TESTED, bestätigter Katalog BLOCKED_BY_EXTERNAL_REQUIREMENTS |
| OFF-2/3 / G02,G04 | Expliziter `local_pilot` im vorhandenen OllamaProvider/Gateway, geschlossene Registry und kein Demo-/Cloudfallback | `backend/app/main.py`, `backend/app/config.py`, `backend/app/llm/model_registry.py`, `backend/app/core/configuration.py`, `backend/app/security/policy_engine.py` | `tests/integration/test_pilot_workflow.py::test_pdf_to_human_finalization_through_real_adapter_with_mock_http`, `tests/security/test_pilot_boundaries.py::test_unapproved_or_unpinned_artifact_cannot_create_network_provider` | Softwareintegration IMPLEMENTED_AND_TESTED mit simuliertem HTTP; echte Inferenz IMPLEMENTED_NOT_VERIFIED |
| OFF-2/5 / G08 | Hochschultransport mit exaktem HTTPS-Host/Port, privaten Pins, TLS-CA/SNI und DNS-Rebinding-Deny | `backend/app/security/egress_policy.py`, `backend/app/llm/providers/ollama.py`, `backend/app/main.py` | `tests/unit/test_audit_regressions.py::test_g08_explicit_https_pin_preserves_tls_hostname_and_denies_dns_rebinding`, negative Pin-/TLSfälle | `phase1-before.xml`, `phase1-after.xml`, `junit-final.xml`; kontrollierter Transport IMPLEMENTED_AND_TESTED, Hochschulbetrieb weiterhin PARTIALLY_IMPLEMENTED/extern blockiert |
| OFF-2/3/4 / G03,G19 | Kuratierte PDF → begrenzter Parserprozess → gehashter Katalog → Assessment → Originalbeleg | `backend/app/services/document_store.py`, `backend/app/services/pdf_worker.py`, `backend/app/assessments/schemas.py`, `backend/app/api/assessments.py`, `backend/app/workflows/assessment_workflow.py` | `tests/integration/test_pilot_workflow.py`, `tests/security/test_pilot_boundaries.py` | `junit-final.xml`, `corpus-cli.json`; synthetischer Dokumentpfad IMPLEMENTED_AND_TESTED, private Sandbox/Upload NOT_IMPLEMENTED |
| OFF-3/4/5 / G15 | Originaloffsets einschließlich eingerückter Mehrzeileneinträge | `backend/app/research/citations.py` | `tests/unit/test_audit_regressions.py::test_g15_original_spans_for_indented_and_multiline_references` | rot vor Korrektur, grün final; IMPLEMENTED_AND_TESTED für exakte Textspannen, keine umfassende Extraktionsgüte |
| OFF-3/5 / G16 | Eine DOI-Normalisierung; mehrdeutige legitime Suffixzeichen bleiben | `backend/app/research/doi.py`, `backend/app/research/provider_registry.py`, `backend/app/research/local_verification.py`, `backend/app/assessments/routine_checks.py` | `tests/unit/test_audit_regressions.py::test_g16_one_canonical_doi_function_preserves_ambiguous_suffixes`, Retraction-Semikolonfall | rot vor Korrektur, grün final; IMPLEMENTED_AND_TESTED für geprüfte Eingaben |
| OFF-3/4/5 / G17 | Fehlendes optionales KI-Kriterium ohne KeyError, getrennte Bearbeitungszustände, Pflichtgate bleibt | `backend/app/assessments/coverage.py`, `backend/app/workflows/assessment_workflow.py`, `frontend/assessment_review.py` | `tests/unit/test_audit_regressions.py::test_g17_missing_optional_finding_can_be_compared_and_finalized`, `test_g17_execution_states_and_required_coverage_are_distinct` | `g17-before.xml` reproduziert KeyError, final grün; IMPLEMENTED_AND_TESTED |
| OFF-4 / G03,G10 | Pilotdateiauswahl, unabhängiger Humanreview, Embargo, Belege, manuelle Klärung und Finale | `frontend/assessment_review.py`, `backend/app/workflows/assessment_workflow.py` | `tests/integration/test_pilot_workflow.py::test_pilot_pdf_can_be_selected_in_ui_with_explicit_inference_mode`, kompletter PDF-/Adaptertest, bestehende `tests/integration/test_assessment_frontend.py` | `ui-pilot.xml`, `junit-final.xml`; IMPLEMENTED_AND_TESTED mit synthetischen Daten/Mockantworten, freie KI-Diskussion bleibt gesperrt |
| OFF-2/4/5 / G06,G22 | Dokument-/Text-/Kriterien-/Architekturbindung und expliziter flüchtiger Ergebnisvertrag | `backend/app/assessments/provenance.py`, `backend/app/workflows/assessment_workflow.py`, `docs/remediation/2026-11-27-pilot-runbook.md` | `tests/integration/test_pilot_workflow.py::test_pilot_abort_delete_and_restart_explicitly_have_no_recovery`, `tests/integration/test_finding_feedback.py` | `junit-final.xml`; Lifecycle/Verlust beim Neustart IMPLEMENTED_AND_TESTED, Persistenz/Restore/integrer Akteuraudit NOT_IMPLEMENTED |
| OFF-3/5 / G07,G26,G27 | Fünf analysierbare PDFs plus geheime Deny-Kontrolle; gleicher A/E-Input; dokumentweise Konsistenz und Referenzzuordnung | `backend/app/evaluation/academic_benchmark.py`, `backend/app/evaluation/lab.py`, `backend/app/evaluation/metrics.py` | `tests/integration/test_pilot_evaluation.py::test_generated_pdf_corpus_runs_a_and_e_without_cross_document_repeat_comparisons`, unregistrierter Korpus wird abgewiesen | 20 Mock-Reviews im Integrationstest; IMPLEMENTED_AND_TESTED für Software; Referenzgüte BLOCKED_BY_EXTERNAL_REQUIREMENTS |
| OFF-2/5 / G09,G20,G23,G24 | Bestehende Prüfgrenzen und Tests erhalten; neue Positiv-/Negativfälle | `pyproject.toml`, `.github/workflows/ci.yml` (beide unverändert), neue Pilot-/Auditregressionen | gesamtes `tests/` | 672 Fälle, 87,30 %, Ruff/Bandit/pip-audit/statische Compose-Prüfung; lokale Softwarechecks IMPLEMENTED_AND_TESTED, neue Docker-/Remote-/Hardwareabnahme IMPLEMENTED_NOT_VERIFIED |

Alle relativen Belegdateinamen in der letzten Spalte liegen unter dem ignorierten
`reports/remediation-2026-11-27/`. Sie werden nicht mit echten Gutachterdaten
veröffentlicht. OFF-5 ist trotz Softwaretests fachlich weiterhin teilweise erfüllt;
kein höherer Testzähler begründet einen wissenschaftlichen Qualitätsgewinn.

## Advanced Review, 27.11.2026

Der [Audit](../architecture/advanced_review_audit.md) priorisiert bestehende Komponenten.
Der [Ergebnisbericht](../evaluation/advanced_review_results.md) dokumentiert die
tatsächlich getestete Umsetzung; fachliche Validierung bleibt getrennt.

| ID | Projektbeitrag | Implementierung / Nachweis | Erfüllungsgrenze |
|---|---|---|---|
| ADV-1 | OFF-2/3/5: lokaler Kontext | context_management, vorhandene Document Intelligence, Kriteriums-/Challengeintegration; test_context_management | Heuristik/Feature-Hash, keine evaluierte gelernte Embeddingsuche |
| ADV-2 | OFF-3/5: wissenschaftliche Beziehungen | ScientificRelationship, consistency_map, Mehrspanprüfung; test_review_intelligence | geerdete Vorschläge, keine automatisch bewiesenen Widersprüche |
| ADV-3 | OFF-2/3/4: kontrollierte Agentik | plan_escalation, vorhandene Factory/Gateway, Pflichtkriterien zuerst, Quoten-/Fehlerfragen | Regeln noch nicht fachlich kalibriert; echte Modellgüte offen |
| ADV-4 | OFF-3/4/5: Evidenz | sechs Qualitätszustände, Gegenbelege, Original-/Kontextrückprüfung, unverlöschte Verifikationsrunden | Quote/Modellkonsens keine Wahrheit; visuelle Extraktion ungeprüft |
| ADV-5 | OFF-4/5: Neutralität | Headerpseudonymisierung, sechs Fairnessfaktoren und Paarmetriken; test_advanced_evaluation | Mockprüfung, keine empirische Fairness-/Anonymitätsgarantie |
| ADV-6 | OFF-2/3/4/5: Nachvollziehbarkeit | Provenance-Snapshot, Modell-/Prompt-/Regel-/Quellen-/Entscheidungsversionen; test_finding_feedback | Git/Quantisierung ohne Beleg UNKNOWN; keine exakte Wiederholbarkeit |
| ADV-7 | OFF-1/4/5: Gutachterfeedback | sechs Aktionen, strukturierte Gründe, History, geschützte UI/API und Entwurfsprüfung | keine automatische Trainings-/Goldlabel-/Aggregationsnutzung |
| ADV-8 | OFF-2/3/5: robuste Ressourcensteuerung | Retries, Timeouts, Kriteriumscalls/-zeiten, Kontext/RSS, optionale VRAM-/Ladesnapshots | keine physische Peakmessung oder dauerhafte Recovery |
| ADV-9 | OFF-5: Evaluation/Informationssicherheit | A–E plus Einzelkomponentenablation, 627 Tests/313 Privacytests, CI-Benchmarks und Docker-E2E/Netzprobe | keine Remote-CI-/Hochschul-/Expertenabnahme |

## Erneutes Security-Hardening, 27.11.2026

Die bestehende Zuordnung zu OFF-1 bis OFF-5 bleibt erhalten. Konkrete zusätzliche
Kontrollen und tatsächlich ausgeführte Nachweise:

| ID | Zuordnung | Implementierung | Nachweis / Grenze |
|---|---|---|---|
| SEC-1 | OFF-1/2 | Frontend-IP-Pinning, feste Requestoptionen, Body-/Antwortgrenzen | test_transport_hardening, echter Frontend-E2E; Zielhost offen |
| SEC-2 | OFF-1/2/3 | getrennte Provisioning-Zone; Freigaben/Version/Herkunft/volle Manifest-Digests | test_provisioning_boundary, Transporttests, Compose; kein echter Modelldownload |
| SEC-3 | OFF-2/3 | Bibliografie-/DOI-Klassifizierung, Analyse-/Dokumentscope, Maximumregel im Quellenreview | test_citation_information_flow; private Modellverarbeitung bleibt gesperrt |
| SEC-4 | OFF-2/4 | lokale Sperrvermerkdetails ohne automatische Entklassifizierung; menschliches Erstbewertungs-/Finalisierungsgate erhalten | synthetische Notice-/Ablauftests, vollständige Embargo-/HITL-Regressionen; organisatorische Freigabe offen |
| SEC-5 | OFF-5 | 568 Regressionen, Privacyablation, echte kontrollierte Docker-Netzprobe, lokale Secret-/Imagescans | [Hardening-Ergebnisse](../security/hardening_results.md); offene OS-CVEs/Host-/Modell-/Rechtsabnahme ausdrücklich benannt |

## Ergänzung: DHBW Mosbach und Quellen, 27.11.2026

Die fünf OFF-Anforderungen stammen aus der übergebenen Aufgabenbeschreibung;
die Original-PowerPoint selbst wurde nicht bereitgestellt. Öffentliche amtliche
Unterlagen wurden neu recherchiert, aber vom Coding-Agenten nicht freigegeben.

| ID | Offizielle Zuordnung | Konkrete Implementierung | Automatisierter Nachweis | Grenze / noch erforderlich |
|---|---|---|---|---|
| MOS-1 | OFF-1/3 | lokale Quellenmetadaten, PA1/DS25, PA2/DS24, BA/DS23, Hierarchie/Versions-/Konfliktauflösung | test_institutional_rules | StuPrO, WI-/Palleduhn-Original und menschliche Freigabe |
| MOS-2 | OFF-2/3 | begrenzte lokale PDF/Office/Textimporte außerhalb Repo, Kandidatenstandard | test_knowledge_import, test_operator_import_cli | interne/private Importe und Parser-Sandbox nicht freigegeben |
| MOS-3 | OFF-3/5 | deterministische Formalien, nachvollziehbare Messdaten, unbekannte Befunde manuell | test_institutional_rules, formal_compliance_benchmark | keine zuverlässige PDF-Layout-/Signaturmessung behaupten |
| MOS-4 | OFF-3/5 | Bibliografie-/Zitatabgleich, lokale Crossref/OpenAlex/RW-Adapter, Quellenstatus | test_citation_engine, test_snapshot_store, citation_benchmark | kleine Teilbestände; keine aktuelle umfassende Quellen-/Semantikprüfung |
| MOS-5 | OFF-2/3 | Quellenqualitätsreview im vorhandenen Gateway, minimale Scopekontexte, überprüfte Quellenzitate | test_source_quality | lokale Modellgüte ungemessen; aktive offizielle Kriterien fehlen |
| MOS-6 | OFF-2/5 | optionale GROBID-Isolation, Konsolidierung aus, gepinnter Adapter | test_academic_privacy, Compose-Validator | echtes geprüftes Image und Host-/Parserqualitätsnachweis offen |
| MOS-7 | OFF-4 | Studiengang/Jahrgang/Regelversionen, Embargo auch für lokale Checks, versionierte menschliche Entscheidungen | test_academic_workflow, Docker ci_e2e | unabhängige Erstbewertung bleibt erhalten; keine automatische Note |
| MOS-8 | OFF-2/5 | Research-Grenze, Public-Snapshot-Hashes, Clearance-Deny, DOTX/XLTX-DLP, scoped Tasklöschung | test_academic_privacy, CI privacy-security | Host-/SSO-/Verschlüsselungs-/Rechtsabnahme ausstehend |
| MOS-9 | OFF-5 | reproduzierbare Quellen-/Formalienbenchmarks und 12×4 Privacy-Control-Ablation | academic_benchmark, privacy_lab in CI | synthetische enge Fixtures, keine repräsentative Effektivitätsstudie |

Ergebnisse und Restrisiken: [Mosbach-Testnachweise](../evaluation/mosbach_results.md).

## Historischer Stand vor den wissenschaftlichen Engineering-Erweiterungen

Audit: 2026-11-26. Grundlage: übergebene offizielle Anforderungen, vorhandenes
Professorenfeedback in `../architecture/professor_feedback_gap.md` und tatsächlicher
Quellcode. Kein offizieller Bewertungskatalog und keine menschlich adjudizierten
Referenzbefunde wurden bereitgestellt. Der bisherige Privacy-Stand bleibt verbindlich.

## Offizielle Projektanforderungen

| ID | Beschreibung | Vorhandene Komponenten / Tests | Status vor Erweiterung | Fehlende Funktion / Nachweis | Wissenschaftlicher Nachweis | Risiko | Priorität |
|---|---|---|---|---|---|---|---|
| OFF-1 | Begutachtungsprozess und Anforderungen analysieren | AssessmentWorkflow, Beispielprofile, Human-review-Tests; Professorenfeedback | teilweise implementiert | offizielle Detailkriterien, Prozessinterviews und Freigaben | Prozessentwurf dokumentiert; keine abgeschlossene Feldstudie | unpassende Kriterien / Erwartungen | P0 |
| OFF-2 | sichere agentische Architektur konzipieren | Gateway, Policy/IFC, Factory/Registry, Privacy-Security-Tests | technisch implementierte synthetische Basis | gemessene Modellzuordnung, an Kriterien gebundene adaptive Analysen | Architektur und synthetische Sicherheitsnachweise; keine Hochschulabnahme | Kontext-/Berechtigungsverlust | P0 |
| OFF-3 | Arbeiten automatisiert analysieren und evidenzbasierte Befunde identifizieren | AISecondReviewer, Legacy-Orchestrator, EvidenceValidator; Workflow-/Evidence-Tests | teilweise implementiert | adversariale Prüfung im kriteriumsweisen Pfad, Kapitel-/Kontextbelege, verbindliche Coverage | Quote-Matching nachgewiesen; fachliche Validität ungemessen | Halluzinationen / unberechtigte Kritik | P0 |
| OFF-4 | Gutachten unter Beteiligung des Gutachters unterstützen | unabhängige Erstbewertung, Embargo, Vergleich, versionierte Entscheidungen, deterministischer Entwurf; API-/UI-Tests | synthetischer vertikaler MVP implementiert | Belegnavigation, selektive Freigabe zusätzlicher Befunde; KI-Diskussion wegen Privacy-Gate gesperrt | Interaktion technisch getestet; Nutzen/Biaswirkung nicht empirisch belegt | Automation Bias / voreilige Übernahme | P0/P1 |
| OFF-5 | Qualität, Nachvollziehbarkeit und Informationssicherheit evaluieren | A–D-Legacymodi, vier synthetische Capability-Probes, Ressourcen/Budgets, Privacy-Canaries | teilweise implementiert | vergleichbare A–E-Experimente, Konsistenz-/Variationstests, Referenzschnittstelle, JSON/CSV | Mocktests belegen Funktion; keine Qualitätsmesswerte realer Modelle | unfairer Vergleich / erfundene Metriken | P0/P1 |

## Engineering-Arbeitspakete und Abnahme

| ID | Beitrag / offizielle Zuordnung | Wiederverwendeter Ausgangspunkt | Geplante konkrete Ergänzung | Test / Nachweisziel | Nicht überprüfte Voraussetzung / Risiko | Priorität |
|---|---|---|---|---|---|---|
| ENG-1 | gemessene Modellauswahl / OFF-2,3,5 | ModelRegistry, LLMGateway, model_benchmark | Capability-Protokoll, Router mit Privacy-first, Digestbindung, Verfügbarkeit und Ressourcenbudget; expliziter manueller Fallback | Routing-/Stale-evidence-/Privacytests; echte lokale Benchmarks separat | keine gemessenen Qualitätswerte oder bestätigte GPU-Kapazität vorhanden | P0 |
| ENG-2 | vollständiger Katalog / OFF-1,3 | ProfileRegistry, fester Criterion Loop | Coverage Checker für fehlende/duplizierte/fremde Kriterien und NOT_ASSESSABLE | deterministische Coverage-/Workflowtests | Beispielprofile sind keine offiziellen DHBW-Kataloge | P0 |
| ENG-3 | adaptive Expertise / OFF-2,3 | bestehende AgentFactory/Registry und Toolrechte | begrenzte thematische Zusatzanalysen, Pflichtbefunde bleiben erhalten | Template-/Factory-/Scope-/Budgettests | Themenheuristik erkennt weder Methodenqualität noch tatsächlichen Bedarf zuverlässig | P0 |
| ENG-4 | unberechtigte Kritik vermeiden / OFF-3,5 | Gateway, Quotevalidator, Konfliktlogik | unabhängiger adversarialer Reviewer, Kontext-/Gegenargumente, begrenzte Runden, erneute deterministische Prüfung | Unterstützungs-/Widerspruchs-/falsche-Beleg-Tests | Modellkonsens bleibt kein Wahrheitsbeweis | P0 |
| ENG-5 | Document Intelligence / OFF-3,4 | Document.pages | lokales strukturiertes Textmodell mit überprüfbaren Spannen, Kapitel-/Absatzreferenzen und Extraktionswarnungen | Offset-/Cross-chapter-/unzuverlässige-Inhalte-Tests | kein freigegebener PDF/OCR-Parser; keine Layout-/Bildbehauptungen | P1 |
| ENG-6 | Evidence Explorer / OFF-3,4 | Assessment UI, Freigabeembargo und ACL | freigegebener Befund → servervalidierte Originalstelle; keine Modellreferenz ungeprüft übernehmen | API-/UI-/Embargotests | exakter Textbeleg beweist keine fachliche Schlussfolgerung | P1 |
| ENG-7 | Quellenvalidierung / OFF-3,5 | DOI-Inventar, ResearchEvidence, geschlossener ResearchGateway | lokale bibliografische Abgleiche mit getrennten Prüfstufen; Unbekannt bleibt unbekannt | lokale DOI-/Version-/Retraktionstests | öffentliche Metadaten und Volltexte fehlen; kein externer Querypfad | P1 |
| ENG-8 | reproduzierbare Evaluation / OFF-5 | bestehende Capability-Probes, Ressourcenmessung | A–E-Lab mit identischen Fixtures, Konfig-/Prompt-/Digestnachweisen, menschlichen Referenzen und konsistenten Metriken; JSON/CSV | deterministische Mockexperimente und fehlende-Referenz-Tests | keine Expertengoldlabels, keine echte Modellqualität | P1 |
| ENG-9 | Konsistenz und Bias / OFF-5 | Lab-Resultate | Wiederholung und einzeln kontrollierte Identitäts-/Format-/Reihenfolge-/Modell-/Injectionvariation | paarweise Übereinstimmungs-/Kontrolltests | Pilotumfang erlaubt keine statistische Generalisierung | P1 |
| ENG-10 | Privacy / OFF-2,5 | vollständige Security-Basis und CI-Gate | neue Pfade müssen ACL, Embargo, IFC, geschlossene Recherche und synthetische Exportgrenzen bewahren | gesamte Privacy-Suite plus neue Exfil-/Scope-Regressionen | Zielhost/SSO/Organisation weiterhin gesperrt | P0 |

## Umsetzung und Ergebnisse

Die Tabellen beschreiben den überprüften Ausgangszustand und den daraus abgeleiteten
Plan, keine vorweggenommenen Implementierungen. Abschließenden Lieferstand,
tatsächlich ausgeführte Tests und weiter fehlende Voraussetzungen in
`../evaluation/results.md` und `../evaluation/limitations.md` nachführen.

Keine neue Hochschulverwaltung, keine parallele zweite Agent Factory und kein
alternativer LLM-Transport. Die Erweiterung integriert den bestehenden Gateway,
die vorhandenen Rechte-/Budgetprüfungen und den unabhängigen menschlichen Review.

## Gelieferter vertikaler MVP und Zuordnung

| Paket | Tatsächlich implementierte Komponenten | Zugehörige neue Tests | Status / verbleibender wissenschaftlicher Nachweis |
|---|---|---|---|
| ENG-1 | model_router.py, Gateway.route, Capability-Probes v2, leere Capability-Registry | test_model_routing.py; bestehende Gatewaytests | technische Auswahl implementiert; echte Qualitätsscores fehlen, manueller Fallback sichtbar |
| ENG-2 | assessments/coverage.py im verbindlichen Criterion Loop | test_scientific_evidence.py, Assessment-API | Abdeckung im Beispielkatalog geprüft; offizieller Detailkatalog fehlt |
| ENG-3 | adaptive_assessment.py mit vorhandener Factory/Registry/ExecutionEngine | A-E-Lab-/Factory-/Securitytests | begrenzte Zusatzagenten implementiert; fachlicher Mehrwert ungemessen |
| ENG-4 | adversarial_verification.py, geteilte deterministische Evidenzfunktion | test_adversarial_verification.py, test_scientific_boundaries.py | Gegenprüfung und unverlöschte Konflikte implementiert; keine garantierte semantische Wahrheit |
| ENG-5 | document_intelligence.py mit Seiten-/Absatzspannen, Kapiteln, Zitaten und Warnungen | test_scientific_evidence.py | Textmodell implementiert; echte PDF-/OCR-/Layoutverarbeitung nicht freigegeben |
| ENG-6 | freigabegeschützte Evidence-API und Streamlit-Navigation | test_evidence_explorer.py | vertikal implementiert; keine Modellreferenz ohne serverseitigen Textabgleich |
| ENG-7 | local_verification.py, DOI-/Version-/Retraktions-/Bibliografie-/Volltextquote-Prüfungen | test_offline_sources.py | lokale Snapshotprüfung implementiert; Korpus und semantische Expertenprüfung fehlen |
| ENG-8 | evaluation/lab.py und metrics.py, ReferenceSet, JSON/CSV | test_evaluation_lab.py | tatsächlich ausgeführte Mockexperimente; fachliche Metriken mangels Expertenreferenzen null |
| ENG-9 | Wiederholungs-/Variantenpaarung, einzeln kontrollierte Bedingungen | Lab-Tests und gespeicherte Pilotresultate | technische Variation implementiert; empirische Bias-/Nutzenstudie offen |
| ENG-10 | bestehende Privacy-Grenzen auch in Router, Verifier und Evidence-API | gesamte Security-Suite, scientific_boundaries | keine neue Freigabe echter Arbeiten; Zielhost-/SSO-/Organisationsnachweise weiterhin erforderlich |

Aktuelle Testzahlen und tatsächlich beobachtete Ergebnisse stehen in
`../evaluation/results.md`. Die formale Projektaufgabe ist damit technisch deutlich
weiter abgedeckt; ein **nachgewiesener wissenschaftlicher Qualitätsgewinn** ist
ohne reale lokale Modellmessungen, Expertenreferenzen und passende Studie noch offen.
