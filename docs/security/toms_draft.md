# Entwurf technischer und organisatorischer Maßnahmen

Status: technischer Entwurf, keine unterzeichneten TOMs oder Datenschutzfreigabe.
Verantwortliche Rollen sind Vorschläge, keine erfolgten Benennungen.

| Ziel | Technisch geliefert | Noch organisatorisch / infrastrukturell erforderlich |
|---|---|---|
| Zutritt | keine Hardware-/Standortkontrolle in Software | Hochschulrechenzentrum, Zutrittskonzept, Dienstleisterkontrolle |
| Identität und Zugang | sichere Modi blockiert, keine selbst erfundenen Passwörter/Tokens | Hochschul-SSO, MFA nach Vorgabe, Joiner/Mover/Leaver, Break-glass |
| Zugriff | Objektzuweisung plus einzelne Berechtigungen, keine automatischen Admin-Inhaltsrechte | echte Identitäten, Mandantenspeicher, dokumentierte Zuweisung und Ausnahmeprüfung |
| Weitergabe | vier Klassen, IFC, externe Modelle/Recherche geschlossen, Defaultmock | Hostfirewall, DNS/IPv6, TLS-/mTLS-Identitäten und Abnahme |
| Eingabe | strikte Schemas, generische Fehler, feste synthetische Quellen und kontrolliert registrierte PUBLIC-Test-PDFs mit begrenztem Preflight/Worker | vollständige private OS-Parser-/Malwareabnahme und institutionelle Autorisierung |
| Nachvollziehbarkeit | technische lokale Auditmetadaten ohne Inhalte | unabhängige Auditintegrität, ACLs, Rotation und Aufbewahrungsfreigabe |
| Verfügbarkeit | Quoten, Timeouts, kontrolliertes Abbrechen; kein Cloudfallback | Hochschulbetrieb, Wiederanlauf-/Restoretest, Notfallplan |
| Trennung | scoped Agenten, getrennte Erstbewertungen, geschlossene Recherche | echte Tenant-/Hostgrenzen, getrennte Provisioning- und CI-Umgebung |
| Minimierung | begrenzte Kontexte/Artefakte, keine Trainings-/Finetuningroute | Kriterienkontexte, Anonymisierung nach Prüfung, Zweck-/Bedarfsfreigabe |
| Lebenszyklus | TTL, explizites Delete, Orphan-Cleanup | Archiv-/Prüfungsfristen, verschlüsselte Backups, Restore-Löschsperren |
| Verschlüsselung | keine eigene Kryptografie; TLS-Prüfung nicht abgeschaltet | Datenträger-/DB-/Backupverschlüsselung, KMS/HSM/Vault nach Vorgabe |
| Entwicklung | Ignores, Docker-Allowlist, DLP-Hook/CI, synthetische Canaries | Schulung: keine Arbeiten in GitHub, IDE-Assistenten, Tickets, Screenshots |
| Vorfälle | dokumentierter Ablauf ohne automatische Inhaltsmeldung | benannte Kontakte, Fristenprüfung, Übungen, Wiederanlaufgenehmigung |

Keine vertraulichen Daten für Training, Fine-Tuning, allgemeine Modellverbesserung,
öffentliche Benchmarks oder fremde Projekte. Jede neue Zweckbestimmung verlangt
eine gesonderte rechtliche und organisatorische Prüfung; sie wird hier nicht
technisch freigegeben. Für reale Inhalte bleiben sämtliche Produktionsblocker aktiv.
