"""Service-level review guards, evidence invalidation and report regeneration."""

import asyncio
from datetime import timedelta
from uuid import uuid4

import pytest
from app.llm.errors import LLMError
from app.schemas.domain import Finding, HumanReview, ModelReview, RunRecord, now

from tests.fixtures.providers import runtime


@pytest.fixture
def review_context(tmp_path):
    app = runtime(tmp_path)
    run = RunRecord(
        mode="D",
        document_id="synthetic-demo",
        criteria=["Methodik"],
        status="WAITING_FOR_REVIEW",
        findings_count=1,
    )
    finding = Finding(
        run_id=run.run_id,
        agent_id="synthetic-agent",
        model_id="qwen",
        model="qwen3:8b",
        manufacturer="Alibaba",
        category="methodology",
        kind="STRENGTH",
        statement="Original synthetic finding",
        rationale="Synthetic rationale",
        page=2,
        quote="Synthetic source quotation",
        evidence_status="VALIDATED",
        review_status="REVIEWED",
        reviews=[
            ModelReview(
                verdict="SUPPORTED",
                rationale="Synthetic model review",
                model_id="mistral",
                manufacturer="Mistral AI",
            )
        ],
    )
    app.runs[run.run_id], app.findings[run.run_id] = run, [finding]
    app.access.create(run.run_id)
    try:
        yield app, run, finding
    finally:
        asyncio.run(app.close())


@pytest.mark.parametrize("state", ["QUEUED", "RUNNING", "FAILED", "CANCELLED"])
def test_review_rejects_non_reviewable_states_without_content_changes(review_context, state):
    app, run, finding = review_context
    run.status = state
    before_run = run.model_dump(exclude={"runtime_seconds"})
    before_finding = finding.model_dump()
    with pytest.raises(LLMError) as error:
        app.human_review(
            run.run_id,
            finding.finding_id,
            HumanReview(decision="ACCEPTED", edited_statement="Forbidden edit"),
        )
    assert error.value.status_code == 409
    assert finding.model_dump() == before_finding
    assert run.model_dump(exclude={"runtime_seconds"}) == before_run


@pytest.mark.parametrize("corruption", ["missing_bucket", "mismatched_run"])
def test_review_does_not_trust_finding_bucket_alone(review_context, corruption):
    app, run, finding = review_context
    if corruption == "missing_bucket":
        app.findings.pop(run.run_id)
    else:
        finding.run_id = str(uuid4())
    before = finding.model_dump()
    with pytest.raises(LLMError) as error:
        app.human_review(run.run_id, finding.finding_id, HumanReview(decision="ACCEPTED"))
    assert error.value.status_code == 404
    assert finding.model_dump() == before
    assert run.status == "WAITING_FOR_REVIEW" and run.final_report is None


def test_expired_review_cannot_be_reopened_through_finding_id(review_context):
    app, run, finding = review_context
    run.finished_at = now() - timedelta(seconds=app.config.limits.retention_seconds + 1)
    before = finding.model_dump()
    with pytest.raises(LLMError) as error:
        app.human_review(run.run_id, finding.finding_id, HumanReview(decision="ACCEPTED"))
    assert error.value.status_code == 404
    assert run.run_id not in app.runs and run.run_id not in app.findings
    assert finding.model_dump() == before


def test_unchanged_statement_preserves_checks_but_rejection_removes_report_content(review_context):
    app, run, finding = review_context
    original_checks = finding.model_dump(include={"reviews", "review_status", "evidence_status"})
    app.human_review(
        run.run_id,
        finding.finding_id,
        HumanReview(decision="ACCEPTED", edited_statement=finding.statement),
    )
    assert finding.statement in run.final_report
    assert (
        finding.model_dump(include={"reviews", "review_status", "evidence_status"})
        == original_checks
    )
    app.human_review(run.run_id, finding.finding_id, HumanReview(decision="REJECTED"))
    assert finding.statement not in run.final_report
    assert finding.quote not in run.final_report
    assert run.status == "COMPLETED"


def test_repeated_edits_preserve_original_and_invalidate_old_evidence(review_context):
    app, run, finding = review_context
    original, original_reviews = finding.statement, list(finding.reviews)
    for statement in ["First human correction", "Second human correction"]:
        app.human_review(
            run.run_id,
            finding.finding_id,
            HumanReview(decision="ACCEPTED", edited_statement=statement),
        )
        assert finding.original_statement == original
        assert finding.superseded_reviews == original_reviews
        assert finding.reviews == [] and finding.review_status == "PENDING"
        assert finding.evidence_status == "NOT_CHECKED" and run.validated_count == 0
        assert statement in run.final_report and original not in run.final_report
    assert "First human correction" not in run.final_report
    assert finding.quote == "Synthetic source quotation"
