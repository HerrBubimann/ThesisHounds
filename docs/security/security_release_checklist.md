# Sicherheitsfreigabe-Checkliste – nicht erteilt

Vor echten Arbeiten schriftlich durch zuständige Hochschulstellen nachweisen:

- Zweck/Rechtsgrundlage, Prüfungsrecht, KI-VO-Rollen/Einstufung und DSFA-Prüfung.
- Jahrgangsgebundene StuPrO, Palleduhn-/WI-Originale, Kriterien-/Versionsfreigabe und Konfliktauflösung.
- Hochschulidentität, Zuweisungen, Rechteentzug und keine pauschalen Admin-Inhaltsrechte.
- Abgenommener Inferenzendpunkt, TLS-Dienstidentität, Modellgewichte/Digest/Lizenz und keine Cloudfunktionen.
- Host-Egress inklusive DNS, IPv4/IPv6, Redirects/Proxys und Telemetrie empirisch geprüft.
- Parser-Sandbox, Dateityp-/Größen-/Malwareprüfung und GROBID ohne externe Konsolidierung getestet.
- Verschlüsselte Datenträger/Backups, ACLs, Swap/Crashdumps und Restoreprozess geprüft.
- Aufbewahrung je Datenart, Löschen/Restore/Snapshots und Modellkontextgrenzen nachgewiesen.
- Inhaltsarmes Logging/Audit, Incidentkontakte, Übung und kontrollierter Wiederanlauf.
- Fachliche Evaluation mit rechtmäßigem Korpus und menschlichen Referenzen; Bedienungs-/Biasstudie.
- Offene HIGH-/CRITICAL-Basisimagebefunde bewerten, Patch-/Basisimageplan dokumentieren;
  Scanner ohne FixedVersion und ein bestandenes Fixable-Gate ersetzen keine Risikoannahme.
- Provisioning-/Runtime-Trennung und Operator-Locking nachweisen; vollständige
  Gewichtsartefakte unabhängig vom gemeldeten Modellserver-Manifestdigest prüfen.

Repository-Checklisten sind **keine** Produktionsfreigabe. `production_readiness.py`
blockiert UNIVERSITY_SECURE/PUBLIC_RESEARCH/MODEL_PROVISIONING als Analysemode.
Es gibt keinen Env-/UI-Schalter, der eine unterschriebene Checkliste simuliert und
damit diese technischen Blocker aufhebt.
