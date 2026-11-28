# Frontendtests und Sichtprüfung

Die neuen Tests laufen in den bestehenden pytest-Suiten und damit im unveränderten
`thesishounds-ci-gate`. Die kombinierte Coverage-Grenze bleibt 80 %. Kein neuer Code
wird zur Umgehung dieser Grenze ausgenommen.

| Prüfung | Nachweis |
|---|---|
| Vollständiger menschlicher Ablauf | `tests/integration/test_assessment_frontend.py` |
| Hauptnavigation, Backendausfall | `tests/integration/test_frontend.py` |
| Anlageassistent, Sitzungsspeicher, Fallliste, technische Seiten | `tests/integration/test_frontend_workspace.py` |
| ACL-/Embargoprojektion, Regeln, Modellmatrix, Original-PDF-Integrität | `tests/integration/test_frontend_read_api.py` |
| Kontrollierte PDF-Auswahl und Originalpipeline | `tests/integration/test_pilot_workflow.py` |
| Notizen, Methode, Sitzungszeit | `tests/integration/test_reviewer_workspace_ui.py` |
| Bestehende Sicherheitsgrenzen | vollständige `tests/security`-Suite und API-Regressionssuite |

Alle Modellantworten dieser automatisierten Tests sind MOCK/SYNTHETIC. Sie sind
kein Nachweis fachlicher Modellqualität oder menschlich validierter Evaluation.

`scripts/frontend_browser_qa.py --stage after` startet ausschließlich temporäre
Loopbackdienste mit Mock-Inferenz und synthetischen Daten, verwendet installiertes
Chrome headless und beendet die eigenen Prozesse danach. Ausgabe:
`reports/frontend/after-*.png` sowie `after-browser-checks.json`. Das Skript prüft
zuvor belegte Ports und berührt keine bereits laufenden Dienste. Das `before`-
Material wurde vor dem Umbau erfasst; ein erneuter before-Aufruf stellt keinen alten
Quellstand wieder her.

Mit `--stage after --pdf-smoke` erzeugt das Skript eine lokale synthetische Test-PDF
und ausschließlich temporäre Testkatalog-/Artefaktnachweise unter dem Testtempordner.
Es verändert keine Repositoryfreigaben. Der echte UI-PDF-Schalter wird aktiviert;
der Lauf verlangt mindestens einen tatsächlich gerenderten PDF-Canvas. Ein separater
Screenshot und das Originprotokoll liegen unter `reports/frontend/pdf-smoke/`.
Die Sichtprüfung bestätigte die gerenderte Originalseite und ausschließlich den
lokalen Streamlit-Origin. Dies ist keine allgemeine PDF-Sicherheitsabnahme.

Aktuelle Ergebnisse und verbleibende Einschränkungen stehen in
[limitations.md](limitations.md). Ein lokaler grüner Lauf ist kein ausgeführter
GitHub-Workflow, Docker-Image-Build oder Merge-Schutz-Nachweis.

## Ergebnis vom 28.11.2026

940 Tests bestanden, 87,05 % kombinierte Coverage. Die frühere Suite blieb erhalten;
veraltete UI-Verträge wurden auf den neuen Anlageassistenten und auf tatsächliche
geschützte Evidence-API-Antworten umgestellt. Neue Tests decken insbesondere
Falllisten-ACL/Embargo, Original-PDF-Integrität, wiederherstellbaren Sitzungsentwurf,
unveränderte Erstfreigabe sowie Snapshotherkunft und Originalspannen der Quellenansicht ab.
