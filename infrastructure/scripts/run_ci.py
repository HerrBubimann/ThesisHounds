"""Run the CI quality checks locally (Windows, Linux, macOS).

    python infrastructure/scripts/run_ci.py <target> [<target> ...]

Targets: lint, format-check, test, test-unit, test-integration, test-security, coverage,
security, docker-check, docker-smoke, ci. `ci` runs every mandatory check that works without
GitHub: lint, format-check, coverage (all test suites once), security, docker-check.

Use the project interpreter, e.g. `.venv/bin/python` or `.\\.venv\\Scripts\\python.exe`.
Security scanners are installed on first use into .tools/scanners from the hashed lock file.
Gitleaks and Trivy run when installed on PATH; otherwise they are reported as SKIPPED.
"""

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
PY = sys.executable
SUITES = {"unit": "tests/unit", "integration": "tests/integration", "security": "tests/security"}
ENV = {
    **os.environ,
    "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
    "LANGSMITH_TRACING": "false",
    "LANGCHAIN_TRACING_V2": "false",
    "OTEL_SDK_DISABLED": "true",
    "PYTHONDONTWRITEBYTECODE": "1",
}
results: list[tuple[str, str]] = []


def run(name: str, *command: str | Path, env: dict | None = None) -> bool:
    print(f"\n==> {name}: {' '.join(str(c) for c in command)}", flush=True)
    ok = subprocess.run([str(c) for c in command], cwd=ROOT, env=env or ENV).returncode == 0
    results.append((name, "PASS" if ok else "FAIL"))
    return ok


def skip(name: str, reason: str) -> None:
    print(f"\n==> {name}: SKIPPED ({reason})")
    results.append((name, f"SKIPPED - {reason}"))


def scanner(tool: str) -> Path:
    bindir = ROOT / ".tools" / "scanners" / ("Scripts" if os.name == "nt" else "bin")
    executable = bindir / (f"{tool}.exe" if os.name == "nt" else tool)
    if not executable.exists():
        print("Installing security scanners into .tools/scanners (one-time) ...")
        venv.create(bindir.parent, with_pip=True, clear=True)
        python = bindir / ("python.exe" if os.name == "nt" else "python")
        subprocess.run(
            [python, "-m", "pip", "install", "-q", "--disable-pip-version-check",
             "--require-hashes", "-r", ROOT / "requirements-security.lock"],
            check=True,
        )  # fmt: skip
    return executable


def compose() -> list[str] | None:
    if shutil.which("docker"):
        return ["docker", "compose"]
    local = ROOT / ".tools" / "docker-compose.exe"
    return [str(local)] if local.exists() else None


def pytest(suite: str, *extra: str) -> bool:
    REPORTS.mkdir(exist_ok=True)
    return run(
        f"test-{suite}",
        PY, "-m", "pytest", SUITES[suite], "-p", "no:cacheprovider",
        f"--junitxml={REPORTS / f'junit-{suite}.xml'}", *extra,
    )  # fmt: skip


def lint() -> None:
    run("lint", PY, "-m", "ruff", "check", ".")
    run("syntax", PY, "-m", "compileall", "-q", "backend", "frontend", "infrastructure", "tests")


def format_check() -> None:
    run("format-check", PY, "-m", "ruff", "format", "--check", ".")


def test() -> None:
    for suite in SUITES:
        pytest(suite)


def coverage() -> None:
    data = REPORTS / "coverage"
    data.mkdir(parents=True, exist_ok=True)
    for old in data.glob("*.coverage"):
        old.unlink()
    for suite in SUITES:
        env = {**ENV, "COVERAGE_FILE": str(data / f"{suite}.coverage")}
        REPORTS.mkdir(exist_ok=True)
        run(
            f"test-{suite} (coverage)",
            PY, "-m", "pytest", SUITES[suite], "-p", "no:cacheprovider",
            f"--junitxml={REPORTS / f'junit-{suite}.xml'}",
            "--cov", "--cov-report=", "--cov-fail-under=0",
            env=env,
        )  # fmt: skip
    combined = {**ENV, "COVERAGE_FILE": str(data / "combined.coverage")}
    files = [str(p) for p in sorted(data.glob("*.coverage")) if p.name != "combined.coverage"]
    run("coverage-combine", PY, "-m", "coverage", "combine", "--keep", *files, env=combined)
    run("coverage-xml", PY, "-m", "coverage", "xml", "--fail-under=0", env=combined)
    run("coverage-html", PY, "-m", "coverage", "html", "--fail-under=0", env=combined)
    run("coverage-threshold", PY, "-m", "coverage", "report", env=combined)


