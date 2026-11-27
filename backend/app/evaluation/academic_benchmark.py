"""Reproducible synthetic extraction/verification and formal decision benchmarks. No model calls."""

import argparse
import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from app.knowledge.formal import FormalMeasurements, check_formal, document_hash
from app.research.citations import extract_citations, verify_citations
from app.research.provider_registry import LocalResearchCache, MetadataRecord, SourceType
from app.services.document_store import Document


def exact_metrics(predicted, expected):
    true_positive = len(predicted & expected)
    false_positive = len(predicted - expected)
    false_negative = len(expected - predicted)
    precision = true_positive / len(predicted) if predicted else None
    recall = true_positive / len(expected) if expected else None
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision and recall else 0.0,
    }


def run_benchmarks() -> dict:
    citation_rows = []
    for work_type in ("PA1", "PA2", "BA"):
        for style in ("numeric", "author_year"):
            body = (
                "Synthetic finding [1]. Unknown citation [9]."
                if style == "numeric"
                else ("Synthetic finding (Muster, 2020). Unknown citation (Fehlt, 2021).")
            )
            doc = Document(
                document_id="synthetic-benchmark",
                classification="PUBLIC",
                complete=True,
                pages={
                    1: body,
                    2: "Literaturverzeichnis\n"
                    "[1] Muster (2020). Synthetischer Titel. doi:10.5555/demo\n"
                    "[2] Intern (2021). Interner Bericht. intern",
                },
            )
            record = MetadataRecord(
                doi="10.5555/demo",
                title="Synthetischer Titel",
                authors=["Muster"],
                year=2020,
                source_type=SourceType.PAPER,
                provider="crossref",
                retrieved_at=datetime(2026, 1, 1, tzinfo=UTC),
                snapshot_sha256="a" * 64,
                provenance="SYNTHETIC_FIXTURE_NOT_AN_API_RESULT",
            )
            extraction = extract_citations(doc)
            reference_metrics = exact_metrics(
                {(e.id, e.author, e.year, e.doi) for e in extraction["entries"]},
                {("1", "Muster", 2020, "10.5555/demo"), ("2", "Intern", 2021, None)},
            )
            mention_metrics = exact_metrics(
                {(m["number"], m["author"], m["year"]) for m in extraction["mentions"]},
                {("1", None, None), ("9", None, None)}
                if style == "numeric"
                else {(None, "Muster", 2020), (None, "Fehlt", 2021)},
            )
            checked = verify_citations(doc, LocalResearchCache([record]))
            mismatch = verify_citations(
                doc, LocalResearchCache([record.model_copy(update={"year": 2022})])
            )
            checks = {
                "reference_count_exact": len(extraction["entries"]) == 2,
                "mentions_exact": len(extraction["mentions"]) == 2,
                "missing_reference_exact": len(checked["missing_reference_candidates"]) == 1,
                "metadata_match": "VERIFIED_METADATA" in checked["references"][0]["statuses"],
                "metadata_mismatch": "METADATA_MISMATCH" in mismatch["references"][0]["statuses"],
                "internal_source": checked["references"][1]["statuses"] == ["INTERNAL_SOURCE"],
            }
            citation_rows.append(
                {
                    "work_type": work_type,
                    "style": style,
                    "checks": checks,
                    "reference_extraction": reference_metrics,
                    "citation_extraction": mention_metrics,
                    "passed": all(checks.values())
                    and reference_metrics["f1"] == 1
                    and mention_metrics["f1"] == 1,
                }
            )
    formal_rows = []
    for count in (19, 20, 30, 31):
        doc = Document(
            document_id="synthetic-formal",
            classification="PUBLIC",
            complete=True,
            pages={i: "Synthetischer Inhalt" for i in range(1, 41)},
        )
        rules = {
            "status": "ACTIVE",
            "rules": [
                {
                    "id": "pages",
                    "description": "Synthetic only",
                    "source_id": "synthetic",
                    "source_location": "fixture",
                    "active": True,
                    "method": "content_pages",
                    "scope": "DOCUMENT",
                    "parameters": {"min": 20, "max": 30, "basis": "REVIEWED_CONTENT"},
                }
            ],
        }
        measured = FormalMeasurements(
            document_hash(doc), "synthetic-human-fixture", count, "REVIEWED_CONTENT"
        )
        decision = check_formal(doc, rules, measured)["checks"][0]
        expected = "PASS" if 20 <= count <= 30 else "FAIL"
        uncertain = check_formal(doc, rules, replace(measured, document_sha256="b" * 64))
        formal_rows.append(
            {
                "case": f"reviewed-content-{count}",
                "expected": expected,
                "actual": decision["status"],
                "passed": decision["status"] == expected
                and uncertain["checks"][0]["status"] == "MANUAL_REVIEW_REQUIRED",
            }
        )
    report = {
        "kind": "SYNTHETIC_ACADEMIC_BENCHMARK",
        "version": 1,
        "citation_cases": citation_rows,
        "formal_cases": formal_rows,
        "model_quality_evaluated": False,
        "grobid_quality_evaluated": False,
        "external_requests": 0,
        "ground_truth": "HAND_AUTHORED_SYNTHETIC_EXPECTATIONS",
        "limitations": "Narrow fixtures; no representative accuracy estimate or expert study.",
    }
    report["passed"] = all(r["passed"] for r in citation_rows + formal_rows)
    report["manifest_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True).encode()
    ).hexdigest()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/academic-benchmark.json"))
    args = parser.parse_args()
    report = run_benchmarks()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "citation_cases": 6,
                "formal_cases": 4,
                "external_requests": 0,
            }
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
