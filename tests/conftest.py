from collections.abc import Callable, Iterator

import httpx
import pytest
from app.api.routes import get_llm_service
from app.config import Settings
from app.main import create_app
from app.services.llm_service import LLMService
from fastapi.testclient import TestClient


@pytest.fixture
def client_factory() -> Iterator[Callable]:
    clients = []

    def make(handler: Callable) -> TestClient:
        settings = Settings(_env_file=None, ollama_base_url="http://ollama:11434")
        application = create_app(settings)
        upstream = httpx.AsyncClient(
            base_url="http://ollama:11434", transport=httpx.MockTransport(handler)
        )
        application.dependency_overrides[get_llm_service] = lambda: LLMService(settings, upstream)
        client = TestClient(application)
        clients.append(client)
        return client

    yield make
    for client in clients:
        client.close()
