"""Identical scoped chunks and queries; quality is null without explicit human relevance labels."""

import argparse
import asyncio
import json
import math
import time
import tracemalloc
from pathlib import Path

from app.assessments.provenance import content_digest
from app.schemas.domain import StrictModel
from app.services.context_management import LocalContextIndex
from app.services.document_store import SYNTHETIC_PAGES, Document
from pydantic import Field


class RetrievalReference(StrictModel):
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    reviewed_by: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=600)
    relevance: dict[str, int]


def ranking_metrics(ranking, relevance, k):
    if not 1 <= k <= 100 or len(ranking) != len(set(ranking)):
        raise ValueError("RETRIEVAL_RANKING_OR_K_DENIED")
    if not relevance or any(type(r) is not int or not 0 <= r <= 3 for r in relevance.values()):
        raise ValueError("RETRIEVAL_RELEVANCE_DENIED")
    positive = {key for key, grade in relevance.items() if grade > 0}
    if not positive:
        raise ValueError("RETRIEVAL_POSITIVE_REFERENCE_REQUIRED")
    selected = ranking[:k]
    dcg = sum((2 ** relevance.get(key, 0) - 1) / math.log2(i + 2) for i, key in enumerate(selected))
    ideal = sum(
        (2**grade - 1) / math.log2(i + 2)
        for i, grade in enumerate(sorted(relevance.values(), reverse=True)[:k])
    )
    return {
        "precision_at_k": len(set(selected) & positive) / k,
        "recall_at_k": len(set(selected) & positive) / len(positive),
        "mrr_at_k": next((1 / (i + 1) for i, key in enumerate(selected) if key in positive), 0),
        "ndcg_at_k": dcg / ideal,
    }


def evaluate_retrieval(document, queries, *, references=(), k=5):
    with LocalContextIndex(document) as index:
        return _evaluate_retrieval(document, queries, index=index, references=references, k=k)


def _evaluate_retrieval(document, queries, *, index, references=(), k=5):
    if not document.analysis_id or not 1 <= k <= 100 or not 1 <= len(queries) <= 100:
        raise ValueError("RETRIEVAL_EVALUATION_SCOPE_OR_LIMIT_DENIED")
    scope = content_digest(document.pages)
    labels = {}
    for reference in references:
        reference = RetrievalReference.model_validate(reference.model_dump())
        if reference.document_sha256 != scope or reference.query in labels:
            raise ValueError("RETRIEVAL_REFERENCE_SCOPE_DENIED")
        if not set(reference.relevance) <= {c.id for c in index.chunks}:
            raise ValueError("RETRIEVAL_REFERENCE_PASSAGE_DENIED")
        labels[reference.query] = reference
    rows = []
    for query in queries:
        for variant in "ABCDE":
            row = {
                "variant": variant,
                "query_sha256": content_digest(query),
                "k": k,
                "metrics": None,
                "reference_status": "NO_HUMAN_REFERENCES",
            }
            if variant in "CDE":
                rows.append({**row, "status": "BLOCKED_NO_APPROVED_EMBEDDING_OR_RERANKER"})
                continue
            started = time.monotonic()
            tracing = tracemalloc.is_tracing()
            if not tracing:
                tracemalloc.start()
            try:
                found = (
                    index.search(
                        query,
                        analysis_id=document.analysis_id,
                        document_id=document.document_id,
                        category="content",
                    )
                    if variant == "A"
                    else index.search_fulltext(
                        query,
                        analysis_id=document.analysis_id,
                        document_id=document.document_id,
                        limit=k,
                    )
                )[:k]
                _, peak = tracemalloc.get_traced_memory()
            finally:
                if not tracing:
                    tracemalloc.stop()
            if query in labels:
                row.update(
                    metrics=ranking_metrics(
                        [c.id for c, _, _ in found], labels[query].relevance, k
                    ),
                    reference_status="OPERATOR_SUPPLIED_HUMAN_LABELS",
                )
            rows.append(
                {
                    **row,
                    "status": "COMPLETED",
                    "search_seconds": time.monotonic() - started,
                    "python_peak_bytes": peak if not tracing else None,
                    "memory_scope": "PYTHON_ALLOCATIONS_NOT_SQLITE_OR_MODEL_RSS",
                    "results": [
                        {
                            "chunk_id": c.id,
                            "page": c.page,
                            "start": c.start,
                            "end": c.end,
                            "score": score,
                        }
                        for c, score, _ in found
                    ],
                }
            )
    return {
        "document_sha256": scope,
        "analysis_id": document.analysis_id,
        "document_id": document.document_id,
        "classification": document.classification,
        "results": rows,
        "semantic_advantage": "NOT_ESTABLISHED",
        "reference_passages": "SAME_CHUNKS_ALL_VARIANTS",
        "absence_proven": False,
        "fts_index_builds": index.fts_build_count,
    }


