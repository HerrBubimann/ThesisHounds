from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.control import router as control_router
from app.api.routes import router
from app.config import Settings
from app.core.runtime import AnalysisRuntime
from app.llm.providers.ollama import OllamaProvider
from app.models.schemas import ErrorResponse, HealthResponse
from app.services.llm_service import LLMError, LLMService


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient(
            base_url=str(config.ollama_base_url), trust_env=False, follow_redirects=False
        ) as client:
            runtime = AnalysisRuntime(config, OllamaProvider(config, client))
            application.state.runtime = runtime
            application.state.llm_service = LLMService(config, client, runtime.gateway)
            runtime.maintain()
            try:
                yield
            finally:
                await runtime.close()

    application = FastAPI(
        title="ThesisHounds API",
        version="0.2.0",
        lifespan=lifespan,
        responses={code: {"model": ErrorResponse} for code in (422, 502, 503, 504)},
    )

    @application.exception_handler(LLMError)
    async def handle_llm_error(_request: Request, exc: LLMError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": f"HTTP_{exc.status_code}"},
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, _exc: RequestValidationError
    ) -> JSONResponse:
        # FastAPI's default includes the rejected input, which can contain confidential prompts.
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Ungültige Eingabe. Die Anfrage entspricht nicht dem API-Schema.",
                "code": "VALIDATION_ERROR",
            },
        )

    @application.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse()

    application.include_router(router)
    application.include_router(control_router)
    return application


app = create_app()