def security() -> None:
    out = REPORTS / "security"
    out.mkdir(parents=True, exist_ok=True)
    targets = [
        "backend/app",
        "frontend",
        "infrastructure/scripts",
        "infrastructure/security/scripts",
    ]
    bandit = scanner("bandit")
    subprocess.run(
        [bandit, "-c", "pyproject.toml", "-r", *targets, "-q", "-f", "json",
         "-o", out / "bandit.json"],
        cwd=ROOT, check=False,
    )  # fmt: skip
    run("bandit (>= medium blocks)", bandit, "-c", "pyproject.toml", "-r", *targets,
        "--severity-level", "medium", "--confidence-level", "medium")  # fmt: skip
    run(
        "pip-audit",
        scanner("pip-audit"), "--strict", "--disable-pip", "--require-hashes",
        "--progress-spinner", "off",
        "-r", "backend/requirements.lock", "-r", "frontend/requirements.lock",
        "-r", "requirements-dev.lock", "-r", "requirements-security.lock",
    )  # fmt: skip
    if shutil.which("gitleaks"):
        run("gitleaks", "gitleaks", "git", "--redact", "--no-banner", ".")
    else:
        skip("gitleaks", "not on PATH, runs in GitHub Actions")
    pytest("security")


def docker_check() -> None:
    command = compose()
    if command is None:
        skip("docker-check", "no Docker Compose CLI")
        return
    run("docker-validate", PY, "infrastructure/scripts/validate_docker.py")
    if shutil.which("docker"):
        for dockerfile in ["backend/Dockerfile", "frontend/Dockerfile",
                           "infrastructure/ollama/Dockerfile"]:  # fmt: skip
            run(f"dockerfile-check {dockerfile}", "docker", "buildx", "build", "--check",
                "-f", dockerfile, ".")  # fmt: skip
    else:
        skip("dockerfile-check", "no Docker engine")


def docker_smoke() -> None:
    if not shutil.which("docker"):
        skip("docker-smoke", "no Docker engine")
        return
    stack = ["docker", "compose", "-f", "compose.yaml", "-f", "compose.ci.yaml"]
    if run("docker-build", "docker", "compose", "build"):
        try:
            if run("stack-up (mock LLM)", *stack, "up", "-d", "--no-build", "--pull", "never",
                   "--wait", "--wait-timeout", "180"):  # fmt: skip
                run("e2e-smoke", PY, "infrastructure/scripts/ci_e2e.py")
        finally:
            subprocess.run([*stack, "down", "--remove-orphans"], cwd=ROOT, check=False)


TARGETS = {
    "lint": [lint],
    "format-check": [format_check],
    "test": [test],
    "test-unit": [lambda: pytest("unit")],
    "test-integration": [lambda: pytest("integration")],
    "test-security": [lambda: pytest("security")],
    "coverage": [coverage],
    "security": [security],
    "docker-check": [docker_check],
    "docker-smoke": [docker_smoke],
    "ci": [lint, format_check, coverage, security, docker_check],
}


def main(argv: list[str]) -> int:
    unknown = [t for t in argv if t not in TARGETS]
    if not argv or unknown:
        print(__doc__)
        return 2
    for target in argv:
        for step in TARGETS[target]:
            step()
    print("\nSummary")
    for name, status in results:
        print(f"  {status:<8} {name}" if status in {"PASS", "FAIL"} else f"  {status}  {name}")
    failed = [name for name, status in results if status == "FAIL"]
    print("\nRESULT:", "FAILED - " + ", ".join(failed) if failed else "PASSED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
