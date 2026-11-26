import pytest
from app.core.configuration import RuntimeConfig
from app.core.task_planner import TaskPlanner
from app.llm.errors import LLMError
from app.schemas.domain import ExecutionPlan, Finding, ModelReview
from app.services.document_store import SYNTHETIC_PAGES, Document
from app.validation.conflict_resolver import ConflictResolver
from app.validation.evidence_validator import EvidenceValidator

from tests.fixtures import CONFIG


def finding(**changes):
    data = dict(
        run_id="r",
        agent_id="a",
        model_id="qwen",
        model="qwen3:8b",
        manufacturer="Alibaba",
        category="methodology",
        statement="Begrenzte Übertragbarkeit",
        kind="CRITICISM",
        page=2,
        quote="Die geringe Stichprobe begrenzt die Übertragbarkeit der Ergebnisse.",
        rationale="Kleine Stichprobe",
    )
    return Finding(**{**data, **changes})


def test_exact_evidence_and_absence_are_separate():
    document = Document(document_id="d", pages=SYNTHETIC_PAGES, complete=True)
    validator = EvidenceValidator()
    good = finding()
    validator.validate(good, document)
    assert good.evidence_status == "VALIDATED"
    invented = finding(quote="ERFUNDEN")
    validator.validate(invented, document)
    assert invented.evidence_status == "REJECTED"
    missing = finding(claim_type="ABSENCE", required_context=[2])
    validator.validate(missing, document)
    assert missing.evidence_status == "CONTEXT_REQUIRED"
    missing.required_context = [1, 2, 3]
    validator.validate(missing, document)
    assert missing.evidence_status == "NOT_CHECKED"


def test_disagreement_preserves_both_findings():
    first, second = finding(), finding(kind="STRENGTH")
    assert ConflictResolver().detect([first, second]) == 2
    assert first.conflict and second.conflict
    first.reviews.append(
        ModelReview(
            model_id="llama", manufacturer="Meta", verdict="UNSUPPORTED", rationale="Kontext fehlt"
        )
    )
    assert ConflictResolver().detect([first]) == 1


def test_task_dependency_order_and_cycles():
    planner = TaskPlanner(RuntimeConfig(CONFIG))
    plan = ExecutionPlan.model_validate(
        {
            "tasks": [
                {"supervisor": "content", "task": "a", "depends_on": []},
                {"supervisor": "methodology", "task": "b", "depends_on": ["content"]},
            ]
        }
    )
    assert [[t.supervisor for t in level] for level in planner.validate(plan)] == [
        ["content"],
        ["methodology"],
    ]
    plan.tasks[0].depends_on = ["methodology"]
    with pytest.raises(LLMError):
        planner.validate(plan)
