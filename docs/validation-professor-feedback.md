# Validation of the professor-feedback MVP

Date: 2026-11-26. Python 3.12.16 on Windows. All data in tests are synthetic;
model/provider responses are explicit mocks. No test below establishes real model
quality, scientific assessment validity or the effectiveness of bias mitigation.

| Check | Observed result |
|---|---|
| Full pytest suite | **176 passed**, 13.19 seconds; no failures/skips in the final run |
| Combined line/branch coverage | **88.28%**; existing 80% threshold retained |
| Ruff lint | Passed |
| Ruff format check | Passed (117 Python files) |
| Python compileall (backend/frontend/infrastructure/tests) | Passed |
| Bandit, blocking medium severity / medium confidence and higher | Passed; 0 medium/high issues, 15 low issues in the full scan statistics |
| pip-audit, all four hash-locked dependency sets | Passed: no known vulnerabilities found at scan time |
| Docker static validation | Passed: CPU, GPU, provisioning, CI mock and standalone university Compose |
| git diff --check | Passed |
| Streamlit → actual FastAPI → mocked local provider | Passed from new assessment through independent first review, comparison, discussion, criterion decisions and final human release |

Commands (repository root):

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --cov --cov-report=term:skip-covered --cov-report=xml --junitxml=reports/junit-professor-feedback.xml
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m compileall -q backend frontend infrastructure tests
.\.venv\Scripts\python.exe infrastructure/scripts/validate_docker.py
.\.tools\scanners\Scripts\bandit.exe -c pyproject.toml -r backend/app frontend infrastructure/scripts --severity-level medium --confidence-level medium
.\.tools\scanners\Scripts\pip-audit.exe --strict --disable-pip --require-hashes --progress-spinner off -r backend/requirements.lock -r frontend/requirements.lock -r requirements-dev.lock -r requirements-security.lock
git diff --check
```

Initial sandboxed pytest failed because Windows temp/cache access was denied; reruns
with authorized access passed. Initial sandboxed pip-audit was blocked by the sandbox
proxy/cache; the authorized rerun completed successfully. These initial environmental
failures are not reported as passing runs.

Not executed: Docker image build/BuildKit checks, actual container runtime smoke,
Trivy image scans and Gitleaks binary scan (Docker/Gitleaks/Trivy are not installed on
PATH in this environment). The standalone Compose renderer was available. These
checks remain mandatory in GitHub Actions; no check or threshold was removed. The
new tests are discovered by the existing unit/integration/security jobs, and the new
university variant is included by the existing Docker-validation command. A failed
new test therefore fails its job and `thesishounds-ci-gate`. Actual merge blocking
still depends on the GitHub ruleset; its remote configuration was not changed or
verified in this task. GitHub Actions itself was not executed from this session.

Not executed: real Ollama capability benchmarks, university TLS/VPN/auth connection,
real HF artifact provisioning, live research-provider requests, official rubric/
grade validation and participant evaluation. Required access, hardware, approved
documents, licenses and study/reference judgments are documented in the backlog and
stakeholder questions. No infrastructure address, stakeholder approval or scientific
performance result has been invented.

Generated coverage/JUnit outputs are under ignored `reports/`; do not commit review
material or confidential test works there or elsewhere in the repository.
