import asyncio
from unittest.mock import AsyncMock

import pytest
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.model_registry import ModelRegistry
from app.security.policy_engine import PolicyConfig, PolicyEngine

from tests.fixtures import CONFIG


@pytest.mark.parametrize(
    "provider",
    [
        "openai",
        "anthropic",
        "gemini",
        "azure",
        "huggingface",
        "openrouter",
        "external_ollama",
    ],
)
@pytest.mark.parametrize("level", ["INTERNAL", "CONFIDENTIAL", "RESTRICTED", None])
def test_no_external_provider_receives_nonpublic_content(provider, level):
    model = (
        ModelRegistry.load(CONFIG / "models.yaml")
        .get("qwen")
        .model_copy(
            update={
                "provider": provider,
                "local": False,
            }
        )
    )
    sink = AsyncMock()
    gateway = LLMGateway(ModelRegistry([model]), {provider: sink}, PolicyEngine(PolicyConfig()))
    with pytest.raises(LLMError):
        asyncio.run(
            gateway.complete(
                model.id,
                "specialist",
                level,
                [{"role": "user", "content": "SYNTHETIC_SECRET_CANARY_72B9"}],
                CallBudget(1, 10000),
            )
        )
    sink.complete.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"deployment_type": "EXTERNAL"},
        {"approved_endpoint": "https://external.invalid"},
        {"approved_endpoint": "http://ollama:443"},
        {"data_processing_location": "UNKNOWN"},
        {"telemetry_enabled": True},
        {"cloud_features_enabled": True},
        {"security_review_status": "UNREVIEWED"},
        {"approval_status": "UNAPPROVED"},
        {"network_access": "EXTERNAL"},
        {"allowed_classifications": []},
    ],
)
def test_claiming_local_is_insufficient(changes):
    model = ModelRegistry.load(CONFIG / "models.yaml").get("qwen").model_copy(update=changes)
    with pytest.raises(LLMError):
        PolicyEngine(PolicyConfig()).check(model, "PUBLIC", "specialist")


def test_local_failure_and_policy_outage_never_dispatch_to_another_provider():
    async def scenario():
        local, external = AsyncMock(), AsyncMock()
        local.complete.side_effect = LLMError(503, "LOCAL_UNAVAILABLE")
        gateway = LLMGateway(
            ModelRegistry.load(CONFIG / "models.yaml"),
            {"ollama": local, "openai": external},
            PolicyEngine(PolicyConfig()),
        )
        with pytest.raises(LLMError):
            await gateway.complete("qwen", "specialist", "PUBLIC", [], CallBudget(1, 10000))
        assert local.complete.call_count == 1
        external.complete.assert_not_called()
        gateway.policy = None
        with pytest.raises(AttributeError):
            await gateway.complete("qwen", "specialist", "PUBLIC", [], CallBudget(1, 10000))
        assert local.complete.call_count == 1
        external.complete.assert_not_called()

    asyncio.run(scenario())
