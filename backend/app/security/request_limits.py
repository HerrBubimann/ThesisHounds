"""Bound the entire request before any state mutation, including chunked uploads."""

import asyncio

from starlette.responses import JSONResponse

MAX_REQUEST_BYTES = 1_048_576


class RequestBodyLimitMiddleware:
    def __init__(self, app, max_bytes=MAX_REQUEST_BYTES, read_timeout=15):
        self.app, self.max_bytes, self.read_timeout = app, max_bytes, read_timeout

    async def reject(self, scope, receive, send, status, code):
        response = JSONResponse(
            status_code=status,
            content={"code": code},
            headers={
                "Cache-Control": "no-store, max-age=0",
                "Pragma": "no-cache",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
            },
        )
        await response(scope, receive, send)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        lengths = [v for k, v in scope.get("headers", []) if k.lower() == b"content-length"]
        try:
            if len(lengths) > 1 or (lengths and (not lengths[0].isdigit())):
                raise ValueError("INVALID_LENGTH")
            if lengths and int(lengths[0]) > self.max_bytes:
                return await self.reject(scope, receive, send, 413, "REQUEST_TOO_LARGE")
        except ValueError:
            return await self.reject(scope, receive, send, 400, "INVALID_REQUEST_LENGTH")
        content = bytearray()
        try:
            async with asyncio.timeout(self.read_timeout):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return  # Never mutate state after the caller disconnects.
                    if message["type"] != "http.request":
                        return await self.reject(scope, receive, send, 400, "INVALID_REQUEST")
                    chunk = message.get("body", b"")
                    if len(content) + len(chunk) > self.max_bytes:
                        return await self.reject(scope, receive, send, 413, "REQUEST_TOO_LARGE")
                    content.extend(chunk)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            return await self.reject(scope, receive, send, 408, "REQUEST_BODY_TIMEOUT")
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(content), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)
