# Data retention and deletion

Ergänzung 27.11.2026: Formalien-/Quellenbefunde und versionierte menschliche
Prüfentscheidungen liegen im selben Assessment-Record und unterliegen dessen TTL,
DELETE und Shutdown. Das Löschen eines Records entfernt nur seinen Task; andere
Analysen bleiben abbrechbar und bereinigbar. Öffentliche Referenzbibliotheken/Snapshots
haben einen gesondert vom Kurator zu bestimmenden Lebenszyklus. Sie dürfen keine
Thesis-Inhalte oder vertraulichen Recherchehistorien enthalten. Private Bibliotheken
sind in diesem Entwicklungsstand nicht zugelassen. Keine physische Löschgarantie
für Host-Backups, Snapshots, Swap oder Modellserverkontexte wird behauptet.

Die Demo-Frist in `config/execution.yaml` ist eine technische Einstellung, keine
behauptete gesetzliche oder hochschulinterne Aufbewahrungsfrist. Ihre Änderung
erfordert Betreiberkonfiguration; Benutzer oder Agenten setzen keine Fristen.

- Legacy-Runs: TTL nach Ausführungsende; Cleanup entfernt Fixture-Datei, Run,
  Findings, Modellkontext, Task, Budget und Agenten einschließlich ACL-Zuweisung.
- Assessments: TTL ab Erstellung, sobald kein aktiver/beschäftigter Vorgang läuft.
  Entfernt Dokument, menschliche/maschinelle Reviews, Versionen, Diskussion und Entwurf.
- Explizit: `DELETE /api/v1/runs/{id}` beendet den Task, bevor Artefakte verschwinden.
  `DELETE /api/v1/assessments/{id}` beendet laufende KI-Tasks; bei aktiver Diskussion
  wird 409 zurückgegeben. Zugriff erfordert Objektzuweisung und `delete`.
- Startup: abgelaufene UUID-JSON-Dateien werden ohne Inhaltslesen bereinigt.
  Fremde Dateien, Verzeichnisse und symbolische Links werden nicht rekursiv verfolgt.
- Shutdown: synthetische Dateien und Assessment-RAM werden bereinigt; Prozessende
  ersetzt keine belegte physische Speicherlöschung. Nach Crash kann TTL-Cleanup nötig sein.

Auditmetadaten enthalten keine Dokumentinhalte und werden nicht mit Dokumenten
gelöscht. Das aktuelle lokale Audit hat noch keine freigegebene Archivierungs-/
Rotationsfrist: im Produktivbetrieb ist ein gesondertes, minimiertes Auditkonzept
mit Berechtigungen, Integrität und Löschfreigabe erforderlich. Dateien wachsen
während längerer Demoläufe; Betreiber müssen die Demoablage nach Tests bereinigen.

Backups, Snapshots, Replikate, Container-Volumes, Browser-Caches, Downloads, Swap,
Crash Dumps und SSD-Wear-Leveling sind **nicht** durch `unlink` oder RAM-Cleanup
nachweislich rückstandsfrei gelöscht. Vor Produktion: verschlüsselte Speicher,
Backupinventar, Löschweitergabe, Sperrlisten bei Restore, genehmigte Fristen,
rechtliche Aufbewahrung offizieller Gutachten und protokollierte Wiederherstellung
testen. Keine vertraulichen Daten auf Entwicklerrechnern oder in Git aufbewahren.
