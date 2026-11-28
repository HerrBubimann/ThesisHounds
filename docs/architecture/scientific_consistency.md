# Wissenschaftliche Konsistenz und Evidenzqualität

OFF-3/4/5: strukturierte Beziehungen ergänzen den bestehenden kriteriumsweisen
Zweitreview. Die Analyse erfindet weder Hochschulkriterien noch eine Graphdatenbank.

Fünfzehn Aspekte: Forschungsfrage, Ziel, Theorie, Forschungsstand, Methode, Datenerhebung,
Analyse, Ergebnisse, Diskussion, Limitationen, Fazit, Hypothese, Quelle, Datensatz
und Experiment. Der lokale Strukturindex
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

## Strukturierte wissenschaftliche Aussagen

`AIObservation.scientific_claims` unterscheidet Tatsachenbehauptung, Hypothese,
eigenes Ergebnis, Schlussfolgerung, methodische Annahme, Verallgemeinerung und
literaturbasierte Aussage. Pro Kriterium maximal sechs Kandidaten mit Originalstelle,
Unterstützung, Gegenbelegen, Literatur-IDs und begründeter Modellbedenkenkategorie.
`update_evidence` prüft diese mit dem vorhandenen Evidence Validator und der lokalen
Citation Verification Engine. Mehrdeutige Literatur-IDs werden nicht aufgelöst.
Quellenmetadaten bestätigen keine semantische Unterstützung. Fehlende Belege,
unpassende Zitate und mögliche fachliche Fehler sind getrennte Zustände; das Modell
kann keinen fachlichen Fehler deterministisch bestätigen.

Die JSON-Beziehungsgraphen erweitern dieselben Beziehungen. Knoten tragen genaue
Originalreferenzen, Kanten Kriterium, Herkunft und Evidenzzustand. Selbst geerdete
Beziehungen bleiben CANDIDATE und fachlich menschlich zu prüfen. Die ersten beiden
Belegstellen gehören in der Modellstruktur zu Quelle und Ziel der Beziehung; weitere
Stellen liefern Kontext. Diese Zuordnung selbst ist eine Modellinterpretation.
Regex-Kapitelanker sind Suchkandidaten, keine semantische Graphvalidierung. Aus
leeren Kandidatenlisten folgt kein nachgewiesener fehlender Zusammenhang.

Der initiale Review liefert den Critical-Reviewer-Vorschlag; die vorhandene unabhängige
Gegenprüfung übernimmt die Counter-Reviewer-Rolle. Höchstens zwei Runden teilen
ein `agent_timeout_seconds`-Zeitbudget für Routing und Inferenz. Der deterministische
Arbiter fasst Status, Konflikt und menschlichen Klärungsbedarf zusammen; er erzeugt
keinen Modellkonsens und keinen neuen fachlichen Wahrheitsanspruch. Vorherige
Modellaussagen werden als Interpretationen weitergegeben und Originalreferenzen
erneut geprüft. Details und Messgrenzen: [Prüfbericht](../evaluation/scientific_reasoning_results.md).
