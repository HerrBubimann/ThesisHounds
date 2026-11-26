"""Server-side API client; no browser requests to internal service addresses."""

import os

import httpx


class BackendError(Exception):
    """A message safe for display in the dashboard."""


def request_backend(method: str, path: str, **kwargs) -> dict:
    base_url = os.getenv("BACKEND_URL", "http://backend:8000")
    timeout = float(os.getenv("FRONTEND_REQUEST_TIMEOUT", "320")) if method == "POST" else 15
    try:
        with httpx.Client(base_url=base_url, trust_env=False, timeout=timeout) as client:
            response = client.request(method, path, **kwargs)
        if response.is_error:
            messages = {
                422: "Eingabe entspricht nicht dem freigegebenen API-Schema.",
                403: "Aktion ist durch die Datenschutzrichtlinie gesperrt.",
                404: "Analyse, Agent oder Befund wurde nicht gefunden oder bereits bereinigt.",
                409: "Aktion ist im aktuellen Ausführungsstatus nicht möglich.",
                429: "Ein Ressourcenlimit oder Modellbudget wurde erreicht.",
                502: "Ollama hat eine fehlerhafte Antwort geliefert.",
                503: "Ollama oder das konfigurierte Modell ist momentan nicht verfügbar.",
                504: "Die Modellantwort hat zu lange gedauert. Bitte später erneut versuchen.",
            }
            raise BackendError(
                messages.get(response.status_code, "Backend-Anfrage fehlgeschlagen.")
            )
        data = response.json()
        if not isinstance(data, (dict, list)):
            raise ValueError("Expected object")
        return data
    except httpx.TimeoutException:
        raise BackendError(
            "Zeitlimit überschritten. Bitte die Serviceverfügbarkeit prüfen."
        ) from None
    except httpx.RequestError:
        raise BackendError("Backend nicht erreichbar. Bitte Docker-Services prüfen.") from None
    except ValueError:
        raise BackendError("Das Backend hat eine ungültige Antwort geliefert.") from None
