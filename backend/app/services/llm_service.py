"""Backward-compatible single-model facade over the policy-controlled LLM gateway."""

import httpx

from app.config import Settings
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.model_registry import ModelRegistry
from app.llm.providers.ollama import OllamaProvider
from app.models.schemas import ChatResponse, LocalModel, StatusResponse
from app.security.policy_engine import PolicyConfig, PolicyEngine

__all__ = ["LLMError", "LLMService"]


class LLMService:
    def __init__(
        self,
        settings: Settings,
        client: httpx.AsyncClient,
        gateway: LLMGateway | None = None,
    ) -> None:
        self.settings = settings
        self.provider = OllamaProvider(settings, client)
        self.gateway = gateway or LLMGateway(
            ModelRegistry.load(settings.config_dir / "models.yaml"),
            {"ollama": self.provider},
            PolicyEngine(PolicyConfig()),
        )

    async def list_models(self) -> list[LocalModel]:
        return await self.provider.discover()

    async def status(self) -> StatusResponse:
        try:
            models = await self.list_models()
        except LLMError as exc:
            return StatusResponse(
                ollama="unavailable",
                model=self.settings.llm_model,
                model_available=False,
                detail=exc.detail,
            )
        available = any(model.name == self.settings.llm_model for model in models)
        return StatusResponse(
            ollama="available",
            model=self.settings.llm_model,
            model_available=available,
            detail="Bereit für Testanfragen."
            if available
            else "Modell fehlt. Bitte Bereitstellung ausführen.",
        )

    async def chat(self, prompt: str) -> ChatResponse:
        model = next(
            (m for m in self.gateway.registry.enabled() if m.name == self.settings.llm_model), None
        )
        if model is None:
            raise LLMError(503, "Standardmodell ist in der Model Registry nicht freigegeben.")
        response, _ = await self.gateway.complete(
            model.id,
            "specialist",
            "CONFIDENTIAL",
            [{"role": "user", "content": prompt}],
            CallBudget(1, 100000),
            max_tokens=self.settings.llm_max_tokens,
        )
        return ChatResponse(model=response.model, answer=response.text)
