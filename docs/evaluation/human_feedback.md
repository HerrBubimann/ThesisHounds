# Strukturiertes lokales Gutachterfeedback

OFF-1/3/4/5. Der bestehende Human-in-the-Loop-Ablauf bleibt verbindlich: unabhängige
Erstbewertung, gemeinsames Ergebnisembargo, explizite menschliche Entscheidungen
und Schlussfreigabe. Befundfeedback ersetzt keine dieser Freigaben.

UI und `POST /api/v1/assessments/{id}/finding-feedback` unterstützen ACCEPT, REJECT,
CORRECT, SUPPLEMENT, NOT_RELEVANT, INSUFFICIENT_EVIDENCE und MANUAL_REVIEW_REQUIRED.
Ablehnung, Korrektur,
Irrelevanz oder Evidenzmangel brauchen einen strukturierten Grund: falsche Aussage,
fehlender Kontext, falsches Kriterium, Quellenfehler, unberechtigte Kritik,
unzureichende Evidenz oder Doppelbefund. Korrektur/Ergänzung braucht eigenen Text.
FACTUAL_ERROR bezeichnet einen vom Menschen bestätigten fachlichen Fehler.
Begründungen sind verpflichtend, Versionen begrenzt, Originalbefunde unverändert.

Feedback gehört zur zugewiesenen Analyse und Befund-ID, erhält RESTRICTED und
monotone Revisionsnummern. Fremde IDs, Feedback vor Freigabe und Änderungen nach
Finalisierung werden abgewiesen. Eine spätere Zustimmung löscht eine vorangegangene
Korrektur nicht aus der Historie. Der Entwurf kann eine ausdrücklich gewählte
menschliche Korrektur und Ergänzungen darstellen; Originalbeleg und Korrekturquelle
werden unterschieden. Zuletzt abgelehnte/irrelevante/unzureichend belegte Befunde
können nicht ungeklärt in einen finalen Entwurf übernommen werden.
MANUAL_REVIEW_REQUIRED sperrt ebenfalls die Übernahme, bis neues menschliches
Feedback die offene Frage klärt.

Ausgaben enthalten zusätzlich normalisierte `outcome`- und `error_category`-Codes:
ACCEPTED, REJECTED, CORRECTED, INSUFFICIENT_EVIDENCE, MANUAL_REVIEW_REQUIRED sowie
MISSING_CONTEXT, INCORRECT_CRITERION, FACTUAL_ERROR und DUPLICATE_FINDING. Die
bestehenden Aktionsnamen bleiben kompatibel. SUPPLEMENT hat SUPPLEMENTED als
eigenen Zustand und wird nicht als neue Akzeptanz gezählt.

`feedback_evaluation` im geschützten Vergleich und in Provenance gruppiert nach
Modell, Agent, Kriterium und Fehlerkategorie. Jede Befund-ID zählt mit ihrem letzten
Feedback genau einmal; Versionszahl und noch unkommentierte Befunde sind separat.
Diese lokale Evidenz unterstützt die menschliche Prüfung der Modellzuordnung,
ändert sie aber nicht automatisch. Akzeptanzzählungen sind keine Präzisionsmessung.

Keine Modellaufrufe, automatisches Training oder Fine-Tuning folgen aus Feedback.
Keine organisationsübergreifende Qualitätsstatistik oder Bewertung einzelner
Gutachter. Ohne organisatorische/rechtliche Freigabe bleibt Cross-Assessment-
Aggregation deaktiviert. Die vorhandene lokale Referenzschnittstelle kann eine
separat genehmigte Evaluation unterstützen; menschliches Accept allein wird nicht
automatisch als wissenschaftliches Goldlabel umgedeutet.

Feedback und Provenance liegen mit dem Assessment im lokalen RAM und werden mit
ihm gelöscht. Manipulationsgeschütztes dauerhaftes Audit, echte Personenidentität,
offizielle Aufbewahrung und Recovery bleiben institutionelle Produktionsblocker.
