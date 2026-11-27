# Incident response

Status: Prozessentwurf, keine erfolgte Hochschulabnahme. Keine automatische externe
Meldung und keine Übermittlung von Dokumentinhalten an Tickets, Chat oder Monitoring.

Auslöser: vertrauliche Datei in Git, unerwartete ausgehende Anfrage, fremder Zugriff,
Inhalte in Logs, kompromittiertes Modell/Dependency, gestohlene Zugangsdaten.

1. Betroffene Verarbeitung stoppen; keine weitere Analyse/Modellinferenz starten.
2. Egress sperren, betroffene Dienste am Netzwerk isolieren; notwendige Management-
   und Beweissicherungspfade nur durch zuständige IT zulassen.
3. Geschützte Beweise lokal sichern: Zeitfenster, pseudonyme IDs, technische
   Entscheidungen, Firewallnachweise. Keine vertraulichen Screenshots/Logs in GitHub.
4. Hochschul-IT, Informationssicherheit, Datenschutzverantwortliche und festgelegte
   Vorfallkoordination über intern autorisierte Kanäle informieren.
5. Zuständige Stellen bewerten betroffene Personen/Unternehmen, Rechtslage,
   Meldepflichten und Fristen; keine erfundenen Rechtsfreigaben oder Automatismen.
6. Ursache, Umfang und mögliche Weiterverbreitung untersuchen. Bei Git-Fund zunächst
   Zugriff begrenzen und Zugangsdaten widerrufen; Historyänderung nur koordiniert.
   Ein privates Repository macht den Vorfall nicht automatisch unkritisch.
7. Fehler beseitigen, Schlüssel/Artefakte ersetzen, Wiederholung mit ausschließlich
   synthetischen Canary-Daten prüfen. Beweise und Löschpflichten abstimmen.
8. Wiederinbetriebnahme nur ausdrücklich nach technischer und organisatorischer
   Freigabe; Nachbericht, Verantwortlichkeit und offene Restrisiken festhalten.

Vor realer Nutzung noch zu benennen: Incident Commander, Datenschutzkontakt,
IT-Bereitschaft, Vertretung, sichere Meldewege und Eskalationsplan der Partnerfirmen.
