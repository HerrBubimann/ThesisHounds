# Datenverarbeitungsübersicht – Entwurf

Arbeitsgrundlage zur VVT-/DSFA-Prüfung; keine bestätigte Rechtsgrundlage oder
vollständiges Verzeichnis nach Art. 30 DSGVO. Implementierungsabgleich 28.11.2026; institutionelle Prüfung weiterhin offen.

| Bestand / Zweck | Daten / Schutzklasse | Speicher / Empfänger | Löschung / offene Entscheidung |
|---|---|---|---|
| Hochschulwissen | öffentliche Regeln PUBLIC; interne Originale standardmäßig RESTRICTED | getrennte lokale Bibliothek; private Importe aktuell gesperrt | versionierte öffentliche Referenzen kontrolliert verwalten; interne Frist offen |
| Öffentliche Forschung | geprüfte Metadaten/Material PUBLIC | lokale Teilbestände, kein automatischer HTTP-Abruf | Kurator verwaltet Aktualität/Lizenzen, keine vertraulichen Suchhistorien |
| Analyse | synthetische Fixture oder registrierte, unabhängig geprüfte öffentliche Pilotdatei PUBLIC; private Arbeit RESTRICTED und gesperrt | lokale CPU/RAM/temporärer Store, In-Process-Mock | technische TTL/DELETE; keine offiziellen Prüfungsfristen behaupten |
| Erst-/Zweitbewertung | menschliche Angaben/abgeleitete Gesamtsicht RESTRICTED | zugewiesene synthetische Sitzung; kein Modellzugriff auf menschliche Erstbewertung | RAM-Record mit TTL/DELETE/Shutdown, Backupgrenzen offen |
| Formalien/Quellenbefunde | Schutzklasse der Arbeit, Bestätigungen RESTRICTED | erst nach Embargo sichtbar, lokale Prüfentscheidungen | gleicher Record-Lifecycle; öffentliches Material wird nicht zum Suchlog umgewidmet |
| Gutachten | Entwurf/Schlussentscheidung RESTRICTED | menschliche Freigabe, expliziter lokaler TXT-/Markdown-Download; kein automatischer Versand | Archivierungsbedarf/Frist durch Prüfungsamt klären |
| Sicherheitsprotokoll | technische IDs/Entscheidungen, kein Dokumenttext | lokal; keine externen Traces | Fristen, Zugriff und Integrität durch Betrieb bestätigen |
| Entwicklung/CI | Code, öffentliche Metadaten und synthetische Tests | Repository/Actions; keine echten Arbeiten | Artefaktfristen sind technische CI-Einstellungen |

Verantwortlicher, Auftragsverarbeiter, Betroffenengruppen, Rechtsgrundlage,
Informationspflichten, Rechteprozess und Datenempfänger müssen institutionell
festgelegt werden. Keine Freigabe durch bloße Bedienung der Demo.
