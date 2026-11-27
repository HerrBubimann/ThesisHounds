# ADR 007: quellengebundene Mosbach-Regeln und lokale Bibliografie

Status: synthetische Entwicklungsbasis implementiert, 27.11.2026; keine Produktionsfreigabe.

Die öffentlichen DS/KI-Unterlagen sind kohortenspezifisch und widersprechen teilweise
der Fakultätsrichtlinie. Ein universeller DHBW-Katalog würde falsche Verbindlichkeit
erzeugen. Metadaten belegen weder wissenschaftliche Aussagebezüge noch Aktualität.
DOI-Listen aus Firmenarbeiten können selbst vertraulich sein.

Entscheidung: exakte Auswahl aus Standort/Studiengang/Jahrgang/Arbeitstyp,
Prüfungsrechtsrahmen, Hierarchie und explizite menschliche Konfliktentscheidung.
Importierte Regeln bleiben Kandidaten; Freigabebelege sind separat und hashgebunden.
Andere Standorte bleiben Orientierung. Fehlende Gewichte bleiben null. Das öffentliche
Formular wird nicht mit dem fehlenden Palleduhn-Original gleichgesetzt.

Recherche nutzt kleine, unabhängig geprüfte öffentliche Offlinebestände, keinen
HTTP-Research-Client. Qualitätsvorschläge verwenden den bestehenden Router/Gateway,
eine geerdete Passage und keine Netztools. GROBID bleibt ein optionaler Adapter ohne
privaten Dokumenteingang. Alle fachlichen Prüfergebnisse unterliegen dem Erstbewertungs-Embargo.

Folgen: reproduzierbare datensparsame Analyse mit expliziter Unvollständigkeit.
Unbekannte Befunde bleiben manuell. Modell-/GROBID-Güte, Identität, Host/Speicher,
Rechts-/Prüfungsfreigabe sind separat nachzuweisen. Die Bibliotheksfreigabelogik wird
getestet, aber nicht als Promotion-API am Entwicklungsserver angeboten.
