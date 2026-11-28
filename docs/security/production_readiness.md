# Production readiness: BLOCKED

**Document Security, 27.11.2026:** zusätzliche PDF-Preflight-/Ressourcenprüfungen,
Python-Audithook, Tool-/Modell-/Actorscope und menschliche Verdachtsprüfung sind
lokal getestet. [737 Tests / tatsächliche Grenzen](../evaluation/security_results.md).
Diese Maßnahmen ersetzen weder OS-Sandbox-/Zielhostabnahme noch freigegebene
Modelle, Fachkatalog, OCR-/Bildprüfung oder Datenschutz-/SSO-/Speicherfreigaben.
Das Sicherheits-Definition-of-Done und private Produktion bleiben offen.

**Remediation 27.11.2026:** Die Produktionssperren bleiben unverändert. Neu ist ein
begrenzter Operator-PDF-Pfad für synthetische/geprüfte öffentliche Testdaten und
ein kontrollierter `local_pilot`-Anschluss an den vorhandenen Ollama-Adapter.
Realer Lauf, Modellartefakte und PA1-Experimentbestätigung fehlen weiterhin.
Die früher genannten Remediation-Markdown-Dateien fehlen im Checkout.
Aktuelle Belege stehen im [Validierungsstand](../validation.md), die tatsächlich
vorhandene Pilotanleitung im [Setup](../setup.md#kontrollierter-public-pilot).
Die nachfolgenden Tabellen beschreiben die vorangegangene Sicherheitsbasis;
der begrenzte PUBLIC-Worker ist keine Freigabe privater Parser oder Hochschuldaten.

Das erneute [Hardening vom 27.11.2026](hardening_results.md) hebt diese Sperre nicht
auf. Insbesondere sind die offenen HIGH-/CRITICAL-Basisimagebefunde zu bewerten;
ein bestandenes Gate für **behebbare** Befunde ist keine Produktivfreigabe.

Mosbach-Erweiterung 27.11.2026: Öffentliche Import-CLIs und Regelkandidaten heben
die Sperre nicht auf. Kein interner Palleduhn-Import, produktiver Parser oder
institutionell freigegebenes Profil wurde aktiviert. MODEL_PROVISIONING bleibt
ebenso wie PUBLIC_RESEARCH als Analysemode gesperrt. Neue Arbeitsgrundlagen:
[Sicherheitscheckliste](security_release_checklist.md), [Rechtsprüfung](legal_requirements.md),
[DSFA-Vorprüfung](dsfa_precheck.md) und [Hochschulfragen](../dhbw/open_questions.md).

Das System ist eine Entwicklungsdemo mit synthetischen oder unabhängig geprüften,
registrierten öffentlichen Testdaten. **Keine vertraulichen wissenschaftlichen Arbeiten
hier eingeben, hochladen oder in Entwicklerwerkzeuge kopieren.**
Der Defaultprovider ist ein In-Process-Mock. Ein gewöhnlicher Benutzer kann weder
Modus, Klassifizierung, Modellendpunkt noch Netzwerkrechte über das UI ändern.

`require_supported_mode` verweigert alle Modi außer DEVELOPMENT. Der Hochschulstack
setzt explizit UNIVERSITY_SECURE und startet deshalb absichtlich nicht. Das Gate
akzeptiert weder eine Umgebungsvariable `approved=true` noch eine selbst ausgefüllte
Datei als Infrastruktur-/Rechtsnachweis. Es gibt keinen produktiven Freigabeschalter.

| Erforderlicher Nachweis / Implementierung | Iststand |
|---|---|
| Freigabe und technische Abnahme der Hochschulinfrastruktur | nicht vorhanden |
| Funktionierende Hochschulauthentifizierung und Serviceidentitäten | Adapter fehlt; nur synthetische Demoidentität |
| Objektzuweisung / rollenunabhängige Rechte | implementierte Service-ACL; echte Identitätsquelle fehlt |
| Lokale Modelle, Gewichte/Digests, Lizenz und Einsatzfreigaben | ausschließlich Demo-/Kandidatenstatus |
| Sperrvermerk-/NDA- und Verarbeitungsautorisierung pro Arbeit | organisatorisch offen |
| Nachgewiesene Default-Deny-Isolation inklusive DNS/IPv6/Hostpfaden | Konfiguration/Vorlage und CI-Probe geliefert; Zielhost nicht geprüft |
| TLS, interne Authentifizierung und Zertifikatsbetrieb | Hochschul-Endpunktadapter nicht freigegeben; mTLS fehlt |
| Geschützte Speicher, Schlüssel, verschlüsselte Backups | nicht auf Zielsystem nachgewiesen |
| Isolierte sichere Dokumentenparser / Malwareprüfung / OCR | kontrollierter PUBLIC-PDF-Preflight/Worker implementiert; vollständige private OS-/Malware-/OCR-Abnahme fehlt |
| Löschkonzept und Restore-/Backupabnahme | Demo-TTL/Delete implementiert; produktive Fristen und Nachweise offen |
| Geschütztes Logging und unabhängige Auditintegrität | inhaltsarme lokale Audits; manipulationsgeschützter Betrieb offen |
| Datenschutz-/Sicherheitstests | aktuelle lokale Nachweise in [validation.md](../validation.md); historische Privacychecks separat |
| Dokumentierte Restrisiken und benannte Verantwortliche | Vorschlag vorhanden; keine Risikoannahme erklärt |
| DSGVO, DSFA, Sperrvermerke, Hochschul-/Prüfungsrecht und KI-Verordnung | zuständige Prüfung und Freigabe offen |

Nächster produktiver Implementierungsschritt: echte Identity-/Speicher-/Parseradapter
innerhalb der Hochschule entwickeln, Nachweise unabhängig abnehmen und erst danach
einen gegen Manipulation geschützten Freigabeprozess spezifizieren. Kein Entwickler
darf durch Löschen eines Blockers behaupten, dass dessen Nachweis erbracht sei.

Die Definition of Done für echte Arbeiten ist damit ausdrücklich **nicht erreicht**.
Diese Erweiterung liefert die sichere Sperre, grundlegende Kontrollen, Test- und
Dokumentationsbasis. Sie behauptet keine abgeschlossene Hochschulinbetriebnahme.
