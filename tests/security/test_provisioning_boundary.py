import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest
import yaml

from infrastructure.scripts import provision, validate_docker


def approved_fixture(**updates):
    return {
        "name": "synthetic-model:v1",
        "local": True,
        "provider": "ollama",
        "enabled": True,
        "version": "SYNTHETIC",
        "expected_digest": "a" * 64,
        "weights_origin": "SYNTHETIC_FIXTURE",
        "approval_status": "APPROVED",
        "license_status": "APPROVED",
        "security_review_status": "APPROVED",
        **updates,
    }


@pytest.mark.parametrize(
    "updates",
    [
        {"expected_digest": None},
        {"expected_digest": "b" * 12},
        {"license_status": "UNREVIEWED"},
        {"security_review_status": "DEVELOPMENT_ONLY"},
        {"weights_origin": None},
        {"version": None},
        {"local": False},
        {"name": "synthetic:cloud"},
    ],
)
def test_model_provisioning_never_downloads_unapproved_or_unpinned_artifacts(tmp_path, updates):
    directory = tmp_path / "config"
    directory.mkdir()
    (directory / "models.yaml").write_text(
        yaml.safe_dump({"models": [approved_fixture(**updates)]}), "utf-8"
    )
    with (
        patch.object(provision, "ROOT", tmp_path),
        patch.object(provision, "docker") as docker,
        patch.object(provision, "run") as compose,
    ):
        with pytest.raises(SystemExit, match="APPROVAL_AND_DIGEST"):
            provision.main()
        compose.assert_not_called()
        docker.assert_not_called()


def test_development_registry_does_not_imply_real_model_download_approval():
    with patch.object(provision, "run") as compose, patch.object(provision, "docker") as docker:
        with pytest.raises(SystemExit, match="APPROVAL_AND_DIGEST"):
            provision.main()
        compose.assert_not_called()
        docker.assert_not_called()


def test_active_model_volume_is_never_changed_or_processing_stack_stopped():
    with (
        patch.object(provision, "provisioning_plan", return_value={"synthetic:v1": "a" * 64}),
        patch.object(provision, "docker", return_value="runtime-container"),
        patch.object(provision, "run") as compose,
    ):
        with pytest.raises(SystemExit, match="VOLUME_IN_USE"):
            provision.main()
        compose.assert_not_called()


def test_digest_verification_failure_always_removes_online_zone():
    calls = []

    def compose(*args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="f" * 64 if "ps" in args else "")

    def docker(*args):
        if args[0] == "run":
            assert "container:" + "f" * 64 in args and "--read-only" in args
            assert not any(arg in {"-v", "--volume", "--mount"} for arg in args)
            raise subprocess.CalledProcessError(3, ["docker", "controlled-helper"])
        return ""

    with (
        patch.object(provision, "provisioning_plan", return_value={"synthetic:v1": "a" * 64}),
        patch.object(provision, "docker", side_effect=docker),
        patch.object(provision, "run", side_effect=compose),
    ):
        with pytest.raises(subprocess.CalledProcessError):
            provision.main()
    assert calls[-1] == (*provision.ONLINE, "down", "--remove-orphans")
    assert not any(call == ("down", "--remove-orphans") for call in calls)


@pytest.mark.parametrize(
    "digest,duplicates,expected", [("a" * 64, False, 0), ("b" * 64, False, 3), ("a" * 64, True, 3)]
)
def test_actual_verifier_program_checks_full_digest_and_duplicate_names(
    digest, duplicates, expected, capsys
):
    models = [{"name": "synthetic:v1", "digest": digest}]
    if duplicates:
        models = models * 2
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps({"models": models}).encode()
    with (
        patch("urllib.request.urlopen", return_value=response) as endpoint,
        patch("sys.argv", ["verify", json.dumps({"synthetic:v1": "a" * 64})]),
    ):
        if expected:
            with pytest.raises(SystemExit) as error:
                exec(compile(provision.VERIFY, "<synthetic-verifier>", "exec"), {})
            assert error.value.code == expected
        else:
            exec(compile(provision.VERIFY, "<synthetic-verifier>", "exec"), {})
            assert "DIGESTS_VERIFIED" in capsys.readouterr().out
        endpoint.assert_called_once_with("http://127.0.0.1:11434/api/tags", timeout=15)


def test_standalone_topology_has_no_application_or_processing_network():
    config = validate_docker.render(["compose.provision.yaml"])
    assert not validate_docker.check_variant("provision", config)
    assert set(config["services"]) == {"model-provisioner"}
    assert set(config["networks"]) == {"provisioning"}
    service = config["services"]["model-provisioner"]
    assert not service.get("ports") and service["logging"]["driver"] == "none"
    merged = validate_docker.render(["compose.yaml", "compose.provision.yaml"])
    assert merged["networks"]["inference"]["internal"]
    assert merged["networks"]["frontend_api"]["internal"]
    assert set(merged["services"]["model-provisioner"]["networks"]) == {"provisioning"}
    assert validate_docker.check_variant("provision", merged)
