import json
import shutil
import subprocess
from unittest.mock import patch

import pytest

from infrastructure.scripts import provision
from tests.fixtures import ROOT


def test_runtime_has_no_external_network_or_public_api() -> None:
    if shutil.which("docker"):
        command = ["docker", "compose"]
    elif (ROOT / ".tools/docker-compose.exe").exists():
        command = [str(ROOT / ".tools/docker-compose.exe")]
    else:
        pytest.skip("Docker Compose CLI is unavailable")
    result = subprocess.run(
        [*command, "-f", "compose.yaml", "config", "--format", "json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    config = json.loads(result.stdout)
    assert all(network["internal"] for network in config["networks"].values())
    services = config["services"]
    assert not services["backend"].get("ports")
    assert not services["ollama"].get("ports")
    assert all(port["host_ip"] == "127.0.0.1" for port in services["frontend"]["ports"])
    assert services["ollama"]["environment"]["OLLAMA_NO_CLOUD"] == "1"


def test_failed_model_download_removes_online_network() -> None:
    calls = []

    def run(*args, **kwargs):
        calls.append(args)
        if args == ("config", "--format", "json"):
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    {"services": {"backend": {"environment": {"LLM_MODEL": "qwen3:8b"}}}}
                ),
            )
        if "pull" in args:
            raise subprocess.CalledProcessError(1, args)
        return subprocess.CompletedProcess(args, 0)

    with (
        patch.object(provision.shutil, "which", return_value="docker"),
        patch.object(provision, "run", side_effect=run),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            provision.main()
    assert calls[-1] == (
        "-f",
        "compose.yaml",
        "-f",
        "compose.provision.yaml",
        "down",
        "--remove-orphans",
    )
