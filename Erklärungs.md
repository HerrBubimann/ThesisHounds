# ThesisHounds einfach erklärt

Stand: 28.11.2026. ThesisHounds unterstützt die **menschliche** Begutachtung von
PA1, PA2 und Bachelorarbeiten. Die KI liefert eine getrennte Zweitmeinung; sie
vergibt keine Punkte und entscheidet keine Note.

Die aktuelle Anwendung ist ein **Testsystem**. Standardmäßig sind Modellantworten
simuliert (Mock). Ein positiver Lauf mit freigegebenen echten lokalen Modellen ist
für den dokumentierten Stand nicht nachgewiesen. Vertrauliche Arbeiten dürfen nicht
hochgeladen werden; zugelassen sind synthetische Beispiele und registrierte,
unabhängig geprüfte öffentliche Test-PDFs.

## Das Grundprinzip in drei Sätzen

1. **Du bewertest zuerst selbst**, ohne die KI-Meinung zu kennen.
2. **Die KI bewertet parallel und unabhängig**, ohne deine Meinung zu kennen.
3. **Erst danach werden beide Sichten nebeneinandergelegt**, und du entscheidest
   allein, was ins Gutachten kommt.

### Warum so umständlich?

Wer einen KI-Vorschlag zuerst sieht, übernimmt ihn leichter, auch wenn er falsch ist
(Ankereffekt bzw. *Automation Bias*). Deshalb ist die Reihenfolge technisch erzwungen
und nicht nur empfohlen:

- Die KI erhält deine Erstbewertung **nie**. Die Schnittstelle der KI-Prüfung nimmt
  nur Dokument und Kriterienkatalog entgegen.
- Die KI-Ergebnisse liegen bis zur Freigabe **gesperrt** im Backend (*Embargo*).
  Vorher zeigt die Oberfläche nur an, *dass* die KI fertig ist
  (`COMPLETED_EMBARGOED`), aber keinen Inhalt.
- Deine Erstbewertung wird mit der Freigabe **eingefroren** und kann danach nicht
  mehr nachträglich an die KI angepasst werden.

Mehr dazu: [Automation Bias](docs/evaluation/automation_bias.md).

## Die beiden Abläufe

| Bereich | Zweck | Menschliche Beteiligung |
|---|---|---|
| Begutachtungsarbeitsbereich / Assessments | unabhängige Erstbewertung und kontrollierte Zweitprüfung | Erstbewertung, Vergleich, Befundprüfung und Schlussfreigabe |
| Agent Control Center / Legacy-Runs A–D | technische Experimente mit verschiedenen KI-Aufbauten | keine unabhängige Erstbewertung; finale Befunde werden dennoch menschlich geprüft |

Die technische Trennung schützt die zurückgehaltenen Assessment-Ergebnisse.
Die Legacy-Laufliste kann sie nicht abrufen. Beide Abläufe teilen Sicherheitsregeln,
Modellgateway und Ressourcenlimits.

Für die eigentliche Begutachtung ist nur der **Begutachtungsarbeitsbereich** gedacht.
In der Seitenleiste findest du ihn unter *Arbeitsbereich* (Dashboard, Neue
Begutachtung, Meine Begutachtungen, Quellenprüfung, DHBW-Richtlinien). Unter
*Technik & Verwaltung* liegen Agent Control Center, Model Center, Evaluation Lab,
Security Center, Systemstatus und Einstellungen.

## Wer macht was?

| Baustein | Aufgabe | Was er **nicht** tut |
|---|---|---|
| **Oberfläche** (Streamlit, Browser) | Formulare, Dokumentleser, Vergleichsansicht | speichert nichts dauerhaft und entscheidet nichts |
| **Backend** (FastAPI) | prüft jede Aktion: Reihenfolge, Zugriffsrechte, Datenschutzklasse, Limits | gibt keine gesperrten Inhalte vorzeitig heraus |
| **LLM-Gateway** | einziger Weg zu einem Modell; prüft pro Aufruf Policy, Budget und Antwortformat | ruft keine externen KI-Dienste auf |
| **Modell** (Mock oder lokales Ollama) | erzeugt strukturierte Befundvorschläge im JSON-Format | hat keine Werkzeuge, kein Internet, keine Notenvergabe |
| **Lokale Prüfungen** | Zitatabgleich, Quellenmetadaten, Formalien, Zahlenhinweise | beurteilen keine fachliche Qualität |
| **Du** | Erstbewertung, Prüfung der Befunde, Entscheidung, Abschluss | – |

