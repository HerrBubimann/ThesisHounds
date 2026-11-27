"""Synthetic assessment responses, not claims about real model quality."""

import asyncio
import json

from app.llm.providers.base import Completion
from app.services.document_store import SYNTHETIC_PAGES

from tests.fixtures.providers import WorkflowProvider


class AssessmentProvider(WorkflowProvider):
    def __init__(self, *, fail=False, delay=0):
        super().__init__()
        self.contexts, self.fail, self.delay = [], fail, delay

    async def complete(self, model, messages, output_schema, max_tokens, *, unload):
        self.contexts.append(messages)
        await asyncio.sleep(self.delay)
        if self.fail:
            return Completion(text='{"points": 100}', model=model.name)
        if "understanding" in output_schema["properties"]:
            data = {
                "understanding": {},
                "agents": [],
                "rationale": "MOCK: No semantic method inference.",
            }
        elif "verdict" in output_schema["properties"]:
            data = {"verdict": "SUPPORTED", "rationale": "MOCK: synthetic verification only."}
        elif "answer" in output_schema["properties"]:
            data = {"answer": "MOCK: Die Belege sind begrenzt; Gegenargumente sind zu prüfen."}
        else:
            data = {
                "judgment": "MIXED",
                "kind": "OPEN_QUESTION",
                "description": "AI_EMBARGO_MARKER",
                "rationale": "MOCK-Begründung",
                "page": 2,
                "quote": SYNTHETIC_PAGES[2],
                "uncertainty": "HIGH",
            }
        return Completion(
            text=json.dumps(data), model=model.name, input_tokens=100, output_tokens=50
        )


def human_submission():
    return {
        "release": True,
        "criteria": [
            {
                "criterion_id": key,
                "judgment": "MIXED",
                "observations": "HUMAN_PRIVATE_MARKER",
                "rationale": "Unabhängige menschliche Begründung",
            }
            for key in ["literature", "methodology", "structure"]
        ],
    }
