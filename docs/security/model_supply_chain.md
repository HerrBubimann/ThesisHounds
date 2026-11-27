# Model supply chain

Modellhersteller, Gewichtequelle, Inferenzanbieter, Betriebsort und Netzwerkziel
sind unterschiedliche Vertrauensentscheidungen. Internationale Gewichte können
lokal zulässig sein; derselbe Modellname bei einem Cloudanbieter bleibt gesperrt.
`config/models.yaml` führt die angeforderten Betriebs-/Privacyattribute. Alle
ausgelieferten Modelle haben ausschließlich DEVELOPMENT_ONLY-Status, PUBLIC als
erlaubte Klasse und **keine produktive Lizenz-/Sicherheitsfreigabe**. Die App
verwendet standardmäßig einen deterministischen Mock, keine echten Gewichte.

## Provisioning

`provision.py` verwendet seit dem Folgeaudit ausschließlich das eigenständige
Projekt `thesishounds-provisioning`. Es startet nur `model-provisioner` in einem
separaten Online-Netz, nicht den Verarbeitungsstack. Vor jeder Änderung wird ein
aktives Modell-Volume abgelehnt. Der bestehende Anwendungsstack wird nicht gestoppt.
Gemountet wird nur das ausdrücklich benannte Modell-Volume. Ein kurzlebiger,
unprivilegierter Helper prüft vollständige Digests über Loopback, ohne Dateimount.
Abschließend wird die Onlinezone auch bei Fehlern entfernt. Keine vertraulichen
Arbeiten, Kontexte oder Verarbeitungsschlüssel dürfen in dieser Zone vorhanden sein.

Vor echten Modellen: Modellsteward prüft Lizenz, Hersteller/Quelle, erlaubten
Einsatzzweck, Dateiformat, Revision/Hash, Herkunft, Schwachstellen, Fähigkeiten,
Hardware, Datenverarbeitungsort und Endpunkt. HF-Metadaten verlangen eine feste
40-stellige Revision, SHA256, GGUF/safetensors und dokumentierte Reviews, bevor
ein Kandidat aktiviert wird. Diese Metadatenvalidierung ist **keine** eigenständige
Prüfung der heruntergeladenen Bytes. Die Registry unterstützt zusätzlich `version`,
`weights_origin` und `expected_digest` für Ollama-Artefakte. Provisioning verlangt
APPROVED für Lizenz/Security/Modell und den vollen Digest; DEVELOPMENT_ONLY genügt
nicht. Router und Ollama-Adapter verweigern einen abweichenden installierten Digest
vor dem Promptversand. Ein Tag-/Dateihash ist trotzdem kein Beweis für sichere
Gewichte oder eine institutionelle Freigabe; produktive Verarbeitung bleibt gesperrt.

Ollamas [Tags-API](https://docs.ollama.com/api/tags) liefert den Manifestdigest des
Servers. Die volle Übereinstimmung verhindert unbeabsichtigte Tagwechsel; sie
beweist keine unveränderten Gewichtsdateien auf einem kompromittierten Server.
Zwischen Statusprüfung und Inferenz bleibt außerdem ein Laufzeitwechsel durch
privilegierte Operatoren möglich. Immutable Artefakte, getrennte Schreibrechte,
Single-Operator-Provisioning und Zielhostabnahme sind weiterhin erforderlich.
Die Volume-Aktivitätsprüfung ist kein verteilter Lock gegen gleichzeitigen Start
durch andere Administratoren. Fehlerhafte Downloads bleiben bis zur berechtigten
Bereinigung im Modell-Volume; sie werden durch den Digestcheck nicht freigegeben.

## Runtime

Kein `pull`/Downloadpfad im Provider, kein HF-Inferenceclient, kein Remote Code,
keine automatische Aktualisierung oder externe Fallbacks. HF/Transformers offline,
HF-Telemetrie aus; Ollama Cloud aus. Modell-/Abhängigkeitsinstallation ist kein
Agententool. Python-Abhängigkeiten und CI-Actions sind bereits hash-/SHA-gepinnt.
Operatoren müssen Basisimage-/Modellprovenienz, SBOM, Signaturen soweit vorhanden,
Schwachstellenscans und einen Widerruf kompromittierter Artefakte ergänzen.

Für neue freigegebene Revisionen: isoliert erwerben → prüfen → immutable Artefakt
und Reviewbeleg archivieren → offline importieren → gegen synthetische Daten
qualifizieren → organisatorisch genehmigen. Bei Änderung eines Digests, Hosts,
Providers oder Telemetrieverhaltens bisherige Freigabe erneut prüfen.