async def review_retrieval(document, profile, runner, *, k=5, references=()):
    """Compare locations using identical scoped chunks; no human review enters queries.

    This online review diagnostic deliberately avoids process-global tracemalloc.
    A semantic advantage can only be evaluated separately with human relevance labels.
    """
    criteria = list(profile.criteria)
    queries = [(c.description + " " + c.expected_evidence)[:600] for c in criteria]
    with LocalContextIndex(document) as index:
        labels = {}
        for reference in references:
            reference = RetrievalReference.model_validate(reference.model_dump())
            if (
                reference.document_sha256 != content_digest(document.pages)
                or reference.query not in queries
                or reference.query in labels
                or not set(reference.relevance) <= {c.id for c in index.chunks}
            ):
                raise ValueError("RETRIEVAL_REFERENCE_SCOPE_DENIED")
            labels[reference.query] = reference

        def lexical():
            rows = []
            for query in queries:
                rows.append(
                    [
                        index.search(
                            query,
                            analysis_id=document.analysis_id,
                            document_id=document.document_id,
                            category="content",
                        )[:k],
                        index.search_fulltext(
                            query,
                            analysis_id=document.analysis_id,
                            document_id=document.document_id,
                            limit=k,
                        ),
                    ]
                )
            return rows

        baseline = await asyncio.to_thread(lexical)
        models = await runner.rankings(index, queries)
        rows = []

        def locations(found):
            return [
                {
                    "chunk_id": c.id,
                    "page": c.page,
                    "start": c.start,
                    "end": c.end,
                    "score": score,
                    "method": method,
                }
                for c, score, method in found
            ]

        for i, criterion in enumerate(criteria):
            rankings = {"feature_hash_hybrid": baseline[i][0], "sqlite_fts5": baseline[i][1]}
            for key, value in models.items():
                if value["status"] == "COMPLETED":
                    rankings[key] = value["rankings"][i][:k]
            combined = index.fuse_rankings(rankings.values(), limit=k)
            metrics = None
            if queries[i] in labels:
                metrics = {
                    key: ranking_metrics(
                        [c.id for c, _, _ in value], labels[queries[i]].relevance, k
                    )
                    for key, value in {**rankings, "combined": combined}.items()
                }
            rows.append(
                {
                    "criterion_id": criterion.id,
                    "query_sha256": content_digest(queries[i]),
                    "methods": {key: locations(value) for key, value in rankings.items()},
                    "combined_locations": locations(combined),
                    "metrics": metrics,
                    "human_relevance_labels": queries[i] in labels,
                }
            )
        return {
            "status": "COMPLETED",
            "results": rows,
            "models": {
                key: {k: v for k, v in value.items() if k != "rankings"}
                for key, value in models.items()
            },
            "fts_index_builds": index.fts_build_count,
            "chunk_count": len(index.chunks),
            "analysis_id": document.analysis_id,
            "document_id": document.document_id,
            "document_sha256": content_digest(document.pages),
            "fusion": "RRF_K60_LOCATIONS_ONLY",
            "semantic_advantage": "NOT_ESTABLISHED",
            "absence_proven": False,
            "automatic_grade_effect": False,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = Document(
        document_id="synthetic-retrieval",
        analysis_id="synthetic-retrieval",
        classification="PUBLIC",
        pages=dict(SYNTHETIC_PAGES),
    )
    report = evaluate_retrieval(document, ["Methodik Limitationen", "Forschungsfrage Ergebnisse"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps({"status": "SYNTHETIC_RETRIEVAL_COMPLETED", "human_references": False}))


if __name__ == "__main__":
    main()
