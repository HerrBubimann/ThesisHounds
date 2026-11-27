"""The frontend may send human review content only to a pinned internal API address."""

import ipaddress
import socket

import httpx

BACKENDS = {
    ("http", "backend", 8000): frozenset({"172.30.10.2"}),
    ("http", "localhost", 8000): frozenset({"127.0.0.1", "::1"}),
    ("http", "127.0.0.1", 8000): frozenset({"127.0.0.1"}),
    ("http", "::1", 8000): frozenset({"::1"}),
}


class BackendTargetDenied(httpx.RequestError):
    pass


class PinnedBackendTransport(httpx.BaseTransport):
    def __init__(self):
        self.transport = httpx.HTTPTransport(retries=0, trust_env=False)

    def handle_request(self, request):
        url = request.url
        allowed = BACKENDS.get((url.scheme, url.host, url.port))
        if not allowed or url.userinfo or url.query or url.fragment:
            raise BackendTargetDenied("BACKEND_TARGET_DENIED")
        try:
            records = socket.getaddrinfo(url.host, url.port, type=socket.SOCK_STREAM)
            addresses = {str(ipaddress.ip_address(item[4][0])) for item in records}
        except (OSError, ValueError):
            raise BackendTargetDenied("BACKEND_DNS_UNAVAILABLE") from None
        if not addresses or not addresses <= allowed:
            raise BackendTargetDenied("BACKEND_DNS_DENIED")
        # Resolve once and connect to this IP; a second DNS resolution cannot rebind it.
        request.url = url.copy_with(host=sorted(addresses)[0])
        return self.transport.handle_request(request)

    def close(self):
        self.transport.close()
