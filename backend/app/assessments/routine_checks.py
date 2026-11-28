"""Conservative text-only inventory, not citation existence or PDF layout validation."""

import re
from collections import Counter
from decimal import Decimal

from app.assessments.provenance import content_digest
from app.research.doi import DOI, normalize_doi
from app.security.classification import classify
from app.services.document_intelligence import INTERPRETATION_CUES, structure_document
from app.services.document_store import Document


def inventory(document: Document) -> dict:
    scope = {
        "classification": classify(document.classification),
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
    }

    occurrences = [
        {**scope, "doi_candidate": normalize_doi(match.group()), "page": page}
        for page, text in document.pages.items()
        for match in DOI.finditer(text)
    ]
    counts = Counter(item["doi_candidate"] for item in occurrences)
    return {
        **scope,
        "method": "deterministic_text_inventory.v1",
        "doi_candidates": occurrences,
        "repeated_doi_mentions": {doi: count for doi, count in counts.items() if count > 1},
        "verification": "UNVERIFIED",
        "limitations": "Repeated mentions are not duplicate bibliography entries. "
        "No source existence, bibliographic completeness, PDF layout "
        "or semantic citation correctness is established.",
    }


METRIC = re.compile(
    r"\b(?P<metric>accuracy|genauigkeit|precision|präzision|recall|sensitivität|f1(?:-score)?|auc|rmse|mae|mse)"
    r"\s*(?:=|:|beträgt|von|\|)\s*(?P<value>[+-]?\d{1,12}(?:[.,]\d{1,12})?)(?!\d|[.,]\d)"
    r"\s*(?P<unit>%|ms\b|s\b|kg\b|g\b|cm\b|mm\b|m\b)?",
    re.I,
)
CONTEXT = {
    "experiment": r"\b(?:Experiment|Versuch)\s+([\w.-]{1,60})",
    "model": r"\b(?:Modell|Model)\s+([\w.-]{1,60})",
    "dataset": r"\b(?:Datensatz|Dataset)\s+([\w.-]{1,60})",
    "split": r"\b(?:Split|Partition)\s+([\w.-]{1,60})",
}
ALIASES = {
    "genauigkeit": "accuracy",
    "präzision": "precision",
    "sensitivität": "recall",
    "f1-score": "f1",
}
UNITS = {
    "ms": ("time", "0.001"),
    "s": ("time", "1"),
    "kg": ("mass", "1"),
    "g": ("mass", "0.001"),
    "m": ("length", "1"),
    "cm": ("length", "0.01"),
    "mm": ("length", "0.001"),
}


