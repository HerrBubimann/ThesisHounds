"""Opt-in local parser adapter; private-document runtime remains blocked pending acceptance."""

import asyncio
import socket
from contextvars import ContextVar
from xml.etree.ElementTree import ParseError

import httpx
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException

from app.llm.errors import LLMError
from app.security.classification import Classification, classify

parser_dispatch: ContextVar[bool] = ContextVar("parser_dispatch", default=False)
PARSER_URL = "http://grobid:8070/api/processFulltextDocument"
PARAMETERS = {
    "consolidateHeader": "0",
    "consolidateCitations": "0",
    "consolidateFunders": "0",
    "consolidatFunders": "0",
    "includeRawCitations": "1",
    "generateIDs": "1",
}


class PinnedParserTransport(httpx.AsyncBaseTransport):
    def __init__(self):
        self.transport = httpx.AsyncHTTPTransport(retries=0, trust_env=False)

    async def handle_async_request(self, request):
        if not parser_dispatch.get() or str(request.url) != PARSER_URL or request.method != "POST":
            raise LLMError(403, "PARSER_TARGET_DENIED")
        try:
            records = await asyncio.get_running_loop().getaddrinfo(
                "grobid", 8070, type=socket.SOCK_STREAM
            )
        except OSError:
            raise LLMError(503, "LOCAL_PARSER_UNAVAILABLE") from None
        addresses = {r[4][0] for r in records}
        if addresses != {"172.30.30.3"}:
            raise LLMError(403, "PARSER_DNS_DENIED")
        request.url = request.url.copy_with(host="172.30.30.3")
        return await self.transport.handle_async_request(request)

    async def aclose(self):
        await self.transport.aclose()


def parse_tei(data: bytes) -> dict:
    if not data or len(data) > 8_000_000:
        raise ValueError("PARSER_OUTPUT_LIMIT")
    try:
        root = ElementTree.fromstring(data)
    except (ParseError, DefusedXmlException):
        raise ValueError("INVALID_LOCAL_PARSER_XML") from None
    ns = {"t": "http://www.tei-c.org/ns/1.0"}
    entries = []
    for entry in root.findall(".//t:listBibl/t:biblStruct", ns):
        entries.append(
            {
                "id": entry.attrib.get("{http://www.w3.org/XML/1998/namespace}id"),
                "title": " ".join("".join(t.itertext()) for t in entry.findall(".//t:title", ns)),
                "authors": ["".join(t.itertext()) for t in entry.findall(".//t:surname", ns)],
                "doi": entry.findtext(".//t:idno[@type='DOI']", None, ns),
                "extraction_verified": False,
            }
        )
    citations = [
        {"text": "".join(r.itertext()), "target": r.attrib.get("target"), "mapping_verified": False}
        for r in root.findall(".//t:ref[@type='bibr']", ns)
    ]
    objects = []
    for element in root.iter():
        kind = element.tag.rsplit("}", 1)[-1]
        if kind not in {"figure", "formula"}:
            continue
        if len(objects) >= 500:
            raise ValueError("PARSER_OBJECT_LIMIT")
        objects.append(
            {
                "id": element.attrib.get("{http://www.w3.org/XML/1998/namespace}id"),
                "kind": "FORMULA"
                if kind == "formula"
                else "TABLE"
                if element.attrib.get("type") == "table"
                else "FIGURE",
                "text": " ".join(element.itertext())[:64000],
                "coordinates": element.attrib.get("coords"),
                "rows": [
                    [" ".join(cell.itertext())[:2000] for cell in row.findall("t:cell", ns)[:50]]
                    for row in element.findall(".//t:row", ns)[:200]
                ],
                "extraction_verified": False,
                "mapping_verified": False,
            }
        )
    return {
        "method": "local-grobid-tei",
        "references": entries,
        "citations": citations,
        "semantic_support": "MANUAL_REVIEW_REQUIRED",
        "external_consolidation": False,
        "objects": objects,
    }


class LocalGrobid:
    def __init__(self, *, enabled=False, client=None):
        self.enabled, self.client = enabled, client

    async def extract(
        self, pdf: bytes, classification, *, authorized=False, public_fixture_confirmed=False
    ):
        if (
            not self.enabled
            or not authorized
            or not public_fixture_confirmed
            or classify(classification) != Classification.PUBLIC
        ):
            raise LLMError(403, "LOCAL_PARSER_NOT_RELEASED_FOR_THIS_INPUT")
        if len(pdf) > 8_000_000 or not pdf.startswith(b"%PDF-"):
            raise LLMError(422, "LOCAL_PARSER_INPUT_DENIED")
        # Client injection is solely for controlled transport tests. Production uses fixed
        # transport/IP/path, certificate validation defaults and no environment proxies.
        client = self.client or httpx.AsyncClient(
            transport=PinnedParserTransport(), trust_env=False, follow_redirects=False, timeout=60
        )
        token = parser_dispatch.set(True)
        try:
            async with client.stream(
                "POST",
                PARSER_URL,
                data=PARAMETERS,
                files={"input": ("document.pdf", pdf, "application/pdf")},
                follow_redirects=False,
            ) as response:
                if response.status_code != 200:
                    raise LLMError(503, "LOCAL_PARSER_UNAVAILABLE")
                content = bytearray()
                async for chunk in response.aiter_bytes():
                    content.extend(chunk)
                    if len(content) > 8_000_000:
                        raise LLMError(502, "LOCAL_PARSER_OUTPUT_LIMIT")
                return parse_tei(bytes(content))
        except (httpx.HTTPError, ValueError):
            raise LLMError(503, "LOCAL_PARSER_UNAVAILABLE") from None
        finally:
            parser_dispatch.reset(token)
            if self.client is None:
                await client.aclose()
