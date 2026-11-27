# Vertraulichkeitsgrenze bei Quellen und GROBID

Siehe [Recherche-Datenfluss](../research/research_privacy.md) und
[Quellenverfahren/GROBID](../research/citation_verification.md).

Literaturverzeichnis und DOI-Kombinationen gehören zum Schutzbereich der Arbeit.
Es existiert kein Weg von einer Analyse zu Crossref/OpenAlex/Semantic Scholar/
DataCite/Unpaywall/arXiv/Retraction Watch über HTTP. Der ResearchGateway lehnt
auch scheinbar PUBLIC deklarierte Suchanfragen ab. Keine Browserbestätigung hebt dies auf.

Der lokale Cache enthält ausschließlich unabhängig geprüfte öffentliche Snapshots.
Rohimporthash, Reviewerkennung, Zeitpunkt und Provenienz werden erhalten; Inhalte
werden weder in allgemeine Logs noch in CI-Berichte geschrieben. Nicht gefundene
Quellen und datenschutzbedingt nicht prüfbare Quellen begründen keinen automatischen
Notenabzug. Interne Quellen werden ohne öffentliche Auffindbarkeitsforderung behandelt.

GROBID bleibt opt-in und für private Daten blockiert. Header-/Citation-/Funder-
Konsolidierung ist im Adapter aus, externe Dienste sind in vorbereiteter Konfiguration
entfernt beziehungsweise auf toten Loopback gerichtet. Ein separates internes Netz
verhindert eine beabsichtigte Internetroute. Die tatsächliche GROBID-Prozess-/Host-
Abnahme ist noch offen; ein Schema-/Mocktest ist kein entsprechender Egressbeleg.

Tests: `test_academic_privacy`, `test_research_gateway`, `test_network_isolation`,
`test_source_quality` und Snapshot-Tampertests. Reale Hochschularbeiten bleiben gesperrt.
