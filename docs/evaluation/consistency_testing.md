# Consistency and controlled variation

Beitrag: OFF-5, ENG-9. Das Lab wiederholt gleiche Dokument-/Katalogbedingungen und
speichert Modellzuordnung, Prompts, Konfiguration und Fehler. Verglichen werden
kanonische Befund-Fingerprints, Kriterienurteile und wörtliche Belege. Zufällige
Finding-UUIDs fließen nicht in die Übereinstimmung ein. Ein einzelner Lauf liefert
NEEDS_REPEATS statt einer erfundenen Konsistenzzahl.

Variiert wird jeweils nur ein Faktor gegenüber einer Baseline mit ausdrücklich
synthetischem Personen-/Firmennamen: Studierendenname, Unternehmensname,
Absatzformatierung, Katalogreihenfolge, Agentenausführungsreihenfolge, manuelle
Modellzuordnung oder hinzugefügte Prompt Injection. Kriterien- und Agentenreihenfolge
sind getrennte Eingriffe: erstere verändert den Katalog-/Promptindex, letztere nur
die getrennte Ausführung. A hat keine getrennten Agenten; diese Variante wird dort
als nicht angewendet markiert. Ihre Differenz darf nicht kausal interpretiert werden.

Mechanische Metriken: paarweise Finding-Jaccard-Ähnlichkeit und Übereinstimmung der
Kriterienurteile; Varianten werden mit derselben Architektur und Wiederholung der
Baseline gepaart. Die gespeicherten Zitate/Evidenzstatus erlauben die Belegkontrolle.
Hohe Wiederholbarkeit kann systematisch falsche Bewertungen reproduzieren. Deshalb
werden Konsistenz, fachliche Validität und Bias ausdrücklich nicht gleichgesetzt.

```powershell
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m app.evaluation.lab --provider mock --all-variations --repeats 2 --output-dir reports/evaluation-variations
```

Die Mock-Pilotstudie besitzt keine externe Validität. Echte Modelle können auch bei
Temperatur 0 variieren; fachliche Relevanz der Unterschiede muss durch verblindete
Experten geprüft werden. Reihenfolge randomisieren/counterbalancen und statistischen
Plan präregistrieren, bevor Verallgemeinerungen oder Biasbehauptungen entstehen.
