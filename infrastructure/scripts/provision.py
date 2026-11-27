"""Acquire approved model artifacts in a separate project with no document access."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "thesishounds-provisioning"
ONLINE = ("--project-name", PROJECT, "-f", "compose.provision.yaml")
HELPER_IMAGE = "thesishounds/backend:0.2.0"
VERIFY = """
import json, sys, urllib.request
expected = json.loads(sys.argv[1])
with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=15) as response:
    data = response.read(4000001)
if len(data) > 4000000: sys.exit(2)
models = json.loads(data)['models']
for name, digest in expected.items():
    matches = [m for m in models if m.get('name') == name]
    if len(matches) != 1 or matches[0].get('digest', '').removeprefix('sha256:') != digest:
        sys.exit(3)
print('PROVISIONED_MODEL_DIGESTS_VERIFIED')
"""


def provisioning_plan() -> dict[str, str]:
    data = yaml.safe_load((ROOT / "config/models.yaml").read_text("utf-8"))
    selected = [m for m in data["models"] if m.get("enabled", True)]
    if not selected:
        raise SystemExit("MODEL_PROVISIONING_NO_APPROVED_ARTIFACTS")
    plan = {}
    for model in selected:
        name, digest = model.get("name", ""), model.get("expected_digest", "")
        if (
            not isinstance(name, str)
            or not isinstance(digest, str)
            or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*(?::[a-zA-Z0-9._-]+)?", name)
            or ":cloud" in name
            or name.endswith("-cloud")
            or name in plan
            or model.get("local") is not True
            or model.get("provider") != "ollama"
            or any(
                model.get(field) != "APPROVED"
                for field in ("license_status", "security_review_status", "approval_status")
            )
            or not model.get("version")
            or not model.get("weights_origin")
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise SystemExit("MODEL_PROVISIONING_APPROVAL_AND_DIGEST_REQUIRED")
        plan[name] = digest
    return plan


def configured_models():
    return list(provisioning_plan())


def run(*args: str, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", *args], cwd=ROOT, check=True, text=True, capture_output=capture
    )


def docker(*args: str):
    return subprocess.run(
        ["docker", *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> None:
    if not shutil.which("docker"):
        raise SystemExit("DOCKER_COMPOSE_REQUIRED")
    plan = provisioning_plan()
    volume = os.getenv("OLLAMA_MODEL_VOLUME", "thesishounds_ollama_models")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}", volume):
        raise SystemExit("MODEL_VOLUME_NAME_DENIED")
    if docker("ps", "--filter", "volume=" + volume, "--format", "{{.ID}}"):
        raise SystemExit("MODEL_VOLUME_IN_USE_STOP_RUNTIME_FIRST")
    run(*ONLINE, "build", "--pull", "model-provisioner")
    run("-f", "compose.yaml", "build", "backend")
    docker("volume", "create", volume)
    try:
        run(
            *ONLINE,
            "up",
            "-d",
            "--no-build",
            "--pull",
            "never",
            "--wait",
            "--wait-timeout",
            "180",
            "model-provisioner",
        )
        for name in plan:
            run(*ONLINE, "exec", "-T", "model-provisioner", "ollama", "pull", name)
        container = run(*ONLINE, "ps", "-q", "model-provisioner", capture=True).stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{12,64}", container):
            raise SystemExit("PROVISIONER_ID_UNVERIFIED")
        docker(
            "run",
            "--rm",
            "--pull",
            "never",
            "--network",
            "container:" + container,
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges:true",
            "--user",
            "10001:10001",
            "--memory",
            "128m",
            "--pids-limit",
            "32",
            HELPER_IMAGE,
            "python",
            "-c",
            VERIFY,
            json.dumps(plan),
        )
    finally:
        run(*ONLINE, "down", "--remove-orphans")
    print("MODEL_PROVISIONING_FINISHED_DIGEST_VERIFIED; PROCESSING_NOT_AUTHORIZED")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"PROVISIONING_COMMAND_FAILED: {error.returncode}") from None
