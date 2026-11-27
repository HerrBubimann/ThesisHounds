"""Specialized local services compose existing policy-controlled review, not parallel runtimes."""

from app.knowledge.formal import check_formal
from app.research.citations import verify_citations
from app.research.provider_registry import LocalResearchCache


class AcademicReviewServices:
    """Rules → formal facts / citation extraction → offline verification → human review.

    No network tools, delegation, document-store search or access to human first reviews.
    Semantic research-quality review remains with the existing criterion-based local reviewer;
    only approved criteria may enter that LLM route, never a generated university rule.
    """

    def __init__(self, registry, cache=None):
        self.registry = registry
        self.cache = cache or LocalResearchCache()

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
