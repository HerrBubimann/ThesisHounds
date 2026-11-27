import asyncio
import json

import pytest
from app.agents.research_quality import review_source_use
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.model_registry import ModelRegistry
from app.llm.providers.base import Completion
from app.research.citations import extract_citations
from app.security.policy_engine import PolicyConfig, PolicyEngine

from tests.fixtures import CONFIG
from tests.fixtures.providers import WorkflowProvider
from tests.unit.test_citation_engine import doc, record
from tests.unit.test_institutional_rules import profile, resolved, rule


class QualityProvider(WorkflowProvider):
    def __init__(self, quote):
        super().__init__()
        self.quote, self.contexts = quote, []

    async def complete(self, model, messages, output_schema, max_tokens, *, unload):
        self.contexts.append(messages)
        return Completion(
            model=model.name,
            text=json.dumps(
                {
                    "relevance": "PLAUSIBLE",
                    "rationale": "Synthetic proposal only",
                    "source_quote": self.quote,
                    "limitation": "Abstract only; no fulltext verification.",
                }
            ),
        )


@pytest.mark.parametrize(
    "quote,expected", [("Synthetic source text", "PROPOSED"), ("invented", "REJECTED_UNGROUNDED")]
)
def test_quality_review_is_bounded_scoped_and_quote_grounded(quote, expected):
    async def scenario():
        provider = QualityProvider(quote)
        gateway = LLMGateway(
            ModelRegistry.load(CONFIG / "models.yaml"),
            {"ollama": provider},
            PolicyEngine(PolicyConfig()),
        )
        document = doc().model_copy(update={"analysis_id": "synthetic-scope"})
        entry = extract_citations(document)["entries"][0]
        rules = resolved(p=profile([rule(id="quality", method="human_quality_review")]))
        snapshot = record(abstract="Synthetic source text")
        result = await review_source_use(
            gateway,
            document,
            rules,
            "quality",
            entry,
            snapshot,
            CallBudget(2, 50000),
            model_id="llama",
            page=1,
            quote="Synthetic" if "Synthetic" in document.pages[1] else "Ergebnis",
        )
        assert result["status"] == expected and result["source_coverage"] == "ABSTRACT"
        assert (
            result["semantic_support"] == "HUMAN_REVIEW_REQUIRED"
            and not result["automatic_grade_effect"]
        )
        context = json.loads(provider.contexts[0][1]["content"])
        assert set(context) == {
            "criterion",
            "untrusted_passage",
            "untrusted_source",
            "source_coverage",
            "entry_id",
        }
        assert "human" not in context and "pages" not in context
        with pytest.raises(LLMError):
            await review_source_use(
                gateway,
                document.model_copy(update={"classification": "RESTRICTED"}),
                rules,
                "quality",
                entry,
                snapshot,
                CallBudget(2, 50000),
                model_id="llama",
                page=1,
                quote="Ergebnis",
            )
        assert len(provider.contexts) == 1

    asyncio.run(scenario())


def test_no_rule_no_passage_or_no_material_does_not_call_a_model():
    async def scenario():
        provider = QualityProvider("source")
        gateway = LLMGateway(
            ModelRegistry.load(CONFIG / "models.yaml"),
            {"ollama": provider},
            PolicyEngine(PolicyConfig()),
        )
        document = doc().model_copy(update={"analysis_id": "scope"})
        entry = extract_citations(document)["entries"][0]
        rules = resolved(p=profile([rule(id="quality", method="human_quality_review")]))
        for key, page, quote in [("unknown", 1, "Ergebnis"), ("quality", 1, "invented")]:
            with pytest.raises(LLMError):
                await review_source_use(
                    gateway,
                    document,
                    rules,
                    key,
                    entry,
                    record(),
                    CallBudget(1, 50000),
                    model_id="llama",
                    page=page,
                    quote=quote,
                )
        result = await review_source_use(
            gateway,
            document,
            rules,
            "quality",
            entry,
            record(),
            CallBudget(1, 50000),
            model_id="llama",
            page=1,
            quote="Ergebnis",
        )
        assert result["reason"] == "METADATA_ONLY" and not provider.contexts
        with pytest.raises(LLMError, match="SCOPE"):
            await review_source_use(
                gateway,
                document,
                rules,
                "quality",
                entry,
                record(doi="10.5555/other", abstract="source"),
                CallBudget(1, 50000),
                model_id="llama",
                page=1,
                quote="Ergebnis",
            )

    asyncio.run(scenario())
