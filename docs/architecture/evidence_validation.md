# Evidence validation and adversarial review

Beitrag: OFF-3/4/5, ENG-4/5/6. Die zentrale deterministische Funktion
`check_evidence` wird von Legacy- und kriteriumsweisem Bewertungsablauf verwendet.
Sie prüft Originaltext, Seite und genaue Zeichenspanne. Ein Treffer bedeutet
QUOTE_MATCHED, niemals bestätigte fachliche Wahrheit. Eine Behauptung über fehlende
Inhalte braucht den vollständigen bereitgestellten Kontext; auch dann bleibt
semantische Abwesenheit unbewiesen. Ein Ausschnitt allein beweist kein Fehlen.

Der Standardpfad E führt nach der fachlichen Analyse und ersten Belegprüfung eine
adversariale Gegenprüfung aus. Das andere Modell soll aktiv unberechtigte Kritik,
Gegenbelege und fehlenden Kontext suchen. Höchstens zwei unterschiedliche andere
Hersteller werden verwendet; diese Metadatentrennung beweist keine statistische
Unabhängigkeit der Modelle. Alle Aufrufe teilen das bestehende Call-/Tokenbudget.

Ein Widerspruch bleibt erhalten, auch wenn ein späteres Modell zustimmt.
Änderungsvorschläge werden als Reviewmaterial gespeichert; sie überschreiben den
ursprünglichen Befund nicht automatisch. Gegenbelege werden ebenfalls wörtlich
geprüft. Anschließend wird der ursprüngliche Beleg deterministisch erneut geprüft.
MODEL_SUPPORTED beschreibt nur einen Modellbefund. Ungültige Zitate werden durch
Zustimmung nicht gültig. Fehlende Reviewer/fehlerhafte Schemas werden als UNAVAILABLE
oder UNRESOLVED mit hoher Unsicherheit sichtbar, ohne Cloudfallback.

`document_intelligence.py` bildet ausschließlich bereits vorhandenen lokalen Text
ab: Seiten, exakte Absatzspannen, heuristische Kapitel-/Unterkapitel, sichtbare Zitate,
Literaturabschnitte und textuelle Hinweise auf Tabellen/Abbildungen/Formeln/Code.
Komplexe Objekte besitzen keine behauptete visuelle Extraktionsqualität.
Forschungsfrage↔Fazit und Methodik↔Ergebnisse können über lokale Abschnitte verbunden
werden; die Verbindung ist kein semantischer Wahrheitsnachweis.

Der Evidence Explorer liefert Originalstellen ausschließlich nach derselben
menschlichen Freigabe und Objekt-ACL wie der Vergleich. Finding- und Analyse-ID
müssen zusammenpassen. Der Server prüft die Stelle erneut; erfundene Seiten werden
nicht als Originalansicht angeboten. Freie Modellantworten werden als Text gerendert.

Für einen späteren lokalen Parser wurden
[Docling](https://docling-project.github.io/docling/) und
[PyMuPDF](https://pymupdf.readthedocs.io/en/latest/about.html) recherchiert. Docling
dokumentiert lokale/air-gapped Verarbeitung und strukturiertes PDF-Verständnis.
PyMuPDF bietet PDF-Verarbeitung unter AGPL-/kommerziellem Lizenzmodell; Einsatz und
Lizenz müssen zuständig geprüft werden. Keine dieser Bibliotheken wurde installiert
oder auf vertraulichen Arbeiten evaluiert. Parser-Sandbox, Modelle/OCR-Artefakte,
Lesereihenfolge, Tabellen-/Formelqualität und Malwaregrenzen bleiben vor echtem
Upload separat abzunehmen. Keine externe OCR oder Dokumentenanalyse wurde ergänzt.
