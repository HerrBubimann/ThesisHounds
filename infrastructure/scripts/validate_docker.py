"""Static validation of all Docker Compose variants and Dockerfiles (no daemon, no GPU needed).

Uses `docker compose config` (or the project-local standalone CLI in .tools/) to render each
variant, then checks the project's infrastructure rules. Exit code 1 on any violation.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VARIANTS = {
    "cpu": ["compose.yaml"],
    "gpu": ["compose.yaml", "compose.gpu.yaml"],
    "provision": ["compose.provision.yaml"],
    "ci-mock": ["compose.yaml", "compose.ci.yaml"],
    "university": ["compose.university.yaml"],
    "grobid": ["compose.yaml", "compose.grobid.yaml"],
}
EXPECTED_SERVICES = {"frontend", "backend", "ollama"}
REQUIRED_FILES = [
    ".env.example",
    "config/agents.yaml",
    "config/execution.yaml",
    "config/models.yaml",
    "config/policies.yaml",
    "frontend/.streamlit/config.toml",
    "backend/requirements.lock",
    "frontend/requirements.lock",
]


def compose_command() -> list[str]:
    if shutil.which("docker"):
        return ["docker", "compose"]
    local = ROOT / ".tools" / "docker-compose.exe"
    if local.exists():
        return [str(local)]
    sys.exit("Docker Compose CLI not found (install Docker or place it in .tools/).")


def render(files: list[str]) -> dict:
    args = [arg for name in files for arg in ("-f", name)]
    result = subprocess.run(
        [*compose_command(), *args, "config", "--format", "json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            **(
                {
                    "GROBID_IMAGE": "grobid/grobid@sha256:" + "a" * 64,
                    "GROBID_CONFIG": str(ROOT / ".env.example"),
                    "COMPOSE_PROFILES": "local-parser",
                }
                if "compose.grobid.yaml" in files
                else {}
            ),
            **(
                {
                    "OLLAMA_BASE_URL": "https://inference.example.invalid",
                    "UNIVERSITY_OLLAMA_HOSTS": '["inference.example.invalid"]',
                    "UNIVERSITY_INFERENCE_NETWORK": "synthetic-restricted-inference",
                    "OLLAMA_AUTH_TOKEN": "",
                }
                if files == ["compose.university.yaml"]
                else {}
            ),
        },
    )
    if result.returncode:
        raise ValueError(f"compose config failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def check_variant(name: str, config: dict) -> list[str]:
    errors: list[str] = []
    services = config.get("services", {})
    networks = config.get("networks", {})
    volumes = config.get("volumes", {}) or {}
    expected = EXPECTED_SERVICES - {"ollama"} if name == "university" else EXPECTED_SERVICES
    if name == "grobid":
        expected = expected | {"grobid"}
    if name == "provision":
        expected = {"model-provisioner"}
    if set(services) != expected:
        errors.append(f"services {sorted(services)} != {sorted(expected)}")
    for network_name, network in networks.items():
        internal = bool(network.get("internal"))
        online_allowed = (name == "provision" and network_name == "provisioning") or (
            name == "university" and network_name == "university_inference"
        )
        if internal == online_allowed:
            errors.append(f"network '{network_name}' internal={internal} is not allowed")
        if (
            name == "university"
            and network_name == "university_inference"
            and not network.get("external")
        ):
            errors.append(
                "university: externally administered restricted inference network required"
            )
    for service_name, service in services.items():
        where = f"service '{service_name}'"
        test = (service.get("healthcheck") or {}).get("test")
        if not test or test == ["NONE"]:
            errors.append(f"{where}: healthcheck missing")
        if not service.get("read_only"):
            errors.append(f"{where}: read_only root filesystem required")
        if "ALL" not in (service.get("cap_drop") or []):
            errors.append(f"{where}: cap_drop ALL required")
        if "no-new-privileges:true" not in (service.get("security_opt") or []):
            errors.append(f"{where}: no-new-privileges required")
        for network_name in service.get("networks") or {}:
            if network_name not in networks:
                errors.append(f"{where}: undeclared network '{network_name}'")
        for mount in service.get("volumes") or []:
            if mount.get("type") == "volume" and mount.get("source") not in volumes:
                errors.append(f"{where}: undeclared volume '{mount.get('source')}'")
            if mount.get("type") == "bind":
                if not mount.get("read_only"):
                    errors.append(f"{where}: bind mount {mount.get('target')} must be read-only")
                if not Path(mount["source"]).exists():
                    errors.append(f"{where}: bind source missing: {mount['source']}")
        ports = service.get("ports") or []
        if service_name != "frontend" and ports:
            errors.append(f"{where}: must not publish ports")
        if any(port.get("host_ip") != "127.0.0.1" for port in ports):
            errors.append(f"{where}: ports must bind to 127.0.0.1")
        build = service.get("build")
        if build and not (Path(build["context"]) / build.get("dockerfile", "Dockerfile")).exists():
            errors.append(f"{where}: Dockerfile missing")
    ollama = services.get("ollama", services.get("model-provisioner", {}))
    devices = (((ollama.get("deploy") or {}).get("resources") or {}).get("reservations") or {}).get(
        "devices"
    ) or []
    has_gpu = any(
        d.get("driver") == "nvidia" and "gpu" in d.get("capabilities", []) for d in devices
    )
    if has_gpu != (name == "gpu"):
        errors.append(f"ollama GPU reservation present={has_gpu} is wrong for this variant")
    if name == "ci-mock" and (
        ollama.get("build") or ollama.get("image") != services.get("backend", {}).get("image")
    ):
        errors.append("ci-mock: ollama must reuse the backend image without building")
    if (
        name not in {"ci-mock", "university"}
        and ollama.get("environment", {}).get("OLLAMA_NO_CLOUD") != "1"
    ):
        errors.append("ollama: OLLAMA_NO_CLOUD=1 required")
    if name == "university":
        environment = services.get("backend", {}).get("environment", {})
        if environment.get("DEPLOYMENT_MODE") != "university":
            errors.append("university: deployment mode required")
        for flag in ("ENABLE_PUBLIC_RESEARCH", "ENABLE_AI_SCORING"):
            if environment.get(flag) != "false":
                errors.append(f"university: {flag}=false required")
    if name == "grobid":
        parser = services.get("grobid", {})
        if not re.fullmatch(r"grobid/grobid@sha256:[0-9a-f]{64}", parser.get("image", "")):
            errors.append("grobid: reviewed immutable upstream image digest required")
        if parser.get("pull_policy") != "never" or parser.get("user") != "10001:10001":
            errors.append("grobid: no downloads and non-root user required")
        if parser.get("dns") != ["127.0.0.1"] or set(parser.get("networks", {})) != {
            "document_processing"
        }:
            errors.append("grobid: isolated parser network and disabled external DNS required")
        if parser.get("logging", {}).get("driver") != "none":
            errors.append("grobid: content-capable container logging must be disabled")
    if name == "provision":
        provisioner = services.get("model-provisioner", {})
        if set(provisioner.get("networks", {})) != {"provisioning"}:
            errors.append("provision: processing networks must not be attached")
        mounts = provisioner.get("volumes", [])
        if len(mounts) != 1 or mounts[0].get("target") != "/home/ollama/.ollama":
            errors.append("provision: only the reviewed model volume may be mounted")
        if any(mount.get("type") != "volume" for mount in mounts):
            errors.append("provision: bind mounts are forbidden")
        if provisioner.get("user") != "10001:10001" or provisioner.get("ports"):
            errors.append("provision: non-root and no published ports required")
    return errors


def check_environment_documented() -> list[str]:
    documented = {
        line.split("=", 1)[0].strip()
        for line in (ROOT / ".env.example").read_text("utf-8").splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    }
    used = set(re.findall(r"\$\{([A-Z0-9_]+)", (ROOT / "compose.yaml").read_text("utf-8")))
    return [
        f".env.example: {name} is used in compose.yaml but not documented"
        for name in sorted(used - documented)
    ]


def check_dockerfiles() -> list[str]:
    errors = []
    for dockerfile in sorted(ROOT.glob("**/Dockerfile")):
        if any(part.startswith(".") for part in dockerfile.relative_to(ROOT).parts):
            continue
        text = dockerfile.read_text("utf-8")
        where = dockerfile.relative_to(ROOT).as_posix()
        for image in re.findall(r"^FROM\s+(\S+)", text, re.MULTILINE):
            if ":" not in image or image.endswith(":latest"):
                errors.append(f"{where}: base image '{image}' must be pinned to a version")
        users = re.findall(r"^USER\s+(\S+)", text, re.MULTILINE)
        if not users or users[-1].split(":")[0] in {"0", "root"}:
            errors.append(f"{where}: must switch to a non-root USER")
        if re.search(r"^ADD\s+https?://", text, re.MULTILINE):
            errors.append(f"{where}: ADD from URL is not allowed")
    return errors


def main() -> int:
    errors = [f"missing file: {path}" for path in REQUIRED_FILES if not (ROOT / path).exists()]
    for name, files in VARIANTS.items():
        try:
            variant_errors = check_variant(name, render(files))
        except ValueError as exc:
            variant_errors = [str(exc)]
        errors += [f"[{name}] {error}" for error in variant_errors]
        print(f"{'FAIL' if variant_errors else 'OK  '} compose variant {name}: {' + '.join(files)}")
    errors += check_environment_documented()
    errors += check_dockerfiles()
    for error in errors:
        print(f"ERROR {error}")
    print("Docker validation", "failed" if errors else "passed")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
