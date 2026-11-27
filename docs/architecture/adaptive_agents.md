# Mandatory and adaptive assessment agents

Beitrag: OFF-2/3, ENG-2/3. `AISecondReviewer` bearbeitet jedes Katalogkriterium
verbindlich. `check_coverage` prüft fehlende Pflichtkriterien, Duplikate und fremde
IDs. NOT_ASSESSABLE zählt als bearbeitet, wird jedoch separat ausgewiesen und ist
kein positives Qualitätsurteil. Ein Abdeckungsfehler verhindert die Veröffentlichung
einer scheinbar vollständigen KI-Erstbewertung.

Die drei ausgelieferten PA1/PA2/BA-Profile bleiben **inoffizielle Beispiele** mit
höchstens sechs Kriterien. Ein offizieller Detailkatalog wurde nicht bereitgestellt.
Das System behauptet keine vollständige Abdeckung realer DHBW-Kataloge.

Seit der semantischen Erweiterung vom 27.11.2026 ist `adaptive_planning_mode: semantic`
der Standard für Zusatzplanung im bestehenden Assessmentpfad D/E. Ein Aufruf des
autorisierten lokalen Providers schlägt strukturierte Methodeneinordnungen und
begründete Prüfaufträge vor. APPLIED, MENTIONED und UNCLEAR sind getrennte Zustände.
Nur an Originalspannen gebundene APPLIED-Verfahren dürfen einen Spezialisten
begründen. Freie fachliche Namen und Aufgaben werden in bestehende, servervalidierte
AgentSpecs übersetzt; Modellwahl, Kategorien und Rechte bleiben serverseitig.
Null zusätzliche Agenten ist ein gültiges Planungsergebnis.

`regex_baseline` erhält die früheren fünf Templates ausdrücklich als Vergleich.
`off` deaktiviert Zusatzplanung. Ein automatischer Regex-Fallback ist standardmäßig
ausgeschaltet; optionaler Fallback bei 503/504 wird als nicht semantisch markiert.
Schema-/Scope-/Privacyfehler aktivieren keinen Fallback. Die Standardoberfläche
verwendet weiterhin einen Mockprovider; dieser liefert keine behauptete echte
Methodenerkennung. Reale Modellfreigaben, Pilotkatalog und Qualitätsnachweise fehlen.

Pro Plan gelten standardmäßig höchstens zwei Vorschläge sowie die bestehenden
Gesamtquoten, Delegationstiefe und ein gemeinsames Aufruf-/Tokenbudget. Der Server
prüft Criterion- und Methodenzuordnung, tatsächlich übermittelten Kontext,
Originalzitate, doppelte Aufgaben, Werkzeuge und begrenzte Laufzeit-/Kontext-/
Ausgabebudgets. Der Aufruf erfolgt über vorhandenen Router/Gateway und die
Ausführung über vorhandene Factory/Registry/ExecutionEngine. Neue Tools, Netzziele,
Programme oder eigenständige Berechtigungserweiterungen entstehen nicht.

Vollständiger Vertrag, Reproduktion, A/B/C-Planungsvergleich und Ausführungsgrenzen:
[Semantische adaptive Planung](semantic_adaptive_planning.md).

Eltern und Kinder teilen Analyse, Schutzklasse und Dokumentzuweisung. Modell- und
Toolrechte sind Teilmengen; die vorhandenen Quoten und Timeouts bleiben wirksam.
Zusatzbefunde werden am zugehörigen Pflichtbefund getrennt gespeichert. Sie können
weder einen Pflichtbefund überschreiben noch ein fehlendes Kriterium verdecken.
Jeder Zusatzbefund besitzt eigene Beleg-, Modell- und Prüfmetadaten.

Die Zusatzagenten verwenden eine assessmentlokale Instanz derselben Registry/Factory.
Sie werden nicht in die generische Legacy-`/agents`-Liste eingefügt, weil diese sonst
verdeckte Assessmentkontexte vor der menschlichen Freigabe offenlegen könnte.
Ihre Modell-/Agentenprovenienz wird erst mit den freigegebenen Befunden sichtbar.

Human-in-the-Loop bleibt unverändert: unabhängige Erstbewertung, serverseitiges
Embargo, ausdrückliche Freigabe, versionierte menschliche Entscheidungen und
deterministische Schlussfassung. Zusätzliche Befunde werden nur über explizite,
kriteriumsgebundene Finding-IDs übernommen. Fremde IDs werden abgelehnt.
Freie menschliche Inhalte sind RESTRICTED; die KI-Diskussion bleibt durch das
Privacy-Gate gesperrt. Die bestätigte menschliche Prüfung ohne Inferenz bleibt nutzbar.

Tests: Coverage-/Scientific-evidence-Tests, bestehende Factory-/Scope-/Budgettests,
Assessment-API und Evidence-Explorer. Fachlicher Zusatznutzen adaptiver Spezialisten
ist erst in der Expertenstudie zu prüfen.
