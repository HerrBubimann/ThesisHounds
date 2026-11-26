from app.core.execution_engine import ExecutionEngine
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget
from app.schemas.domain import AgentRecord, Finding, ModelReview, ReviewOutput
from app.services.document_store import Document


class CrossModelReview:
    def __init__(self, engine: ExecutionEngine):
        self.engine = engine

    async def review(
        self, finding: Finding, reviewer: AgentRecord, document: Document, budget: CallBudget
    ) -> None:
        if reviewer.manufacturer == finding.manufacturer:
            raise LLMError(403, "Review muss von einem anderen Modellhersteller stammen.")

        async def operation():
            return await self.engine.ask(
                reviewer,
                document,
                budget,
                "review",
                {
                    "finding": finding.model_dump(
                        include={"statement", "kind", "quote", "page", "rationale"}
                    ),
                    "document": document.pages,
                    "checks": [
                        "Nachvollziehbarkeit",
                        "Textbeleg",
                        "fachliche Berechtigung",
                        "Kontext",
                        "Halluzination",
                    ],
                },
                ReviewOutput,
            )

        result = await self.engine.execute(reviewer, operation)
        finding.reviews.append(
            ModelReview(
                **result.model_dump(),
                model_id=reviewer.model_id,
                manufacturer=reviewer.manufacturer,
            )
        )
        finding.review_status = "REVIEWED"
