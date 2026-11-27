import asyncio
import json
from uuid import uuid4

from app.assessments.adversarial_verification import verify_finding
from app.assessments.schemas import AssessmentFinding
from app.core.configuration import RuntimeConfig
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.providers.base import Completion
from app.services.document_intelligence import structure_document
from app.services.document_store import Document

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider


class Challenger(AssessmentProvider):
    def __init__(self, verdicts, counter_quote):
        super().__init__()
        self.verdicts = iter(verdicts)
        self.counter_quote = counter_quote

    async def complete(self, model, messages, output_schema, max_tokens, *, unload):
        self.contexts.append(messages)
        return Completion(
            model=model.name,
            text=json.dumps(
                {
                    "verdict": next(self.verdicts),
                    "rationale": "Synthetic challenge",
                    "counterargument": "Other chapters limit the interpretation.",
                    "counter_page": 2,
                    "counter_quote": self.counter_quote,
                }
            ),
        )


def scenario(
    verdicts, *, quote="Original statement", max_rounds=2, counter_quote="Invented counterquote"
):
    async def run():
        config = RuntimeConfig(CONFIG)
        config.limits = config.limits.model_copy(update={"max_conflict_reviews": max_rounds})
        provider = Challenger(verdicts, counter_quote)
        gateway = LLMGateway(config.models, {"ollama": provider}, config.policy)
        key = str(uuid4())
        document = Document(
            document_id="synthetic",
            analysis_id=key,
            classification="PUBLIC",
            pages={1: "Original statement", 2: "Counterargument in another chapter"},
        )
        finding = AssessmentFinding(
            assessment_id=key,
            criterion_id="methodology",
            category="methodology",
            model_id="qwen",
            manufacturer="Alibaba",
            agent_id="synthetic",
            judgment="NEGATIVE",
            kind="WEAKNESS",
            description="Synthetic criticism",
            rationale="Synthetic rationale",
            page=1,
            quote=quote,
            data_classification="PUBLIC",
        )
        budget = CallBudget(10, 100000)
        available = {m.name: m.digest for m in await provider.discover()}
        await verify_finding(
            gateway, config, finding, document, structure_document(document), budget, available
        )
        return finding, budget, provider

    return asyncio.run(run())


def test_a_later_supporter_does_not_erase_an_adversarial_disagreement():
    finding, budget, provider = scenario(["UNSUPPORTED", "SUPPORTED"])
    assert finding.conflict and finding.verification_status != "MODEL_SUPPORTED"
    assert budget.calls == 2 and len(provider.contexts) == 2
    assert all(r["manufacturer"] != "Alibaba" for r in finding.verification_rounds)
    assert finding.verification_rounds[0]["counter_evidence_status"] == "REJECTED"
    assert finding.description == "Synthetic criticism"  # Original review remains intact.


def test_unanimous_support_cannot_validate_an_invented_quote():
    finding, budget, _ = scenario(["SUPPORTED"], quote="Invented quotation", counter_quote="")
    assert finding.evidence_status == "REJECTED" and finding.conflict
    assert finding.verification_status == "UNRESOLVED" and budget.calls == 1


def test_verification_is_bounded_and_an_unresolved_claim_is_visible():
    finding, budget, _ = scenario(["UNCERTAIN", "UNCERTAIN"])
    assert budget.calls == 2 and finding.verification_status == "UNRESOLVED"
    assert finding.uncertainty == "HIGH"


def test_invented_reviewer_counterquotes_cannot_be_treated_as_reliable_confirmation():
    finding, budget, _ = scenario(["SUPPORTED", "SUPPORTED"])
    assert finding.conflict and finding.verification_status == "UNRESOLVED"
    assert budget.calls == 2
