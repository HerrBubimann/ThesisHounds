import asyncio
import json
import time
from typing import Any

import httpx
from pydantic import ValidationError

from app.config import Settings
from app.llm.errors import LLMError
from app.llm.model_registry import ModelDefinition
from app.llm.providers.base import Completion
from app.models.schemas import LocalModel, ModelsResponse
from app.security.egress_policy import approved_target, inference_dispatch

MAX_PROVIDER_RESPONSE_BYTES = 8_000_000


class OllamaProvider:
    def __init__(
        self, settings: Settings, client: httpx.AsyncClient, *, measure_streaming=False
    ) -> None:
        self.settings = settings
        self.client = client
        self.measure_streaming = measure_streaming

    async def request(self, method: str, path: str, *, chat: bool = False, **kwargs: Any) -> dict:
        target = self.client.base_url.join(path)
        approved_target(target, self.settings)
        if path == "/api/chat" and (
            not inference_dispatch.get()
            or kwargs.get("json", {}).get("model") != inference_dispatch.get()
        ):
            raise LLMError(403, "INFERENCE_GATEWAY_REQUIRED")
        if str(self.client.base_url).rstrip("/") != str(self.settings.ollama_base_url).rstrip("/"):
            raise LLMError(403, "INFERENCE_ENDPOINT_MISMATCH")
        try:
            started = time.monotonic()
            streaming = chat and kwargs.get("json", {}).get("stream") is True
            pending, pieces, final, first_content = bytearray(), [], None, None

            def frame(raw):
                nonlocal final, first_content
                value = json.loads(raw)
                if (
                    not isinstance(value, dict)
                    or final is not None
                    or value.get("model") != inference_dispatch.get()
                ):
                    raise ValueError("INVALID_STREAM_FRAME")
                message = value.get("message", {})
                text = message.get("content", "")
                if not isinstance(text, str) or message.get("tool_calls"):
                    raise ValueError("INVALID_STREAM_CONTENT")
                if text:
                    if first_content is None:
                        first_content = time.monotonic() - started
                    pieces.append(text)
                if value.get("done") is True:
                    final = value

            deadline = self.settings.llm_chat_timeout if chat else self.settings.llm_status_timeout
            async with (
                asyncio.timeout(deadline),
                self.client.stream(
                    method,
                    path,
                    follow_redirects=False,
                    timeout=httpx.Timeout(
                        self.settings.llm_chat_timeout
                        if chat
                        else self.settings.llm_status_timeout,
                        connect=self.settings.llm_connect_timeout,
                    ),
                    **kwargs,
                ) as response,
            ):
                response.raise_for_status()
                content = bytearray()
                async for chunk in response.aiter_bytes():
                    if len(content) + len(chunk) > MAX_PROVIDER_RESPONSE_BYTES:
                        raise LLMError(502, "LOCAL_PROVIDER_RESPONSE_TOO_LARGE")
                    content.extend(chunk)
                    if streaming:
                        pending.extend(chunk)
                        while b"\n" in pending:
                            line, _, remainder = pending.partition(b"\n")
                            pending = bytearray(remainder)
                            if line.strip():
                                frame(line)
                if streaming:
                    if pending.strip():
                        frame(pending)
                    if final is None:
                        raise ValueError("INCOMPLETE_STREAM")
                    data = {
                        **final,
                        "message": {"content": "".join(pieces)},
                        "_client_first_content_seconds": first_content,
                    }
                else:
                    data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("Invalid object")
            return data
        except (httpx.TimeoutException, TimeoutError):
            raise LLMError(504, "Zeitlimit bei Ollama überschritten.") from None
        except httpx.HTTPStatusError as exc:
            if chat and exc.response.status_code == 404:
                raise LLMError(503, "Das angeforderte Modell ist lokal nicht verfügbar.") from None
            raise LLMError(502, "Ollama konnte die Anfrage nicht verarbeiten.") from None
        except httpx.RequestError:
            raise LLMError(503, "Ollama ist momentan nicht erreichbar.") from None
        except (ValueError, TypeError, AttributeError):
            raise LLMError(502, "Ollama hat eine ungültige Antwort geliefert.") from None

    async def discover(self) -> list[LocalModel]:
        try:
            return ModelsResponse.model_validate(await self.request("GET", "/api/tags")).models
        except ValidationError:
            raise LLMError(502, "Ollama hat eine ungültige Modellliste geliefert.") from None

    async def health(self) -> bool:
        try:
            await self.discover()
            return True
        except LLMError:
            return False

    async def capabilities(self, name: str) -> dict[str, Any]:
        data = await self.request("POST", "/api/show", json={"model": name})
        # Return only capability metadata, never templates or embedded model instructions.
        return {"capabilities": data.get("capabilities", []), "details": data.get("details", {})}

    async def resources(self) -> dict[str, Any]:
        data = await self.request("GET", "/api/ps")
        try:
            return {
                "loaded_models": [
                    {
                        "name": str(m["name"]),
                        "size_bytes": int(m["size"]),
                        "vram_bytes": int(m["size_vram"])
                        if m.get("size_vram") is not None
                        else None,
                    }
                    for m in data["models"]
                ]
            }
        except (KeyError, TypeError, ValueError):
            raise LLMError(502, "Ungültige Ressourceninformationen von Ollama.") from None

    async def complete(
        self,
        model: ModelDefinition,
        messages: list[dict[str, str]],
        output_schema: dict[str, Any] | None,
        max_tokens: int,
        *,
        unload: bool,
    ) -> Completion:
        if inference_dispatch.get() != model.name:
            raise LLMError(403, "INFERENCE_GATEWAY_REQUIRED")
        matches = [m for m in await self.discover() if m.name == model.name]
        if len(matches) != 1:
            raise LLMError(503, "Das angeforderte Modell ist lokal nicht verfügbar.")
        if (
            model.expected_digest
            and matches[0].digest.removeprefix("sha256:") != model.expected_digest
        ):
            raise LLMError(403, "LOCAL_MODEL_DIGEST_MISMATCH")
        payload: dict[str, Any] = {
            "model": model.name,
            "messages": messages,
            "stream": self.measure_streaming,
            "options": {"num_predict": max_tokens, "num_ctx": model.context_length},
            "keep_alive": 0 if unload else "5m",
        }
        if model.name.startswith("qwen3"):
            payload["think"] = False
        if output_schema is not None:
            payload["format"] = output_schema
            payload["options"]["temperature"] = 0
        data = await self.request("POST", "/api/chat", chat=True, json=payload)
        try:
            text = data["message"]["content"]
            if data.get("model") != model.name:
                raise ValueError("Unexpected model identity")
            if data.get("done") is not True or not isinstance(text, str) or not text.strip():
                raise ValueError("Incomplete")
            if data["message"].get("tool_calls"):
                raise ValueError("Unsolicited tools")

            def seconds(key):
                raw = data.get(key)
                if raw is None:
                    return None
                if type(raw) is not int or raw < 0:
                    raise ValueError("INVALID_PROVIDER_DURATION")
                return raw / 1_000_000_000

            return Completion(
                text=text,
                model=data["model"],
                input_tokens=data.get("prompt_eval_count"),
                output_tokens=data.get("eval_count"),
                load_duration_seconds=seconds("load_duration"),
                total_duration_seconds=seconds("total_duration"),
                generation_duration_seconds=seconds("eval_duration"),
                prompt_duration_seconds=seconds("prompt_eval_duration"),
                first_content_seconds=data.get("_client_first_content_seconds")
                if self.measure_streaming
                else None,
            )
        except (KeyError, TypeError, ValueError, ValidationError):
            raise LLMError(502, "Ollama hat eine ungültige Chatantwort geliefert.") from None
