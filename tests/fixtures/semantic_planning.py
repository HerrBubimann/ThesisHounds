"""Scripted semantic responses, never evidence of an actual model understanding text."""

import json

from app.llm.providers.base import Completion

from tests.fixtures.assessments import AssessmentProvider

NO_BUZZWORDS = (
    "Wir teilten zwölf gleiche Prüfkörper per Los auf zwei Gruppen auf. "
    "Nur die erste Gruppe wurde erhitzt. Danach verglichen wir die Bruchlast beider Gruppen."
)
MENTION_ONLY = (
    "Neuronale Netze werden nur im Ausblick erwähnt und hier nicht eingesetzt. "
    "Die Arbeit beschreibt ausschließlich die Grenzen einer einzelnen Fallbeschreibung."
)


class SemanticProvider(AssessmentProvider):
    def __init__(
        self, *, applied=True, count=1, mutate=None, fail_supplement=False, model_digest="MOCK"
    ):
        super().__init__()
        self.applied, self.count, self.mutate = applied, count, mutate
        self.fail_supplement = fail_supplement
        self.model_digest = model_digest
        self.planning_calls, self.supplement_calls = [], []

    async def discover(self):
        return [
            m.model_copy(update={"digest": self.model_digest}) if m.name == "qwen3:8b" else m
            for m in await super().discover()
        ]

    async def complete(self, model, messages, output_schema, max_tokens, *, unload):
        payload = json.loads(messages[-1]["content"])
        if "understanding" in output_schema["properties"]:
            self.planning_calls.append(payload)
            span = payload["untrusted_spans"][0]
            reference = {"span_id": span["id"], "quote": span["text"][:300]}
            plan = {
                "understanding": {
                    "research_question": "SYNTHETIC: Wie unterscheiden sich die Gruppen?",
                    "objective": "SYNTHETIC: Vergleich erklären.",
                    "field": "SYNTHETIC: Werkstoffprüfung",
                    "methodology": "SYNTHETIC: Vergleich zweier Gruppen",
                    "procedures": [
                        {
                            "id": "comparison",
                            "name": "Gruppenvergleich",
                            "use": "APPLIED" if self.applied else "MENTIONED",
                            "evidence": [reference],
                        }
                    ],
                    "data_basis": "SYNTHETIC: Prüfkörper",
                    "experimental_design": "SYNTHETIC: Zwei Gruppen",
                    "scientific_challenges": ["SYNTHETIC: Vergleichbarkeit"],
                    "criterion_ids": ["methodology"],
                },
                "agents": [
                    {
                        "key": f"causal_{i}",
                        "name": "Prüfung der Vergleichbarkeit von Prüfkörpern",
                        "task": "Prüfe Gruppenvergleich und alternative Erklärungen.",
                        "rationale": "Die Einteilung begründet eine zusätzliche Vergleichsprüfung.",
                        "criterion_id": "methodology",
                        "method_id": "comparison",
                        "evidence": [reference],
                        "expected_result": "Belegte Grenzen und offene Fragen",
                        "required_capabilities": ["methodology", "evidence"],
                    }
                    for i in range(self.count)
                ],
                "rationale": "SCRIPTED_MOCK_NOT_MODEL_QUALITY: gezielter Testauftrag"
                if self.count
                else "SCRIPTED_MOCK: kein zusätzlicher Spezialist notwendig.",
            }
            if self.mutate:
                self.mutate(plan)
            return Completion(
                text=json.dumps(plan, ensure_ascii=False),
                model=model.name,
                input_tokens=100,
                output_tokens=120,
            )
        if payload.get("supplemental_focus"):
            self.supplement_calls.append(payload)
            if self.fail_supplement:
                return Completion(
                    text="SCRIPTED_INVALID_JSON", model=model.name, input_tokens=10, output_tokens=5
                )
        response = await super().complete(model, messages, output_schema, max_tokens, unload=unload)
        if "judgment" in output_schema["properties"]:
            observation = json.loads(response.text)
            page, text = next(iter(payload["untrusted_pages"].items()))
            observation.update(page=int(page), quote=text.split("\n…\n")[0][:300])
            return response.model_copy(update={"text": json.dumps(observation, ensure_ascii=False)})
        return response
