"""Run the container smoke payload against the real API without requiring Docker."""

import io
import urllib.error
import urllib.request
from urllib.parse import urlsplit

from app.config import Settings
from app.main import create_app
from fastapi.testclient import TestClient

from infrastructure.scripts.ci_e2e import FRONTEND_CHECK
from tests.fixtures import CONFIG


def test_container_smoke_payload_matches_current_api(tmp_path, monkeypatch, capsys):
    app = create_app(Settings(_env_file=None, config_dir=CONFIG, document_store_dir=tmp_path))
    with TestClient(app) as client:

        def urlopen(request, timeout=30):
            if isinstance(request, str):
                assert request == "http://127.0.0.1:8501/_stcore/health"
                return io.BytesIO(b"ok")
            url = urlsplit(request.full_url)
            assert url.scheme == "http" and url.netloc == "backend:8000"
            response = client.request(
                request.get_method(),
                url.path,
                content=request.data,
                headers={"Content-Type": "application/json"},
            )
            if response.is_error:
                raise urllib.error.HTTPError(
                    request.full_url,
                    response.status_code,
                    "Synthetic API response",
                    response.headers,
                    io.BytesIO(response.content),
                )
            return io.BytesIO(response.content)

        def request_backend(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

        monkeypatch.setattr(urllib.request, "urlopen", urlopen)
        monkeypatch.setattr("frontend.api_client.request_backend", request_backend)
        # Execute the exact source passed to Python in the frontend container. Unlike
        # checking for a string, this catches incompatible requests and later assertions.
        exec(compile(FRONTEND_CHECK, "<container-smoke>", "exec"), {"__name__": "__main__"})

    output = capsys.readouterr().out
    assert "OK  criterion E:" in output
    assert "OK  Mosbach DS25:" in output
    assert "OK  advanced review:" in output
