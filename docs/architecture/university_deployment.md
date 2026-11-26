# Local and university deployment

Local development continues with `docker compose up --build` after existing offline
model provisioning. Ollama has no published host port; internal networks and
`OLLAMA_NO_CLOUD=1` remain. Native development may use localhost. No university access
is required for tests; no model is downloaded by the assessment workflow.

University deployment uses the standalone `compose.university.yaml`, not an overlay
on `compose.yaml`. Prepare an ignored `.env.university` with values actually supplied
by university IT. Do not infer a hostname from the examples below:

```dotenv
OLLAMA_BASE_URL=https://REPLACE-WITH-APPROVED-INTERNAL-HOST
UNIVERSITY_OLLAMA_HOSTS=["REPLACE-WITH-APPROVED-INTERNAL-HOST"]
UNIVERSITY_INFERENCE_NETWORK=REPLACE-WITH-IT-MANAGED-NETWORK
OLLAMA_DEFAULT_MODEL=qwen3:8b
OLLAMA_REQUEST_TIMEOUT=300
MAX_CONCURRENT_MODEL_REQUESTS=1
```

The model tag must exist on the university server and match a reviewed entry in
`config/models.yaml`; category model assignments are in `config/agents.yaml`.
`OLLAMA_DEFAULT_MODEL` configures the simple chat, not all supervisor assignments.
Memory and capabilities in existing registry entries are estimates/configuration,
not empirical benchmark results. Use smaller licensed models for constrained local
hardware; do not assume that current default model tags are the latest or suitable.

IT must provision the external network with default-deny egress (only approved
Ollama IP/port plus necessary internal DNS), VPN routes and private ingress rules.
Docker's external network setting does not implement those firewall rules. Verify
that neither the application nor Ollama is publicly accessible. The UI binds to
loopback; backend has no host port. No production student data is supported yet.

If the university supplies a private CA, mount its PEM read-only using a deployment
override and set `OLLAMA_CA_FILE` in the backend to the mounted absolute path.
Certificate verification cannot be disabled. Set `OLLAMA_AUTH_TOKEN` only when the
university's internal reverse proxy expects bearer authentication. No auth method
is assumed to exist in Ollama itself. mTLS/SSO schemes need an approved proxy design;
do not put credentials in URLs. Prefer managed secret injection over plain env files.
The backend sends no requests through ambient HTTP proxies and follows no redirects.

```powershell
docker compose -f compose.university.yaml --env-file .env.university config --quiet
docker compose -f compose.university.yaml --env-file .env.university up --build -d
```

Legacy `LLM_MODEL`/`LLM_CHAT_TIMEOUT` remain accepted. New native environment aliases
`OLLAMA_DEFAULT_MODEL`/`OLLAMA_REQUEST_TIMEOUT` take precedence when both are set.
The university Compose stack passes the new aliases. Local Compose retains legacy
variables. The effective concurrency is bounded by execution.yaml, the environment
limit and sequential model loading (which forces one call at a time).

## Required university information — all pending

| Information | Decision owner / acceptance |
|---|---|
| Server address, internal DNS, port | IT: approved allowlist, private routing and ownership |
| GPU, VRAM, RAM, model sizes, storage | IT: runnable models and peak capacity measurements |
| Quotas, simultaneous requests, scheduling | IT: agreed concurrency/time/token budgets |
| Auth, TLS CA, possible VPN/mTLS | IT/security: tested credentials, rotation and verified trust |
| Network restrictions and cloud disablement | IT/security: default-deny egress and no public Ollama API |
| Privacy approval, retention and logs | Data owner/privacy officer: approved data flow before real uploads |
| Model deployment process | IT/model steward: pinned origin, license, artifact digest, test and rollback |

No live university connection, GPU benchmark, VPN, DNS or certificate validation has
been performed in this implementation session.
