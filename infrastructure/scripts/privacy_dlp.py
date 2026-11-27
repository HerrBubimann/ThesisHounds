"""Path-based DLP gate. Never prints confidential names or opens document content.

This cannot establish public provenance of arbitrary source text. Secret scanning
and operator review remain necessary. Git must be present: fail closed otherwise.
"""

import base64
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath

DENIED_PARTS = frozenset(
    {
        "uploads",
        "documents",
        "data",
        "reports",
        "output",
        "outputs",
        ".runtime",
        "backups",
        "snapshots",
        "embeddings",
        "vectorstore",
        "private",
        "secrets",
    }
)
DENIED_SUFFIXES = frozenset(
    {
        ".pdf",
        ".doc",
        ".docx",
        ".dotx",
        ".odt",
        ".rtf",
        ".pptx",
        ".xlsx",
        ".xltx",
        ".xls",
        ".csv",
        ".tsv",
        ".sqlite",
        ".sqlite3",
        ".db",
        ".parquet",
        ".jsonl",
        ".log",
        ".zip",
        ".7z",
        ".pem",
        ".key",
        ".p12",
        ".pfx",
        ".safetensors",
        ".gguf",
        ".bin",
    }
)


def prohibited(path: str) -> bool:
    value = PurePosixPath(path.replace("\\", "/").casefold())
    return (
        bool(set(value.parts) & DENIED_PARTS)
        or value.suffix in DENIED_SUFFIXES
        or value.name.startswith(".env")
        and value.name != ".env.example"
        or value.suffix == ".txt"
        and not value.name.startswith("requirements")
    )


def main() -> int:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "-z"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        print("DLP_FAILED: Git index unavailable")
        return 1
    paths = result.stdout.decode("utf-8", errors="strict").split("\0")
    count = sum(prohibited(p) for p in paths if p)
    print(f"DLP: {count} prohibited indexed paths; file names and contents suppressed")
    return int(count > 0)


def inspect_artifacts(root: Path, markers: list[str]) -> int:
    """Return nonzero on leaked plain/encoded markers or unverifiable files."""
    if not root.is_dir() or root.is_symlink() or not markers:
        return 1
    needles = [
        value
        for marker in markers
        for value in (
            marker.encode(),
            base64.b64encode(marker.encode()),
            marker.encode().hex().encode(),
        )
    ]
    overlap = max(map(len, needles)) - 1
    for path in root.rglob("*"):
        if path.is_symlink():
            return 1
        if not path.is_file():
            continue
        try:
            with path.open("rb") as stream:
                tail = b""
                while chunk := stream.read(65536):
                    content = tail + chunk
                    if any(needle in content for needle in needles):
                        return 1
                    tail = content[-overlap:]
        except OSError:
            return 1
    return 0


def artifact_gate() -> int:
    repository = Path(__file__).resolve().parents[2]
    try:
        markers = json.loads(
            (repository / "tests/fixtures/synthetic/privacy_canaries.json").read_text("utf-8")
        )
        result = inspect_artifacts(repository / "reports", markers)
    except (OSError, ValueError, TypeError):
        result = 1
    print("ARTIFACT_PRIVACY_FAILED" if result else "ARTIFACT_PRIVACY_PASSED")
    return result


if __name__ == "__main__":
    sys.exit(artifact_gate() if sys.argv[1:] == ["artifacts"] else main())
