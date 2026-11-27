"""Explicit projections prevent independent review contents leaking through status APIs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.assessments.schemas import (
    AcademicDecision,
    AssessmentRequest,
    CriterionDecision,
    DiscussionRequest,
    DocumentSecurityDecision,
    ExplicitRelease,
    FindingFeedback,
    HumanReviewSubmission,
)
from app.llm.errors import LLMError
from app.services.document_store import pilot_documents
from app.workflows.assessment_workflow import AssessmentWorkflow

router = APIRouter(prefix="/api/v1/assessments", tags=["Synthetic assessment MVP"])


def get_assessments(request: Request) -> AssessmentWorkflow:
    return request.app.state.runtime.assessments


Dependency = Annotated[AssessmentWorkflow, Depends(get_assessments)]


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


@router.get("/{assessment_id}/academic-checks")
async def academic_checks(assessment_id: UUID, service: Dependency):
    return service.academic_checks(str(assessment_id))


@router.post("/{assessment_id}/academic-decisions")
async def academic_decide(assessment_id: UUID, payload: AcademicDecision, service: Dependency):
    return service.academic_decide(str(assessment_id), payload)


@router.post("/{assessment_id}/human-review")
async def human_review(assessment_id: UUID, payload: HumanReviewSubmission, service: Dependency):
    return service.submit_human(str(assessment_id), payload)


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
