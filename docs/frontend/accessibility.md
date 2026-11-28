# Barrierefreiheit

Ziel: WCAG 2.2 AA. Dies ist keine Konformitätsbescheinigung.

Implementiert: beschriftete native Eingaben/Buttons, sichtbare 3-px-Fokuskontur,
textuelle Statusinformationen neben Farbe, ausreichende Abstände, mindestens
40-px-Buttons, lokale Systemschriften, reduzierte Bewegung bei entsprechender
Systempräferenz. Mensch-/KI-Spalten verwenden dieselben neutralen Farben.

Der mobile Standard sind Registerkarten; drei Spalten lassen sich ausdrücklich
wählen. Streamlit stapelt Spalten auf schmalen Anzeigen. Browserprüfung bei 1440,
820 und 390 px protokolliert Viewport-/Dokumentbreite. Die PDF-Ansicht besitzt ein
zugängliches Label und eine separate Textansicht; Bild-/Formel-/Tabelleninhalte sind
damit noch nicht vollständig erschlossen.

Die Sichtprüfung korrigierte den Kontrast der aktiven Sidebaraktion (dunkelrot mit
weißem Text) und einen überdeckten mobilen Titel. Fokus per Tab wurde im echten
Browser beobachtet. Automatisierte AppTests prüfen Eingabelabels und ausdrückliche
Freigaben, ersetzen aber keine vollständige Tastatur-/Screenreaderprüfung.

Offen: NVDA/JAWS/VoiceOver-Prüfung, vollständiger Fokusreihenfolge-/Dialogtest,
200–400-%-Zoom, Hochkontrastmodus, umfangreiche lange Literaturtabellen und PDF-
Bedienung mit assistiven Technologien. Insbesondere der optionale Streamlit-PDF-
Viewer wird nicht pauschal als barrierefrei zertifiziert.
