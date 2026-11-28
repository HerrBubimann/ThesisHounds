"""Server-side API client; no browser requests to internal service addresses."""

import json
import math
import os

import httpx

from frontend.egress import PinnedBackendTransport

MAX_BACKEND_RESPONSE_BYTES = 8_000_000


class BackendError(Exception):
    """A message safe for display in the dashboard."""


def request_backend(method: str, path: str, **kwargs) -> dict | list:
    return _request(method, path, **kwargs)


def request_pdf(path: str) -> bytes:
    """Binary original through exactly the same pinned server-side transport."""
    if not path.endswith("/original-pdf"):
        raise BackendError("Nicht freigegebenes Backend-Ziel.")
    return _request("GET", path, pdf=True)


def _request(method: str, path: str, *, pdf=False, **kwargs):
    base_url = os.getenv("BACKEND_URL", "http://backend:8000")
    try:
        target = httpx.URL(base_url)
        relative = httpx.URL(path)
    except httpx.InvalidURL:
        raise BackendError("Nicht freigegebenes Backend-Ziel.") from None
    if (
        target.scheme != "http"
        or target.host not in {"backend", "localhost", "127.0.0.1", "::1"}
        or target.port != 8000
        or target.userinfo
        or target.query
        or target.fragment
        or target.path not in {"", "/"}
        or relative.is_absolute_url
        or relative.query
        or relative.fragment
        or path.startswith("//")
        or method not in {"GET", "POST", "DELETE"}
        or not set(kwargs) <= {"json"}
        or not (path == "/health" or path.startswith("/api/v1/"))
    ):
        raise BackendError("Nicht freigegebenes Backend-Ziel.")
    try:
        timeout = float(os.getenv("FRONTEND_REQUEST_TIMEOUT", "320")) if method == "POST" else 15
        if not math.isfinite(timeout) or not 0 < timeout <= 1800:
            raise ValueError("INVALID_REQUEST_TIMEOUT")
        with httpx.Client(
            base_url=base_url,
            trust_env=False,
            timeout=timeout,
            transport=PinnedBackendTransport(),
            follow_redirects=False,
        ) as client:
            with client.stream(method, path, follow_redirects=False, **kwargs) as response:
                if pdf and not response.is_error and not response.is_redirect:
                    if response.headers.get("content-type", "").split(";")[0] != "application/pdf":
                        raise ValueError("Expected PDF")
                    data = _read_bytes(response)
                    if not data.startswith(b"%PDF-"):
                        raise ValueError("Expected PDF")
                    return bytes(data)
                return read_response(response)
    except httpx.TimeoutException:
        raise BackendError(
            "Zeitlimit überschritten. Bitte die Serviceverfügbarkeit prüfen."
        ) from None
    except httpx.RequestError:
        raise BackendError("Backend nicht erreichbar. Bitte Docker-Services prüfen.") from None
    except ValueError:
        raise BackendError("Das Backend hat eine ungültige Antwort geliefert.") from None


def read_response(response):
    if response.is_redirect:
        raise BackendError("Backend-Weiterleitung ist nicht freigegeben.")
    if response.is_error:
        messages = {
            401: "Eine verifizierte Anmeldung ist erforderlich.",
            405: "Diese Schnittstelle erlaubt keine Änderung.",
            423: (
                "Weitere Dokumentverarbeitung ist bis zur menschlichen Sicherheitsprüfung gesperrt."
            ),
            422: "Eingabe entspricht nicht dem freigegebenen API-Schema.",
            403: "Aktion ist durch die Datenschutzrichtlinie gesperrt.",
            404: "Analyse, Agent oder Befund wurde nicht gefunden oder bereits bereinigt.",
            409: "Aktion ist im aktuellen Ausführungsstatus nicht möglich.",
            429: "Ein Ressourcenlimit oder Modellbudget wurde erreicht.",
            413: "Die Anfrage überschreitet das zulässige Größenlimit.",
            408: "Die Anfrage wurde nicht rechtzeitig vollständig übertragen.",
            502: "Ollama hat eine fehlerhafte Antwort geliefert.",
            503: "Ollama oder das konfigurierte Modell ist momentan nicht verfügbar.",
            504: "Die Modellantwort hat zu lange gedauert. Bitte später erneut versuchen.",
        }
        raise BackendError(messages.get(response.status_code, "Backend-Anfrage fehlgeschlagen."))
    if response.status_code == 204:
        return {}
    data = json.loads(_read_bytes(response))
    if not isinstance(data, (dict, list)):
        raise ValueError("Expected object")
    return data


def _read_bytes(response):
    content = bytearray()
    for chunk in response.iter_bytes():
        if len(content) + len(chunk) > MAX_BACKEND_RESPONSE_BYTES:
            raise BackendError("Die Backend-Antwort überschreitet das zulässige Größenlimit.")
        content.extend(chunk)
    return content
