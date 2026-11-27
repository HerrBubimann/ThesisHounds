import asyncio
from dataclasses import FrozenInstanceError, replace

import pytest
from app.agents.research_quality import review_source_use
from app.assessments.routine_checks import inventory
from app.llm.errors import LLMError
from app.research.citations import extract_citations, verify_citations

from tests.unit.test_citation_engine import doc, record
from tests.unit.test_institutional_rules import profile, resolved, rule


@pytest.mark.parametrize("classification", ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"])
def test_citation_derivatives_retain_document_classification_and_scope(classification):
    document = doc(classification=classification).model_copy(update={"analysis_id": "scope"})
    extracted = extract_citations(document)
    entry = extracted["entries"][0]
    for item in [
        extracted,
        *extracted["mentions"],
        inventory(document),
        *inventory(document)["doi_candidates"],
    ]:
        assert item["classification"] == classification
        assert item["analysis_id"] == "scope" and item["document_id"] == document.document_id
    assert entry.classification == classification and entry.analysis_id == "scope"
    assert entry.document_id == document.document_id
    with pytest.raises(FrozenInstanceError):
        entry.classification = "PUBLIC"
    result = verify_citations(document, extracted=extracted)
    assert result["classification"] == classification
    assert result["references"][0]["classification"] == classification
    assert result["external_requests"] == 0


def test_unlabelled_or_higher_citation_cannot_downgrade_public_result():
    document = doc()
    extracted = extract_citations(document)
    entry = extracted["entries"][0]
    for value in ["RESTRICTED", None, "malformed"]:
        altered = {**extracted, "entries": [replace(entry, classification=value)]}
        result = verify_citations(document, extracted=altered)
        assert result["classification"] == "RESTRICTED"
        assert "RESEARCH_BLOCKED_BY_PRIVACY" in result["references"][0]["statuses"]
    del extracted["classification"]
    assert verify_citations(document, extracted=extracted)["classification"] == "RESTRICTED"


@pytest.mark.parametrize(
    "mutation",
    [{"analysis_id": "foreign"}, {"document_id": "foreign"}, {"classification": "RESTRICTED"}],
)
def test_foreign_or_private_entry_never_reaches_source_quality_model(mutation):
    class DenyingGateway:
        def __init__(self):
            self.levels = []

        async def route(self, task, role, level, model_id):
            self.levels.append(level)
            raise LLMError(403, "PRIVATE_SOURCE_DENIED")

    async def scenario():
        document = doc().model_copy(update={"analysis_id": "scope"})
        entry = replace(extract_citations(document)["entries"][0], **mutation)
        gateway = DenyingGateway()
        with pytest.raises(LLMError):
            await review_source_use(
                gateway,
                document,
                resolved(p=profile([rule(id="quality", method="human_quality_review")])),
                "quality",
                entry,
                record(abstract="Synthetic source"),
                None,
                model_id="llama",
                page=1,
                quote="Ergebnis",
            )
        assert gateway.levels == (["RESTRICTED"] if "classification" in mutation else [])

    asyncio.run(scenario())
