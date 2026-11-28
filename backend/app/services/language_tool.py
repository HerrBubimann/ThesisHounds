"""Opt-in self-hosted LanguageTool suggestions; no cloud URL, correction or grade effect."""

import asyncio
import json

import httpx

from app.llm.errors import LLMError
from app.security.classification import Classification, classify
from app.services.document_intelligence import structure_document

LOCAL_CHECK_URL = "http://127.0.0.1:8081/v2/check"


class LocalLanguageTransport(httpx.AsyncBaseTransport):
    def __init__(self):
        self.transport = httpx.AsyncHTTPTransport(retries=0, trust_env=False)

    async def handle_async_request(self, request):
        if str(request.url) != LOCAL_CHECK_URL or request.method != "POST":
            raise LLMError(403, "LANGUAGE_TOOL_TARGET_DENIED")
        return await self.transport.handle_async_request(request)

    async def aclose(self):
        await self.transport.aclose()


def python_offset(text, units):
    """LanguageTool uses UTF-16 offsets; preserve Python original-page positions."""
    if type(units) is not int or units < 0:
        raise ValueError("LANGUAGE_TOOL_OFFSET_DENIED")
    used = 0
    for index, ch in enumerate(text):
        if used == units:
            return index
        used += 2 if ord(ch) > 0xFFFF else 1
    if used == units:
        return len(text)
    raise ValueError("LANGUAGE_TOOL_OFFSET_DENIED")


class LocalLanguageTool:
    def __init__(self, *, enabled=False, transport=None):
        self.enabled, self.transport = enabled, transport

    async def check(self, document, criterion, *, language="de-DE", terminology=()):
        result = {
            "status": "DISABLED",
            "criterion_id": criterion.id,
            "suggestions": [],
            "analysis_id": document.analysis_id,
            "document_id": document.document_id,
            "classification": document.classification,
            "automatic_grade_effect": False,
            "original_changed": False,
            "model_inference": False,
        }
        if not self.enabled:
            return result
        if criterion.category != "formal" or "language" not in criterion.local_checks:
            return {**result, "status": "NOT_APPLICABLE_TO_CONFIGURED_CRITERION"}
        if classify(document.classification) != Classification.PUBLIC:
            raise LLMError(403, "LANGUAGE_TOOL_PRIVATE_PROCESSING_NOT_RELEASED")
        if language not in {"de-DE", "en-US", "en-GB"}:
            raise LLMError(422, "LANGUAGE_TOOL_LANGUAGE_DENIED")
        structure = structure_document(document)
        blocks, used = [], 0
        for block in structure.blocks:
            if block.kind != "PARAGRAPH" or not block.reliable:
                continue
            if len(blocks) >= 20 or used + len(block.text) > 12000:
                break
            used += len(block.text)
            blocks.append(block)
        try:
            async with (
                asyncio.timeout(15),
                httpx.AsyncClient(
                    transport=self.transport or LocalLanguageTransport(),
                    follow_redirects=False,
                    trust_env=False,
                    timeout=5,
                ) as client,
            ):
                for block in blocks:
                    async with client.stream(
                        "POST",
                        LOCAL_CHECK_URL,
                        data={
                            "text": block.text,
                            "language": language,
                            "enabledOnly": "false",
                        },
                    ) as response:
                        if response.status_code != 200:
                            raise ValueError("LOCAL_LANGUAGE_TOOL_UNAVAILABLE")
                        raw = bytearray()
                        async for data in response.aiter_bytes():
                            raw.extend(data)
                            if len(raw) > 1_000_000:
                                raise ValueError("LANGUAGE_TOOL_RESPONSE_LIMIT")
                    payload = json.loads(raw)
                    matches = payload.get("matches", [])
                    if not isinstance(matches, list) or len(matches) > 1000:
                        raise ValueError("LANGUAGE_TOOL_MATCH_LIMIT")
                    for match in matches:
                        offset, length = match["offset"], match["length"]
                        if type(offset) is not int or type(length) is not int or length <= 0:
                            raise ValueError("LANGUAGE_TOOL_OFFSET_DENIED")
                        start = python_offset(block.text, offset)
                        end = python_offset(block.text, offset + length)
                        quote = block.text[start:end]
                        # Quoted passages, code/formula-like text and accepted terminology
                        # are not mechanically criticized by general language rules.
                        if quote in terminology or any(
                            c in block.text for c in ('"', "„", "“", "$", "`")
                        ):
                            continue
                        result["suggestions"].append(
                            {
                                "page": block.page,
                                "start": block.start + start,
                                "end": block.start + end,
                                "quote": quote,
                                "rule_id": str(match.get("rule", {}).get("id", "UNKNOWN"))[:100],
                                "message": str(match.get("message", ""))[:600],
                                "status": "CANDIDATE_REQUIRES_HUMAN",
                                "origin": "LOCAL_RULE_ENGINE",
                            }
                        )
                        if len(result["suggestions"]) >= 100:
                            return {**result, "status": "PARTIAL_SUGGESTION_LIMIT"}
        except (httpx.HTTPError, TimeoutError, ValueError, KeyError, TypeError):
            return {**result, "status": "UNAVAILABLE_REQUIRES_HUMAN"}
        return {
            **result,
            "status": "COMPLETED_BOUNDED_TEXT_CHECK",
            "checked_characters": used,
            "complete_document_check": False,
        }
