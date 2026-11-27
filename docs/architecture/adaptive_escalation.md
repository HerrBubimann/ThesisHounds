# Kontrollierte Review-Eskalation

OFF-2/3/4/5: vorhandene Factory, Registry, Gateway, Budgets und menschlicher
Begutachtungsprozess werden erweitert. Kein Agent erhält neue Tools oder Netzrechte.

| Stufe | Tatsächliche Verarbeitung | Wechselbedingung |
|---|---|---|
| 1 | lokale Struktur-/Kontext-/Quoteprüfung; vorhandene deterministische Formalien-/Metadatenprüfungen | semantisches Pflichtkriterium ist damit nicht entschieden |
| 2 | ein kriteriumsbezogener lokaler Gatewayaufruf mit begrenztem Kontext | kritische Aussage, offene fachliche Frage, unzureichende Evidenz oder Beziehungskandidat |
| 3 | unabhängiger Challenge-/Cross-Model-Review; Fachagent nur bei Thema **und** Befundbedarf | Konflikt, Kontextlücke, ungeprüfte Abwesenheit, Ressourcen-/Agentenfehler |
| 4 | explizite menschliche Klärung, kein weiterer externer Fallback | bleibt offen bis zu einer menschlichen Entscheidung |

Die aktuellen Beispielkriterien verlangen semantische Interpretation; deshalb
ersetzt eine DOI-Zählung kein vollständiges Literaturgutachten und ein Kapitelindex
keine Aufbaukritik. Formal deterministisch entscheidbare Fakten bleiben im vorhandenen
lokalen Academic-Service. Es gibt keine erfundene regelbasierte Fachentscheidung.

`plan_escalation` berücksichtigt Befundart, Evidenzqualität, Konflikte, Themenkomplexität
und Ressourcen. LLM-Uncertainty allein ist kein Trigger. Nachvollziehbare Gründe und
erforderliche Prüfungen stehen am Befund. Kritische negative Aussagen erhalten in E
eine unabhängige Prüfung; deklarierter Herstellerunterschied ist nur ein technisches
Unabhängigkeitskriterium, kein Beweis statistisch unabhängiger Modelle.

Alle Pflichtkriterien werden zuerst verarbeitet und durch den bestehenden Coverage-
Checker geprüft. Optionale Agenten können sie nicht verdrängen. Scheitert eine
Pflichtanalyse trotz begrenzter Wiederholung, wird die Analyse FAILED und kein
Teilergebnis als erfolgreiche Bewertung freigegeben. Fehlende optionale Agenten oder
Verifikation erzeugen sichtbare Klärungsfragen und menschliche Eskalation. Ressourcen
werden nicht durch einen Cloudfallback ersetzt. Stärken mit direkten, brauchbaren
Belegen benötigen nicht automatisch einen zweiten oder dritten Agenten.

COMPLETED beschreibt den technischen Abschluss der Pflichtverarbeitung.
`analysis_complete=false` kennzeichnet weiterhin fachlichen Klärungsbedarf, auch bei
abgeschlossenen Modellaufrufen. Sämtliche Befunde brauchen weiterhin die bestehende
menschliche Schlussfreigabe. Keine KI vergibt Punkte oder erzwingt Konsens.

Standardpfad ist E. Die getrennte synthetische Evaluation kann einzelne Komponenten
gezielt deaktivieren; UI/API bieten dafür keinen Sicherheitsschalter.
