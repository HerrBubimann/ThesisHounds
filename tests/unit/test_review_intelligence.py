import asyncio
import json

import pytest
from app.assessments.adversarial_verification import ground_finding
from app.assessments.ai_review import AISecondReviewer
from app.assessments.escalation import plan_escalation
from app.assessments.profile_registry import ProfileRegistry
from app.assessments.schemas import AssessmentFinding, EvidencePassage, ScientificRelationship
from app.assessments.scientific_consistency import consistency_map, update_evidence
from app.core.configuration import RuntimeConfig
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.providers.base import Completion
from app.services.document_intelligence import structure_document
from app.services.document_store import SYNTHETIC_PAGES, Document

from tests.fixtures import CONFIG
from tests.fixtures.assessments import AssessmentProvider


def evidence_fixture(**updates):
    doc = Document(
        document_id="synthetic",
        analysis_id="scope",
        classification="PUBLIC",
        pages={
            1: "Forschungsfrage: Verbessert X die Wirkung?",
            2: "Methodik: Nur sechs Fälle.",
            3: "Fazit: Keine nachgewiesene Wirkung.",
        },
        complete=True,
    )
    value = dict(
        assessment_id="scope",
        criterion_id="methodology",
        category="methodology",
        model_id="qwen",
        manufacturer="Alibaba",
        agent_id="test",
        judgment="POSITIVE",
        kind="STRENGTH",
        description="Synthetic proposal",
        rationale="Synthetic rationale",
        page=1,
        quote=doc.pages[1],
        data_classification="PUBLIC",
    )
    return doc, AssessmentFinding(**(value | updates))


@pytest.mark.parametrize(
    "expected,updates",
    [
        ("DIRECT_EVIDENCE", {}),
        (
            "MULTIPLE_EVIDENCE",
            {"supporting_passages": [EvidencePassage(page=2, quote="Methodik: Nur sechs Fälle.")]},
        ),
        ("INSUFFICIENT", {"quote": "Invented"}),
        ("NOT_ASSESSABLE", {"judgment": "NOT_ASSESSABLE"}),
        (
            "CONTRADICTORY",
            {
                "conflict": True,
                "verification_rounds": [
                    {
                        "round": 1,
                        "verdict": "UNSUPPORTED",
                        "counter_page": 3,
                        "counter_quote": "Fazit: Keine nachgewiesene Wirkung.",
                    }
                ],
            },
        ),
        ("INSUFFICIENT", {"conflict": True}),
    ],
)
def test_evidence_state_requires_grounding_and_never_equates_uncertainty_with_counterevidence(
    expected, updates
):
    doc, finding = evidence_fixture(**updates)
    ground_finding(finding, doc, structure_document(doc))
    update_evidence(finding, doc)
    assert finding.evidence_quality == expected
    assert finding.description == "Synthetic proposal"


def test_relationships_need_two_distinct_real_spans_and_remain_proposals():
    doc, finding = evidence_fixture()
    relation = ScientificRelationship(
        source="QUESTION",
        target="CONCLUSION",
        relation="POSSIBLE_CONTRADICTION",
        rationale="Synthetic possible inconsistency",
        passages=[
            EvidencePassage(page=1, quote=doc.pages[1]),
            EvidencePassage(page=3, quote=doc.pages[3]),
        ],
    )
    finding.relationships = [relation]
    ground_finding(finding, doc, structure_document(doc))
    update_evidence(finding, doc)
    assert finding.evidence_quality == "INFERRED"
    assert finding.relationship_checks[0]["status"] == "GROUNDED_PROPOSAL"
    assert not finding.relationship_checks[0]["automatic_criticism"]
    finding.relationships = [
        relation.model_copy(update={"passages": [EvidencePassage(page=1, quote=doc.pages[1])] * 2})
    ]
    update_evidence(finding, doc)
    assert finding.evidence_quality == "INSUFFICIENT"
    mapping = consistency_map(doc, structure_document(doc))
    assert {"HYPOTHESIS", "SOURCE", "DATASET", "EXPERIMENT"} <= {
        node["aspect"] for node in mapping["nodes"]
    }
    assert not mapping["absence_proven"]


def test_quote_outside_selected_context_and_private_derivatives_stay_insufficient_and_private():
    doc, finding = evidence_fixture(
        data_classification="RESTRICTED", context_trace={"selection": []}
    )
    ground_finding(finding, doc, structure_document(doc))
    update_evidence(finding, doc)
    assert finding.evidence_quality == "INSUFFICIENT"
    assert "QUOTE_OUTSIDE_SELECTED_CONTEXT" in finding.open_questions
    assert all(p["classification"] == "RESTRICTED" for p in finding.supporting_evidence)


