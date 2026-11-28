# Begutachtungsworkflow

1. Arbeitstyp PA1 / PA2 / BA, Studiengang und Jahrgang auswählen.
2. Synthetisches Dokument oder vom Operator registrierte PUBLIC-Pilotdatei wählen.
   Keine freie PDF-Einlieferung. Local-Pilot benötigt den passenden Dokument-/Katalogpfad.
3. Testdatengrenze und Datenschutzhinweise ausdrücklich bestätigen.
4. Tatsächlich angebotenen Bewertungs-/Experimentkatalog mit Kriterien und Herkunft prüfen.
5. Zusammenfassung bestätigen und genau einen Backendfall anlegen.
6. Originaltext lesen und unabhängige Erstbewertung je Kriterium verfassen.
   „Entwurf in Sitzung speichern“ gibt noch nichts frei. Unveränderliche Erstfreigabe
   benötigt eine eigene Bestätigung; die API validiert alle Kriterien.
7. Unabhängige KI-Prüfung starten. Sie darf parallel zur Erstbewertung laufen,
   erhält aber keine menschlichen Bewertungen. Solange sie läuft, wird nur der echte
   Ausführungsstatus abgefragt; keine erfundenen Prozentwerte/Restzeiten.
8. Nach beiden Abschlüssen ausdrücklich zum Vergleich öffnen. Lokale Sicherheits-
   verdachtsfälle können zuvor eine menschliche Dokumentprüfung erforderlich machen.
9. Einschätzungen neutral vergleichen, Befunde suchen/filtern und Originalbelege prüfen.
   Der Arbeitsbereich bietet Tabs oder drei Spalten. Die Kriterien stammen aus dem
   aktiven Katalog; Kapitelhinweise stammen nur aus extrahierter Textstruktur.
10. Befundfeedback, eigene Notizen, Methodenbestätigung und Gegenargumente dokumentieren.
    RESTRICTED-Diskussion bleibt im aktuellen Modus für Modelle gesperrt; eine
    dokumentierte menschliche Prüfung ersetzt keine erfolgreiche KI-Diskussion.
11. Eigene Schlussfolgerung und Begründung pro Kriterium versioniert speichern;
    ausdrücklich übernommene Befunde und Notizen bestimmen den Entwurf. Vorschau und
    TXT-/Markdown-Download sind lokal. Endgültiger Abschluss bleibt eine menschliche Aktion.

Menschliche Bewertung ist RESTRICTED, auch wenn das Testdokument PUBLIC ist.
Eine Modellmehrheit, ein bestätigtes Zitat oder ein lokaler Metadatentreffer beweisen
keine wissenschaftliche Richtigkeit. Es gibt keine automatische Notenvergabe.

Entwürfe sind flüchtig; bei unklarer Antwort nach einem POST zuerst den Status prüfen,
statt eine schreibende Anfrage automatisch zu wiederholen. Abbruch wartet im Backend
auf die Beendigung untergeordneter Arbeit. Löschen entfernt den Fall, nicht den separat
verwalteten öffentlichen Referenzkatalog.
