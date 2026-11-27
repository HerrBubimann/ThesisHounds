# Advanced Review: Lieferstand und tatsächliche Ergebnisse

Stand **27.11.2026, Europe/Berlin**. Ausschließlich synthetische Fixtures, Quellcode
und bereits geprüfte öffentliche Unterlagen. Keine echte wissenschaftliche Arbeit,
keine institutionelle Freigabe, kein Modelltraining und keine Übertragung vertraulicher
Inhalte. Die Produktionssperren bleiben bestehen. Ausgangspunkt und Plan:
[Repository-Audit](../architecture/advanced_review_audit.md).

## Implementierter Verbesserungsdurchlauf

| Verbesserung | Tatsächlich integriert | Projektbeitrag / verbleibende Grenze |
|---|---|---|
| Dokumentkontext | lokaler Index, Satz-/Kapitelchunks, Feature-Hash-Vektoren, Keyword/Cosinus-Hybridranking, Kapiteldiversität, Seiten-/Scopefilter und modellgenau reservierte Promptbudgets | OFF-2/3/5; keine vortrainierten semantischen Embeddings oder gemessene Retrievalgüte |
| Wissenschaftliche Konsistenz | elf Aspektkandidaten, strukturierte Modellbeziehungen, mindestens zwei verschiedene validierte Spannen, konservative Fehlstellenbehandlung | OFF-3/5; Beziehungsdeutung bleibt menschlich zu prüfen |
| Adaptive Eskalation | Pflichtkriterien zuerst; E verlangt Thema plus Befundbedarf für Zusatzagenten; kritische/ungeklärte Befunde unabhängig prüfen; Fehler und Ressourcenlücken menschlich klären | OFF-2/3/4; transparente Regeln sind noch nicht fachlich kalibriert |
| Evidenz | sechs Evidenzqualitäten, Support/Gegenbelege, Kontextabgleich, offene Fragen, unverifizierbare Aspekte, Originalbefund und unverlöschte Challengehistorie | OFF-3/4/5; Quote/Modellkonsens beweisen keine Wahrheit |
| Neutralität | lokale Headerpseudonymisierung und zusätzliche Gendernamen-/Notenerwartungsvarianten mit gepaarten Outcome-Metriken | OFF-4/5; kein Nachweis realer Fairness oder Anonymität |
| Provenance | dokument-/katalog-/richtliniengebundener Snapshot, Modelle/Digests/Parameter, Prompts-/Workflowversionen, Agenten, Ressourcen, tatsächlich geprüfte Quellen und menschliche Versionen | OFF-2/3/4/5; Git/Quantisierung bleiben ohne Beleg UNKNOWN/null; keine exakte Reproduzierbarkeit |
| Feedback | sechs Befundaktionen, sieben strukturierte Gründe, Korrektur/Ergänzung, Historie, geschützte API/UI, widersprüchliche Übernahme im Entwurf gesperrt | OFF-1/4/5; keine automatische Goldlabelbildung, Aggregation oder Trainingsnutzung |
| Robustheit/Ressourcen | begrenzte lokale Retries, leere Kontexte ohne LLM, Pflichtfehler FAILED, optionale Fehler sichtbar, Kriteriumscalls/-zeiten, Context/RSS und optionale Inferenzsnapshots | OFF-2/3/5; kein dauerhafter verschlüsselter Wiederanlauf, keine realen GPU-Peaks |

Die OFF-Zuordnung folgt der übergebenen Projektbeschreibung und dem vorhandenen
Professorenfeedback. Die ursprüngliche PowerPoint selbst wurde nicht bereitgestellt.
Offizielle DHBW-Kandidaten werden nicht durch den Agenten freigegeben; die Demo
verwendet weiterhin Beispielkriterien. Keine zweite Factory, Datenbank oder
Modelltransportarchitektur und keine neue Drittanbieterabhängigkeit wurden eingeführt.

## Tatsächlich ausgeführte Prüfungen

