# Lokale Fairness- und Neutralitätstests

OFF-4/5: bewertungsirrelevante Variationen werden kontrolliert untersucht, ohne
Fairness oder Biasfreiheit zu behaupten. Das bestehende A–E-Labor wird verwendet.

`--all-variations` enthält Basis, Studentenname, Unternehmensname, namensbezogenes
Geschlechtsmerkmal, Kriterienreihenfolge, irrelevante Absatzformatierung und
vermeintliche Notenerwartung. Zusätzliche vorhandene Bedingungen variieren Agenten-
reihenfolge, Modellzuordnung und eingebettete Anweisungen. Jede Bedingung verändert
nur den bezeichneten Faktor; Modell-/Dokument-/Katalogkonfiguration und Scope sind
im Manifest nachprüfbar. Personen/Firmen und Notenhinweise sind ausschließlich synthetisch.
Namensassoziationen sind keine zuverlässigen Aussagen über die Identität einer Person.

Die Paarung vergleicht dieselbe Architektur, Wiederholung und Ablation mit der
entsprechenden Basis. Ausgewiesen werden Kritikanzahl/-arten, Evidenzverteilung,
Kriteriumsurteile und Befundfingerprints. Punkteabweichungen bleiben `null`, weil
KI-Punktevergabe deaktiviert ist. Unterschiede können untersucht werden, sind aber
allein keine nachgewiesene kausale Diskriminierung. Ein deterministischer Mock kann
die Paarungssoftware prüfen, aber keine Fairness eines realen Modells messen.

Der lokale Kontextpfad maskiert nur explizit bezeichnete Identitätsheader auf der
ersten Seite und erhält Textlängen/Offsets. Keine globale Entfernung von Firmennamen:
fachlich relevante Informationen im Fließtext bleiben erhalten. Header können
trotzdem fachlich relevant sein; Auswahl und Maskierung sind vor realem Einsatz
mit Gutachtern zu prüfen. Kein Anonymitätsversprechen, kein Absenken der Schutzklasse.

Reproduktion mit synthetischen Daten und In-Process-Mock:

```text
python -m app.evaluation.lab --all-variations --output-dir reports/advanced-fairness
```

Vorher `PYTHONPATH=backend` setzen. Reale lokale Modellstudien benötigen freigegebene
Artefakte, Hardware, korrespondierende Expertenreferenzen, mehr Fälle, Wiederholungen,
Counterbalancing und Unsicherheits-/Effektgrößen. Menschliche Zeitersparnis und
Automation Bias erfordern eine separate genehmigte Nutzungsstudie.
