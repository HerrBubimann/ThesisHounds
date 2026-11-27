# Scientific workflow security evaluation

Ergänzung 27.11.2026: `app.evaluation.privacy_lab` bietet eine reproduzierbare
12×4-Control-Ablation mit Memory-Sinks: A ungeschützt, B ignorierter Promptmock,
C Policy, D Policy/IFC/Zielprüfung. Unsichere Adapter sind keine Runtimeprovider.
Keine tatsächliche Netzwerkverbindung, empirische LLM-Robustheit oder Hostisolation
wird daraus abgeleitet. Ergebnisse: [Mosbach-Nachweise](mosbach_results.md).

Beitrag: OFF-2/5, ENG-10. Die bisherige Privacy-Architektur bleibt verbindlich.
Neue Modellaufrufe laufen ausschließlich durch denselben Gateway und die gleiche
Policy; RESTRICTED/CONFIDENTIAL/INTERNAL bleiben in DEVELOPMENT gesperrt. Das Lab
verarbeitet nur servergenerierte PUBLIC-Fixtures und akzeptiert keine Dokumentpfade
oder freie Dokumenttexte. JSON-/CSV-Exporte sind lokale synthetische Forschungsartefakte,
keine neue Exportfreigabe für Gutachten oder menschliche Bewertungen.

Zusätzliche Tests prüfen Policy-Vorrang vor Capability-Scores, exakte Digestbindung,
Ressourcenlimits, unabhängige Reviewerwahl, erhaltene Datenklasse beim Review eines
vertraulicheren Befunds, Gegenargumente mit erfundenen Zitaten, Coverage-Grenzen,
Finding-/Analysezuordnung und das Ergebnisembargo des Evidence Explorers.
Quellenprüfung führt keine HTTP-Anfragen aus; unbestätigte Existenz/Retraktion und
fehlender Volltext bleiben unbekannt. Alte Quellen erhalten keine automatische Strafe.

Kein Shell-/Python-/Netzwerktool wurde hinzugefügt. Adaptive Templates vergeben keine
zusätzlichen Rechte. Die vorhandenen Data-Leakage-Canaries, Artefakt-Uploadprüfungen
und das verpflichtende `privacy-security`/`thesishounds-ci-gate` bleiben bestehen.
Neue Unit-/Integrations-/Securitydateien werden durch die vorhandenen Testpfade
automatisch Teil des Gates; schwere echte Modellbenchmarks sind kein CI-Job.

Die bereits gelieferte Docker-Listenerprobe wird erneut auf dem lokalen synthetischen
Stack ausgeführt. Dieser Nachweis ersetzt weiterhin weder Hochschulnetz-/SSO-/
Speicherabnahme noch Angriffe auf echte PDF-/OCR-Schichten. Der Text-Injectiontest
prüft keine unsichtbaren PDF-Fontangriffe; solche Angriffe bleiben Parser-/Studienarbeit.
Keine rechtliche, organisatorische oder fachliche Freigabe wird aus Mocktests abgeleitet.
