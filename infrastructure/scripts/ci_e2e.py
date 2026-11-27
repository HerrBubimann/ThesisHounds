"""Reproducible end-to-end smoke test of the running synthetic development stack.

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
import json, time, urllib.request, urllib.error

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
from frontend.api_client import request_backend
assert request_backend('GET', '/health')['status'] == 'ok'
print('OK  frontend healthy')
assert call('/health')['status'] == 'ok'
print('OK  frontend -> backend /health')
status = call('/api/v1/status')
assert status['ollama'] == 'available' and status['model_available'], status
print('OK  backend synthetic provider, model', status['model'], 'available')
answer = call('/api/v1/chat', {'prompt': 'Test'})['answer']
assert answer.startswith('MOCK'), 'mock answer missing'
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
assessment = call('/api/v1/assessments', {'work_type': 'PA1', 'profile_id': 'pa1-example',
    'program': 'data_science_ai', 'cohort': 'DS25'})
assert assessment['institutional_rules']['profile']['cohort'] == 'DS25'
assert assessment['institutional_rules']['status'] == 'MANUAL_REVIEW_REQUIRED'
assert not any(rule['active'] for rule in assessment['institutional_rules']['rules'])
path = '/api/v1/assessments/' + assessment['id']
call(path + '/ai-review', {})
deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    state = call(path)
    if state['ai_state'] not in {'PENDING', 'RUNNING'}:
        break
    time.sleep(0.2)
assert state['ai_state'] == 'COMPLETED', 'criterion review did not complete'
for embargoed in ('/comparison', '/academic-checks', '/provenance'):
    try:
        call(path + embargoed)
    except urllib.error.HTTPError as error:
        assert error.code == 409
    else:
        raise AssertionError('independent review embargo was bypassed')
call(path + '/human-review', {'release': True, 'criteria': [
    {'criterion_id': c['id'], 'judgment': 'MIXED', 'observations': 'Synthetic first review',
     'rationale': 'Synthetic independent human rationale'}
    for c in assessment['profile']['criteria']
]})
call(path + '/release', {'confirmed': True})
comparison = call(path + '/comparison')
academic = call(path + '/academic-checks')
assert academic['external_requests'] == 0
assert all(row['status'] == 'MANUAL_REVIEW_REQUIRED' for row in academic['formal']['checks'])
call(path + '/academic-decisions', {'finding_id': academic['formal']['checks'][0]['finding_id'],
    'decision': 'ACCEPTED', 'rationale': 'Synthetic human note; no official release'})
assert comparison['coverage']['complete']
assert not any(row['ai']['supplemental'] for row in comparison['criteria'])
assert all(row['ai']['verification_rounds'] for row in comparison['criteria'])
finding = comparison['criteria'][0]['ai']
assert finding['context_trace']['classification'] == 'PUBLIC'
trace = finding['context_trace']
assert trace['estimated_input_tokens'] + trace['output_reservation'] <= trace['model_context_limit']
assert not finding['context_trace']['absence_proven']
call(path + '/finding-feedback', {'finding_id': finding['finding_id'], 'action': 'CORRECT',
    'reason': 'MISSING_CONTEXT', 'rationale': 'Synthetic human feedback',
    'correction': 'Synthetic corrected finding'})
provenance = call(path + '/provenance')
assert provenance['adaptive_planning']['mocked']
assert provenance['adaptive_planning']['status'] == 'VALIDATED_PROPOSAL'
assert not provenance['adaptive_planning']['proposals']
assert provenance['current_document_matches_snapshot'] and provenance['finding_feedback']
assert provenance['classification'] == 'RESTRICTED' and not provenance['automatic_training']
assert provenance['model_calls'] > 0 and provenance['findings']
evidence = call(path + '/findings/' + finding['finding_id'] + '/evidence')
assert evidence['matched'] and evidence['quote'] in evidence['original_text']
call(path + '/manual-review', {'confirmed': True})
for row in comparison['criteria']:
    call(path + '/decisions', {'criterion_id': row['criterion_id'],
        'include_ai_finding': False, 'conclusion': 'Synthetic human conclusion',
        'rationale': 'Synthetic final rationale'})
draft = call(path + '/finalize', {'confirmed': True})
assert draft['label'] == 'Menschlich freigegeben'
assert 'MOCK:' not in draft['text']
print('OK  criterion E: routing, coverage, supplements, verification, evidence, human final')
print('OK  Mosbach DS25: candidates, conflicts, embargoed offline checks, human decision')
print('OK  advanced review: scoped contexts, budgets, private provenance, versioned feedback')
"""


def run_in(service: str, code: str) -> None:
    command = [*COMPOSE, "exec", "-T", service, "python", "-c", code]
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode:
        sys.exit(f"E2E smoke test failed in service '{service}'")


def main() -> None:
    run_in("frontend", FRONTEND_CHECK)
    # Egress is tested separately against the controlled listener created by
    # infrastructure/security/scripts/network_acceptance.py, never a public IP.
    print("E2E smoke test passed.")


if __name__ == "__main__":
    main()
