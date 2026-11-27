# Einzelkomponentenablation und Architekturvergleich

OFF-2/3/5. Vorhandenes `evaluation.lab` führt A–E mit identischen synthetischen
Dokumenten und Kriterien aus: einfacher Single-LLM-Batch, spezialisierter Single-
LLM-Workflow, feste Multi-LLM-Zuordnung, dynamische Zusatzagenten und adaptive
Eskalation mit unabhängiger Gegenprüfung. Die Pflicht-Coverage bleibt verbindlich.

Zusätzlich stehen `baseline`, `no_retrieval`, `no_dynamic` und `no_verification`
zur Verfügung. Pro Vergleich wird genau ein Komponentenflag verändert. Hashes
belegen gleiche Dokument-/Katalogdaten; Paarung erfolgt innerhalb derselben
Architektur, Variation und Wiederholung. Verschiedene Ablationen werden nicht
als Wiederholungen zusammengefasst. Nicht verwendete Komponenten einer Architektur
dürfen einen Nullunterschied zeigen; dies ist ein negativer Kontrollfall.

`no_retrieval` verwendet Quellreihenfolge statt hybrider Auswahl; dieselben Mengen-
und Modellkontextgrenzen bleiben erhalten. Es deaktiviert keine Privacykontrolle.
`no_dynamic` lässt Pflichtbefunde erhalten. `no_verification` ist ausschließlich eine
bewusste synthetische Laborbedingung; der Anwendungsstandard bleibt E. Alle Modi
verwenden weiterhin Gateway-/IFC-/Policy-/Quoteprüfungen und erlaubte lokale Ziele.

```text
python -m app.evaluation.lab --all-ablations --repeats 1 --output-dir reports/advanced-ablation
```

Das globale Aufrufbudget begrenzt auch Wiederholungen/Ablationen; erschöpfte Läufe
werden FAILED/INCOMPLETE statt erfolgreich. Ein vollständiges faktorielles Experiment
kann ein ausdrücklich gesetztes höheres Budget bis zur bestehenden Obergrenze
erfordern. Es gibt keine automatische Budgetausweitung oder externen Ersatzdienst.

Berichte zeigen Aufrufdifferenzen und Unterschiede in Kritik/Evidenz/Urteilen.
Precision/Recall, falsche Kritik und Halluzinationsrate bleiben ohne dokumenten-/
kataloggebundene menschliche Adjudikation `null`. Weniger Calls oder mehr Modelle
beweisen keinen Qualitätsvorteil. Die HumanReferenceSet-Schnittstelle ist vorhanden;
es wurden keine menschlich geprüften Referenzbefunde erfunden.
