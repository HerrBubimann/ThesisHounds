"""Sweep only expired, UUID-named document artifacts; never traverse directories."""

from pathlib import Path
from time import time
from uuid import UUID


def purge_orphan_documents(
    root: Path, retention_seconds: float, *, clock: float | None = None
) -> int:
    if retention_seconds <= 0:
        raise ValueError("RETENTION_INVALID")
    if root.is_symlink():
        raise ValueError("STORE_SYMLINK_DENIED")
    if not root.exists():
        return 0
    cutoff, count = (time() if clock is None else clock) - retention_seconds, 0
    for path in root.glob("*.json"):
        try:
            if str(UUID(path.stem)) != path.stem or path.is_symlink() or not path.is_file():
                continue
            if path.stat().st_mtime < cutoff:
                path.unlink()
                count += 1
        except ValueError:
            continue
    return count