| Prüfung | Ergebnis | Aussagegrenze |
|---|---|---|
| Gesamtes pytest einschließlich UI/API/Security | **627 bestanden, 0 Fehler, 0 übersprungen** | technische synthetische Regressionen, 59 zusätzliche Tests gegenüber 568 |
| Kombinierte Statement-/Branch-Coverage | **89,08 %**, unveränderte Mindestschwelle 80 % | keine Gleichsetzung von Coverage mit Sicherheit/Qualität |
| Separater Privacy-Security-Umfang | **313 bestanden**, strenger JUnit-Gate-Parser bestanden | entspricht lokaler Verzeichnisauswahl des CI-Jobs, kein Remote-Lauf |
| Ruff Lint/Format, Compileall, pip check | bestanden | statische Qualität/Syntax und Dependencykonsistenz |
| Bandit | unverändertes MEDIUM-Severity/Confidence-Gate bestanden | LOW und unbekannte Fehler nicht pauschal freigegeben |
| pip-audit | vier Hash-Lockdateien, keine bekannten Befunde, Exit 0 | OS-Pakete separat beurteilen |
| Sechs Compose-Varianten | CPU/GPU/Provisioning/CI-Mock/University/GROBID statisch bestanden | keine echte Hochschul-/GROBID-Abnahme |
| Endgültige App-Images / Docker-E2E | gebaut, alle Healthchecks; Legacy D, kriteriumsweises E, Mosbach-Gates, Kontextbudgets, geschützte Provenance, Befundkorrektur und menschliche Finalisierung bestanden | nur In-Process-/HTTP-Mocks, keine echten Gewichte |
| Docker-Netzprobe | erlaubter gepinnter lokaler Mockaufruf; kontrollierter separater Listener aus drei privaten Namespaces nicht erreichbar | gezielter IPv4/TCP-Test, kein vollständiger Hochschul-Egressnachweis |
| Gitleaks / Git-DLP / Artefaktcanaries / Diff | lokale History und zugelassener Arbeitsbaum, Index-/Reportprüfungen und CRLF-bewusster Whitespacecheck bestanden | keine Geheimnisfreiheitsgarantie beliebiger Texte oder privater Festplattenpfade |
| Trivy, beide aktuellen App-Images | vollständige Offlineberichte; bestehendes Gate für behebbare HIGH/CRITICAL bestanden | offene OS-Befunde unten, keine behauptete Schwachstellenfreiheit |

Lokale JUnit-/Coverage-/Scanner-/JSON-/CSV-Berichte liegen ausschließlich unter
ignoriertem `reports/`. Die bestehende CI erhält die neuen Securitytests über ihre
Verzeichnisauswahl und zusätzliche synthetische Fairness-/Ablationsbefehle. Der
verpflichtende `thesishounds-ci-gate` bleibt erhalten; keine Schwelle, Ausnahme oder
Skipregel wurde abgesenkt. Kein GitHub-Actions-Lauf, Commit, Push oder Remote-Ruleset-
Eingriff wurde vorgenommen. Der isolierte Teststack wird nach der Prüfung entfernt.

## Ausgeführte Experimente: strikt Mocknachweise

`evaluation.lab --all-variations`: **100 vollständig ausgeführte Läufe**, fünf
Architekturen × zehn Bedingungen × zwei Wiederholungen, **460 Mockaufrufe** und
**90** gepaarte Variationsvergleiche. Pro Lauf: A 1, B 3, C 3, D 4, E 12 Calls.
Der deterministische Mock erzeugt keine fachlich validierten Befunde.
E prüft im Mock offene Fragen zweimal, wenn kein geklärter
Konsens entsteht; mehr Aufrufe werden nicht als Qualitätsgewinn interpretiert.

