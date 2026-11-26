"""Explicit projections prevent independent review contents leaking through status APIs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.assessments.schemas import (
    AssessmentRequest,
    CriterionDecision,
    DiscussionRequest,
    ExplicitRelease,
    HumanReviewSubmission,
)
from app.workflows.assessment_workflow import AssessmentWorkflow

router = APIRouter(prefix="/api/v1/assessments", tags=["Synthetic assessment MVP"])


def get_assessments(request: Request) -> AssessmentWorkflow:
    return request.app.state.runtime.assessments


Dependency = Annotated[AssessmentWorkflow, Depends(get_assessments)]


@router.get("/profiles")
async def profiles(service: Dependency):
    return [p.model_dump() for p in service.profiles.profiles.values()]


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


@router.post("/{assessment_id}/discussion")
async def discussion(assessment_id: UUID, payload: DiscussionRequest, service: Dependency):
    return await service.discuss(str(assessment_id), payload)


@router.post("/{assessment_id}/decisions")
async def decide(assessment_id: UUID, payload: CriterionDecision, service: Dependency):
    return service.decide(str(assessment_id), payload)


@router.get("/{assessment_id}/draft")
async def draft(assessment_id: UUID, service: Dependency):
    return service.draft(str(assessment_id))


@router.post("/{assessment_id}/finalize")
async def finalize(assessment_id: UUID, payload: ExplicitRelease, service: Dependency):
    return service.finalize(str(assessment_id))


@router.post("/{assessment_id}/cancel")
async def cancel(assessment_id: UUID, service: Dependency):
    return await service.cancel(str(assessment_id))
