# Lokaler PDF-Eingang, 27.11.2026

`backend/app/services/pdf_security.py` und `pdf_worker.py` bilden den gemeinsamen
PDF-Pfad für kontrollierte PUBLIC-Pilotdokumente und Knowledge-Kandidaten. Sie
erweitern den vorhandenen Import; private Uploads werden nicht freigeschaltet.

| Prüfung / Begrenzung | Tatsächliches Verhalten |
|---|---|
| Dateityp/Signatur | PDF-Header 1.0–1.7 oder 2.0, EOF-Marker in letzten 1.024 Bytes, anschließend strikter pypdf-Parser; kein alleiniger MIME-/Endungsvertrauen |
| Umfang | maximal 8.000.000 Eingabebytes, 1–200 Seiten, 20.000 besuchte Strukturknoten, 200.000 Inhaltsoperatoren/Seite, 2.000.000 extrahierte UTF-8-Bytes |
| Eingebettete Objekte | Rohstream maximal 4.000.000 Bytes; EmbeddedFile/EF/EmbeddedFiles abgelehnt; keine vollständige Analyse aller dekodierten Bild-/Fontdaten |
| Aktive Inhalte | JS/JavaScript, OpenAction, AA, Launch, RichMedia, XFA sowie SubmitForm/ImportData/GoToR/GoToE-Aktionen abgelehnt, auch in verschachtelten Annotationen |
| Verschlüsselung/Struktur | verschlüsselte und nicht strikt parsbare PDFs abgelehnt, keine Passworteingabe oder Reparatur im Bewertungsprozess |
| URLs | URI nur passiver Indikator; niemals automatisch laden/anklicken; Referenzen werden nicht als Netzwerkauftrag interpretiert |
| Metadaten/Annotationen | ausgewählte Stringfelder Contents/T/Subject/Author/Title/Keywords auf Regeln/Länge prüfen; normale Metadaten kein pauschaler Angriff; keine vollständige XMP-/Producer-/Creator-Prüfung |
| Fehler | stabile technische Ablehnung, keine rohen Parserexceptions, Dateinamen oder PDF-Inhalte an Client/Logs |

### Prozessgrenze

Der feste Worker startet über `python -I -B`, Eingabe über stdin, bereinigte
Umgebung, 20 Sekunden äußere Deadline. Windows: JobObject mit 384 MiB Prozess-RAM,
10 CPU-Sekunden und einem aktiven Prozess. POSIX: RLIMIT_AS/RLIMIT_CPU; dieser
Zweig wurde auf dem aktuellen Windows-Host nicht ausgeführt. Fehler beim Setzen
der Grenzen lehnen die Verarbeitung ab. stdout wird nach Abschluss auf 4 MB
geprüft; dies ist keine während des Lesens durchgesetzte 4-MB-Streamgrenze.

Nach lokalen Imports verbietet ein Python-Audithook Socketoperationen, neue
Prozesse, Dateischreibzugriffe und zusätzliche Bibliotheksladungen. Lesezugriffe
sind auf Python-/Backend-Verzeichnisse beschränkt; der Input kommt über stdin.
Die Regression führt Socket-/Prozess-/Dateischreibversuche tatsächlich in einem
separaten Python-Prozess aus und erwartet Ablehnung.

**Das ist keine vollständige Betriebssystem-Sandbox.** Native Exploits können
Python-Hooks umgehen; der Worker läuft unter derselben OS-Identität. Keine
AppContainer-/seccomp-/Netznamespace-/Hostfirewallabnahme, kein Antivirusnachweis.
Die vorhandenen internen Compose-Netze und Egressrichtlinien ersetzen diese
ausstehende Worker-/Zielhostgrenze nicht. Daher keine Freigabe privater Dateien.

### Original und Belegkette

