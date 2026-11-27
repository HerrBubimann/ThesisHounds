import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from app.llm.errors import LLMError
from app.research.gateway import ResearchGateway, ResearchQuery
from pydantic import ValidationError


@pytest.mark.parametrize("classification", ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"])
def test_research_is_networkless_even_with_a_forged_public_label(classification):
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as outgoing:
        with pytest.raises(LLMError):
            asyncio.run(
                ResearchGateway().search(
                    ResearchQuery(
                        terms="SYNTHETIC_SECRET_QUERY_CANARY",
                        classification=classification,
                        provider="crossref",
                    )
                )
            )
        outgoing.assert_not_called()
    assert not hasattr(ResearchGateway(), "store")


def test_missing_research_classification_is_not_accepted():
    with pytest.raises(ValidationError):
        ResearchQuery(terms="synthetic", provider="crossref")
