# Benchmark: konservative Formalienprüfung

`app.evaluation.academic_benchmark` enthält vier deterministische Inhaltsumfangsfälle
mit 19/20/30/31 überprüften Inhaltsseiten bei jeweils 40 synthetischen Gesamtseiten.
Die Referenzregel (20–30) ist ausdrücklich eine synthetisch aktivierte Testregel,
keine erteilte Hochschulfreigabe.

Lokal beobachtet am 27.11.2026: FAIL/PASS/PASS/FAIL wie erwartet, vier von vier Fällen.
Für jeden Fall wird zusätzlich eine ungültige Dokumenthashbindung geprüft: Ergebnis
MANUAL_REVIEW_REQUIRED. Der Validator zählt niemals einfach 40 PDF-Gesamtseiten als
Inhaltsseiten. Der Bericht enthält erwarteten und tatsächlichen Status statt einer
erfundenen Layoutmessung.

Weitere Regressionen prüfen exakte Abstractspannen, Wortgrenzen, unsichere
Seitenumbrüche, Inhaltsverzeichnisüberschriften, Schrift-/Nummerierungswerte nur aus
geprüften Messdaten sowie die Grenzen bei Unterschrift und organisatorischen Nachweisen.
Kandidatenregeln und offene Konflikte führen unabhängig vom Dokument zu manueller Prüfung.

Nicht gemessen sind OCR, tatsächliche Schrift-/Randextraktion, Unterschriftsauthentizität,
visuelle Vollständigkeit und Gutachterübereinstimmung. Diese benötigen eigene
Parser- und Expertenbenchmarks. Ergebnisse dürfen nicht auf echte Prüfungsleistungen
oder eine produktive Rechts-/Sicherheitsfreigabe verallgemeinert werden.
