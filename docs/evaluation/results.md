# Scientific engineering results

Historischer Stand dieser Engineering-Iteration. Aktuelle Ergebnisse einschließlich
Kontextmanagement, Fairness/Ablation, Feedback und 627 Regressionen:
[Advanced Review](advanced_review_results.md).

Stand: 2026-11-26. Abschließender lokal beobachteter Stand dieser Erweiterung.
Es wurden ausschließlich synthetische Daten und Mock-Provider verwendet.

## Tatsächlich ausgeführte Pilotläufe

- Capability-Probes v2: 3 konfigurierte Mock-Presets × 11 Dimensionen × 2 Wiederholungen
  = 66 Schema-/Timing-Probes. Datei: `reports/model-capabilities-mock.json`.
- Evaluation Lab: 5 Architekturen × 8 Bedingungen × 2 Wiederholungen = 80 abgeschlossene
  synthetische Mock-Durchläufe mit insgesamt 368 Modelladapteraufrufen.
- Adapteraufrufe über alle Bedingungen: A 16, B 48, C 48, D 64, E 192.
- 40 Wiederholungsgruppen und 70 Baseline-Variantenpaare wurden gespeichert.
- Alle 80 Läufe melden NO_HUMAN_REFERENCES. Precision/Recall, unberechtigte Kritik,
  falsch negative Befunde, Halluzinationsrate und Quellenkorrektheit bleiben leer.
- JSON und CSV liegen unter `reports/evaluation-variations/` und sind durch die
  bestehenden Repository-/Dockerregeln von Veröffentlichung ausgeschlossen.

Diese Zähler beschreiben tatsächlich ausgeführte Softwarepfade. Sie sind **keine**
Messung realer Qwen-/Mistral-/Llama-Qualität, keine empirische Überlegenheit von E
und kein Beleg für weniger Halluzinationen. Laufzeit-/Ressourcenwerte stehen in den
Rohdateien und betreffen diesen lokalen Mocklauf.

## Abschließende Verifikation

| Prüfung | Tatsächlich beobachtetes Ergebnis | Aussagegrenze |
|---|---|---|
| Gesamte Pytest-Suite | 448 bestanden, keine Fehler/Skips | 34 zusätzliche Testfälle gegenüber der Privacy-Basis; ausschließlich synthetische Daten |
| kombinierte Line-/Branch-Coverage | 89,53 %, Pflichtschwelle unverändert 80 % | konfigurierte Python-Quellen, keine fachliche Validitätsmetrik |
| Ruff lint und Format | bestanden | statische Codeprüfung |
| compileall | bestanden | Syntax, keine fachliche Prüfung |
| Docker-Compose-Validator | alle 5 Varianten bestanden | Universität nur statisch geprüft, Start weiterhin gesperrt |
| Backend-/Frontendbuild und Healthchecks | bestanden im getrennten Projekt thesishounds-science-ci | Mockbetrieb ohne echte Modellgewichte/GPU |
| Docker-End-to-End | Legacy D und neuer kriteriumsweiser E-Pfad bestanden | überprüft Routing, Coverage, Zusatzagenten, Gegenprüfung, Ergebnisembargo, Evidence Explorer und menschliche Schlussfreigabe |
| kontrollierte Netzprobe | IP-gepinnte interne Mock-Inferenz erlaubt; externer Mocklistener aus 3 privaten Namespaces nicht erreichbar | kein vollständiger Hochschul-/DNS-/IPv6-/TLS-Abnahmenachweis |
| Gitindex-DLP und Diffprüfung | 0 gesperrte indexierte Pfade, Diff-Check erfolgreich | netzwerkloser read-only Git-Prüfcontainer; kein History-/Inhaltsscan |
| Artefakt-Canaryprüfung | bestanden, aktuelle lokale Reports markerfrei | bekannte synthetische Marker, keine universelle DLP |
| Bandit | keine blockierenden Befunde ab MEDIUM-Schweregrad/-Konfidenz | schließt LOW-/unbekannte Probleme nicht aus |
| pip-audit, alle 4 Lockfiles | keine bekannten Schwachstellen gemeldet | Datenbankstand zum Lauf; keine Image-/Modell-Supply-Chain-Freigabe |
| pip check | keine verletzten Paketabhängigkeiten | lokale Testumgebung; keine Dependency-/Lockänderung erforderlich |
| GitHub Actions / Ruleset, Gitleaks-Historyscan, Trivy | nicht remote/lokal ausgeführt bzw. verifiziert | keine erfolgreiche Remote-Pipeline oder aktive Merge-Sperre behauptet |

Die bestehende Pipeline sammelt die neuen deterministischen Tests über unveränderte
Unit-/Integrations-/Securitypfade. Der Docker-Job führt zusätzlich den neuen E-Pfad
über das vorhandene Smoke-Skript aus. Name und Pflichtstatus von
`thesishounds-ci-gate` sowie das Ruleset wurden nicht gelockert. Echte Modellbenchmarks
bleiben getrennte, manuell gestartete lokale Versuche; CI verwendet Mocks.

Zuordnung zur Projektaufgabe: OFF-1 erhielt die Requirements-Matrix; OFF-2 den
Privacy-first-Router und die kontrollierte adaptive Architektur; OFF-3 Coverage,
geteilte Belegprüfung und adversariale Reviews; OFF-4 Belegnavigation und selektive
menschliche Befundfreigabe; OFF-5 reproduzierbare Capability-, A–E-, Konsistenz- und
Variationsversuche mit ehrlicher Referenzlücke. Details und Testdateien stehen in
`../requirements/traceability.md`.

Noch erforderlich: offizielle Kataloge und Prozessabstimmung, menschlich geprüfte
Referenzen, bestätigte lokale Modellartefakte/Hardware, fachliche Capability-Scores,
geplante Experimente mit angemessener Stichprobe und die unveränderten organisatorischen
Produktionsfreigaben. Insbesondere ist **kein fachlicher Qualitätsgewinn** gegenüber
menschlicher Begutachtung oder einfacheren Architekturen nachgewiesen.

Die Rohdateien unter `reports/` sind lokal und ignoriert. Der temporäre synthetische
Teststack wird nach den Prüfungen bereinigt. Es wurden keine echten Arbeiten geöffnet,
keine vertraulichen Suchanfragen gestellt, keine externen KI-Provider genutzt und
keine Änderungen veröffentlicht oder gepusht.
