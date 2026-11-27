"""Pinned inference transport; complements, but never replaces, host egress rules."""

import asyncio
import ipaddress
import socket
import ssl
from contextvars import ContextVar
from typing import TYPE_CHECKING

import httpx

from app.llm.errors import LLMError

if TYPE_CHECKING:
    from app.config import Settings
ENDPOINTS = {
    ("http", "ollama", 11434): frozenset({"172.30.20.3"}),
    ("http", "localhost", 11434): frozenset({"127.0.0.1", "::1"}),
    ("http", "127.0.0.1", 11434): frozenset({"127.0.0.1"}),
    ("http", "::1", 11434): frozenset({"::1"}),
}
PATHS = frozenset({"/api/chat", "/api/tags", "/api/show", "/api/ps"})
inference_dispatch: ContextVar[str | None] = ContextVar("inference_dispatch", default=None)


def approved_target(url: httpx.URL, settings: "Settings | None" = None) -> frozenset[str]:
    addresses = ENDPOINTS.get((url.scheme, url.host, url.port or 80))
    if settings and settings.deployment_mode == "university":
        configured = httpx.URL(str(settings.ollama_base_url))
        pins = frozenset(settings.university_ollama_ips)
        private_ranges = [
            ipaddress.ip_network(s)
            for s in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
        ]
        try:
            valid_pins = pins and all(
                any(ipaddress.ip_address(ip) in network for network in private_ranges)
                for ip in pins
            )
        except ValueError:
            valid_pins = False
        if (
            valid_pins
            and configured.scheme == url.scheme == "https"
            and configured.host == url.host
            and configured.port == url.port
            and url.host in settings.university_ollama_hosts
        ):
            addresses = pins
    if not addresses or url.userinfo or url.query or url.fragment or url.path not in PATHS:
        raise LLMError(403, "NETWORK_TARGET_DENIED")
    return addresses


class PinnedInferenceTransport(httpx.AsyncBaseTransport):
    def __init__(self, settings: "Settings | None" = None, *, verify=True):
        if verify is False or (
            isinstance(verify, ssl.SSLContext)
            and (not verify.check_hostname or verify.verify_mode != ssl.CERT_REQUIRED)
        ):
            raise ValueError("TLS_VERIFICATION_REQUIRED")
        self.settings = settings
        self.transport = httpx.AsyncHTTPTransport(retries=0, trust_env=False, verify=verify)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        allowed = approved_target(request.url, self.settings)
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
        if request.url.scheme == "https":
            request.extensions["sni_hostname"] = request.url.host
        request.url = request.url.copy_with(host=sorted(addresses)[0])
        return await self.transport.handle_async_request(request)

    async def aclose(self):
        await self.transport.aclose()