`evaluation.lab --all-ablations --repeats 1`: **20 vollständig ausgeführte Läufe**,
**80 Calls**, **15** Paarvergleiche. Je Paar exakt ein Flag verändert, gleiche
Dokument-/Kataloghashes. E: Basis 12, ohne Retrievalranking 12, ohne dynamische
Zusatzagenten 9, ohne Verifikation 4 Calls. Für Architekturen ohne betreffende
Komponente ist ein Nullunterschied ein erwarteter Kontrollfall. Retrievalablation
betrifft sowohl Kriteriums- als auch Challengeauswahl; Kontext- und Privacygrenzen
bleiben unverändert.

Die beobachteten Mocklaufzeiten sind reine Softwaremessungen. Sie belegen weder
Inferenzgeschwindigkeit noch menschliche Zeitersparnis. Precision, Recall,
Falsch-positive-Kritik und Halluzinationsrate bleiben ohne tatsächliche menschliche
Adjudikation `null`; Punktevergleiche bleiben wegen deaktivierter KI-Punktevergabe
ebenfalls `null`. Es wurden keine Expertenlabels oder echten Modellresultate erfunden.

Privacy-Ablation erneut: 12 Szenarien × vier Architekturen = 48 Memory-Sink-Läufe;
D blockiert alle elf unerlaubten Aktionen und erlaubt die eine PUBLIC-Lokalkontrolle.
Academic-Benchmark erneut: sechs Quellen- und vier Formalienfälle bestanden, keine
externen Anfragen. Diese engen Experimente beweisen keine repräsentative Fachgüte.

## Containerbefunde bleiben offen

Trivy 0.76.2 mit der lokal vorliegenden öffentlichen DB vom **26.11.2026 19:04 UTC**.
Die eigentlichen Imagescans und Gates liefen offline mit `--network none`.
Je Image weiterhin 382 Paket/CVE-Zuordnungen: 114 LOW, 148 MEDIUM, **100 HIGH**,
**2 CRITICAL**, 18 UNKNOWN; keine vom Scanner als behebbar gemeldeten HIGH/CRITICAL.
Die zwei CRITICAL betreffen weiterhin libsqlite3-0 und zlib1g. Kein neuer Ignoreeintrag
und keine Ausnutzbarkeits-/Unbedenklichkeitsbehauptung. Risikoannahme/Patchplan und
Produktionsfreigabe bleiben offen; Details im [Hardening-Bericht](../security/hardening_results.md).

Gescannt: Backend `sha256:d2696dd28cfaf513b82f196e4fe3bf77a9988b7e28b88ee5b77f798c84cae018`,
Frontend `sha256:f5d0153598868343302e806f52f28fbc5369a1a5c53f2e35a493b171d4263ba2`.
Ein paralleler Trivylauf konnte den gemeinsamen Cache nicht sperren; der Backend-
Vollscan und dessen Gate wurden anschließend einzeln wiederholt. Der Zwischenfehler
ist kein bestandener Scan und führte zu keiner Regeländerung.

## Fehlende Nachweise und Entscheidungen

Keine reale lokale Modell-/Embedding-/GPU-Studie, kein menschlich adjudizierter
Referenzkorpus, keine repräsentative Retrieval-, Konsistenz-, Fairness- oder
Zeitersparnismessung. Keine echte Parser-/OCR-/GROBID- oder Hochschuleinsatzabnahme.
SSO, TLS-/Serviceidentität, Host-DNS/IPv6, Verschlüsselung/Backups/Swap, dauerhafte
Audit-/Recovery-/Löschprozesse und rechtliche/organisatorische Freigaben bleiben offen.

Mit dem Professor zu klären: freigegebene Kriterien und kritische Befundarten,
Referenzpassagen/Adjudikation, erlaubte Identitätsmaskierung, geeignete lokale
Embedding-/Modellartefakte und Hardware, sinnvolle Budgets/Eskalationsschwellen und
Freigabe einer Feedback-/Zeit-/Biasstudie. Siehe [Grenzen](limitations.md),
[Fairness](fairness.md), [Ablation](ablation_studies.md), [Performance](performance.md),
[Feedback](human_feedback.md) und [Hochschulblocker](../security/production_readiness.md).
