"""Closed MVP boundary. No HTTP client, document store, arbitrary URL or provider execution."""

from typing import Literal

from app.llm.errors import LLMError
from app.schemas.domain import StrictModel
from pydantic import Field


class ResearchQuery(StrictModel):
    terms: str = Field(min_length=1, max_length=300)
    classification: Literal["PUBLIC", "CONFIDENTIAL", "INTERNAL", "RESTRICTED", "SYNTHETIC"]
    provider: Literal[
        "crossref",
        "openalex",
        "semantic_scholar",
        "arxiv",
        "datacite",
        "unpaywall",
        "retraction_watch",
    ]


class ResearchGateway:
    """Fail closed until isolated deployment, human query approval and providers are reviewed."""

    async def search(self, query: ResearchQuery):
        if query.classification != "PUBLIC":
            raise LLMError(403, "Nicht öffentliche Rechercheanfrage gesperrt.")
        # PUBLIC supplied by a caller is not proof of public provenance or human approval.
        raise LLMError(403, "Öffentliche Recherche ist noch nicht freigegeben.")
