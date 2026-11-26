"""Explicitly mocked LLM provider for workflow tests; never used by the production runtime."""

import asyncio
import json

from app.config import Settings
from app.core.runtime import AnalysisRuntime
from app.llm.errors import LLMError
from app.llm.providers.base import Completion
from app.models.schemas import LocalModel
from app.services.document_store import SYNTHETIC_PAGES

from tests.fixtures import CONFIG


class WorkflowProvider:
    """Explicitly mocked LLM, never used by the production runtime."""

    def __init__(self, *, disagree=False, delay=0, missing=()):
        self.disagree, self.delay, self.missing = disagree, delay, set(missing)
        self.calls = []
        self.active = self.maximum_active = 0

    async def discover(self):
        return [
            LocalModel(name=name, size=1, digest="MOCK")
            for name in ["qwen3:8b", "mistral:7b", "llama3.1:8b"]
            if name not in self.missing
        ]

    async def resources(self):
        return {"loaded_models": []}

    async def complete(self, model, messages, output_schema, max_tokens, *, unload):
        if model.name in self.missing:
            raise LLMError(503, "Modell fehlt.")
        self.active += 1
        self.maximum_active = max(self.active, self.maximum_active)
        try:
            self.calls.append(model.id)
            await asyncio.sleep(self.delay)
            purpose = messages[0]["content"].split("task: ")[1].split(".")[0]
            payload = json.loads(messages[1]["content"])
            if purpose == "plan":
                data = {
                    "tasks": [
                        {"supervisor": category, "task": f"Prüfe {category}", "depends_on": []}
                        for category in ["content", "methodology"]
                    ]
                }
            elif purpose == "delegate":
                data = {
                    "agents": [
                        {
                            "agent_id": f"{payload['category']}_leaf",
                            "name": "Synthetic specialist",
                            "description": "Synthetische Analyse",
                            "role": "specialist",
                            "task": payload["task"],
                            "category": payload["category"],
                            "model_id": payload["suggested_model_id"],
                            "supervisor_id": payload["supervisor_id"],
                            "allowed_tools": ["document.read"],
                            "input_schema": "document.v1",
                            "output_schema": "findings.v1",
                            "max_iterations": 1,
                            "max_runtime_seconds": 300,
                            "max_delegation_depth": 2,
                            "can_delegate": False,
                        }
                    ]
                }
            elif purpose == "analyze":
                from app.services.document_store import DocumentInput

                assert (
                    DocumentInput.model_validate(payload["input"]).document.classification
                    == "SYNTHETIC"
                )
                category = payload["category"]
                page = 2 if category == "methodology" else 1
                data = {
                    "findings": [
                        {
                            "category": category,
                            "statement": "Synthetischer Testbefund",
                            "kind": "CRITICISM" if page == 2 else "STRENGTH",
                            "page": page,
                            "quote": SYNTHETIC_PAGES[page],
                            "rationale": "Synthetischer Beleg",
                            "claim_type": "TEXT",
                            "required_context": [],
                        }
                    ]
                }
            elif purpose == "review":
                data = {
                    "verdict": "UNSUPPORTED"
                    if self.disagree and model.id == "qwen"
                    else "SUPPORTED",
                    "rationale": "Mock-Review",
                    "missing_context": False,
                    "possible_hallucination": False,
                }
            elif purpose == "synthesize":
                data = {"summary": "MOCK-Entwurf; keine reale Modellbewertung."}
            else:
                raise AssertionError(purpose)
            return Completion(
                text=json.dumps(data, ensure_ascii=False),
                model=model.name,
                input_tokens=100,
                output_tokens=50,
            )
        finally:
            self.active -= 1


def runtime(tmp_path, **provider_options):
    return AnalysisRuntime(
        Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path / "docs"),
        WorkflowProvider(**provider_options),
        mocked=True,
    )
