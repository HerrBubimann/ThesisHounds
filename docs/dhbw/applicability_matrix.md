# Anwendbarkeit und Mosbach-First

Die anwendbare Studien- und Prüfungsordnung bildet den Rahmen. Darunter gilt die
Reihenfolge: DS/KI Mosbach für konkreten Jahrgang → Mosbacher Bewertungsbogen →
ausdrücklich delegierte WI-Mosbach-Vorgaben → Fakultät Wirtschaft Mosbach →
DHBW-Ergänzungen → allgemeine Wissenschaftsstandards → andere Standorte nur Orientierung.

| Studiengang | Jahrgang | Arbeit | Öffentliche Kandidaten | Noch fehlend |
|---|---|---|---|---|
| DS/KI Mosbach | DS25 | PA1 | DS-Seite, PA1-Paket, gemeinsames Formular, Fakultät 5.0 | StuPrO-/Versionsbindung, Konfliktentscheidung, menschliche Freigabe |
| DS/KI Mosbach | DS24 | PA2 | DS-Seite, PA2-Paket, gemeinsames Formular, Fakultät 5.0 | Wie oben; widersprüchlichen Moodle-Jahrgang klären |
| DS/KI Mosbach | DS23 | BA | DS-Seite, BA-Paket und BA-Regeln 2026, gemeinsames Formular, Fakultät 5.0 | Dokumentkopf „Stand 2024“ versus Titel 2026 und Seitenzählung klären |
| DS/KI Mosbach | andere | alle | kein übertragbares Profil | Originalvorgaben für genaue Kombination |
| WI Mosbach | alle | alle | noch kein eigenständiges Profil | Programmeigene Bestätigung; DS-Delegation legitimiert keine umgekehrte Übertragung |
| andere Standorte | alle | alle | höchstens Orientierung | niemals automatisch verbindlich |

`InstitutionalRegistry.resolve` wählt **exakt** Studiengang, Jahrgang und Arbeitstyp.
Mehrere Profilversionen werden nicht durch eine vermeintlich neueste ersetzt.
Unbekannte Gültigkeit, fehlende Prüfsumme/Freigabe oder offene Konflikte verhindern
Aktivierung. Menschliche Konfliktentscheidungen müssen am Profilhash hängen;
eine rangniedrigere Regel kann dabei den Prüfungsrechtsrahmen nicht überstimmen.
Nicht öffentliche Quellen werden im DEVELOPMENT-Katalog weder inhaltlich noch als
Metadaten ausgegeben. Eine behauptete höhere Clearance öffnet diesen Bestand nicht.

Tests: `test_institutional_rules.py`, `test_academic_privacy.py`, `test_academic_workflow.py`.
