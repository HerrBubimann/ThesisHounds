"""Policy tests for the CI workflow itself, so the quality gate cannot be weakened unnoticed."""

import re

import pytest
import yaml

from tests.fixtures import ROOT

WORKFLOW_FILES = sorted((ROOT / ".github").glob("**/*.yml"))
CI = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text("utf-8"))
JOBS = CI["jobs"]
GATE = JOBS["thesishounds-ci-gate"]


def test_triggers_cover_prs_main_merge_queue_and_manual_runs() -> None:
    triggers = CI[True]  # YAML 1.1 parses the key `on` as True
    assert triggers["pull_request"]["branches"] == ["main"]
    assert triggers["push"]["branches"] == ["main"]
    assert "merge_group" in triggers and "workflow_dispatch" in triggers
    assert "pull_request_target" not in triggers


def test_gate_has_stable_name_and_depends_on_every_job() -> None:
    assert GATE["name"] == "thesishounds-ci-gate"
    assert GATE["if"] == "${{ always() }}"
    others = set(JOBS) - {"thesishounds-ci-gate"}
    assert set(GATE["needs"]) == others
    assert set(GATE["steps"][-1]["env"]["MANDATORY_JOBS"].split()) == others


@pytest.mark.parametrize("name", sorted(JOBS))
def test_jobs_are_least_privilege_and_never_ignore_errors(name) -> None:
    job = JOBS[name]
    assert job["permissions"] == {"contents": "read"}
    assert job["timeout-minutes"] <= 45
    assert "continue-on-error" not in job
    assert all("continue-on-error" not in step for step in job["steps"])
    for step in job["steps"]:
        if step.get("uses", "").startswith("actions/checkout"):
            assert step["with"]["persist-credentials"] is False


def test_workflow_defaults_to_no_permissions_and_uses_no_secrets() -> None:
    assert CI["permissions"] == {}
    for path in WORKFLOW_FILES:
        assert "secrets." not in path.read_text("utf-8"), path


@pytest.mark.parametrize("path", WORKFLOW_FILES, ids=lambda p: p.name)
def test_third_party_actions_are_pinned_to_commit_sha(path) -> None:
    for action in re.findall(r"uses:\s*(\S+)", path.read_text("utf-8")):
        assert action.startswith("./") or re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", action)
