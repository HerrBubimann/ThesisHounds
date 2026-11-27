# Technische und organisatorische Maßnahmen – Entwurf

Dies ist eine technische Arbeitsgrundlage vom 27.11.2026, keine unterzeichnete
Vereinbarung, Prüfung oder rechtliche Freigabe. Die ausführliche Basistabelle steht
in [TOMs-Entwurf](toms_draft.md); diese Ergänzung behandelt Wissensbasis und Quellen.

| Kontrolle | Technische Umsetzung | Noch zugewiesene/zu bestätigende Organisation |
|---|---|---|
| Öffentliche Herkunft | manuell geprüfter Import, SHA-256, separate Original-/Versionsmetadaten | Kurator benennen, Rechte und zulässige Nutzung prüfen |
| Verbindlichkeit | Kandidatenstandard, separate hashgebundene Freigabebelege, Konfliktgate | Studiengang/Prüfungsamt müssen Gültigkeit/Kohorte verbindlich bestätigen |
| Zugriff | kein öffentlicher Datei-/Freigabe-HTTP-Endpunkt; private Bibliothek gesperrt | SSO, Rollen, Zuweisung und interne Kataloge abnehmen |
| Datenminimierung | lokale Quellenchecks, ein Quellenreviewkontext ohne menschliche Erstbewertung | Erforderlichen Mindestkontext mit Gutachtern prüfen |
| Weitergabe | keine Recherche-HTTP-Provider; Parser/IP-Pinning und internes Netz | Host-Egress inklusive DNS/IPv6/TLS abnehmen |
| Speicherung | öffentliche Bibliothek außerhalb Repo, exklusive Dateien, keine makro-/formelausführenden Importe | Verschlüsselung, ACLs, Backup-/Restoretest, sichere Aufbewahrung |
| Protokollierung | Importstatus/Zähler/Hash; Parser-/Validierungsfehler ohne Inhaltsausgabe | Audit-/Backupzugriff, Aufbewahrung und Incidentübung |
| Entwicklung | DOTX/XLTX zusätzlich ignoriert/DLP-gesperrt; nur synthetische/öffentliche Fixtures | Keine Originalarbeiten in IDE-Assistenten, PRs, Screenshots oder Cloudtests |
| Menschliche Kontrolle | Embargo auch für Formalien/Quellen; explizite Bestätigung/Ablehnung mit Revision | Bias-/Nutzungsstudie, Verantwortlichkeit der Schlussentscheidung |

Schlüsselverwaltung, Datenträgerverschlüsselung, Swap/Crashdumps und Modellserver-
Kontextisolation sind noch keine nachgewiesenen Eigenschaften dieses Repositorys.
