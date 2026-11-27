import asyncio
import socket
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.config import Settings
from app.llm.errors import LLMError
from app.llm.gateway import CallBudget, LLMGateway
from app.llm.model_registry import ModelRegistry
from app.llm.providers.ollama import OllamaProvider
from app.main import create_app
from app.security.policy_engine import PolicyConfig, PolicyEngine
from app.security.request_limits import RequestBodyLimitMiddleware
from app.security.sperrvermerk_detector import detect_sperrvermerk
from fastapi.testclient import TestClient

from frontend.api_client import BackendError, request_backend
from frontend.egress import BackendTargetDenied, PinnedBackendTransport
from tests.fixtures import CONFIG


@pytest.mark.parametrize("addresses", [["1.1.1.1"], ["172.30.10.2", "1.1.1.1"], ["::1"], []])
def test_frontend_dns_does_not_expand_the_private_boundary(monkeypatch, addresses):
    records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 8000)) for ip in addresses]
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: records)
    with PinnedBackendTransport() as transport:
        with patch.object(transport.transport, "handle_request") as sink:
            with pytest.raises(BackendTargetDenied):
                transport.handle_request(
                    httpx.Request(
                        "POST", "http://backend:8000/api/v1/assessments", json={"synthetic": "data"}
                    )
                )
            sink.assert_not_called()


def test_frontend_connects_to_approved_ip_and_never_follows_backend_redirect(monkeypatch):
    records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("172.30.10.2", 8000))]
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: records)
    monkeypatch.setenv("BACKEND_URL", "http://backend:8000")
    seen = []

    def sink(_transport, request):
        seen.append(str(request.url))
        return httpx.Response(
            307, headers={"location": "https://controlled-sink.invalid"}, request=request
        )

    with patch("httpx.HTTPTransport.handle_request", sink):
        with pytest.raises(BackendError, match="Weiterleitung"):
            request_backend("POST", "/api/v1/assessments", json={"synthetic": "private"})
    assert seen == ["http://172.30.10.2:8000/api/v1/assessments"]


@pytest.mark.parametrize(
    "path,kwargs",
    [
        ("/api/v1/status?secret=data", {}),
        ("/api/v1/status#fragment", {}),
        ("/api/v1/status", {"follow_redirects": True}),
        ("/api/v1/status", {"auth": ("synthetic", "synthetic")}),
        ("/api/v1/status", {"params": {"derived": "data"}}),
    ],
)
def test_frontend_request_options_cannot_override_transport_policy(path, kwargs):
    with patch("httpx.Client.request") as sink:
        with pytest.raises(BackendError):
            request_backend("GET", path, **kwargs)
        sink.assert_not_called()


def test_chunked_request_limit_precedes_any_state_mutation(tmp_path, caplog):
    app = create_app(Settings(_env_file=None, document_store_dir=tmp_path))
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/assessments",
            content=iter([b"x" * 600_000, b"y" * 600_000]),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 413 and response.json() == {"code": "REQUEST_TOO_LARGE"}
        assert response.headers["cache-control"].startswith("no-store")
        assert not app.state.runtime.assessments.records
    assert "xxxxxx" not in caplog.text


@pytest.mark.parametrize(
    "headers,status",
    [
        ([(b"content-length", b"9999")], 413),
        ([(b"content-length", b"-1")], 400),
        ([(b"content-length", b"1"), (b"content-length", b"1")], 400),
    ],
)
def test_bad_lengths_are_rejected_without_reading_body(headers, status):
    async def scenario():
        app = AsyncMock()
        receive = AsyncMock(side_effect=AssertionError("BODY_SHOULD_NOT_BE_READ"))
        sent = []

        async def send(message):
            sent.append(message)

        await RequestBodyLimitMiddleware(app, max_bytes=100)(
            {"type": "http", "headers": headers}, receive, send
        )
        assert sent[0]["status"] == status
        app.assert_not_called()
        receive.assert_not_called()

    asyncio.run(scenario())