`services/document_store.py` speichert akzeptierte Originalbytes unverändert,
UUID, SHA-256, Dokument-/Extraktionsversion, Importzeitpunkt, tatsächliche
pypdf-Version und `secure-pdf-preflight.v1`-Inspektion. Text- und
Inspektionshash gehen in `assessments/provenance.py` ein und werden erneut
geprüft. Abgelehnte aktive/verschlüsselte Dateien werden nicht als registrierte
Originale aufbewahrt. Es gibt keine stillschweigende Bereinigung.

Alte Katalogeinträge ohne neuen Inspektionsnachweis werden abgelehnt; kontrolliert
erneut importieren/prüfen, nicht Metadaten von Hand als geprüft markieren.
Blank-PDFs sind ausschließlich als Knowledge-Kandidaten zulässig, nicht als
bewertbares Pilotdokument. Speicher liegt außerhalb des Repositorys. Ein
vollständig schreibberechtigter Speicheroperator kann Metadaten neu fälschen;
Hashes sind keine signierte Attestation. `chmod(0600)` beweist keine NTFS-ACL.

### Hidden Content: vorhandene Heuristiken und Lücken

pypdf-Visitor erfassen kleine Schrift, Render-Modus 3/7, geringe Alpha-Werte,
weiße Füllfarbe, Position außerhalb der Cropbox, Clipping und möglicherweise
überlagerte Textursprünge. Originaltext wird erhalten. Weißer Text bedeutet
ausdrücklich **nicht** geprüften weißen Hintergrund; Clipping beweist keine
Unsichtbarkeit. Mehrspaltigkeit, Transformationen, Formulare und komplexe PDFs
können Koordinaten verfälschen. Normale Schrift/Metadaten haben Negativkontrollen.

Rendering, Hintergrundrekonstruktion, OCR-Mismatch und Anweisungen in Bildern
sind `NOT_IMPLEMENTED`. Befunde bleiben Verdachtsindikatoren. Es gibt keinen
Dual-Extraction-Erfolg oder visuell geprüften Rastervergleich.

### Werkzeugentscheidung

| Werkzeug | Eignung nach Primärquelle | Aktuelle Grenze |
|---|---|---|
| [pypdf](https://github.com/py-pdf/pypdf/blob/main/docs/user/extract-text.md) | vorhandene Text-/Visitor-API, keine neue Abhängigkeit | kein OCR; komplexe Visitor-Koordinaten können unzutreffend sein |
| [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/about.html) / [Lizenz](https://pymupdf.io/licensing) | Kandidat für lokales Raster/Layout | AGPL/kommerzielle Lizenz projektspezifisch prüfen; nicht installiert/aktiviert |
| [pikepdf](https://pikepdf.readthedocs.io/en/stable/topics/security.html) | Struktur-/Verschlüsselungsverarbeitung | kein Rendering/semantischer Angriffsbeweis; nicht installiert |
| [qpdf --check](https://qpdf.readthedocs.io/en/stable/cli.html#option-check) | zusätzliche Strukturdiagnostik | keine Malware-/Promptprüfung; CLI nicht vorhanden |
| Tesseract / lokale Malwareprüfung | mögliche weitere lokale Prüfschichten | Tesseract/ClamAV nicht vorhanden, keine Ausführung oder Scanfreigabe; keine Cloudscanner verwenden |

Zusätzliche Werkzeuge erst nach Lizenz-/Dependencyprüfung und isoliertem Lauf
einführen. Keine Pakete, Locks oder Modellartefakte wurden hierfür ergänzt.
[OWASP File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
begründet die Kombination aus Inhaltsprüfung, Größenlimit und getrennter
Verarbeitung, stellt selbst aber keinen projektspezifischen Sicherheitsnachweis dar.

Tests: `tests/security/test_secure_document_gateway.py`,
`tests/security/test_pilot_boundaries.py`, `tests/unit/test_knowledge_import.py`.
Die exakten ausgeführten Suitezahlen stehen im [Prüfprotokoll](../evaluation/security_results.md).
