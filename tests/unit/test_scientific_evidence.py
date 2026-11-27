from app.assessments.coverage import check_coverage
from app.assessments.profile_registry import ProfileRegistry
from app.assessments.schemas import AssessmentFinding
from app.services.document_intelligence import structure_document
from app.services.document_store import Document
from app.validation.evidence_validator import check_evidence

from tests.fixtures import CONFIG


def finding(criterion, **changes):
    return AssessmentFinding(
        assessment_id="synthetic",
        criterion_id=criterion,
        category="methodology",
        model_id="qwen",
        manufacturer="Alibaba",
        agent_id="synthetic",
        judgment="MIXED",
        kind="OPEN_QUESTION",
        description="Synthetic observation",
        rationale="Synthetic rationale",
        **changes,
    )


def test_coverage_counts_not_assessable_without_claiming_correctness():
    profile = ProfileRegistry(CONFIG / "assessment_profiles").get("pa1-example", "PA1")
    values = [finding(c.id) for c in profile.criteria]
    values[0].judgment = "NOT_ASSESSABLE"
    result = check_coverage(profile, values)
    assert result.complete and result.not_assessable == ("literature",)
    assert check_coverage(profile, values[:-1]).missing == ("structure",)
    assert not check_coverage(profile, values + [values[0]]).complete
    assert check_coverage(profile, values + [finding("foreign")]).unexpected == ("foreign",)


def test_structure_spans_and_cross_chapter_links_are_exact():
    document = Document(
        document_id="synthetic",
        analysis_id="scope",
        pages={
            1: "1 Forschungsfrage\n\nWelche Wirkung hat ein System?",
            2: "2 Methodik\n\nSechs synthetische Fälle.",
            3: "3 Fazit\n\nEine Wirkung ist nicht nachgewiesen.",
        },
    )
    structure = structure_document(document)
    assert structure.classification == "RESTRICTED" and structure.analysis_id == "scope"
    for block in structure.blocks:
        assert document.pages[block.page][block.start : block.end] == block.text
    link = structure.related("Forschungsfrage", "Fazit")
    assert link["first"] and link["second"] and not link["semantic_relation_verified"]
    assert structure.locate(2, "ERFUNDENE TEXTSTELLE") is None


def test_complex_objects_are_marked_as_unverified_text_extraction():
    document = Document(
        document_id="synthetic",
        pages={
            1: "Tabelle 1: Werte\n\nAbbildung 1: Diagramm\n\n"
            "```python\nprint('synthetic')\n```\n\n$x=2$"
        },
    )
    structure = structure_document(document)
    assert {b.kind for b in structure.blocks} == {"TABLE", "FIGURE", "CODE", "FORMULA"}
    assert all(not b.reliable for b in structure.blocks) and structure.warnings


def test_absence_is_never_proved_by_a_quote_or_an_incomplete_context():
    document = Document(
        document_id="synthetic", pages={1: "Original text", 2: "Full context"}, complete=True
    )
    assert (
        check_evidence(
            document, 1, "Original text", claim_type="ABSENCE", required_context=[1]
        ).status
        == "CONTEXT_REQUIRED"
    )
    assert (
        check_evidence(
            document, 1, "Original text", claim_type="ABSENCE", required_context=[1, 2]
        ).status
        == "ABSENCE_UNPROVEN"
    )
    assert check_evidence(document, 2, "Original text").status == "REJECTED"
    assert check_evidence(document, 1, "Original text").start == 0
