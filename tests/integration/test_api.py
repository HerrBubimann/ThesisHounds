import httpx
import pytest
from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

from tests.fixtures import MODEL


def test_health_without_ollama() -> None:
    with TestClient(create_app(Settings(_env_file=None))) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_status_and_models(client_factory) -> None:
    client = client_factory(lambda _: httpx.Response(200, json={"models": [MODEL]}))
    assert client.get("/api/v1/models").json() == {"models": [MODEL]}
    status = client.get("/api/v1/status").json()
    assert status["ollama"] == "available"
    assert status["model_available"] is True
    assert status["model"] == "qwen3:8b"


def test_missing_model_does_not_attempt_inference(client_factory) -> None:
    def handler(request):
        assert request.url.path == "/api/tags"
        return httpx.Response(200, json={"models": []})

    client = client_factory(handler)
    status = client.get("/api/v1/status").json()
    assert status["ollama"] == "available"
    assert status["model_available"] is False
    assert client.post("/api/v1/chat", json={"prompt": "Test"}).status_code == 503


def test_chat_contract_and_no_content_in_logs(client_factory, caplog) -> None:
    import json

    def handler(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [MODEL]})
        assert request.url.path == "/api/chat"
        payload = json.loads(request.content)
        assert payload["model"] == "qwen3:8b"
        assert payload["stream"] is False
        assert payload["think"] is False
        assert payload["messages"] == [{"role": "user", "content": "Test"}]
        assert payload["options"]["num_predict"] == 512
        assert request.extensions["timeout"]["read"] == 300
        return httpx.Response(
            200,
            json={"model": "qwen3:8b", "message": {"content": "PRIVATE_ANSWER"}, "done": True},
        )

    client = client_factory(handler)
    response = client.post("/api/v1/chat", json={"prompt": "Test"})
    assert response.status_code == 200
    assert response.json() == {"model": "qwen3:8b", "answer": "PRIVATE_ANSWER"}
    assert "PRIVATE_PROMPT" not in caplog.text
    assert "PRIVATE_ANSWER" not in caplog.text


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"prompt": ""},
        {"prompt": "  "},
        {"prompt": "x" * 16001},
        {"prompt": 123},
        {"prompt": "PRIVATE_PROMPT", "model": "evil-cloud"},
    ],
)
def test_validation_does_not_echo_input(client_factory, payload) -> None:
    def handler(_):
        pytest.fail("Invalid input must not reach Ollama")

    response = client_factory(handler).post("/api/v1/chat", json=payload)
    assert response.status_code == 422
    assert "PRIVATE_PROMPT" not in response.text
    assert "input" not in response.json()


@pytest.mark.parametrize(
    "kind,expected",
    [
        ("connection", 503),
        ("timeout", 504),
        ("http", 502),
        ("json", 502),
        ("schema", 502),
        ("redirect", 502),
    ],
)
def test_upstream_failures_are_sanitized(client_factory, kind, expected) -> None:
    def handler(request):
        if kind == "connection":
            raise httpx.ConnectError("PRIVATE_UPSTREAM", request=request)
        if kind == "timeout":
            raise httpx.ReadTimeout("PRIVATE_UPSTREAM", request=request)
        if kind == "http":
            return httpx.Response(500, json={"error": "PRIVATE_UPSTREAM"})
        if kind == "json":
            return httpx.Response(200, text="PRIVATE_UPSTREAM")
        if kind == "redirect":
            return httpx.Response(302, headers={"location": "https://external.example"})
        return httpx.Response(200, json={"models": [{"name": "PRIVATE_UPSTREAM"}]})

    client = client_factory(handler)
    response = client.get("/api/v1/models")
    assert response.status_code == expected
    assert "PRIVATE_UPSTREAM" not in response.text
    status = client.get("/api/v1/status")
    assert status.status_code == 200
    assert status.json()["ollama"] == "unavailable"


@pytest.mark.parametrize("status_code,expected", [(404, 503), (500, 502)])
def test_chat_upstream_http_failure(client_factory, status_code, expected) -> None:
    def handler(request):
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [MODEL]})
        return httpx.Response(status_code, json={"error": "PRIVATE_PROMPT"})

    response = client_factory(handler).post("/api/v1/chat", json={"prompt": "Test"})
    assert response.status_code == expected
    assert "PRIVATE_PROMPT" not in response.text


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"model": "qwen3:8b", "message": {"content": ""}, "done": True},
        {"model": "qwen3:8b", "message": {"content": "x"}, "done": False},
    ],
)
def test_invalid_chat_response(client_factory, data) -> None:
    def handler(request):
        return httpx.Response(
            200, json={"models": [MODEL]} if request.url.path == "/api/tags" else data
        )

    assert client_factory(handler).post("/api/v1/chat", json={"prompt": "Test"}).status_code == 502
