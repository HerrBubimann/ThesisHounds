"""Local design system. Only static CSS and escaped labels enter HTML."""

from html import escape

import streamlit as st

TOKENS = {
    "accent": "#9F2338",
    "ink": "#202735",
    "muted": "#526071",
    "canvas": "#F6F7F9",
    "surface": "#FFFFFF",
    "border": "#D5DAE2",
    "sidebar": "#202735",
    "focus": "#245FCC",
}

CSS = """
<style>
:root { --th-accent:#9f2338;
 --th-ink:#202735;
 --th-muted:#526071;

 --th-border:#d5dae2;
 --th-surface:#fff;
 --th-focus:#245fcc;
 }
.stApp {background:#f6f7f9;
color:var(--th-ink);
}
.block-container {max-width:1540px;
padding:2rem 2.8rem 4rem;
}
h1 {font-size:1.9rem!important;
letter-spacing:-.04em;
font-weight:700!important;
}
h2 {font-size:1.5rem!important;
letter-spacing:-.02em;
}
h3 {font-size:1.1rem!important;
}
p, li {line-height:1.6;
}
[data-testid="stSidebar"] {background:#202735;
color:#f8fafc;
}
[data-testid="stSidebar"] .stCaption {color:#c9d0dc;
}
[data-testid="stSidebar"] button {justify-content:flex-start;
min-height:42px;
}
[data-testid="stMetric"] {background:#fff;
border:1px solid var(--th-border);

 padding:1.15rem 1.3rem;
border-radius:10px;
}
[data-testid="stMetricLabel"] {color:var(--th-muted);
}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius:10px;
}
button, input, textarea, select {border-radius:6px!important;
}
button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible,
[role="combobox"]:focus-visible {outline:3px solid var(--th-focus)!important;
outline-offset:3px!important;
}
button {min-height:40px!important;
}
.th-eyebrow {font-size:.75rem;
font-weight:700;
letter-spacing:.12em;
text-transform:uppercase;
color:#526071;
margin-bottom:.35rem;
}
.th-status {display:inline-block;
border:1px solid #bdc7d3;
border-radius:5px;

 padding:.18rem .55rem;
background:#edf0f4;
color:#243145;
font-size:.8rem;
margin-right:.45rem;
}
.th-empty {padding:2rem;
border:1px dashed #aab5c3;
border-radius:10px;
background:#fff;
}
.th-brand {font-weight:750;
font-size:1.45rem;
letter-spacing:-.04em;
color:#fff;
margin-bottom:.3rem;
}
.th-brand span {color:#ee96a4;
}
[data-testid="stAppDeployButton"] {display:none;
}
@media(max-width:1000px) {.block-container {padding:1.5rem 1.2rem 3rem;
}}
@media(max-width:700px) {h1 {font-size:1.55rem!important;
} .block-container {padding:3.5rem .8rem 2rem;
}}
@media(prefers-reduced-motion:reduce) {*,*::before,*::after {animation:none!important;
transition:none!important;
}}
</style>
"""

LABELS = {
    "PROFILE_SELECTED": "Erstbewertung offen",
    "INDEPENDENT_REVIEWS_RUNNING": "Unabhängige Prüfungen laufen",
    "AI_REVIEW_COMPLETED": "KI fertig · Inhalte gesperrt",
    "HUMAN_REVIEW_COMPLETED": "Erstbewertung abgeschlossen",
    "READY_FOR_COMPARISON": "Vergleich freigegeben",
    "DISCUSSION_IN_PROGRESS": "Menschliche Prüfung",
    "READY_FOR_FINALIZATION": "Bereit zum Abschluss",
    "FINALIZED": "Menschlich freigegeben",
    "CANCELLED": "Abgebrochen",
    "FAILED": "Fehlgeschlagen",
    "POSITIVE": "Positiv",
    "MIXED": "Gemischt",
    "NEGATIVE": "Kritisch",
    "NOT_ASSESSABLE": "Nicht bewertbar",
    "QUOTE_MATCHED": "Originalzitat bestätigt",
    "AGREEMENT": "Übereinstimmende Einschätzung",
    "PARTIAL_AGREEMENT": "Teilweise übereinstimmend",
    "DISAGREEMENT": "Unterschiedliche Einschätzung",
    "UNVERIFIABLE": "Nicht überprüfbar",
    "STRENGTH": "Wissenschaftliche Stärke",
    "WEAKNESS": "Wissenschaftliche Schwäche",
    "METHOD_CONCERN": "Methodische Auffälligkeit",
    "FORMAL_ISSUE": "Formale Auffälligkeit",
    "SOURCE_ISSUE": "Quellenproblem",
    "OPEN_QUESTION": "Offene Frage",
    "SECURITY_INCIDENT": "Sicherheitsverdacht",
    "IMPROVEMENT_SUGGESTION": "Verbesserungsvorschlag",
    "VERIFIED_METADATA": "Metadaten bestätigt",
    "METADATA_MISMATCH": "Metadatenkonflikt",
    "NOT_FOUND": "Im lokalen Bestand nicht gefunden",
    "INTERNAL_SOURCE": "Interne Quelle · lokale Prüfung",
    "RESEARCH_BLOCKED_BY_PRIVACY": "Recherche durch Datenschutz gesperrt",
    "MANUAL_REVIEW_REQUIRED": "Menschliche Prüfung erforderlich",
    "RETRACTED": "Retraktionshinweis vorhanden",
    "PROVIDER_CONFLICT": "Widersprüchliche Metadatenbestände",
    "FUZZY_MATCH_CANDIDATE": "Ähnlicher Eintrag · unbestätigter Kandidat",
    "PARTIAL_METADATA": "Metadaten nur teilweise überprüfbar",
}


def label(value):
    return LABELS.get(value, value or "Nicht erhoben")


def install_design():
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title, subtitle, *, area="Begutachtung"):
    st.caption(f"ThesisHounds / {area} / {title}")
    st.subheader(title)
    st.write(subtitle)


def status_badges(*values):
    st.markdown(
        "".join(f'<span class="th-status">{escape(str(label(v)))}</span>' for v in values),
        unsafe_allow_html=True,
    )


def empty_state(title, description):
    st.markdown(
        f'<div class="th-empty"><strong>{escape(title)}</strong><p>{escape(description)}</p></div>',
        unsafe_allow_html=True,
    )


def details(data, *, title="Technische Details"):
    with st.expander(title):
        st.json(data)


def assessment_phase(record):
    stages = [
        ("Angelegt", True),
        ("Menschliche Erstbewertung", record["human_completed"]),
        ("Unabhängige KI-Prüfung", record["ai_state"] == "COMPLETED"),
        ("Vergleich freigegeben", record["ai_released"]),
        ("Menschlicher Abschluss", record["state"] == "FINALIZED"),
    ]
    st.caption("   /   ".join(("✓ " if done else "○ ") + title for title, done in stages))
    if record["ai_state"] == "RUNNING":
        st.info(
            "KI-Prüfung läuft. Dauer und Zwischenschritte sind noch nicht "
            "bestimmbar. Inhalte bleiben bis zur Freigabe gesperrt."
        )
    else:
        status_badges(record["state"])