def numerical_consistency(document):
    """Conservative text candidates; no values inferred from chart pixels or formulas."""
    structure = structure_document(document)
    claims, arithmetic, references, unparsed = [], [], [], []
    scope = {
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
        "classification": classify(document.classification),
        "document_sha256": content_digest(document.pages),
    }
    captions = set()
    for block in structure.blocks:
        if block.kind in {"BIBLIOGRAPHY", "CODE", "FORMULA"}:
            continue
        caption = re.match(
            r"\s*(Tabelle|Table|Abbildung|Figure|Abb\.)\s+(\d+)\s*:", block.text, re.I
        )
        if caption:
            captions.add(
                ("TABLE" if caption[1].lower() in {"tabelle", "table"} else "FIGURE", caption[2])
            )
        for match in re.finditer(
            r"\b(Tabelle|Table|Abbildung|Figure|Abb\.)\s+(\d+)\b", block.text, re.I
        ):
            if len(references) >= 200:
                break
            references.append(
                {
                    "kind": "TABLE" if match[1].lower() in {"tabelle", "table"} else "FIGURE",
                    "label": match[2],
                    "page": block.page,
                    "start": block.start + match.start(),
                    "end": block.start + match.end(),
                }
            )
        context = {}
        for key, pattern in CONTEXT.items():
            values = {
                m[1] for m in re.finditer(pattern + r"(?=\s*(?:[;:|,\n]|$))", block.text, re.I)
            }
            context[key] = next(iter(values)) if len(values) == 1 else None
        required_context_complete = all(context.values())
        for key, pattern in {
            "run": r"\b(?:Run|Lauf|Durchlauf|Wiederholung)\s+([\w.-]{1,60})",
            "seed": r"\b(?:Seed|Zufallsseed)\s*(?:=|:)?\s*(\d{1,12})",
            "fold": r"\b(?:Fold|Faltung)\s+([\w.-]{1,60})",
        }.items():
            values = {m[1] for m in re.finditer(pattern, block.text, re.I)}
            context[key] = (
                next(iter(values)) if len(values) == 1 else "AMBIGUOUS" if values else None
            )
        # A table row is considered only if it repeats its complete context explicitly.
        for match in METRIC.finditer(block.text):
            if len(claims) + len(unparsed) >= 200:
                break
            if any(
                q["page"] == block.page and q["start"] <= block.start + match.start() < q["end"]
                for q in structure.quotations
            ):
                continue
            # A recognized decimal prefix is not the value of an exponent, interval,
            # ratio or unknown attached suffix. Keep a bounded original-text warning.
            tail = block.text[match.end("unit") if match["unit"] else match.end("value") :]
            if re.match(r"[\w]|[.,]\d|\s*(?:[/–—-]\s*[+-]?\d|(?:bis|to)\s+\d)", tail):
                end = min(len(block.text), match.end() + 80)
                unparsed.append(
                    {
                        "page": block.page,
                        "start": block.start + match.start(),
                        "end": block.start + end,
                        "quote": block.text[match.start() : end],
                        "status": "UNSUPPORTED_NUMERIC_NOTATION_REQUIRES_HUMAN",
                        "human_review_required": True,
                    }
                )
                continue
            value = Decimal(match["value"].replace(",", "."))
            places = (
                len(match["value"].replace(",", ".").split(".")[1])
                if "." in match["value"].replace(",", ".")
                else 0
            )
            unit = (match["unit"] or "").lower()
            metric = ALIASES.get(match["metric"].lower(), match["metric"].lower())
            dimension, factor = UNITS.get(unit, (unit or "UNSPECIFIED", "1"))
            if metric in {"accuracy", "precision", "recall", "f1", "auc"}:
                if unit == "%":
                    dimension, factor = "fraction", "0.01"
                elif not unit and 0 <= value <= 1:
                    dimension = "fraction"
            claims.append(
                {
                    "id": f"numeric-{block.page}-{block.start + match.start()}",
                    "metric": metric,
                    "value": str(value),
                    "unit": unit or None,
                    "dimension": dimension,
                    "normalized": str(value * Decimal(factor)),
                    "rounding_radius": str(
                        Decimal("0.5") * Decimal(10) ** -places * Decimal(factor)
                    ),
                    "context": context,
                    "context_complete": required_context_complete
                    and "AMBIGUOUS" not in context.values(),
                    "metric_variant": next(
                        (
                            m[0].casefold()
                            for m in re.finditer(
                                r"\b(?:macro|micro|weighted)\b",
                                block.text[max(0, match.start() - 25) : match.start()],
                                re.I,
                            )
                        ),
                        None,
                    ),
                    "uncertainty_present": bool(
                        re.search(
                            r"±|\b(?:CI|Konfidenzintervall|confidence interval|ungefähr|"
                            r"approximately|mindestens|höchstens|zwischen)\b",
                            block.text,
                            re.I,
                        )
                        or INTERPRETATION_CUES.search(block.text)
                    ),
                    "page": block.page,
                    "start": block.start + match.start(),
                    "end": block.start + match.end(),
                    "quote": match.group(),
                    "chapter": block.chapter,
                    "extraction_verified": block.reliable and not document.extraction_warnings,
                    "visual_extraction_verified": False,
                }
            )
        for match in re.finditer(
            r"\b(\d{1,12})\s+(?:von|out of)\s+(\d{1,12})\s*(?:entsprechen|sind|=)\s*"
            r"(\d{1,3}(?:[.,]\d{1,6})?)\s*%",
            block.text,
            re.I,
        ):
            if len(arithmetic) >= 100:
                break
            if any(
                q["page"] == block.page and q["start"] <= block.start + match.start() < q["end"]
                for q in structure.quotations
            ):
                continue
            part, whole, percent = (
                Decimal(match[1]),
                Decimal(match[2]),
                Decimal(match[3].replace(",", ".")),
            )
            expected = part / whole * 100 if whole > 0 else None
            places = (
                len(match[3].split("," if "," in match[3] else ".")[1])
                if "." in match[3] or "," in match[3]
                else 0
            )
            radius = Decimal("0.5") * Decimal(10) ** -places
            arithmetic.append(
                {
                    "id": f"ratio-{block.page}-{block.start + match.start()}",
                    "page": block.page,
                    "start": block.start + match.start(),
                    "end": block.start + match.end(),
                    "quote": match.group(),
                    "reported_percent": str(percent),
                    "calculated_percent": str(expected) if expected is not None else None,
                    "status": "UNVERIFIED_EXTRACTION_REQUIRES_HUMAN"
                    if not block.reliable or document.extraction_warnings
                    else "UNCERTAINTY_REQUIRES_HUMAN"
                    if INTERPRETATION_CUES.search(block.text)
                    else "NOT_ASSESSABLE_INVALID_DENOMINATOR"
                    if expected is None
                    else "ARITHMETIC_MATCH"
                    if abs(expected - percent) <= radius
                    else "ARITHMETIC_MISMATCH_CANDIDATE",
                    "experimental_truth_verified": False,
                }
            )
    comparisons = []
    for i, first in enumerate(claims):
        for second in claims[i + 1 :]:
            if (
                first["metric"] != second["metric"]
                or first["context"] != second["context"]
                or first["metric_variant"] != second["metric_variant"]
            ):
                continue
            if (
                not first["context_complete"]
                or first["dimension"] == "UNSPECIFIED"
                or first["dimension"] != second["dimension"]
            ):
                continue
            if first["uncertainty_present"] or second["uncertainty_present"]:
                status = "UNCERTAINTY_REQUIRES_HUMAN"
            elif not first["extraction_verified"] or not second["extraction_verified"]:
                status = "UNVERIFIED_EXTRACTION_REQUIRES_HUMAN"
            else:
                difference = abs(Decimal(first["normalized"]) - Decimal(second["normalized"]))
                radius = Decimal(first["rounding_radius"]) + Decimal(second["rounding_radius"])
                status = (
                    "VALUE_AGREEMENT"
                    if difference == 0
                    else "ROUNDING_COMPATIBLE"
                    if difference <= radius
                    else "NUMERIC_CONFLICT_CANDIDATE"
                )
            comparisons.append(
                {
                    "first_id": first["id"],
                    "second_id": second["id"],
                    "status": status,
                    "sections": [first["chapter"], second["chapter"]],
                    "human_review_required": True,
                }
            )
            if len(comparisons) >= 200:
                break
        if len(comparisons) >= 200:
            break
    for row in references:
        row["status"] = (
            "CAPTION_CANDIDATE_LOCATED"
            if (row["kind"], row["label"]) in captions
            else "NOT_LOCATED_IN_EXTRACTED_TEXT"
        )
    return {
        **scope,
        "status": "COMPLETED_BOUNDED_TEXT_CHECK",
        "claims": claims,
        "unparsed_candidates": unparsed,
        "arithmetic": arithmetic,
        "comparisons": comparisons,
        "object_references": references[:200],
        "objects": list(structure.objects)[:100],
        "absence_proven": False,
        "automatic_grade_effect": False,
        "experiment_context_required": list(CONTEXT),
        "limits": {
            "claims_and_unparsed_combined": 200,
            "claims": 200,
            "comparisons": 200,
            "arithmetic": 100,
            "objects": 100,
        },
        "limitations": "Text extraction only; quotations, OCR and tables require human "
        "verification. No chart or formula interpretation.",
    }
