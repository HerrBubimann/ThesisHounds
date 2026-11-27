# Sperrvermerk policy

Alle echten Arbeiten bleiben standardmäßig RESTRICTED und derzeit unzulässig.
`detect_sperrvermerk` durchsucht lokal sämtliche gelieferten Seiten sowie Metadaten
und vorhandenen OCR-Text. Die Seitenposition ist unerheblich: Titelseite, spätere
Seiten und extrahierte Kopf-/Fußzeilen werden gleichermaßen erfasst. Normalisierung
umfasst NFKC, Groß-/Kleinschreibung, Leerraum und unsichtbare Formatzeichen.

Indikatoren: Sperrvermerk, Vertraulich, Streng vertraulich, Nur für den internen
Gebrauch, Nicht zur Veröffentlichung bestimmt, Confidential, Strictly Confidential,
Restricted, Internal Use Only, Non-Disclosure Agreement, Geschäftsgeheimnis,
Betriebsgeheimnis. Die Ausgabe enthält feste Indikatornamen, keine Textzitate.

Kein Treffer bedeutet keine Freigabe. Ablaufdaten, Zusammenfassungen oder entfernte
Namen senken die Schutzklasse nicht. Die Erkennung ersetzt weder Sperrvermerkprüfung
noch die Autorisierung durch Unternehmen/Hochschule. Eine allgemeine Firmen-/
Personenerkennung, verbindliche Fristinterpretation oder Genehmigungsentscheidung
wird nicht automatisiert.

Die lokale Detailerkennung liefert ausschließlich Kandidaten: explizit mit
Firma/Unternehmen bezeichnete Namen, ein mit `bis` bezeichnetes Datum, eng begrenzte
numerische Jahres-/Monatsfristen, bezeichnete Adressaten und Genehmigungshinweise.
Zeilenumbruch-Silbentrennung und Soft-Hyphens werden normalisiert. Detailfelder
werden nicht im Objekt-Repr ausgegeben und nicht durch die Status-API veröffentlicht.
`legal_validity=REQUIRES_AUTHORIZED_REVIEW` bleibt unverändert; selbst eine abgelaufene
synthetische Frist bewirkt weder Freigabe noch eine niedrigere Klasse. Freie
Formulierungen, Kalendergültigkeit und Rechtswirkung prüft eine berechtigte Person.

Es gibt keinen freigegebenen privaten PDF-Eingang oder OCR-Dienst. Der Detektor kann nur Text untersuchen,
der bereits lokal bereitsteht; Bilder, fehlerhafte Extraktion und unbekannte
Formulierungen können Treffer verhindern. Parser-Sandbox, Malwareprüfung,
Metadatenextraktion und OCR-Abnahme bleiben vor echtem Upload erforderlich.
Der UI-Status bezieht sich derzeit ausschließlich auf die synthetische Fixture.
Öffentliche Bibliotheksimporte und der optionale GROBID-Adapter ersetzen diese Freigabe nicht.
