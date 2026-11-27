# Modellsicherheit und reale Betriebsgrenze

DEVELOPMENT verwendet ausschließlich den In-Process-Mock. Modellhersteller und
Betriebsort sind getrennte Registryfelder. Qwen/Meta/Mistral im Modellkatalog sind
keine Cloudfreigabe und keine gemessenen Qualitätszusagen. Weitere HF-Artefakte
benötigen überprüfte Revision, Lizenz, Format, Hash und Herkunft, bevor sie enabled werden.

Der lokale Gateway erzwingt vor jedem Aufruf Provider-, Rollen-, Endpunkt-, Schutzklassen-
und Budgetprüfung. Routerauswahl, dynamische Agenten und Quellenqualitätsreview
nutzen diese Grenze. Keine externen Provider, OCR-/Embeddingdienste oder Modellfallbacks
sind registriert. Ein Ausfall endet kontrolliert; das Ausweichziel wird nicht extern.

Der Ollama-Adapter pinnt Zieladresse/IP/Port/Pfad, ignoriert Proxyumgebungen und
Redirects. Die universitäre Inferenzadresse ist **noch nicht** technisch abgenommen;
Konfiguration `LOCAL`/`UNIVERSITY` ersetzt diesen Nachweis nicht. Reale Modelldigests,
Hostkapazität und GPU-Messwerte fehlen weiterhin. Siehe [Model Supply Chain](model_supply_chain.md).

MODEL_PROVISIONING ist ein eigener benannter Sicherheitsmodus, besitzt aber keinen
Zugang zum Analyseprozess: Settings/Privacy-Engine lehnen diesen Modus dort ab.
Das eigenständige Provisioning-Projekt darf nur ohne Thesis-/Gutachtenspeicher laufen.
Keine automatischen Downloads, Remote-Code-Ausführung oder Updates während einer Bewertung.
Root-/Modellserveradministratoren bleiben eine organisatorisch abzusichernde Vertrauensgrenze.
