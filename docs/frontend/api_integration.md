# API-Anbindung

`frontend/api_client.py` bleibt der einzige produktive HTTP-Client. `egress.py` pinnt
das Backendziel. HTTP nur für freigegebene interne/Loopbackhosts auf Port 8000;
kein Proxy aus Umgebungsvariablen, keine Redirects, URL-Querys, Fremdhosts oder
Browseraufrufe interner FastAPI-Adressen. GET-Timeout 15 s, POST konfiguriert und
begrenzt; Antworten maximal 8 MB. Modellaufrufe bleiben ausschließlich im Backend.

| Oberfläche | Tatsächlicher Vertrag |
|---|---|
| Dashboard / Fälle | `GET /api/v1/assessments` – neue explizite ACL-/Metadatenprojektion |
| Anlage | `GET .../profiles`, `GET .../pilot-documents`, `POST /api/v1/assessments` |
| Dokument | `GET .../{id}/document`; `GET .../{id}/original-pdf` für registrierte Originale |
| Vergleich / Belege | vorhandene `/comparison`, `/findings/{finding_id}/evidence`, `/provenance` |
| Review | bestehende `/human-review`, `/ai-review`, `/release`, `/finding-feedback`, `/discussion`, `/manual-review`, `/decisions` |
| Gutachterwerkzeuge | bestehende `/reviewer-notes`, `/review-methods`, `/reviewer-time` |
| Quellen / Formalien | bestehende `/academic-checks`, `/academic-decisions` |
| Richtlinien | neues `POST /api/v1/assessments/rules-preview` mit festem validiertem Schema |
| Modelle | bestehendes `/api/v1/models/status`; neues lesendes `/api/v1/models/capabilities` |
| Sicherheit / Ressourcen | bestehende `/api/v1/security/status`, `/api/v1/system/resources`, `/health` |
| Abschluss / Verwaltung | bestehende `/draft`, `/finalize`, `/cancel`, `DELETE .../{id}` |

Der PDF-Pfad prüft ACL, registrierten PUBLIC-Import, Dokumentversion, Sicherheitshinweise
und SHA-256 erneut. Verdachtsindikatoren erlauben keine Browser-PDF-Vorschau. Die
Originalbytes laufen durch denselben gepinnten Client, MIME-/Signatur-/Größenprüfung
und den lokalen Viewer. Synthetische Textfixtures besitzen kein Original-PDF.

Statuspolling nur für aktive Assessment-/Legacy-Läufe im 5-s-Fragment, ohne POST.
Im Ruhezustand kein Hintergrundpolling. Der Backendstatus liefert keine laufenden
Teilbefunde. Ein nicht bestimmbarer Fortschritt bleibt als solcher beschriftet.
Fehlertexte verwenden bekannte sichere Statusmeldungen, keine Rohantworten.

Die Evaluations-Report-API fehlt weiterhin ausdrücklich. Die Oberfläche liest keine
beliebigen Reportpfade und erfindet weder API-Endpunkte noch Messergebnisse.
