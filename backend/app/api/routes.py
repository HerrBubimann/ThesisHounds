from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.models.schemas import ChatRequest, ChatResponse, ModelsResponse, StatusResponse
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api/v1")


def get_llm_service(request: Request) -> LLMService:
    return request.app.state.llm_service


LLMDependency = Annotated[LLMService, Depends(get_llm_service)]


@router.get("/status", response_model=StatusResponse)
async def status(service: LLMDependency) -> StatusResponse:
    return await service.status()


@router.get("/models", response_model=ModelsResponse)
async def models(service: LLMDependency) -> ModelsResponse:
    return ModelsResponse(models=await service.list_models())


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, service: LLMDependency) -> ChatResponse:
    return await service.chat(payload.prompt)
