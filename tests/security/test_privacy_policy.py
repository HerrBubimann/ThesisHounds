"""LOCAL_ONLY guarantees: no external provider can be reached, whatever the configuration says."""

import asyncio

import pytest
import yaml
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.model_registry import ModelDefinition, ModelRegistry
from app.llm.providers.base import Completion
from app.security.policy_engine import PolicyConfig, PolicyEngine
from pydantic import ValidationError

from tests.fixtures import CONFIG

EXTERNAL = {
    "id": "cloud",
    "name": "gpt-synthetic",
    "manufacturer": "External",
    "provider": "openai",
    "local": False,
    "capabilities": ["chat", "structured_output"],
    "context_length": 8192,
    "estimated_ram_gib": 1,
    "estimated_vram_gib": 0,
    "allowed_roles": ["orchestrator", "specialist"],
    "privacy": "CONFIDENTIAL",
}


class RecordingProvider:
    """Records whether the gateway ever dispatched a request; it must not."""

    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, *_args, **_kwargs) -> Completion:
        self.calls += 1
        return Completion(text="leak", model="gpt-synthetic", input_tokens=1, output_tokens=1)

    async def discover(self):
        return []


@pytest.mark.parametrize("classification", ["SYNTHETIC", "PUBLIC", "CONFIDENTIAL", None])
def test_gateway_never_dispatches_to_external_provider(classification) -> None:
    provider = RecordingProvider()
    gateway = LLMGateway(
        ModelRegistry([ModelDefinition.model_validate(EXTERNAL)]),
        # Even an explicitly registered external provider must stay unreachable.
        {"openai": provider, "ollama": provider},
        PolicyEngine(PolicyConfig()),
    )
    budget = CallBudget(5, 100000)
    with pytest.raises(LLMError) as error:
        asyncio.run(
            gateway.complete(
                "cloud", "specialist", classification, [{"role": "user", "content": "x"}], budget
            )
        )
    assert error.value.status_code == 403
    assert provider.calls == 0 and budget.calls == 0


def test_provider_outside_policy_allowlist_is_blocked() -> None:
    model = ModelRegistry.load(CONFIG / "models.yaml").get("qwen")
    with pytest.raises(LLMError) as error:
        PolicyEngine(PolicyConfig(allowed_providers=[])).check(model, "SYNTHETIC", "orchestrator")
    assert error.value.status_code == 403


@pytest.mark.parametrize(
    "config",
    [
        {"mode": "EXPERIMENTAL"},
        {"experimental_enabled": True},
        {"mode": "EXPERIMENTAL", "experimental_enabled": True},
    ],
)
def test_experimental_mode_cannot_be_enabled_in_process(config) -> None:
    with pytest.raises(ValueError):
        PolicyEngine(PolicyConfig(**config))


def test_policy_rejects_unknown_switches() -> None:
    with pytest.raises(ValidationError):
        PolicyConfig.model_validate({"mode": "LOCAL_ONLY", "allow_cloud": True})


def test_shipped_policy_is_local_only() -> None:
    # Guards against configuration drift in a PR: the repository default must stay LOCAL_ONLY.
    policy = PolicyConfig.model_validate(yaml.safe_load((CONFIG / "policies.yaml").read_text()))
    assert policy.mode == "LOCAL_ONLY" and not policy.experimental_enabled
    assert policy.allowed_providers == ["ollama"]
    assert policy.allowed_tools == ["document.read"]
    registry = ModelRegistry.load(CONFIG / "models.yaml")
    assert all(m.local and m.provider == "ollama" for m in registry.models.values())


@pytest.mark.parametrize("name", ["qwen3:8b:cloud", "gpt-oss:120b-cloud"])
def test_registry_rejects_cloud_tags_declared_as_local(name) -> None:
    with pytest.raises(ValidationError):
        ModelDefinition.model_validate(
            {**EXTERNAL, "provider": "ollama", "local": True, "name": name}
        )
