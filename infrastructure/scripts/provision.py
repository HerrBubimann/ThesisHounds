"""Online model acquisition; afterwards all online containers/networks are removed."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def configured_models() -> list[str]:
    data = yaml.safe_load((ROOT / "config/models.yaml").read_text("utf-8"))
    models = [
        model["name"]
        for model in data["models"]
        if model.get("enabled", True) is True
        and model.get("local") is True
        and model.get("provider") == "ollama"
    ]
    if not models or len(models) != len(set(models)):
        raise SystemExit("Keine eindeutigen lokalen Modelle in config/models.yaml konfiguriert.")
    if any(
        not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._:-]*", model)
        or ":cloud" in model
        or model.endswith("-cloud")
        for model in models
    ):
        raise SystemExit("Model Registry enthält einen ungültigen lokalen Modelltag.")
    return models


def run(*args: str, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "compose", *args], cwd=ROOT, check=True, text=True, capture_output=capture
    )


def main() -> None:
    if not shutil.which("docker"):
        raise SystemExit("Docker mit Compose v2 muss installiert und gestartet sein.")
    config = json.loads(run("config", "--format", "json", capture=True).stdout)
    models = configured_models()
    if config["services"]["backend"]["environment"]["LLM_MODEL"] not in models:
        raise SystemExit("LLM_MODEL muss einem freigegebenen lokalen Registry-Modell entsprechen.")
    print("Online-Bereitstellung: Images bauen; laufende Anwendung danach vorübergehend stoppen.")
    run("build", "--pull")
    run("down", "--remove-orphans")
    online = ("-f", "compose.yaml", "-f", "compose.provision.yaml")
    try:
        run(*online, "up", "-d", "--no-deps", "--wait", "--wait-timeout", "180", "ollama")
        for model in models:
            run(*online, "exec", "-T", "ollama", "ollama", "pull", model)
        run(*online, "exec", "-T", "ollama", "ollama", "list")
    finally:
        # Keep the volume; remove the network that allowed registry access, even after a failure.
        run(*online, "down", "--remove-orphans")
    print(
        "Modell gespeichert. Offline starten: docker compose up -d --no-build --pull never --wait"
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Docker-Befehl fehlgeschlagen (Exit-Code {exc.returncode}).") from None