## Eine Begutachtung durchführen

```mermaid
flowchart TD
    A[Arbeit und zugelassenes Dokument auswählen] --> S{Sicherheitsverdacht im Dokument?}
    S -->|nein| H[Menschliche Erstbewertung]
    S -->|nein| K[Unabhängige KI-Prüfung]
    S -->|ja, Quarantäne| H
    H --> P[Menschliche Dokument-Sicherheitsprüfung]
    P --> K
    H --> F{Beide abgeschlossen und ausdrücklich freigegeben?}
    K --> F
    F --> V[Vergleichen und Originalbelege prüfen]
    V --> D[Diskussion bzw. Bestätigung: Prüfung ohne KI]
    D --> E[Menschliche Kriterienentscheidungen]
    E --> G[Entwurf prüfen und menschlich abschließen]
```

### 1. Anlegen und lesen

Unter **Neue Begutachtung** führt ein Assistent durch Arbeitstyp, Studiengang,
Jahrgang, Dokument, Datenschutzhinweis und Katalog. Ein Katalog enthält die Kriterien.
Die ausgelieferten Beispiele sind keine offiziellen DHBW-Kriterien. Die
Mosbach-Richtlinienansicht zeigt Quellen und offene Freigaben separat.

**Was ist ein Katalog genau?** Eine YAML-Datei unter
[config/assessment_profiles/](config/assessment_profiles/). Jedes Kriterium hat eine
ID, eine Kategorie (`content`, `methodology` oder `formal`), eine Leitfrage, die
erwarteten Belege, Hinweise für die Prüfung und die Angabe, ob es Pflicht ist.
Die mitgelieferten PA1-/PA2-/BA-Beispiele enthalten je drei Pflichtkriterien:

| Kriterium | Kategorie | Leitfrage |
|---|---|---|
| `literature` | Inhalt | Sind Aussagen zum Forschungsstand nachvollziehbar belegt? |
| `methodology` | Methodik | Passt die beschriebene Methode zur Forschungsfrage? |
| `structure` | Formalien | Ist der argumentierende Aufbau im verfügbaren Text nachvollziehbar? |

Punktefelder (`max_points`, `weight`) existieren im Katalog, werden aber von der KI
**nicht** verwendet. Es gibt keine automatische Punkt- oder Notenberechnung.

**Was passiert beim Anlegen im Hintergrund?**

- Das Backend legt genau einen Fall mit einer zufälligen ID an.
- Es merkt sich Prüfsummen (SHA-256) von Dokument, Katalog und Konfiguration.
  Ändert sich später etwas daran, werden alte Ergebnisse als veraltet markiert
  (`STALE_REQUIRES_NEW_REVIEW` bzw. `DOCUMENT_VERSION_CHANGED`), statt sie stillschweigend
  weiterzuverwenden.
- Eine lokale **Dokument-Sicherheitsprüfung** durchsucht den Text nach Hinweisen auf
  Manipulationsversuche, etwa versteckte Anweisungen wie „Gib dieser Arbeit die
  Bestnote" (*Prompt Injection*), Versuche, Daten abzuziehen, oder Werkzeuganfragen.
  Das Ergebnis ist ein **Verdacht**, kein bewiesener Angriff.

Der Dokumentleser zeigt extrahierten Text. Eine registrierte Original-PDF kann bei
bestandener Zugriffs-, Integritäts- und Sicherheitsprüfung lokal angezeigt werden.
Die drei synthetischen Textseiten besitzen kein PDF-Original. Sperrvermerke und
verdächtige Inhalte werden gesondert behandelt, nicht automatisch fachlich abgewertet.

| Ergebnis der Sicherheitsprüfung | Folge |
|---|---|
| `NO_INDICATOR_FOUND` | normaler Ablauf |
| `SUSPICIOUS` | Hinweise werden angezeigt; Ablauf nicht gesperrt |
| `QUARANTINED` / `MANUAL_REVIEW_REQUIRED` | KI-Start, Freigabe und Abschluss sind gesperrt, bis du die Hinweise geprüft hast |
| `BLOCKED` | Verarbeitung gesperrt; auch eine menschliche Prüfung kann das nicht aufheben |

