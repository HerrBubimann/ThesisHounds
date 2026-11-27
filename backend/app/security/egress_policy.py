"""Pinned inference transport; complements, but never replaces, host egress rules."""

import asyncio
import ipaddress
import socket
from contextvars import ContextVar

import httpx

from app.llm.errors import LLMError

ENDPOINTS = {
    ("http", "ollama", 11434): frozenset({"172.30.20.3"}),
    ("http", "localhost", 11434): frozenset({"127.0.0.1", "::1"}),
    ("http", "127.0.0.1", 11434): frozenset({"127.0.0.1"}),
    ("http", "::1", 11434): frozenset({"::1"}),
}
PATHS = frozenset({"/api/chat", "/api/tags", "/api/show", "/api/ps"})
inference_dispatch: ContextVar[str | None] = ContextVar("inference_dispatch", default=None)


def approved_target(url: httpx.URL) -> frozenset[str]:
    addresses = ENDPOINTS.get((url.scheme, url.host, url.port or 80))
    if not addresses or url.userinfo or url.query or url.fragment or url.path not in PATHS:
        raise LLMError(403, "NETWORK_TARGET_DENIED")
    return addresses


class PinnedInferenceTransport(httpx.AsyncBaseTransport):
    def __init__(self):
        self.transport = httpx.AsyncHTTPTransport(retries=0, trust_env=False)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        allowed = approved_target(request.url)
        loop = asyncio.get_running_loop()
        try:
            records = await loop.getaddrinfo(
                request.url.host, request.url.port, type=socket.SOCK_STREAM
            )
            addresses = {str(ipaddress.ip_address(r[4][0])) for r in records}
        except (OSError, ValueError):
            raise LLMError(503, "INFERENCE_DNS_UNAVAILABLE") from None
        if not addresses or not addresses <= allowed:
            raise LLMError(403, "INFERENCE_DNS_DENIED")
        # Connect to the validated IP, preventing a second DNS lookup/rebinding.
        request.url = request.url.copy_with(host=sorted(addresses)[0])
        return await self.transport.handle_async_request(request)

    async def aclose(self):
        await self.transport.aclose()
