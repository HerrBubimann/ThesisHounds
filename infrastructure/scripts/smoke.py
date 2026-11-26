"""Verify live internal communication without publishing backend or Ollama ports."""

import argparse
import subprocess
from pathlib import Path

CHECK = """
import json
import urllib.request

def get(path):
    with urllib.request.urlopen('http://backend:8000' + path, timeout=15) as response:
        return json.load(response)

assert get('/health')['status'] == 'ok', 'Backend health failed'
status = get('/api/v1/status')
assert status['ollama'] == 'available', status['detail']
assert status['model_available'], status['detail']
models = get('/api/v1/models')['models']
assert any(model['name'] == status['model'] for model in models), 'Model is missing'
print('OK: Frontend-Netz -> Backend -> Ollama; konfiguriertes Modell vorhanden.')
"""

CHAT_CHECK = """
request = urllib.request.Request(
    'http://backend:8000/api/v1/chat',
    data=json.dumps({'prompt': 'Antworte kurz mit: ThesisHounds ist bereit.'}).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST',
)
with urllib.request.urlopen(request, timeout=1850) as response:
    result = json.load(response)
assert result['answer'].strip(), 'Empty answer'
print('OK: Lokale Inferenz hat eine nicht leere Antwort geliefert.')
"""

ANALYSIS_CHECK = """
import time
def post(path, data):
    request = urllib.request.Request(
        'http://backend:8000' + path, data=json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'}, method='POST',
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)

created = post('/api/v1/runs', {
    'mode': ANALYSIS_MODE, 'document_id': 'synthetic-demo',
})
deadline = time.monotonic() + 3700
while time.monotonic() < deadline:
    run = get('/api/v1/runs/' + created['run_id'])
    if run['status'] not in {'QUEUED', 'RUNNING'}:
        break
    time.sleep(3)
else:
    post('/api/v1/runs/' + created['run_id'] + '/cancel', {})
    raise SystemExit('Analysis timeout; cancellation requested')
assert run['status'] in {'WAITING_FOR_REVIEW', 'COMPLETED'}, run.get('error')
assert not run['mocked'], 'Expected real local inference, received MOCK'
assert run['findings_count'] > 0, 'No findings returned by the models'
print('OK: Synthetische Analyse mit echten Modellen bis zur menschlichen Prüfung ausgeführt.')
keys = ['run_id', 'mode', 'model_calls', 'tokens', 'findings_count']
print(json.dumps({key: run[key] for key in keys}))
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chat", action="store_true", help="Auch echte lokale Inferenz testen")
    parser.add_argument("--gpu", action="store_true", help="GPU-Compose-Override verwenden")
    parser.add_argument(
        "--analysis", action="store_true", help="Synthetischen Analyseworkflow testen"
    )
    parser.add_argument("--mode", choices=["A", "B", "C", "D"], default="D")
    args = parser.parse_args()
    compose = ["docker", "compose", "-f", "compose.yaml"]
    if args.gpu:
        compose += ["-f", "compose.gpu.yaml"]
    result = subprocess.run(
        [
            *compose,
            "exec",
            "-T",
            "frontend",
            "python",
            "-c",
            CHECK
            + (CHAT_CHECK if args.chat else "")
            + (f"ANALYSIS_MODE = {args.mode!r}\n" + ANALYSIS_CHECK if args.analysis else ""),
        ],
        cwd=Path(__file__).resolve().parents[2],
        check=False,
    )
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
