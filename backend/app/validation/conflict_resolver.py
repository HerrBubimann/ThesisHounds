from app.schemas.domain import Finding


class ConflictResolver:
    def detect(self, findings: list[Finding]) -> int:
        for finding in findings:
            finding.conflict = finding.conflict or any(
                review.verdict in {"UNSUPPORTED", "PARTIALLY_SUPPORTED", "UNCERTAIN"}
                or review.missing_context
                or review.possible_hallucination
                for review in finding.reviews
            )
        for index, first in enumerate(findings):
            for second in findings[index + 1 :]:
                # Conservative candidate conflict: same category/page, opposing evaluation.
                # Do not silently merge, discard or claim semantic contradiction certainty.
                if (
                    first.category == second.category
                    and first.page == second.page
                    and first.kind != second.kind
                ):
                    first.conflict = second.conflict = True
        return sum(finding.conflict for finding in findings)
