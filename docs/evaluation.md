# Vorbereitung der wissenschaftlichen Evaluation

## Vergleichsbedingungen

Alle vier Modi erhalten dasselbe serverseitige synthetische Dokument, dieselbe Aufgabenstellung und dieselben Bewertungskriterien. Der Dokument-Digest wird im Run gespeichert. Die Registry-Konfiguration, lokal entdeckten Modell-Digests, Ausführungslimits und Modellzuordnungen können über Run- und Agenten-API nachvollzogen werden. Für eine Studie zusätzlich Repository-Commit, Hardware, Ollama-Version und sämtliche Prompt-/Konfigurationsstände archivieren.

| Modus | Hierarchie | Modellhersteller | Dynamische Specs | Modellreview | Belegprüfung |
| --- | --- | --- | --- | --- | --- |
| A | Keine; einfacher Prompt | Ein Modell | Nein | Nein | Nein |
| B | Orchestrator / Supervisor / statische Spezialisten | Gleiches Modell | Nein | Nein | Nein |
| C | Orchestrator / Supervisor / statische Spezialisten | Verschiedene | Nein | Ja | Nein |
| D | Orchestrator / Supervisor / dynamische Spezialisten | Verschiedene | Ja | Ja | Ja |

Modus A verwendet dasselbe Befund-Ausgabeschema, aber nur einen einfachen Analyseprompt. Modus B nutzt `single_model` für sämtliche Rollen. C und D verwenden die konfigurierten Modellzuordnungen. Ein Herstellerwechsel wird beim Review serverseitig geprüft. Die Zahl der Supervisoren und Subagenten sowie der Aufwand unterscheiden sich absichtlich zwischen Modi; die Modi isolieren daher nicht jeden einzelnen Einflussfaktor. Für kausale Aussagen wären zusätzliche Ablationen und budgetgleiche Vergleichsbedingungen notwendig.

## Erfasste Messwerte

- Ausführungsdauer, Status, Fortschritt und Fehlerstatus.
- Gateway-Aufrufversuche einschließlich fehlgeschlagener Modell-Vorprüfungen und Wiederholungen. Der Zähler ist kein unabhängiger Nachweis, dass Ollama jeden Versuch tatsächlich inferiert hat.
- Vom Provider gemeldete Input-/Outputtokens, konservativ reserviertes Budget und Anzahl unvollständig gemessener Aufrufe.
- OS-CPU/RAM, Backend-RSS, verfügbare Ollama-Modell-VRAM-Samples und beobachtete Spitzenwerte. Diese Messungen sind nicht vollständig pro Run/Container isoliert; kurze Peaks können fehlen.
- Anzahl erzeugter Befunde, mechanisch bestätigter Zitate, abgelehnter Zitate bzw. `UNSUPPORTED`-Reviews und erkannter Konfliktkandidaten.
- Modelle, Hersteller, Parent-Child-Beziehungen sowie Agentenlaufzeiten und -aufrufe.

`validated_count` zählt im Modus D **Zitate, die auf einer Seite vorkommen**, keine fachlich korrekten Befunde. `unsupported_count` kombiniert abgelehnte Belege und negative Modellreviews und ist keine gemessene Halluzinationsrate. Unterschiede zwischen A–C und D in diesen Zählern spiegeln auch aktivierte Prüfungen wider. Für vergleichbare Qualitätsmessungen müssen die Rohbefunde aller Modi nach derselben unabhängigen Referenzregel ausgewertet werden.

## Notwendige menschliche Referenzbewertungen

Für Precision und Recall ist ein von Fachpersonen annotierter Goldstandard nötig: relevante Stärken/Kritikpunkte, Kategorie, genaue Belegstellen, zulässige Paraphrasen und Bewertungsbegründung pro Dokument. Ein Zitat allein ist kein positives Referenzlabel. Abwesenheitsbehauptungen benötigen eine Annotation des erforderlichen vollständigen Dokumentkontexts.

Mindestens zwei unabhängige fachkundige Bewertende sollten Befunde verblindet beurteilen; Konflikte benötigen ein dokumentiertes Adjudikationsverfahren. Übereinstimmung der Bewertenden, Kategorienunterschiede und Unsicherheiten separat erfassen. Eine vorher festgelegte Matching-Regel muss Modellbefunde zu Referenzbefunden zuordnen und Duplikate behandeln. Danach gilt: Precision = korrekt zugeordnete Befunde / alle ausgegebenen Befunde; Recall = gefundene Referenzbefunde / alle relevanten Referenzbefunde. Keine dieser Größen ergibt sich aus Modellmehrheiten oder `VALIDATED` allein.

Weitere Qualitätsdimensionen: fachliche Berechtigung, Vollständigkeit, Kontexttreue, Beleggenauigkeit, Nützlichkeit für Gutachten und menschlicher Korrekturaufwand. Für Laufzeitvergleiche Warm-/Cold-Starts, sequentielles Entladen, Quantisierung und Kontextlänge kontrollieren. Mehrere Wiederholungen mit vorab festgelegten Bedingungen und dokumentierten Abbrüchen/Schemafehlern durchführen; fehlgeschlagene Läufe nicht aus der Ergebnisdarstellung entfernen.

Die synthetische Fixture demonstriert Infrastruktur und Prüfgrenzen, ist kein repräsentativer Datensatz wissenschaftlicher Arbeiten. Eine tatsächliche wissenschaftliche Evaluation mit menschlichen Referenzen wurde noch nicht durchgeführt. Die aktuellen Unit-/Integrationstests verwenden gekennzeichnete Mock-Antworten und belegen Funktionen, keine Bewertungsqualität.
