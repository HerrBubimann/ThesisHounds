import json

import pytest
import yaml

from infrastructure.scripts import ci_summary, privacy_dlp
from tests.fixtures import ROOT
from tests.unit.test_ci_scripts import junit


def test_privacy_job_is_mandatory_and_requires_its_own_report():
    jobs = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text("utf-8"))["jobs"]
    gate = jobs["thesishounds-ci-gate"]
    assert "privacy-security" in gate["needs"]
    assert any(s.get("with", {}).get("name") == "privacy-security-report" for s in gate["steps"])
    job = jobs["privacy-security"]
    assert "continue-on-error" not in job
    commands = "\n".join(step.get("run", "") for step in job["steps"])
    assert "tests/security" in commands and "privacy_dlp.py" in commands
    assert "ci_summary.py junit" in commands
    for job in jobs.values():
        for step in job["steps"]:
            if step.get("uses", "").startswith("actions/upload-artifact@"):
                assert "steps.artifact-privacy.outcome == 'success'" in step["if"]
                assert any(s.get("id") == "artifact-privacy" for s in job["steps"])


@pytest.mark.parametrize("state", ["missing", "skipped", "empty", "failure"])
def test_gate_cannot_pass_without_complete_privacy_evidence(tmp_path, monkeypatch, state):
    for suite in ("unit", "integration", "security"):
        junit(tmp_path / f"junit-{suite}.xml")
    if state != "missing":
        junit(
            tmp_path / "junit-privacy.xml",
            tests=0 if state == "empty" else 3,
            skipped=int(state == "skipped"),
            failures=int(state == "failure"),
        )
    (tmp_path / "coverage.xml").write_text('<coverage lines-covered="9" lines-valid="10"/>')
    monkeypatch.setenv("REPORTS_DIR", str(tmp_path))
    monkeypatch.setenv("MANDATORY_JOBS", "privacy-security")
    monkeypatch.setenv("NEEDS_JSON", json.dumps({"privacy-security": {"result": "success"}}))
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert ci_summary.cmd_gate() == 1


def test_dlp_fails_closed_when_index_unavailable(monkeypatch):
    def unavailable(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(privacy_dlp.subprocess, "run", unavailable)
    assert privacy_dlp.main() == 1
