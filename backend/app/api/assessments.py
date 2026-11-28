"""Explicit projections prevent independent review contents leaking through status APIs."""

import asyncio
import hashlib
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.assessments.human_import import extract_review
from app.assessments.schemas import (
    AcademicDecision,
    AssessmentRequest,
    CriterionDecision,
    DiscussionRequest,
    DocumentSecurityDecision,
    ExplicitRelease,
    FindingFeedback,
    HumanReviewImport,
    HumanReviewSubmission,
    MethodConfirmation,
    ReviewerNote,
    ReviewerTimeAction,
)
from app.knowledge.importer import ImportRejected
from app.llm.errors import LLMError
from app.services.document_store import checked_pilot_root, load_pilot_document, pilot_documents
from app.workflows.assessment_workflow import AssessmentWorkflow

router = APIRouter(prefix="/api/v1/assessments", tags=["Synthetic assessment MVP"])


def get_assessments(request: Request) -> AssessmentWorkflow:
    return request.app.state.runtime.assessments


Dependency = Annotated[AssessmentWorkflow, Depends(get_assessments)]


class RulesPreview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    program: Literal["data_science_ai", "wirtschaftsinformatik"]
    cohort: str = Field(pattern=r"^(DS|WI)(23|24|25)$")
    work_type: Literal["PA1", "PA2", "BA"]


@router.get("")
async def listing(service: Dependency):
    """ACL-filtered metadata only, including while independent contents are embargoed."""
    service.cleanup()
    rows = []
    fields = (
        "id",
        "state",
        "created_at",
        "updated_at",
        "work_type",
        "document_id",
        "program",
        "cohort",
        "classification",
        "human_completed",
        "ai_state",
        "ai_released",
    )
    for key in list(service.records):
        if service.access.allows(key):
            row = service.status(key, include_analysis=False)
            rows.append({name: row[name] for name in fields})
    return sorted(rows, key=lambda row: row["created_at"], reverse=True)


@router.post("/rules-preview")
async def rules_preview(payload: RulesPreview, service: Dependency):
    return service.academic.rules(payload.program, payload.cohort, payload.work_type)


@router.get("/pilot-documents")
async def registered_documents(service: Dependency):
    try:
        return {
            "documents": pilot_documents(service.settings.pilot_document_dir),
            "profile_id": service.settings.pilot_profile_id,
            "inference_mode": service.settings.inference_mode,
        }
    except (OSError, ValueError, KeyError, TypeError):
        raise LLMError(503, "PILOT_CATALOG_UNAVAILABLE_OR_CHANGED") from None


@router.get("/profiles")
async def profiles(service: Dependency):
    return [
        p.model_dump()
        for p in service.profiles.profiles.values()
        if p.data_classification == "PUBLIC" and p.status != "CANDIDATE"
    ]


@router.post("", status_code=201)
async def create(payload: AssessmentRequest, service: Dependency):
    return service.create(payload)


@router.get("/{assessment_id}")
async def status(assessment_id: UUID, service: Dependency):
    return service.status(str(assessment_id))


@router.get("/{assessment_id}/document")
async def document(assessment_id: UUID, service: Dependency):
    # Only the fixed synthetic fixture can be created by the assessment API.
    return service.get(str(assessment_id)).document.model_dump()


@router.get("/{assessment_id}/original-pdf", response_class=Response)
async def original_pdf(assessment_id: UUID, service: Dependency):
    record = service.get(str(assessment_id))
    document = record.document
    if not document.source_sha256 or not service.settings.pilot_document_dir:
        raise LLMError(404, "ORIGINAL_PDF_NOT_AVAILABLE")
    try:
        root = checked_pilot_root(service.settings.pilot_document_dir)
        verified = load_pilot_document(root, document.document_id, record.id)
        # No PDF links, scripts or other suspicious objects reach the browser renderer.
        # No client-controlled filename, URL, classification or approval is accepted.
        if verified != document or verified.security_inspection.get("indicators"):
            raise ValueError("PDF_PREVIEW_REQUIRES_TEXT_FALLBACK")
        data = (root / (verified.source_sha256 + ".pdf")).read_bytes()
        if len(data) > 8_000_000 or hashlib.sha256(data).hexdigest() != document.source_sha256:
            raise ValueError("PDF_CHANGED")
    except (OSError, ValueError, KeyError, TypeError):
        raise LLMError(403, "ORIGINAL_PDF_NOT_CLEARED_FOR_PREVIEW") from None
    return Response(
        data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="review-document.pdf"'},
    )


@router.get("/{assessment_id}/academic-checks")
async def academic_checks(assessment_id: UUID, service: Dependency):
    return service.academic_checks(str(assessment_id))


@router.post("/{assessment_id}/academic-decisions")
async def academic_decide(assessment_id: UUID, payload: AcademicDecision, service: Dependency):
    return service.academic_decide(str(assessment_id), payload)


@router.post("/{assessment_id}/human-review")
async def human_review(assessment_id: UUID, payload: HumanReviewSubmission, service: Dependency):
    return service.submit_human(str(assessment_id), payload)


