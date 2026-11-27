# Requirements traceability and engineering gap analysis

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
