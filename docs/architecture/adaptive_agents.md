# Mandatory and adaptive assessment agents

Beitrag: OFF-2/3, ENG-2/3. `AISecondReviewer` bearbeitet jedes Katalogkriterium
verbindlich. `check_coverage` prüft fehlende Pflichtkriterien, Duplikate und fremde
IDs. NOT_ASSESSABLE zählt als bearbeitet, wird jedoch separat ausgewiesen und ist
kein positives Qualitätsurteil. Ein Abdeckungsfehler verhindert die Veröffentlichung
einer scheinbar vollständigen KI-Erstbewertung.

Die drei ausgelieferten PA1/PA2/BA-Profile bleiben **inoffizielle Beispiele** mit
höchstens sechs Kriterien. Ein offizieller Detailkatalog wurde nicht bereitgestellt.
Das System behauptet keine vollständige Abdeckung realer DHBW-Kataloge.

Die vorhandene AgentFactory/AgentRegistry erzeugt zusätzlich höchstens zwei
themenspezifische Spezialisten aus festen Templates: Statistik, Experteninterviews,
Machine Learning, Softwarearchitektur und Literaturreview. Arbeitstyp, verfügbare
Kriterien und lokale Textsignale bestimmen die Auswahl. Dies ist eine kontrollierte
Heuristik, kein nachgewiesener semantischer Methodenklassifikator. Neue Tools,
Netzziele, Programme oder Berechtigungen können dadurch nicht entstehen.

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
