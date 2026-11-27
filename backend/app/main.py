import os
import ssl
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.assessments import router as assessment_router
from app.api.control import router as control_router
from app.api.routes import router
from app.config import Settings
from app.core.runtime import AnalysisRuntime
from app.llm.providers.base import LLMProvider
from app.llm.providers.demo import DemoProvider
from app.models.schemas import ErrorResponse, HealthResponse
from app.security.access_control import DEMO_PRINCIPAL, current_principal
from app.security.audit_service import disable_content_logging
from app.security.egress_policy import PinnedInferenceTransport
from app.security.production_readiness import readiness_status
from app.security.request_limits import RequestBodyLimitMiddleware
from app.services.llm_service import LLMError, LLMService


def create_provider(config: Settings, client: httpx.AsyncClient) -> LLMProvider:
    # Only supported mode is DEVELOPMENT. No env/UI switch selects a network model.
    return DemoProvider()


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    # Pin these before runtime/provider creation; ambient env cannot re-enable exporters.
    for name in ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2", "HF_HUB_ENABLE_HF_TRANSFER"):
        os.environ[name] = "false"
    for name in (
        "OTEL_SDK_DISABLED",
        "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE",
        "HF_HUB_DISABLE_TELEMETRY",
        "DO_NOT_TRACK",
    ):
        os.environ[name] = "1" if name != "OTEL_SDK_DISABLED" else "true"
    disable_content_logging()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        tls = ssl.create_default_context(
            cafile=str(config.ollama_ca_file) if config.ollama_ca_file else None
        )
        headers = (
            {"Authorization": f"Bearer {config.ollama_auth_token.get_secret_value()}"}
            if config.ollama_auth_token
            else {}
        )
        async with httpx.AsyncClient(
            base_url=str(config.ollama_base_url),
            trust_env=False,
            follow_redirects=False,
            verify=tls,
            headers=headers,
            transport=PinnedInferenceTransport(),
        ) as client:
            provider = create_provider(config, client)
            runtime = AnalysisRuntime(config, provider, mocked=isinstance(provider, DemoProvider))
            application.state.runtime = runtime
            application.state.llm_service = LLMService(config, client, runtime.gateway, provider)
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

    @application.middleware("http")
    async def privacy_boundary(request: Request, call_next):
        # Development is one synthetic session, not university authentication.
        # No identity/role/classification headers supplied by clients are trusted.
        token = current_principal.set(DEMO_PRINCIPAL)
        try:
            try:
                response = await call_next(request)
            except Exception:
                # Do not propagate raw errors to Uvicorn's exception logger.
                response = JSONResponse(status_code=500, content={"code": "INTERNAL_ERROR"})
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "no-referrer"
            return response
        finally:
            current_principal.reset(token)

    @application.get("/api/v1/security/status")
    async def security_status(request: Request):
        runtime = getattr(request.app.state, "runtime", None)
        return {
            "mode": config.security_mode.value,
            "classification_default": "RESTRICTED",
            "demo_classification": "PUBLIC",
            "sperrvermerk": "NO_REAL_DOCUMENT_INGRESS",
            "public_research": False,
            "external_models": False,
            "identity": "SYNTHETIC_DEMO_ONLY",
            "network": "HOST_ACCEPTANCE_PENDING",
            "retention_seconds": runtime.config.limits.retention_seconds if runtime else None,
            "models": [
                {
                    "id": model.id,
                    "approval": model.approval_status,
                    "classifications": model.allowed_classifications,
                }
                for model in runtime.config.models.enabled()
            ]
            if runtime
            else [],
            "inference": "IN_PROCESS_MOCK_ONLY",
            "telemetry": "DISABLED",
            **readiness_status(),
        }

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
    application.include_router(assessment_router)
    application.add_middleware(RequestBodyLimitMiddleware)
    return application


app = create_app()
