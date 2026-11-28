"""Specialized local services compose the existing policy-controlled review."""

import asyncio
import time
from collections import Counter

from app.assessments.provenance import content_digest
from app.assessments.routine_checks import numerical_consistency
from app.evaluation.retrieval import review_retrieval
from app.knowledge.formal import check_formal
from app.llm.errors import LLMError
from app.research.citations import verify_citations
from app.research.provider_registry import LocalResearchCache
from app.security.classification import classify
from app.services.citation_style import LocalCitationStyle
from app.services.language_tool import LocalLanguageTool
from app.services.local_embeddings import LocalEmbeddingRunner


class AcademicReviewServices:
    """Rules → formal facts / citation extraction → offline verification → human review.

    No public network tools, delegation, document-store search or access to human first reviews.
    Optional loopback language suggestions require an explicitly configured formal criterion.
    Semantic research-quality review remains with the existing criterion-based local reviewer;
    only approved criteria may enter that LLM route, never a generated university rule.
    """

    def __init__(
        self, registry, cache=None, language_tool=None, embeddings=None, citation_style=None
    ):
        self.registry = registry
        self.cache = cache or LocalResearchCache()
        self.language_tool = language_tool or LocalLanguageTool()
        self.embeddings = embeddings or LocalEmbeddingRunner()
        self.citation_style = citation_style or LocalCitationStyle()

    async def run_checks(self, document, profile, resolved, review, *, slots, runtime_limit):
        """Bounded siblings; required failures cancel and drain the whole task group.

        Only document/profile snapshots enter operations, never the human first review.
        Optional failures remain visible without discarding the independent core review.
        """
        if classify(document.classification) != "PUBLIC":
            raise LLMError(403, "PARALLEL_PRIVATE_PROCESSING_NOT_RELEASED")
        results, execution = {}, {}

        async def run(name, operation, required=False):
            async with slots:
                started = time.monotonic()
                try:
                    async with asyncio.timeout(runtime_limit):
                        results[name] = await operation()
                    status = "COMPLETED"
                except Exception:
                    if required:
                        raise
                    status = "FAILED_REQUIRES_HUMAN"
                    results[name] = {"status": status}
                execution[name] = {
                    "status": status,
                    "required": required,
                    "seconds": time.monotonic() - started,
                }
                value = results[name]
                if isinstance(value, dict):
                    execution[name]["result_status"] = value.get(
                        "status", "LOCAL_FACTS_REQUIRES_HUMAN"
                    )
                elif name == "language":
                    execution[name]["result_status"] = sorted({r["status"] for r in value})
                else:
                    execution[name]["result_status"] = "MODEL_FINDINGS_REQUIRES_HUMAN"

        operations = [
            ("scientific_review", review, True),
            ("academic", lambda: asyncio.to_thread(self.check, document, resolved), True),
            ("language", lambda: self.check_language(document, profile), False),
            ("retrieval", lambda: review_retrieval(document, profile, self.embeddings), False),
            ("citation_style", lambda: self.citation_style.check(document, profile), False),
            ("numerical", lambda: asyncio.to_thread(numerical_consistency, document), False),
        ]
        async with asyncio.TaskGroup() as group:
            for name, operation, required in operations:
                group.create_task(run(name, operation, required), name="assessment:" + name)
        return {
            "results": {name: results[name] for name, _, _ in operations},
            "execution": {name: execution[name] for name, _, _ in operations},
            "document_sha256": content_digest(document.pages),
            "profile_sha256": content_digest(profile.model_dump()),
            "analysis_id": document.analysis_id,
            "document_id": document.document_id,
            "automatic_grade_effect": False,
        }

    @staticmethod
    def summarize(bundle, findings):
        """Stable synthesis of execution and unresolved evidence, never majority voting."""
        results = bundle["results"]
        flat = [v for f in findings for v in [f, *f.supplemental]]
        limitations = []
        for name, execution in bundle["execution"].items():
            if execution["status"] != "COMPLETED":
                limitations.append({"check": name, "status": execution["status"]})
        optional = {"citation_style": results["citation_style"]}
        for key, value in results["retrieval"].get("models", {}).items():
            optional["embedding:" + key] = value
            if value.get("complete_document_search") is False:
                limitations.append({"check": "embedding:" + key, "status": "BOUNDED_CHUNK_SUBSET"})
        for i, value in enumerate(
            results["language"] if isinstance(results["language"], list) else []
        ):
            optional["language:" + str(i)] = value
        for name, value in optional.items():
            status = value.get("status", "UNKNOWN")
            if status == "DISABLED" and value.get("configured"):
                status = "BLOCKED_LOCAL_LANGUAGE_TOOL_DISABLED"
            if status not in {
                "COMPLETED",
                "COMPLETED_REQUIRES_HUMAN",
                "NOT_APPLICABLE",
                "DISABLED",
                "NOT_APPLICABLE_TO_CONFIGURED_CRITERION",
                "COMPLETED_BOUNDED_TEXT_CHECK",
            }:
                limitations.append({"check": name, "status": status})
        citations = results["academic"]["citations"]["references"]
        return {
            "status": "HUMAN_REVIEW_REQUIRED",
            "execution_complete": not any(
                v["status"] != "COMPLETED" for v in bundle["execution"].values()
            ),
            "checks": bundle["execution"],
            "configured_checks_complete": not any(
                row["status"] != "BLOCKED_NO_APPROVED_ARTIFACT" for row in limitations
            ),
            "limitations": limitations,
            "conflicting_finding_ids": [f.finding_id for f in flat if f.conflict],
            "not_assessable_criterion_ids": sorted(
                {f.criterion_id for f in flat if f.judgment == "NOT_ASSESSABLE"}
            ),
            "source_status_counts": dict(Counter(s for r in citations for s in r["statuses"])),
            "finding_count": len(flat),
            "automatic_grade_effect": False,
            "consensus_establishes_truth": False,
            "semantic_advantage": "NOT_ESTABLISHED",
            "numeric_conflict_candidates": sum(
                c["status"] == "NUMERIC_CONFLICT_CANDIDATE"
                for c in results.get("numerical", {}).get("comparisons", [])
            ),
            "document_sha256": bundle["document_sha256"],
            "profile_sha256": bundle["profile_sha256"],
            "analysis_id": bundle["analysis_id"],
            "document_id": bundle["document_id"],
            "origins": {
                "scientific_review": "MODEL_INTERPRETATION",
                "academic": "LOCAL_RULES_AND_METADATA",
                "retrieval": "ORIGINAL_DOCUMENT_LOCATIONS",
                "citation_style": "LOCAL_CSL_FORMAT_CANDIDATES",
                "language": "LOCAL_LANGUAGE_SUGGESTIONS",
            },
        }

    async def check_language(self, document, profile):
        return [
            {
                **await self.language_tool.check(document, criterion),
                "configured": "language" in criterion.local_checks,
            }
            for criterion in profile.criteria
            if criterion.category == "formal"
        ]

    def rules(self, program, cohort, work_type):
        return self.registry.resolve(program, cohort, work_type, clearance="PUBLIC")

    def check(self, document, resolved):
        result = {
            "classification": document.classification,
            "formal": check_formal(document, resolved),
            "citations": verify_citations(document, self.cache),
            "rules_status": resolved["status"],
            "quality_review": "HUMAN_REVIEW_REQUIRED",
            "external_requests": 0,
        }
        refs = [
            {
                "criterion_id": r["id"],
                "source_id": r["source_id"],
                "source_location": r["source_location"],
                "status": r["status"],
            }
            for r in resolved["rules"]
            if r["method"] in {"citation_consistency", "human_quality_review"}
        ]
        for row in result["citations"]["references"]:
            row["criterion_references"] = refs
        return result