def test_model_digest_change_denies_chat_before_any_content_is_sent():
    async def scenario():
        registry = ModelRegistry.load(CONFIG / "models.yaml")
        model = registry.get("qwen").model_copy(update={"expected_digest": "a" * 64})
        registry = ModelRegistry([model])
        seen = []

        def sink(request):
            seen.append(request.url.path)
            return httpx.Response(
                200, json={"models": [{"name": model.name, "digest": "b" * 64, "size": 1}]}
            )

        async with httpx.AsyncClient(
            base_url="http://ollama:11434", transport=httpx.MockTransport(sink)
        ) as client:
            gateway = LLMGateway(
                registry,
                {"ollama": OllamaProvider(Settings(_env_file=None), client)},
                PolicyEngine(PolicyConfig()),
            )
            with pytest.raises(LLMError, match="DIGEST_MISMATCH"):
                await gateway.complete(
                    "qwen",
                    "orchestrator",
                    "PUBLIC",
                    [{"role": "user", "content": "Synthetic data"}],
                    CallBudget(1, 10000),
                    max_tokens=100,
                )
            assert seen == ["/api/tags"]
            with pytest.raises(LLMError):
                await gateway.route("scientific_text", "orchestrator", "PUBLIC", "qwen")

    asyncio.run(scenario())


def test_oversize_local_provider_response_is_a_sanitized_failure(monkeypatch):
    async def scenario():
        monkeypatch.setattr("app.llm.providers.ollama.MAX_PROVIDER_RESPONSE_BYTES", 100)
        async with httpx.AsyncClient(
            base_url="http://ollama:11434",
            transport=httpx.MockTransport(
                lambda r: httpx.Response(200, content=b"synthetic-sensitive" * 50)
            ),
        ) as client:
            provider = OllamaProvider(Settings(_env_file=None), client)
            with pytest.raises(LLMError, match="RESPONSE_TOO_LARGE") as error:
                await provider.request("GET", "/api/tags")
            assert "synthetic-sensitive" not in str(error.value)

    asyncio.run(scenario())


def test_sperrvermerk_details_are_candidates_and_never_expiry_based_release():
    notice = (
        "Sperr-\nvermerk\nUnternehmen: Synthetische Firma\nSperrfrist: 5 Jahre\n"
        "Gesperrt bis: 01.01.2000\nZugriffsberechtigt: Prüfer und Firma\n"
        "Genehmigung notwendig"
    )
    result = detect_sperrvermerk({1: notice})
    assert result.detected and result.classification == "RESTRICTED"
    assert (
        result.details.company == "Synthetische Firma" and result.details.stated_until.year == 2000
    )
    assert result.details.stated_duration == "5 Jahre" and result.details.approval_reference
    assert (
        result.requires_authorized_review
        and result.details.legal_validity == "REQUIRES_AUTHORIZED_REVIEW"
    )
    assert "Synthetische Firma" not in repr(result) and "Prüfer" not in repr(result)
    assert (
        detect_sperrvermerk({1: "Sperrvermerk\nGesperrt bis: 99.99.2000"}).details.stated_until
        is None
    )


def test_slow_request_body_is_rejected_before_application_execution():
    async def scenario():
        application = AsyncMock()

        async def receive():
            await asyncio.sleep(1)

        sent = []

        async def send(message):
            sent.append(message)

        await RequestBodyLimitMiddleware(application, read_timeout=0.001)(
            {"type": "http", "headers": []}, receive, send
        )
        assert sent[0]["status"] == 408
        application.assert_not_called()

    asyncio.run(scenario())


def test_frontend_oversized_responses_are_bounded(monkeypatch):
    from frontend.api_client import read_response

    monkeypatch.setattr("frontend.api_client.MAX_BACKEND_RESPONSE_BYTES", 100)
    with pytest.raises(BackendError, match="Größenlimit"):
        read_response(httpx.Response(200, content=b"x" * 101))


@pytest.mark.parametrize(
    "missing", ["version", "expected_digest", "weights_origin", "license_status"]
)
def test_approved_status_without_artifact_evidence_never_authorizes_inference(missing):
    approved = (
        ModelRegistry.load(CONFIG / "models.yaml")
        .get("qwen")
        .model_copy(
            update={
                "approval_status": "APPROVED",
                "security_review_status": "APPROVED",
                "license_status": "APPROVED",
                "version": "SYNTHETIC_FIXTURE",
                "weights_origin": "SYNTHETIC_FIXTURE",
                "expected_digest": "a" * 64,
            }
        )
    )
    policy = PolicyEngine(PolicyConfig())
    policy.check(approved, "PUBLIC", "orchestrator")  # Positive control, no model call.
    update = {missing: None if missing != "license_status" else "UNREVIEWED"}
    with pytest.raises(LLMError):
        policy.check(approved.model_copy(update=update), "PUBLIC", "orchestrator")
    with pytest.raises(LLMError):
        policy.check(approved, "RESTRICTED", "orchestrator")