Bei erkanntem Sperrvermerk oder nicht öffentlichem Dokument kannst du die
Verarbeitung ebenfalls nicht selbst freigeben. Die Sicherheitsprüfung siehst du
erst **nach** deiner Erstbewertung, damit auch sie deine Meinung nicht vorab prägt.

### 2. Unabhängig bewerten

Du dokumentierst Beobachtungen, Stärken, Kritikpunkte, Begründung und offene Fragen
je Kriterium. Nicht Beurteilbares wird als **NOT_ASSESSABLE** markiert.
**Entwurf in Sitzung speichern** speichert nur vorübergehend in dieser Browsersitzung.
Erst deine ausdrückliche Erstfreigabe friert die Bewertung im Backend ein.

Pro Kriterium wählst du eine von vier groben Einschätzungen:

| Einschätzung | Bedeutung |
|---|---|
| `POSITIVE` | Kriterium überwiegend erfüllt |
| `MIXED` | teils erfüllt, teils mit Schwächen |
| `NEGATIVE` | Kriterium überwiegend nicht erfüllt |
| `NOT_ASSESSABLE` | mit dem vorliegenden Text nicht beurteilbar |

Pflichtfelder sind *Beobachtungen* und *Begründung*. Das Backend akzeptiert die
Erstfreigabe nur, wenn **jedes** Kriterium des Katalogs **genau einmal** bearbeitet
wurde. Nach der Freigabe gilt der Fall als `RESTRICTED`, weil er jetzt deine
persönliche Einschätzung enthält, auch wenn das Testdokument selbst öffentlich ist.

Die KI-Prüfung kann parallel laufen, erhält aber deine Erstbewertung nicht.
Sie bearbeitet den Katalog unter festen Grenzen. Weitere begründete Fachprüfungen
und lokale Formalien-/Quellen-/Zahlenprüfungen ergänzen den vorhandenen Ablauf.
Nicht konfigurierte Werkzeuge und fehlende Artefakte werden als solche ausgewiesen.

#### Was die KI-Prüfung Schritt für Schritt macht

