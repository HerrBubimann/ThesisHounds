# Experiment design

Ergänzung 27.11.2026: Das bestehende Lab unterstützt einen getrennten
**Planungsvergleich A/B/C** auf demselben D-Kriterienkern: keine Zusatzplanung,
Regexbaseline, semantischer LLM-Plan. Diese Varianten heißen `planning_variant`
und ändern die historischen Architekturbezeichnungen unten nicht.
[Protokoll und Reproduktion](../architecture/semantic_adaptive_planning.md#abc-vergleich-im-bestehenden-lab),
[tatsächliche Mocknachweise und offene Realabnahme](semantic_planning_results.md).

Beitrag: OFF-5, ENG-8. Protokoll v1, 2026-11-26. Das neue Lab benutzt denselben
kriteriumsweisen Reviewer, Gateway, Katalog, Dokumenttyp, Factory und dieselbe Policy
wie der vertikale MVP. Es ersetzt nicht die Legacy-A–D-Modi, deren historische
Kontrollen teilweise andere Unterschiede enthalten.

| Arm | Ausführung im neuen Lab |
|---|---|
| A | ein Modell, ein Batchprompt für alle Katalogkriterien |
| B | ein ausgewähltes Modell, getrennte kriterienspezifische Aufrufe |
| C | aufgabenspezifische Modellzuordnung, feste Pflichtkriterien |
| D | C plus kontrollierte thematische Zusatzagenten |
| E | D plus begrenzte adversariale Gegenprüfung und erneute deterministische Belegprüfung |

Alle Arme behalten grundlegende deterministische Quote-Audits. Sicherheitsmaßnahmen
werden nicht als Experiment abgestellt. Der Vergleich D↔E isoliert deshalb das
zusätzliche Reviewpaket; er beweist keinen isolierten Effekt eines einzelnen
deterministischen Validators. Tatsächlich eingesetzte Modell-IDs/Digests und die
Zuordnungsquelle werden gespeichert. Fehlende Modellvielfalt ist zu berichten.

Pro Lauf: identische serverseitige synthetische Fixture und Beispielkatalog,
separates Budget, vollständige Konfig-/Promptnachweise, Eingabemanifest, Modellmetadaten,
Umgebung und Rohbeobachtungen. Modell-Seed bleibt ungesetzt und wird als `null`
dokumentiert. Auch Temperatur 0 ist keine Determinismusgarantie. Reale GPU-/Token-
und Laufzeitbenchmarks erfolgen separat auf bestätigter lokaler Infrastruktur.

Primäre spätere Endpunkte: Rate unberechtigter Kritik und Recall fachlich relevanter
Befunde. Mindestens unabhängige Expertenreferenzen mit Adjudikation vorsehen;
Abweichungen nicht automatisch einem einzigen Expertenurteil unterwerfen.
`HumanReferenceSet` verbindet Dokument-/Kataloghash und explizit menschlich
adjudizierte Vorhersage-Fingerprints mit Referenzbefunden. Textähnlichkeit oder ein
gleicher Beleg sind kein automatisches semantisches Goldlabel.

Ohne vollständige menschliche Adjudikation bleiben Precision, Recall, falsche
Kritik, falsch negative Befunde, Halluzinationsrate und Quellenkorrektheit leer.
Mechanische Belegtreffer und Kriterienabdeckung bleiben getrennte Metriken.
Punktabweichungen sind mangels freigegebener Punkteskala nicht implementiert.

Vor einer fachlichen Studie: Hypothesen, primäre Metriken, Matchingregeln,
Stichprobengröße/Power, Stratifikation, Ausschlüsse, Ausführungsreihenfolge und
Fehlerbehandlung präregistrieren. Gegenwärtig gibt es keine Teilnehmerstudie,
keine freigegebenen echten Arbeiten und keine bestätigten Qualitätsgewinne.
