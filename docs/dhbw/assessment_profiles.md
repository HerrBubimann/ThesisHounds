# Versionierte Bewertungsprofile und Freigabe

Die drei Kandidaten liegen unter
`config/institutions/dhbw/mosbach/data_science_ai/profiles/{pa1,pa2,ba}.yaml`.
Sie enthalten die jeweilige Kohorte, Version, Regel-ID, Kategorie, Verpflichtungsgrad,
Messverfahren, Parameter, Originaldokument/Fundstelle und Freigabestatus.
Gewichte und Maximalpunkte sind optional; nur tatsächlich im gemeinsamen Formular
gefundene Kategorie-Maximalpunkte wurden eingetragen. Die älteren synthetischen
Beispielprofile bleiben eine ausdrücklich gekennzeichnete Demonstration.

Importablauf für autorisierte lokale Operatoren:

1. Öffentliche Herkunft, Lizenz und genaue Dokumentversion unabhängig prüfen.
2. Metadaten nach `SourceDocument` bereitstellen; Klassifizierung ist standardmäßig RESTRICTED.
3. Ausschließlich ausdrücklich öffentliche Dateien offline importieren:

```powershell
$env:PYTHONPATH='backend'
.venv\Scripts\python.exe -m app.knowledge.cli public-guideline.pdf metadata.yaml `
  --store C:\ApprovedPublicLibrary --curator reviewer-id --public-provenance-reviewed
```

4. Import bleibt `CANDIDATE`. PDF/DOCX/DOTX/XLSX/Markdown/HTML/YAML/JSON werden
   begrenzt lokal extrahiert. Keine Makros, Formelauswertung, externen Ressourcen,
   OCR, visuelle Vollständigkeit oder zuverlässige Seitengeometrie werden behauptet.
5. Kriterien und Zahlen manuell mit Originalfundstellen abgleichen. Palleduhn-Original
   erst nach Bereitstellung identifizieren; Beispielkriterien niemals als sein Original ausgeben.
6. Gültigkeit, Jahrgang, StuPrO und Konflikte durch zuständige Personen bestätigen.
   Separate `HumanApproval`-Belege binden Reviewer, Zeitpunkt und Inhaltshash.

**Der Entwicklungsserver hat keinen Freigabe-/Import-HTTP-Endpunkt und lädt keine
Approval-Dateien aus dem Repository.** Die Bibliothekslogik für überprüfte Freigaben
wird synthetisch getestet; produktive Rollen-/Freigabespeicherung bleibt gesperrt,
bis Identität, Parser und Speicher auf der Hochschule abgenommen sind. Eine
CLI-Angabe ist kein SSO-Rollennachweis und autorisiert keine vertraulichen Importe.

`KnowledgeStore` speichert Originalhash/Extraktion/Metadaten in einer privaten
Verzeichnisstruktur außerhalb des Repositorys. Exklusive Dateierstellung und
Symlink-/Traversal-/ZIP-Expansionsprüfungen begrenzen Dateirisiken. Geprüfte öffentliche
Bibliotheksbestände haben einen anderen Lebenszyklus als flüchtige Begutachtungsdaten.
Private Bibliotheken und analyseübergreifende RAG-Indizes sind nicht freigegeben.

Formalien liefern PASS/FAIL nur bei aktiver Regel und zuverlässigem Messwert.
Seitenumfang verwendet eine überprüfte, dokumenthashgebundene Inhaltssegmentierung;
die Gesamtzahl der PDF-Seiten wird nie als Inhaltsumfang ausgegeben. Unklare Grenzen,
Layout, Unterschriften und organisatorische Nachweise bleiben `MANUAL_REVIEW_REQUIRED`.
Die Abstractzählung unterstützt explizit abgegrenzte Textblöcke; unsichere Seitenumbrüche
werden nicht als vollständiges Abstract gezählt.
