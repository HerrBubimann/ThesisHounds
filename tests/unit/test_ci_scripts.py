"""The quality gate must never report success for failed, cancelled, skipped or missing results."""

import json

import pytest

from infrastructure.scripts import ci_summary, validate_docker

JOBS = ["code-quality", "unit-tests", "integration-tests"]


def junit(path, tests=3, failures=0, errors=0, skipped=0):
    path.write_text(
        f'<testsuites><testsuite name="pytest" tests="{tests}" failures="{failures}" '
        f'errors="{errors}" skipped="{skipped}"/></testsuites>',
        encoding="utf-8",
    )


@pytest.fixture
def reports(tmp_path, monkeypatch):
    for suite in ("unit", "integration", "security", "privacy"):
        junit(tmp_path / f"junit-{suite}.xml")
    (tmp_path / "coverage.xml").write_text(
        '<coverage lines-valid="10" lines-covered="9" branches-valid="0" branches-covered="0"/>',
        encoding="utf-8",
    )
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    monkeypatch.setenv("MANDATORY_JOBS", " ".join(JOBS))
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    return tmp_path


def set_needs(monkeypatch, **overrides):
    needs = {job: {"result": "success"} for job in JOBS}
    needs.update({job: {"result": result} for job, result in overrides.items()})
    monkeypatch.setenv("NEEDS_JSON", json.dumps(needs))


def test_gate_passes_only_when_everything_succeeded(reports, monkeypatch):
    set_needs(monkeypatch)
    assert ci_summary.cmd_gate() == 0


@pytest.mark.parametrize("result", ["failure", "cancelled", "skipped", ""])
def test_gate_fails_for_any_non_success_result(reports, monkeypatch, result):
    set_needs(monkeypatch, **{"unit-tests": result})
    assert ci_summary.cmd_gate() == 1


def test_gate_fails_without_mandatory_job_list(reports, monkeypatch):
    set_needs(monkeypatch)
    monkeypatch.setenv("MANDATORY_JOBS", "")
    assert ci_summary.cmd_gate() == 1


def test_gate_fails_when_mandatory_job_is_missing(reports, monkeypatch):
    monkeypatch.setenv("NEEDS_JSON", json.dumps({"code-quality": {"result": "success"}}))
    assert ci_summary.cmd_gate() == 1


@pytest.mark.parametrize("counts", [{"failures": 1}, {"errors": 1}, {"skipped": 1}, {"tests": 0}])
def test_gate_fails_for_bad_test_reports(reports, monkeypatch, counts):
    set_needs(monkeypatch)
    junit(reports / "junit-integration.xml", **counts)
    assert ci_summary.cmd_gate() == 1


@pytest.mark.parametrize("missing", ["junit-security.xml", "coverage.xml"])
def test_gate_fails_for_missing_reports(reports, monkeypatch, missing):
    set_needs(monkeypatch)
    (reports / missing).unlink()
    assert ci_summary.cmd_gate() == 1


def test_scanner_counts(tmp_path):
    report = tmp_path / "audit.json"
    report.write_text(json.dumps({"dependencies": [{"vulns": [{"id": "X"}]}, {"vulns": []}]}))
    assert ci_summary.count_findings("pip-audit", report) == 1
    report.write_text(json.dumps({"Results": [{"Vulnerabilities": [{}, {}]}, {}]}))
    assert ci_summary.count_findings("trivy", report) == 2


def valid_service(**changes):
    service = {
        "healthcheck": {"test": ["CMD", "true"]},
        "read_only": True,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "networks": {"inference": None},
        "environment": {"OLLAMA_NO_CLOUD": "1"},
    }
    return {**service, **changes}


def config(**service_changes):
    return {
        "services": {
            "frontend": valid_service(),
            "backend": valid_service(),
            "ollama": valid_service(**service_changes),
        },
        "networks": {"inference": {"internal": True}},
    }


def test_docker_validator_accepts_valid_config():
    assert validate_docker.check_variant("cpu", config()) == []


@pytest.mark.parametrize(
    "change",
    [
        {"healthcheck": {}},
        {"read_only": False},
        {"cap_drop": []},
        {"ports": [{"host_ip": "0.0.0.0", "published": "11434"}]},
        {"networks": {"undeclared": None}},
        {"volumes": [{"type": "volume", "source": "undeclared", "target": "/x"}]},
        {"environment": {}},
    ],
)
def test_docker_validator_rejects_unsafe_services(change):
    assert validate_docker.check_variant("cpu", config(**change))


def test_docker_validator_requires_gpu_only_in_gpu_variant():
    gpu = {
        "resources": {"reservations": {"devices": [{"driver": "nvidia", "capabilities": ["gpu"]}]}}
    }
    assert validate_docker.check_variant("gpu", config(deploy=gpu)) == []
    assert validate_docker.check_variant("gpu", config())
    assert validate_docker.check_variant("cpu", config(deploy=gpu))


def test_docker_validator_rejects_external_network():
    bad = config()
    bad["networks"]["inference"]["internal"] = False
    assert validate_docker.check_variant("cpu", bad)
    # Provisioning may never admit a processing stack connected to an online network.
    assert validate_docker.check_variant("provision", bad)


def test_repository_dockerfiles_and_env_are_valid():
    assert validate_docker.check_dockerfiles() == []
    assert validate_docker.check_environment_documented() == []
