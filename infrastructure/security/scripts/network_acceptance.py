"""CI/host probe using only a controlled synthetic listener, never a public API.

Run after compose.yaml + compose.ci.yaml are healthy. Requires Docker Engine.
An isolated CI check is not university deployment acceptance. No production data.
"""

import json
import subprocess
import sys
from uuid import uuid4

INFERENCE_PROBE = """
import asyncio, httpx
from app.config import Settings
from app.security.egress_policy import PinnedInferenceTransport
from app.services.llm_service import LLMService
async def probe():
    config = Settings()
    async with httpx.AsyncClient(
        base_url=str(config.ollama_base_url), trust_env=False,
        follow_redirects=False, transport=PinnedInferenceTransport()
    ) as client:
        result = await LLMService(config, client).chat('Test')
        assert result.answer.startswith('MOCK')
asyncio.run(probe())
"""


def docker(*args: str) -> str:
    return subprocess.run(
        ["docker", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=90,
    ).stdout.strip()


def main() -> int:
    # No generic targets accepted; this script creates its own non-private mock.
    name = "thesishounds-egress-canary-" + uuid4().hex[:10]
    listener = (
        "import socket; s=socket.socket(); s.bind(('0.0.0.0',8080)); "
        "s.listen(16); "
        "\nwhile True:\n c,a=s.accept(); c.close()"
    )
    try:
        # Positive control: exercise the real pinned provider against ONLY the
        # CI Ollama mock, using the fixed PUBLIC connectivity fixture.
        docker(
            "compose",
            "-f",
            "compose.yaml",
            "-f",
            "compose.ci.yaml",
            "exec",
            "-T",
            "backend",
            "python",
            "-c",
            INFERENCE_PROBE,
        )
        docker(
            "run",
            "--detach",
            "--name",
            name,
            "--pull",
            "never",
            "--network",
            "bridge",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges:true",
            "--user",
            "10001:10001",
            "thesishounds/backend:0.2.0",
            "python",
            "-c",
            listener,
        )
        target = json.loads(docker("inspect", name))[0]["NetworkSettings"]["Networks"]["bridge"][
            "IPAddress"
        ]
        if not target:
            raise RuntimeError("MOCK_ADDRESS_MISSING")
        # Positive control in the listener's namespace proves it is actually reachable.
        docker(
            "exec",
            name,
            "python",
            "-c",
            ("import socket; s=socket.create_connection(('127.0.0.1',8080),5); s.close()"),
        )
        for service in ("frontend", "backend", "ollama"):
            container = docker(
                "compose", "-f", "compose.yaml", "-f", "compose.ci.yaml", "ps", "-q", service
            )
            if not container:
                raise RuntimeError("PROCESSING_SERVICE_MISSING")
            inspection = json.loads(docker("inspect", container))[0]
            for network in inspection["NetworkSettings"]["Networks"]:
                if not json.loads(docker("network", "inspect", network))[0]["Internal"]:
                    raise RuntimeError("NON_PRIVATE_RUNTIME_NETWORK")
            probe = (
                "import socket,sys\n"
                "try:\n"
                f" s=socket.create_connection(({target!r},8080),2)\n"
                "except OSError: sys.exit(0)\n"
                "else: s.close(); sys.exit(1)\n"
            )
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
                "thesishounds/backend:0.2.0",
                "python",
                "-c",
                probe,
            )
        print(
            "NETWORK_CI_PROBE_PASSED: pinned mock inference allowed; "
            "public listener denied in 3 namespaces"
        )
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print("NETWORK_CI_PROBE_FAILED: missing evidence or unexpected reachability")
        return 1
    finally:
        try:
            docker("rm", "--force", name)
        except (OSError, subprocess.SubprocessError):
            print("NETWORK_PROBE_CLEANUP_REQUIRED")


if __name__ == "__main__":
    sys.exit(main())