def test_escalation_uses_evidence_criticality_complexity_and_resources_not_confidence_alone():
    doc, finding = evidence_fixture()
    ground_finding(finding, doc, structure_document(doc))
    update_evidence(finding, doc)
    finding.uncertainty = "HIGH"
    assert plan_escalation(finding, complex_topic=True)["level"] == 2
    finding.kind, finding.judgment = "WEAKNESS", "NEGATIVE"
    result = plan_escalation(finding, complex_topic=True)
    assert (
        result["level"] == 3
        and result["specialist_needed"]
        and result["independent_verification_required"]
    )
    assert plan_escalation(finding, resources_available=False)["human_required"]
    finding.open_questions = ["SUPPLEMENT_FAILED_REQUIRES_HUMAN:504"]
    assert plan_escalation(finding)["level"] == 4


class ControlledProvider(AssessmentProvider):
    def __init__(self, *, failures=0, positive=False, absence=False):
        super().__init__()
        self.failures, self.positive, self.absence = failures, positive, absence

    async def complete(self, *args, **kwargs):
        if self.failures:
            self.failures -= 1
            return Completion(model=args[0].name, text='{"untrusted": "SYNTHETIC_PRIVATE_ERROR"}')
        result = await super().complete(*args, **kwargs)
        data = json.loads(result.text)
        if "judgment" in data:
            if self.positive:
                data.update(judgment="POSITIVE", kind="STRENGTH")
                pages = json.loads(args[1][-1]["content"])["untrusted_pages"]
                page = next(iter(pages))
                data.update(page=int(page), quote=pages[page].split("\n…\n")[0])
            if self.absence:
                data.update(claim_type="ABSENCE", required_context=[1])
        return result.model_copy(update={"text": json.dumps(data)})


def run_review(provider, **options):
    config = RuntimeConfig(CONFIG)
    gateway = LLMGateway(config.models, {"ollama": provider}, config.policy)
    doc = Document(
        document_id="synthetic",
        analysis_id="scope",
        classification="PUBLIC",
        pages=dict(SYNTHETIC_PAGES),
        complete=True,
    )
    budget = options.pop("budget", CallBudget(32, 100000))
    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    return asyncio.run(
        AISecondReviewer(gateway, config).review("scope", doc, profile, budget, **options)
    ), budget


def test_positive_grounded_review_uses_lower_stage_without_gratuitous_topic_agents():
    findings, budget = run_review(ControlledProvider(positive=True))
    assert len(findings) == 3 and budget.calls == 3
    assert all(f.escalation["level"] == 2 and not f.supplemental for f in findings)


def test_transient_invalid_output_is_retried_locally_and_usage_is_recorded():
    findings, budget = run_review(ControlledProvider(failures=1, positive=True))
    assert budget.calls == 4 and findings[0].performance["retries"] == 1
    assert findings[0].performance["model_calls"] == 2
    assert "SYNTHETIC_PRIVATE_ERROR" not in str(findings)


def test_exhausted_or_invalid_mandatory_analysis_never_returns_success():
    with pytest.raises(LLMError):
        run_review(ControlledProvider(failures=99))
    with pytest.raises(LLMError):
        run_review(ControlledProvider(positive=True), budget=CallBudget(1, 100000))


def test_absence_expands_search_and_stays_a_human_question():
    findings, _ = run_review(ControlledProvider(absence=True), architecture="B")
    assert all(f.context_trace["expanded_search_candidates"] >= 3 for f in findings)
    assert all(
        not f.context_trace["absence_proven"] and f.escalation["human_required"] for f in findings
    )


def test_empty_context_is_explicitly_not_assessable_without_wasting_a_model_call():
    config = RuntimeConfig(CONFIG)
    provider = ControlledProvider()
    gateway = LLMGateway(config.models, {"ollama": provider}, config.policy)
    document = Document(
        document_id="synthetic", analysis_id="scope", classification="PUBLIC", pages={}
    )
    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    budget = CallBudget(32, 100000)
    findings = asyncio.run(
        AISecondReviewer(gateway, config).review(
            "scope", document, profile, budget, architecture="B"
        )
    )
    assert budget.calls == 0 and not provider.contexts
    assert len(findings) == 3 and all(
        f.judgment == "NOT_ASSESSABLE" and f.escalation["human_required"] for f in findings
    )


def test_failed_optional_agent_keeps_mandatory_results_and_human_escalation():
    class FailedSupplement(ControlledProvider):
        async def complete(self, *args, **kwargs):
            if json.loads(args[1][-1]["content"]).get("supplemental_focus"):
                return Completion(model=args[0].name, text="INVALID_SYNTHETIC_JSON")
            return await super().complete(*args, **kwargs)

    findings, budget = run_review(FailedSupplement(), planning_mode="regex_baseline")
    assert len(findings) == 3
    method = next(f for f in findings if f.criterion_id == "methodology")
    assert not method.supplemental and method.escalation["human_required"]
    assert any("SUPPLEMENT_FAILED_REQUIRES_HUMAN" in q for q in method.open_questions)
    assert budget.calls <= 10


