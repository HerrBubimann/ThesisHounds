# Wissenschaftliche Konsistenz und Evidenzqualität

OFF-3/4/5: strukturierte Beziehungen ergänzen den bestehenden kriteriumsweisen
Zweitreview. Die Analyse erfindet weder Hochschulkriterien noch eine Graphdatenbank.

Elf Aspekte: Forschungsfrage, Ziel, Theorie, Forschungsstand, Methode, Datenerhebung,
Analyse, Ergebnisse, Diskussion, Limitationen und Fazit. Der lokale Strukturindex
liefert referenzierte Kandidaten, keine zuverlässige semantische Inhaltsklassifikation.
Leere Kandidatenlisten bedeuten keine fehlenden Kapitel oder unbeantworteten Fragen.

Das lokale Modell kann unter dem zugewiesenen Kriterium ALIGNED,
POSSIBLE_CONTRADICTION, UNANSWERED, UNSUPPORTED_CONCLUSION oder NOT_ASSESSABLE
vorschlagen. Der Server fordert für eine geerdete Beziehung mindestens zwei
verschiedene echte Textspannen und unterschiedliche Aspekte. Falsche/duplizierte
Belege bleiben INSUFFICIENT_EVIDENCE. Auch ein GROUNDED_PROPOSAL beweist keine
fachliche Richtigkeit und erzeugt keinen automatischen Kritikpunkt. Nicht aktivierte
DHBW-Profile bleiben Kandidaten; die Demo verwendet ausdrücklich Beispielkriterien.

| Evidenzzustand | Bedeutung |
|---|---|
| DIRECT_EVIDENCE | ein passendes Textzitat; keine bestätigte Interpretation |
| MULTIPLE_EVIDENCE | mehrere unterschiedliche passende Belege |
| INFERRED | textlich geerdeter Beziehungsvorschlag, Schlussfolgerung menschlich prüfen |
| CONTRADICTORY | Konflikt mit textlich passendem Gegenbeleg; dessen Deutung bleibt zu prüfen |
| INSUFFICIENT | falsche/unzulängliche Belege, Zitat außerhalb Modellkontext oder ungelöster Reviewkonflikt |
| NOT_ASSESSABLE | fachlich im gelieferten Kontext nicht beurteilbar |

Vorhandene `evidence_status`-Textprüfungen bleiben als separate Dimension erhalten.
Unterstützende und widersprechende Belege tragen Scope, Klasse, Originalspannen
und Prüfstatus. Reasoning, offene Fragen, unverifizierbare Aspekte, Verifikationsrunden
und menschliche Feedbackversionen werden zusätzlich gespeichert. Ursprüngliche
Modellaussagen bleiben erhalten; Korrekturen sind getrennte Vorschläge/Annotationen.

Challenge sucht gezielt Gegenargumente und andere Kapitel. Eine spätere Zustimmung
löscht frühere Konflikte nicht. Modellkonsens ist kein Wahrheitsnachweis; UNSUPPORTED
mit erfundenem Gegenbeleg wird nicht als bestätigte Widerlegung gewertet. Alle
Prüfungen bleiben in der lokalen Gateway-/Privacygrenze.
