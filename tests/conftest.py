from collections.abc import Callable, Iterator

import httpx
import pytest
from app.api.routes import get_llm_service
from app.config import Settings
from app.main import create_app
from app.security.access_control import DEMO_PRINCIPAL, current_principal
from app.services.llm_service import LLMService
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def synthetic_service_identity():
    """Direct service tests have the same single synthetic identity as the demo API."""
    token = current_principal.set(DEMO_PRINCIPAL)
    try:
        yield
    finally:
        current_principal.reset(token)


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