Standard ist der Aufbau **E** („adaptive Eskalation mit unabhängiger Gegenprüfung").

1. **Ein Modellaufruf pro Kriterium.** Jedes Kriterium wird je nach Kategorie an ein
   eigenes Modell geleitet. In der Beispielkonfiguration:
   Inhalt → Llama (Meta), Methodik → Mistral (Mistral AI), Formalien → Qwen (Alibaba).
   Im Mock-Modus antwortet stattdessen ein simuliertes Modell.
2. **Begrenzter Kontext.** Das Modell bekommt nicht unbedingt das ganze Dokument,
   sondern die zum Kriterium passendsten Textstellen, bis ein festes Größenbudget
   erreicht ist. Es wird ausdrücklich darauf hingewiesen, dass der Kontext unvollständig
   ist und fehlende Treffer **nicht** beweisen, dass etwas in der Arbeit fehlt.
   Findet sich gar kein passender Kontext, wird ohne Modellaufruf `NOT_ASSESSABLE`
   gesetzt.
3. **Strukturierte Antwort.** Das Modell muss JSON in einem festen Schema liefern:
   Einschätzung, Art des Befunds (Stärke, Schwäche, Methodenbedenken, offene Frage,
   Verbesserungsvorschlag, …), Begründung, **Seite und wörtliches Zitat** als Beleg,
   Unsicherheit sowie erkannte wissenschaftliche Aussagen und Zusammenhänge
   (z. B. „Fazit passt nicht zu den Ergebnissen"). Es soll positive und negative
   Punkte gleichermaßen belegen und **keine** Mindestzahl an Kritik erzeugen.
4. **Zitatprüfung (deterministisch, ohne KI).** Das Backend sucht das angegebene Zitat
   wörtlich auf der angegebenen Seite. Gefunden → `QUOTE_MATCHED`, nicht gefunden →
   `REJECTED`. Das prüft nur, *ob die Stelle existiert*, nicht ob die Deutung stimmt.
5. **Pflichtabdeckung.** Fehlt ein Pflichtkriterium, ist eines doppelt oder taucht ein
   unbekanntes auf, bricht die KI-Prüfung als Ganzes ab. Teilergebnisse werden dann
   **nicht** angezeigt; du legst einen neuen Fall an.
6. **Eskalation.** Für jeden Befund wird festgelegt, wie viel weitere Prüfung nötig ist:

   | Stufe | Wann | Folge |
   |---|---|---|
   | 2 | unkritischer, belegter Befund | keine weitere Modellprüfung |
   | 3 | Kritik (`NEGATIVE`, Schwäche, Quellen-/Formalproblem), schwache Belege, Widerspruch, offene Zusammenhänge | unabhängige Gegenprüfung |
   | 4 | unzureichende Belege, Abwesenheitsbehauptung, Konflikt, Ressourcengrenze | ausdrücklich menschliche Klärung nötig |

   Die reine „Selbstsicherheit" des Modells löst **keine** Eskalation aus.
7. **Zusätzliche Spezialisten (optional).** Wenn ein Befund es erfordert, darf das
   System bis zu zwei zusätzliche, eng begrenzte Fachprüfungen planen (z. B. für eine
   bestimmte Methode). Das Modell schlägt sie nur vor; eine feste Prüfinstanz kontrolliert
   Rolle, Modell, Budget und Laufzeit. Ergebnisse erscheinen als **Ergänzung** zum
   Pflichtbefund (`ADAPTIVE`), nicht als Ersatz.
8. **Gegenprüfung durch einen anderen Hersteller.** Ein Modell eines *anderen*
   Herstellers erhält den Befund mit dem Auftrag, ihn zu **widerlegen**, und darf ein
   Gegenzitat nennen. Bis zu zwei Runden. Ergebnis:

   | Status | Bedeutung |
   |---|---|
   | `MODEL_SUPPORTED` | Gegenprüfer hat nichts Wesentliches gefunden, Zitat stimmt |
   | `CHALLENGED` | Gegenprüfer hält den Befund für unbegründet |
   | `UNRESOLVED` | Zweifel, fehlender Kontext oder ungültiges Gegenzitat |
   | `UNAVAILABLE` | kein unabhängiges Modell bzw. Budget verfügbar |
   | `NOT_REQUESTED` | Gegenprüfung war nicht nötig (Stufe 2) |

   Ein einmal aufgetretener Widerspruch bleibt als **Konflikt** sichtbar, auch wenn eine
   spätere Runde zustimmt. Zustimmung zweier Modelle ist **kein** Beweis.
9. **Parallele lokale Prüfungen.** Gleichzeitig laufen sechs begrenzte Prüfpfade:

   | Prüfpfad | Pflicht? | Was er liefert |
   |---|---|---|
   | Wissenschaftliche Bewertung | ja | die oben beschriebenen KI-Befunde |
   | Formalien und Quellen | ja | Literaturverzeichnis auslesen, mit lokalem Metadatenbestand abgleichen, Richtlinienregeln prüfen |
   | Sprache | nein | Hinweise von lokalem LanguageTool, nur wenn eingerichtet |
   | Retrieval | nein | Fundstellen im Originaltext über lokale Encoder, nur wenn eingerichtet |
   | Zitierformat | nein | lokale CSL-Formatkandidaten, nur wenn eingerichtet |
   | Zahlenprüfung | nein | Kennzahlen (Accuracy, F1, RMSE, …) im Text finden, Rechen- und Widerspruchskandidaten markieren |

   Scheitert ein Pflichtpfad, scheitert die ganze KI-Prüfung. Scheitert ein optionaler
   Pfad, bleibt das als Lücke (`FAILED_REQUIRES_HUMAN`) sichtbar.

Budgetgrenzen (Standard): höchstens 32 Modellaufrufe und 100000 konservativ
reservierte Tokens pro Fall, ein Modellaufruf gleichzeitig, ein aktiver Lauf.
Während die Prüfung läuft, zeigt die Oberfläche nur den echten Status, keine
erfundenen Fortschrittsbalken oder Restzeiten.

### 3. Vergleich öffnen und prüfen

Erst nach beiden Abschlüssen und ausdrücklicher Freigabe werden die KI-Inhalte sichtbar.
Der Arbeitsbereich bietet Registerkarten oder drei Spalten für Kriterien, Dokument
und Befunde. Du kannst suchen, filtern, Originalzitate öffnen und Gegenbelege prüfen.

**Vergleichsmarkierung je Kriterium.** Sie vergleicht nur die groben Einschätzungen,
nicht ob die Begründungen inhaltlich übereinstimmen:

| Markierung | Wann |
|---|---|
| `AGREEMENT` | gleiche Einschätzung, KI-Zitat gefunden |
| `PARTIAL_AGREEMENT` | eine Seite `MIXED`, die andere `POSITIVE` oder `NEGATIVE` |
| `DISAGREEMENT` | `POSITIVE` gegen `NEGATIVE` |
| `INSUFFICIENT_EVIDENCE` | KI-Zitat nicht bestätigt oder eine Seite `NOT_ASSESSABLE` |

Auch `AGREEMENT` heißt nur „gleiche Richtung", nicht „beide haben recht".

**Belege und lokale Prüfungen.**

| Befund | Was daraus folgt |
|---|---|
| Originalzitat stimmt mit dem Text überein | Die Fundstelle ist bestätigt; die fachliche Deutung bleibt offen. |
| Zitat ist nicht eindeutig bestätigt | Keine belastbare Textzuordnung; mögliche Extraktions-/Kontext-/Zitierprobleme manuell klären. |
| Quellenmetadaten lokal gefunden | Nur die tatsächlich verglichenen bibliografischen Felder sind geprüft. |
| Quelle lokal nicht gefunden | Der lokale Bestand kann unvollständig sein; kein Beweis einer erfundenen Quelle. |
| Zahlen-/Reproduzierbarkeitshinweis | Prüfvorschlag aus dokumentiertem Kontext; kein reproduziertes Experiment und keine automatische Abwertung. |

**Weitere Hilfen im Arbeitsbereich.**

- **Rückfragen-Entwürfe:** Das System formuliert feste Fragen, etwa bei Konflikten,
  fehlenden Belegen, unklarer Methode, fehlenden Reproduzierbarkeitsangaben oder
  Zahlenabweichungen. Jede Frage ist an Kriterium und Originalstelle gebunden. Sie
  sind ohne KI erzeugt und nur Vorschläge, z. B. für ein Kolloquium.
- **Dublettengruppen:** Sehr ähnliche Befunde zur selben Textstelle werden als
  Gruppe vorgeschlagen. Es wird nichts gelöscht.
- **Methodenbestätigung:** Erkennt das System eine angewandte Methode (z. B.
  Statistik, Machine Learning, Experteninterviews), kannst du sie mit Belegstelle
  bestätigen. Daraus leitet sich eine Checkliste typischer Reproduzierbarkeitsangaben ab.
- **Zeitmessung:** Optional kannst du Prüfsitzungen starten und stoppen. Gemessen
  wird nur die ausdrücklich gestartete Zeit, keine „gesparte" Zeit.
- **Abdeckungsbericht:** Zeigt, welche Textbereiche tatsächlich an ein Modell gingen,
  welche Teilprüfungen fehlten und welche Entscheidungen noch offen sind. „Vollständig"
  ist ein Fall nur, wenn wirklich nichts davon offen ist.

**Auf Befunde reagieren.** Du kannst Befunde akzeptieren, ablehnen, korrigieren oder
ergänzen und eigene Notizen speichern:

| Aktion | Bedeutung |
|---|---|
| `ACCEPT` | Befund ist zutreffend |
| `REJECT` / `NOT_RELEVANT` | Befund falsch oder nicht relevant (Grund erforderlich) |
| `CORRECT` | Befund wird mit deinem Text korrigiert (Grund und Korrektur erforderlich) |
| `SUPPLEMENT` | Befund wird um deinen Text ergänzt |
| `INSUFFICIENT_EVIDENCE` / `MANUAL_REVIEW_REQUIRED` | noch nicht übernehmbar, weitere Klärung nötig |

Jede Reaktion wird als neue Version gespeichert; ältere bleiben sichtbar.
Ein abgelehnter oder ungeklärter Befund kann nicht ins Gutachten übernommen werden.

Kriterienspezifische Rückfragen sind vorgesehen. **Eine freie KI-Diskussion
über menschliche Inhalte ist derzeit durch die Datenschutzpolicy gesperrt.**
Grund: Die Diskussion müsste deine Bewertung (`RESTRICTED`) an ein Modell senden,
die konfigurierten Modelle sind aber nur für öffentliche Daten (`PUBLIC`) freigegeben.
Die Oberfläche zeigt die Sperre; eine dokumentierte menschliche Prüfung ohne KI ist möglich.

> **Wichtig für den Ablauf:** Kriterienentscheidungen sind erst möglich, nachdem
> entweder eine Diskussion stattgefunden hat oder du ausdrücklich
> **„Menschliche Prüfung ohne Modellaufruf"** bestätigt hast. Da die Diskussion
> derzeit gesperrt ist, ist diese Bestätigung im Normalfall der nächste Schritt.

### 4. Menschlich abschließen

Pro Kriterium speicherst du eine eigene Schlussfolgerung und Begründung.
Überarbeitungen bleiben versioniert. Der Entwurf enthält nur menschliche Entscheidungen
und ausdrücklich übernommene Befunde beziehungsweise Notizen. Die KI schreibt beim
Abschluss keine neue Kritik hinzu. TXT und Markdown können lokal heruntergeladen werden;
ein PDF-/DOCX-Gutachtenexport und automatische Abgabe sind nicht angebunden.

**Wie der Entwurf entsteht.** Er wird nach festen Regeln zusammengesetzt, ohne
Modellaufruf. Pro Kriterium steht darin:

1. deine Schlussfolgerung und Begründung,
2. für jeden von dir übernommenen KI-Befund: Beschreibung (bzw. deine Korrektur),
   Originalzitat mit Seite und Kapitel, Zitatstatus, Unsicherheit, Ergebnis der
   Gegenprüfung und ob ein Konflikt bestand,
3. deine Ergänzungen,

danach die für den Entwurf markierten Notizen und akzeptierten Hinweise aus den
lokalen Prüfungen. Eine Übernahme ist **nie** vorausgewählt; du musst sie aktiv setzen.
Identische übernommene Befunde werden zusammengefasst.

**Abschluss.** Erst wenn zu jedem Kriterium eine Entscheidung vorliegt und keine
Sicherheitsprüfung offen ist, kannst du ausdrücklich abschließen. Danach ist der Fall
schreibgeschützt (`FINALIZED`) und der Entwurf trägt die Überschrift
„Menschlich freigegeben".

## Zustände eines Falls

Die Oberfläche zeigt den aktuellen Zustand an. So hängen sie zusammen:

| Zustand | Bedeutung | Nächster Schritt |
|---|---|---|
| `PROFILE_SELECTED` | Fall angelegt | Erstbewertung schreiben, KI-Prüfung starten |
| `INDEPENDENT_REVIEWS_RUNNING` | KI-Prüfung läuft | abwarten, weiter bewerten |
| `AI_REVIEW_COMPLETED` | KI fertig, Ergebnis gesperrt | eigene Erstbewertung freigeben |
| `HUMAN_REVIEW_COMPLETED` | Erstbewertung eingefroren | ggf. KI starten oder abwarten, dann Vergleich freigeben |
| `READY_FOR_COMPARISON` | beide Sichten sichtbar | Befunde prüfen, „Prüfung ohne KI" bestätigen |
| `DISCUSSION_IN_PROGRESS` | Diskussion bzw. Bestätigung erfolgt | Kriterienentscheidungen treffen |
| `READY_FOR_FINALIZATION` | alle Kriterien entschieden | Entwurf lesen und abschließen |
| `FINALIZED` | abgeschlossen | nur noch lesen und herunterladen |
| `FAILED` | KI-Prüfung gescheitert | neuen Fall anlegen |

## Häufige Stolperstellen

| Meldung oder Situation | Ursache | Lösung |
|---|---|---|
| KI-Start oder Freigabe gesperrt (`LOCAL_DOCUMENT_REVIEW_REQUIRED`) | Sicherheitsverdacht im Dokument | Erstbewertung freigeben, dann Sicherheitshinweise prüfen |
| „Beide Erstbewertungen müssen abgeschlossen sein." | Vergleich vor Ende beider Zweige angefordert | Erstbewertung freigeben bzw. KI-Prüfung abwarten |
| „Jedes Kriterium muss genau einmal bearbeitet werden." | Kriterium fehlt oder ist doppelt | alle Kriterien ausfüllen, ggf. `NOT_ASSESSABLE` |
| „Zunächst die Bewertungen diskutieren." | keine Diskussion bzw. Bestätigung | „Menschliche Prüfung ohne Modellaufruf" bestätigen |
| „Befundfeedback vor Übernahme klären." | übernommener Befund ist abgelehnt oder ungeklärt | Feedback ändern oder Befund nicht übernehmen |
| Fall verschwunden | Backend neu gestartet oder Aufbewahrungszeit (1 Stunde) abgelaufen | Fall neu anlegen; Entwürfe vorher herunterladen |
| Nach einem Fehler keine Antwort sicher | Netzwerk- oder Zeitproblem | zuerst Status prüfen, nicht blind erneut absenden |

## Forschung und Grenzen

Die Legacy-Runs vergleichen A: einzelner Auftrag, B: feste Agenten mit einem Modell,
C: feste Agenten mit mehreren Modellen und Gegenprüfung, D: dynamische Agenten mit
Gegenprüfung. Das separate **CLI-Evaluationslabor A–E** nutzt den gemeinsamen
Kriterienpfad für kontrolliertere Vergleiche und Ablationen. Mock-Ergebnisse zeigen
technisches Verhalten, keine wissenschaftliche Modellqualität.

Im Evaluationslabor lassen sich einzelne Bausteine gezielt abschalten (ohne Retrieval,
ohne Zusatzspezialisten, ohne Gegenprüfung), um ihren Einfluss zu messen. Kennzahlen
wie Präzision oder Halluzinationsrate bleiben leer, solange keine menschlich geprüften
Referenzbefunde vorliegen; es werden keine erfunden.
Details: [Ablationen](docs/evaluation/ablation_studies.md).

- Begutachtungen liegen flüchtig im Backend-RAM; ein Neustart verliert sie.
  Standardmäßig werden Fälle nach einer Stunde entfernt, höchstens 20 werden gleichzeitig
  aufbewahrt. Öffentliche Referenzkataloge und lokale Modellgewichte haben eigene Speicherwege.
- Die Demo verwendet eine gemeinsame Identität. Sie ist kein freigegebenes
  Mehrbenutzersystem und besitzt keine Hochschulanmeldung.
- Verarbeitungswege sind lokal begrenzt. Installation, getrennte Modellbereitstellung
  und öffentlicher Metadaten-Sync können Internet benötigen; daraus folgt keine
  allgemeine Sicherheits- oder Datenschutzfreigabe.
- Offizielle Kriterien, reale Modellnachweise und organisatorische Freigaben bleiben offen.

## Kleines Glossar

| Begriff | Erklärung |
|---|---|
| **Befund** (*Finding*) | ein einzelner KI-Vorschlag zu einem Kriterium, mit Beleg |
| **Embargo** | KI-Ergebnisse sind gespeichert, aber bis zur Freigabe unsichtbar |
| **Gegenprüfung** | ein Modell eines anderen Herstellers versucht, einen Befund zu widerlegen |
| **Konflikt** | Modelle oder Belege widersprechen sich; bleibt bis zu deiner Entscheidung sichtbar |
| **Mock** | simuliertes Modell für Tests; Ergebnisse sind nicht fachlich aussagekräftig |
| **Prompt Injection** | versteckte Anweisungen im Dokumenttext, die eine KI manipulieren sollen |
| **Provenance** | Herkunftsnachweis: welches Modell, welcher Prompt, welcher Dokumentstand |
| **`PUBLIC` / `RESTRICTED`** | Schutzklassen; menschliche Bewertungen sind immer `RESTRICTED` |
| **Sperrvermerk** | Hinweis auf vertraulichen Inhalt; solche Dokumente werden nicht verarbeitet |

[Bedienablauf](docs/frontend/review_workflow.md) · [Einrichtung](docs/setup.md) ·
[Verifizierter Stand und Grenzen](docs/validation.md) · [Architektur](docs/architecture.md)
