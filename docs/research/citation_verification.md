# Lokale mehrstufige Quellenprüfung

`research/citations.py` ergänzt das bestehende DOI-Inventar und
`local_verification.py`. Der alte Prüfer behält seine Schnittstelle; neue Prüfungen
verwenden dieselben konservativen Evidenzgrenzen. Kein zweiter LLM-Runtimepfad entsteht.

| Stufe | Implementierter Nachweis | Ausdrückliche Grenze |
|---|---|---|
| 1 Extraktion | Nummerierte Einzeleinträge, einfache Autor-Jahr-Angaben, DOI-Kandidaten, genaue Seite/Zeichenoffsets | Mehrzeilige, komplexe, gescannte und uneindeutige Literatur bleibt unvollständig/manuell |
| 2 Konsistenz | Zitat ohne extrahierten Eintrag, unbenutzte Kandidaten, Duplikatkandidaten, fehlende Autor/Titel/Jahr-Felder | Ein Parserfehler beweist weder fehlende Literatur noch Täuschung. Nicht jede Quellenart benötigt DOI/Jahr/öffentlichen Fundort |
| 3 Metadaten | Lokaler DOI-/Titel-/Autoren-/Jahres-/Typ-/Versionsabgleich mit Provider, Snapshotzeit, Hash und geprüften Feldern | Titelabgleich ist eine dokumentierte Zeichenähnlichkeitsheuristik, keine Identitäts- oder Bedeutungswahrheit |
| 4 Qualität | Begrenzter `research_quality.review_source_use` über bestehenden Router/Gateway: eine geerdete Passage, zugehöriger Eintrag, lokales Abstract/Volltext und freigegebenes Kriterium | Keine Hochschulregeln generieren. Ohne aktive Regel, passendes Dokument oder Material keine Modellkritik. Ergebnis nur PROPOSED/HUMAN_REVIEW_REQUIRED; falsche Quellenzitate werden zurückgewiesen. Im UI wegen ungeklärter offizieller Freigaben nicht automatisch aktiviert |
| 5 Aktualität | Lokale Retraction-/Correction-Notices und Versionsmismatch; Snapshotprovenienz | Kein aktueller Gesamtindex. Neue relevante Forschung/Versionen benötigen separat bereitgestellte Bestände und menschliche Prüfung. Alter allein bewirkt keine Abwertung |

Statusvokabular: VERIFIED_METADATA, VERIFIED_ABSTRACT, VERIFIED_FULLTEXT,
METADATA_MISMATCH, NOT_FOUND, RETRACTED, CORRECTED, UPDATED_VERSION_AVAILABLE,
INTERNAL_SOURCE, RESEARCH_BLOCKED_BY_PRIVACY, PROVIDER_UNAVAILABLE,
MANUAL_REVIEW_REQUIRED. Der MVP vergibt ABSTRACT/FULLTEXT **nicht** allein wegen
einer URL oder vorhandener Datei. Lokale Textverfügbarkeit und exakter Zitatabgleich
werden getrennt von semantischer Stützung berichtet. Nicht implementierte Live-Prüfungen
werden nicht als erfolgreich ausgegeben.

`NOT_FOUND` bedeutet ausschließlich „kein Treffer im lokalen Teilbestand“.
Ohne DOI und bei unklarer Extraktion ist menschliche Prüfung notwendig. Interne
Unternehmensquellen sind `INTERNAL_SOURCE`, keine Halluzinationsbeweise. Unterstützte
Typen umfassen Paper, Konferenz, Preprint, Buch/Fachbuch, Dataset, Dokumentation,
Standard, Web, interne Quelle, Interview und eigene Daten; der Fallbackparser gibt
bei unbekannter Gattung UNKNOWN aus, statt eine Klassifikation zu erfinden.

## GROBID als optionale lokale Ergänzung

Grundlagen: [REST-Parameter](https://grobid.readthedocs.io/en/latest/Grobid-service/),
[Consolidation](https://grobid.readthedocs.io/en/latest/Consolidation/),
[offizielle Konfiguration](https://github.com/grobidOrg/grobid/blob/master/grobid-home/config/grobid.yaml).
GROBID kann bibliografische Einträge, Textverweise und vorgeschlagene TEI-Verknüpfungen
liefern. Diese Zuordnungen sind ausdrücklich noch nicht fachlich validiert.

`compose.grobid.yaml` ist ein **nicht aktiviertes Experiment** für PUBLIC/synthetische
Fixtures: eigenes internes Netz, DNS aus, keine Hostports, kein Thesis-Mount,
read-only Root, UID 10001, Ressourcenlimits, kein Containerlogging, kein Pull zur Runtime.
`GROBID_IMAGE` muss eine überprüfte unveränderliche Imageadresse sein; der Validator
verlangt `grobid/grobid@sha256:…`. `GROBID_CONFIG` muss eine geprüfte vorbereitete
Konfiguration referenzieren. Keine erfundene Digestadresse ist ein Deploymentbeleg.

```powershell
.venv\Scripts\python.exe infrastructure/scripts/prepare_grobid.py `
  reviewed-upstream-grobid.yaml C:\ApprovedParserConfig\grobid.yaml
```

Das Hilfsprogramm erhält die Modellkonfiguration und setzt den Konsolidierungsdienst
auf einen nicht betriebenen Loopbackdienst; Crossref-Key/Proxy sind entfernt.
Der Adapter sendet außerdem Header/Citation/Funder-Consolidation explizit als `0`,
folgt keinen Redirects und pinnt den Dienst auf `172.30.30.3:8070`. Die Netzsperre
bleibt die maßgebliche zweite Barriere gegen versehentliche Fremdanfragen.

**Nicht gemessen:** Startfähigkeit eines konkreten freigegebenen GROBID-Images unter
diesen Restriktionen, PDF-Extraktionsgüte und Egress aus einem echten GROBID-Prozess.
Die Upstream-Konfiguration und Parser-Scratch-/Modellpfade unterscheiden sich nach
Version. Deshalb vor Aktivierung Image/UID/Pfade, Healthcheck und Netzsperre auf dem
Zielhost abnehmen. Kein Modell-/Image-Massendownload wurde dafür ausgelöst.
Bei Ausfall steht der lokale Textfallback zur Verfügung; ein unzuverlässiges Ergebnis
führt zu MANUAL_REVIEW_REQUIRED, niemals zu einem externen Parserfallback.
