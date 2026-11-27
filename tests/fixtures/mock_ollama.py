"""Mock Ollama HTTP service for container smoke tests in CI.

Implements the subset of the Ollama API that the backend uses (/api/tags, /api/ps,
/api/show, /api/chat) and answers with deterministic, synthetic, clearly marked MOCK
content. It never loads a model, needs no GPU and contacts no external service.

Run inside the backend image (see compose.ci.yaml):
    python -m tests.fixtures.mock_ollama
"""

import asyncio
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

from tests.fixtures.providers import WorkflowProvider

# Model tag -> registry id, mirroring config/models.yaml.
MODELS = {"qwen3:8b": "qwen", "mistral:7b": "mistral", "llama3.1:8b": "llama"}
CHAT_ANSWER = "MOCK: ThesisHounds ist bereit."
PROVIDER = WorkflowProvider()


def structured_answer(model: str, messages: list[dict]) -> str:
    definition = SimpleNamespace(name=model, id=MODELS[model])
    completion = asyncio.run(PROVIDER.complete(definition, messages, None, 0, unload=True))
    return completion.text


class Handler(BaseHTTPRequestHandler):
    server_version = "mock-ollama"

    def log_message(self, *_args) -> None:
        # No request logging: keeps CI logs free of prompts, even synthetic ones.
        pass

    def reply(self, status: int, data: dict) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/tags":
            models = [{"name": name, "size": 1, "digest": "MOCK"} for name in MODELS]
            self.reply(200, {"models": models})
        elif self.path == "/api/ps":
            self.reply(200, {"models": []})
        elif self.path in {"/", "/api/version"}:
            self.reply(200, {"version": "mock"})
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self.reply(400, {"error": "invalid json"})
            return
        model = payload.get("model")
        if model not in MODELS:
            self.reply(404, {"error": "model not found"})
            return
        if self.path == "/api/show":
            self.reply(200, {"capabilities": ["completion"], "details": {"format": "mock"}})
        elif self.path == "/api/chat":
            messages = payload.get("messages", [])
            try:
                text = structured_answer(model, messages) if "format" in payload else CHAT_ANSWER
            except Exception:  # mirror a failing model as an HTTP error
                self.reply(500, {"error": "mock could not answer"})
                return
            self.reply(
                200,
                {
                    "model": model,
                    "message": {"role": "assistant", "content": text},
                    "done": True,
                    "prompt_eval_count": 100,
                    "eval_count": 50,
                },
            )
        else:
            self.reply(404, {"error": "not found"})


def create_server(host: str = "0.0.0.0", port: int = 11434) -> ThreadingHTTPServer:  # nosec B104
    # 0.0.0.0 is only reachable inside the internal-only compose network.
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    create_server().serve_forever()


if __name__ == "__main__":
    main()