@router.get("/{assessment_id}/human-review")
async def original_human_review(assessment_id: UUID, service: Dependency):
    return service.human_review(str(assessment_id))


@router.post("/{assessment_id}/human-review/start")
async def begin_human_review(assessment_id: UUID, service: Dependency):
    return service.begin_human(str(assessment_id))


@router.post("/{assessment_id}/human-review/import-preview")
async def import_human_review(assessment_id: UUID, payload: HumanReviewImport, service: Dependency):
    service.access.require(str(assessment_id), "review")
    record = service.get(str(assessment_id))
    service.writable(record)
    if record.human:
        raise LLMError(409, "INITIAL_REVIEW_ALREADY_SUBMITTED")
    binding = record.confirmed_binding
    try:
        preview = await asyncio.to_thread(
            extract_review, payload, record.profile.model_copy(deep=True)
        )
    except ImportRejected:
        raise LLMError(422, "LOCAL_REVIEW_IMPORT_REJECTED") from None
    # Extraction yields control: recheck deletion, finalization and source binding.
    if service.get(str(assessment_id)).confirmed_binding != binding:
        raise LLMError(409, "REVIEW_DOCUMENT_OR_PROFILE_CHANGED")
    return service.import_human(str(assessment_id), preview)


@router.get("/{assessment_id}/decision-ledger")
async def decision_ledger(assessment_id: UUID, service: Dependency):
    return service.decision_history(str(assessment_id))


@router.get("/{assessment_id}/human-review/import-preview")
async def human_import_preview(assessment_id: UUID, service: Dependency):
    return service.human_import_preview(str(assessment_id))


@router.delete("/{assessment_id}/human-review/import-preview")
async def discard_human_import(assessment_id: UUID, service: Dependency):
    return service.discard_human_import(str(assessment_id))


@router.post("/{assessment_id}/ai-review", status_code=202)
async def ai_review(assessment_id: UUID, service: Dependency):
    return service.start_ai(str(assessment_id))


@router.post("/{assessment_id}/release")
async def release(assessment_id: UUID, payload: ExplicitRelease, service: Dependency):
    return service.release_ai(str(assessment_id))


@router.get("/{assessment_id}/comparison")
async def comparison(assessment_id: UUID, service: Dependency):
    return service.comparison(str(assessment_id))


@router.get("/{assessment_id}/provenance")
async def provenance(assessment_id: UUID, service: Dependency):
    return service.provenance(str(assessment_id))


@router.post("/{assessment_id}/finding-feedback")
async def finding_feedback(assessment_id: UUID, payload: FindingFeedback, service: Dependency):
    return service.feedback(str(assessment_id), payload)


@router.post("/{assessment_id}/reviewer-notes")
async def reviewer_notes(assessment_id: UUID, payload: ReviewerNote, service: Dependency):
    return service.reviewer_note(str(assessment_id), payload)


@router.post("/{assessment_id}/review-methods")
async def review_methods(assessment_id: UUID, payload: MethodConfirmation, service: Dependency):
    return service.confirm_method(str(assessment_id), payload)


@router.post("/{assessment_id}/reviewer-time")
async def reviewer_time(assessment_id: UUID, payload: ReviewerTimeAction, service: Dependency):
    return service.reviewer_time(str(assessment_id), payload)


@router.get("/{assessment_id}/document-security")
async def document_security(assessment_id: UUID, service: Dependency):
    return service.security_findings(str(assessment_id))


@router.post("/{assessment_id}/document-security/review")
async def review_document_security(
    assessment_id: UUID, payload: DocumentSecurityDecision, service: Dependency
):
    return service.review_security(str(assessment_id), payload)


@router.post("/{assessment_id}/discussion")
async def discussion(assessment_id: UUID, payload: DiscussionRequest, service: Dependency):
    return await service.discuss(str(assessment_id), payload)


@router.get("/{assessment_id}/findings/{finding_id}/evidence")
async def evidence(assessment_id: UUID, finding_id: UUID, service: Dependency):
    return service.evidence(str(assessment_id), str(finding_id))


@router.post("/{assessment_id}/decisions")
async def decide(assessment_id: UUID, payload: CriterionDecision, service: Dependency):
    return service.decide(str(assessment_id), payload)


@router.post("/{assessment_id}/manual-review")
async def manual_review(assessment_id: UUID, payload: ExplicitRelease, service: Dependency):
    return service.acknowledge_manual_review(str(assessment_id))


@router.get("/{assessment_id}/draft")
async def draft(assessment_id: UUID, service: Dependency):
    return service.draft(str(assessment_id))


@router.post("/{assessment_id}/finalize")
async def finalize(assessment_id: UUID, payload: ExplicitRelease, service: Dependency):
    return service.finalize(str(assessment_id))


@router.post("/{assessment_id}/cancel")
async def cancel(assessment_id: UUID, service: Dependency):
    return await service.cancel(str(assessment_id))


@router.delete("/{assessment_id}", status_code=204)
async def delete(assessment_id: UUID, service: Dependency) -> None:
    await service.delete(str(assessment_id))
