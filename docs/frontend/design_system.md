# Designsystem

Stand: 28.11.2026. Implementierung: `frontend/design.py` und
`frontend/.streamlit/config.toml`. Alle Schriften kommen aus dem lokalen System:
Arial / sans-serif und monospace. Keine CDN-Fonts, Tracking-Skripte oder fremden Logos.

| Token | Wert | Verwendung |
|---|---|---|
| Akzent | `#9F2338` | primäre Aktion, aktive Navigation; weiße Beschriftung |
| Text | `#202735` | Fließtext, Überschriften |
| Sekundärtext | `#526071` | erklärende Beschriftungen |
| Hintergrund | `#F6F7F9` | ruhige Arbeitsfläche |
| Oberfläche | `#FFFFFF` | Karten und Eingaben |
| Rand | `#D5DAE2` | Gruppierung; nicht alleinige Zustandsinformation |
| Sidebar | `#202735` | Navigation mit hellem Text |
| Fokus | `#245FCC` | sichtbare Tastaturkontur |

Maximale Inhaltsbreite 1540 px. Desktop: großzügige Seitenränder; unter 1000 px
reduziert; unter 700 px zusätzlicher Abstand zum Streamlit-Kopf. Schriftgrößen
verwenden rem. Kartenradius 10 px, Eingaben 6 px. Schaltflächen mindestens 40 px hoch.
Keine Abhängigkeit von Hover für wesentliche Inhalte; Zustände immer mit Text.

Menschliche und KI-Einschätzungen verwenden dieselben neutralen Statusflächen.
Es gibt keine dekorativen Confidence-Werte, Qualitätsampeln oder behauptete
Notenwirkung. Die Wortmarke bezeichnet den Prototyp und kein offizielles DHBW-Produkt.