def test_subagent_limit_is_explicit_and_does_not_drop_mandatory_criteria():
    config = RuntimeConfig(CONFIG)
    config.limits = config.limits.model_copy(update={"max_dynamic_agents": 1})
    provider = ControlledProvider()
    gateway = LLMGateway(config.models, {"ollama": provider}, config.policy)
    pages = dict(SYNTHETIC_PAGES)
    pages[2] += " Zusätzlich Interviews und qualitative Kodierung."
    document = Document(
        document_id="synthetic", analysis_id="scope", classification="PUBLIC", pages=pages
    )
    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    findings = asyncio.run(
        AISecondReviewer(gateway, config).review(
            "scope", document, profile, CallBudget(32, 100000), planning_mode="regex_baseline"
        )
    )
    assert len(findings) == 3 and sum(len(f.supplemental) for f in findings) == 1
    assert any(
        "SUPPLEMENT_FAILED_REQUIRES_HUMAN:429" in q for f in findings for q in f.open_questions
    )


def test_criterion_metrics_reconcile_mandatory_supplement_and_verification_calls():
    findings, budget = run_review(ControlledProvider())
    assert sum(f.performance["criterion_model_calls"] for f in findings) == budget.calls
    assert all(
        f.performance["criterion_active_seconds"] >= f.performance["duration_seconds"]
        for f in findings
    )
    assert all(r["duration_seconds"] >= 0 for f in findings for r in f.verification_rounds)


def test_single_batch_does_not_fabricate_individual_criterion_costs():
    from app.llm.providers.demo import DemoProvider

    findings, budget = run_review(DemoProvider(), architecture="A")
    assert budget.calls == 1
    assert all(
        f.performance["shared_batch"] and f.performance["batch_model_calls"] == 1 for f in findings
    )
    assert all(f.performance["criterion_model_calls"] is None for f in findings)


def test_unverified_visual_extraction_is_not_direct_academic_evidence():
    doc, finding = evidence_fixture(quote="Tabelle 1: Nur synthetische Textwerte.")
    doc = doc.model_copy(update={"pages": {1: finding.quote}})
    ground_finding(finding, doc, structure_document(doc))
    update_evidence(finding, doc)
    assert finding.evidence_status == "QUOTE_MATCHED" and finding.evidence_quality == "INSUFFICIENT"
    assert plan_escalation(finding)["human_required"]


@pytest.mark.parametrize("resource_failure", [False, True])
def test_real_provider_adapter_records_load_and_optional_vram_snapshot_with_mock_http(
    resource_failure,
):
    import httpx
    from app.config import Settings
    from app.llm.providers.ollama import OllamaProvider

    async def scenario():
        config = RuntimeConfig(CONFIG)
        config.limits = config.limits.model_copy(update={"capture_inference_resources": True})
        names = [m.name for m in config.models.enabled()]

        def handler(request):
            if request.url.path == "/api/tags":
                return httpx.Response(
                    200, json={"models": [{"name": n, "size": 1, "digest": "MOCK"} for n in names]}
                )
            if request.url.path == "/api/ps":
                return httpx.Response(
                    503 if resource_failure else 200,
                    json={"models": [{"name": n, "size": 64, "size_vram": 32} for n in names]},
                )
            data = json.loads(request.content)
            pages = json.loads(data["messages"][-1]["content"])["untrusted_pages"]
            page = next(iter(pages))
            observation = {
                "judgment": "POSITIVE",
                "kind": "STRENGTH",
                "description": "Synthetic",
                "rationale": "Synthetic",
                "page": int(page),
                "quote": pages[page].split("\n…\n")[0],
            }
            return httpx.Response(
                200,
                json={
                    "done": True,
                    "model": data["model"],
                    "message": {"content": json.dumps(observation)},
                    "load_duration": 1_500_000_000,
                },
            )

        settings = Settings(_env_file=None, ollama_base_url="http://ollama:11434")
        async with httpx.AsyncClient(
            base_url=str(settings.ollama_base_url), transport=httpx.MockTransport(handler)
        ) as client:
            provider = OllamaProvider(settings, client)
            gateway = LLMGateway(config.models, {"ollama": provider}, config.policy)
            document = Document(
                document_id="synthetic",
                analysis_id="scope",
                classification="PUBLIC",
                pages=dict(SYNTHETIC_PAGES),
            )
            profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
            findings = await AISecondReviewer(gateway, config).review(
                "scope", document, profile, CallBudget(32, 100000)
            )
        for f in findings:
            assert f.performance["model_load_seconds"] == 1.5
            assert f.performance["vram_bytes"] == (None if resource_failure else 32)
            assert f.performance["inference_resource_scope"] == (
                "UNAVAILABLE"
                if resource_failure
                else "PROVIDER_POST_CALL_SNAPSHOT_NOT_PEAK_OR_PHYSICAL_RAM"
            )

    asyncio.run(scenario())
