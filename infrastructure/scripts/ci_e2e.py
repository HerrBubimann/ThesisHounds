"""Reproducible end-to-end smoke test of the running stack against the mock Ollama service.

Prerequisite (CI and local, needs Docker):
    docker compose -f compose.yaml -f compose.ci.yaml up -d --no-build --pull never --wait

All checks run inside the containers, so no backend or Ollama port is published. Only the
server-owned synthetic demo document is analysed; every model answer is MOCK data.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ["docker", "compose", "-f", "compose.yaml", "-f", "compose.ci.yaml"]

FRONTEND_CHECK = r"""
import json, time, urllib.request

def call(path, data=None, timeout=30):
    request = urllib.request.Request(
        'http://backend:8000' + path,
        data=None if data is None else json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'},
        method='GET' if data is None else 'POST',
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)

urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=10)
print('OK  frontend healthy')
assert call('/health')['status'] == 'ok'
print('OK  frontend -> backend /health')
status = call('/api/v1/status')
assert status['ollama'] == 'available' and status['model_available'], status
print('OK  backend -> mock ollama, model', status['model'], 'available')
answer = call('/api/v1/chat', {'prompt': 'Synthetischer CI-Test'})['answer']
assert answer.startswith('MOCK'), 'chat did not reach the mock service'
print('OK  chat round trip (mock answer)')
run = call('/api/v1/runs', {'mode': 'D', 'document_id': 'synthetic-demo'})
deadline = time.monotonic() + 120
while run['status'] in {'QUEUED', 'RUNNING'} and time.monotonic() < deadline:
    time.sleep(1)
    run = call('/api/v1/runs/' + run['run_id'])
assert run['status'] == 'WAITING_FOR_REVIEW', run.get('error') or run['status']
assert run['findings_count'] > 0 and run['final_report'] is None
graph = call('/api/v1/runs/' + run['run_id'] + '/graph')
dynamic = sum(node['dynamic'] for node in graph['nodes'])
assert dynamic >= 1, 'no dynamic subagent was created'
print(f"OK  synthetic workflow D: {run['findings_count']} findings, {dynamic} dynamic agents,"
      f" {run['model_calls']} mock model calls, waiting for human review")
"""

EGRESS_CHECK = r"""
import socket
try:
    socket.create_connection(('1.1.1.1', 443), timeout=3).close()
except OSError:
    print('OK  backend has no internet egress (internal networks)')
else:
    raise SystemExit('backend unexpectedly reached the internet')
"""


def run_in(service: str, code: str) -> None:
    command = [*COMPOSE, "exec", "-T", service, "python", "-c", code]
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode:
        sys.exit(f"E2E smoke test failed in service '{service}'")


def main() -> None:
    run_in("frontend", FRONTEND_CHECK)
    run_in("backend", EGRESS_CHECK)
    print("E2E smoke test passed.")


if __name__ == "__main__":
    main()
