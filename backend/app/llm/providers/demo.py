"""Deterministic, in-process DEVELOPMENT provider. No sockets, files or telemetry."""

import json

from app.llm.errors import LLMError
from app.llm.providers.base import Completion
from app.models.schemas import LocalModel
from app.services.document_store import SYNTHETIC_PAGES


class DemoProvider:
    async def discover(self):
        return [
            LocalModel(name=name, size=1, digest="MOCK")
            for name in ("qwen3:8b", "mistral:7b", "llama3.1:8b")
        ]

    async def resources(self):
        return {"loaded_models": []}

    async def health(self):
        return True

    async def capabilities(self, name):
        return {"capabilities": ["completion"], "mocked": True}

    async def complete(self, model, messages, output_schema, max_tokens, *, unload):
        if output_schema is None:
            return Completion(text="MOCK: synthetischer Verbindungstest.", model=model.name)
        properties = output_schema["properties"]
        payload = json.loads(messages[-1]["content"])
        if "observations" in properties:
            data = {
                "observations": [
                    {
                        "criterion_id": c["id"],
                        "observation": {
                            "judgment": "MIXED",
                            "kind": "OPEN_QUESTION",
                            "description": "MOCK: Beobachtung.",
                            "rationale": "MOCK: keine fachliche Bewertung.",
                            "page": 1,
                            "quote": SYNTHETIC_PAGES[1],
                            "uncertainty": "UNKNOWN",
                        },
                    }
                    for c in payload["criteria"]
                ]
            }
        elif "tasks" in properties:
            data = {
                "tasks": [
                    {"supervisor": c, "task": "Synthetische Prüfung", "depends_on": []}
                    for c in ("content", "methodology")
                ]
            }
        elif "agents" in properties:
            data = {
                "agents": [
                    {
                        "agent_id": payload["category"] + "_demo",
                        "name": "MOCK Spezialist",
                        "description": "Synthetische Demonstration",
                        "task": "Prüfe ausschließlich das synthetische Beispieldokument.",
                        "category": payload["category"],
                        "model_id": payload["suggested_model_id"],
                        "supervisor_id": payload["supervisor_id"],
                    }
                ]
            }
        elif "findings" in properties:
            data = {
                "findings": [
                    {
                        "category": payload["category"],
                        "statement": "MOCK: synthetischer Befund.",
                        "kind": "STRENGTH",
                        "page": 1,
                        "quote": SYNTHETIC_PAGES[1],
                        "rationale": "MOCK: keine fachliche Bewertung.",
                    }
                ]
            }
        elif "verdict" in properties:
            data = {"verdict": "UNCERTAIN", "rationale": "MOCK: menschliche Prüfung erforderlich."}
        elif "summary" in properties:
            data = {"summary": "MOCK: synthetischer Entwurf, keine fachliche Bewertung."}
        elif "judgment" in properties:
            data = {
                "judgment": "MIXED",
                "kind": "OPEN_QUESTION",
                "description": "MOCK: synthetische Beobachtung.",
                "rationale": "MOCK: keine fachliche Bewertung.",
                "page": 1,
                "quote": SYNTHETIC_PAGES[1],
                "uncertainty": "UNKNOWN",
            }
        else:
            raise LLMError(403, "DEMO_SCHEMA_NOT_RELEASED")
        return Completion(
            text=json.dumps(data, ensure_ascii=False),
            model=model.name,
            input_tokens=0,
            output_tokens=0,
        )
