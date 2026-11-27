"""Operator import of small PUBLIC metadata subsets, outside the repository; no HTTP client."""

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from app.research.provider_registry import PROVIDERS, LocalResearchCache, import_metadata

MAX_SNAPSHOTS = 32


def checked_root(root: Path):
    repository = Path(__file__).resolve().parents[3]
    if root.resolve().is_relative_to(repository) or any(
        p.is_symlink() for p in (root, *root.parents)
    ):
        raise ValueError("SNAPSHOT_STORAGE_BOUNDARY")
    return root


def store_snapshot(
    root,
    data,
    provider,
    *,
    reviewer,
    provenance,
    public_provenance_checked=False,
    retrieved_at=None,
):
    root = checked_root(root)
    if not reviewer or not public_provenance_checked:
        raise ValueError("PUBLIC_SNAPSHOT_REVIEW_REQUIRED")
    timestamp = retrieved_at or datetime.now(UTC)
    records = import_metadata(
        data,
        provider,
        retrieved_at=timestamp,
        provenance=provenance,
        public_provenance_checked=True,
    )
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if len(list(root.iterdir())) >= MAX_SNAPSHOTS:
        raise ValueError("PUBLIC_SNAPSHOT_COUNT_LIMIT")
    digest = hashlib.sha256(data).hexdigest()
    wrapper = {
        "kind": "REVIEWED_PUBLIC_METADATA",
        "classification": "PUBLIC",
        "provider": provider,
        "reviewer": reviewer,
        "provenance": provenance,
        "retrieved_at": timestamp.isoformat(),
        "sha256": digest,
        "raw_utf8": data.decode("utf-8-sig"),
    }
    # Preserve a BOM if present: the checksum always refers to the original bytes.
    wrapper["utf8_bom"] = data.startswith(b"\xef\xbb\xbf")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(
        os.open(root / (digest + ".json"), flags, 0o600), "w", encoding="utf-8"
    ) as stream:
        json.dump(wrapper, stream, ensure_ascii=False)
    return {"status": "PUBLIC_METADATA_IMPORTED", "records": len(records), "sha256": digest}


def load_cache(root: Path | None):
    if root is None:
        return LocalResearchCache()
    root = checked_root(root)
    files = sorted(root.iterdir())
    if len(files) > MAX_SNAPSHOTS:
        raise ValueError("PUBLIC_SNAPSHOT_COUNT_LIMIT")
    records = []
    for path in files:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16_100_000:
            raise ValueError("PUBLIC_SNAPSHOT_FILE_DENIED")
        wrapper = json.loads(path.read_text("utf-8"))
        if (
            wrapper.get("kind") != "REVIEWED_PUBLIC_METADATA"
            or wrapper.get("classification") != "PUBLIC"
            or not wrapper.get("reviewer")
        ):
            raise ValueError("PUBLIC_SNAPSHOT_PROVENANCE_REQUIRED")
        data = wrapper["raw_utf8"].encode("utf-8-sig" if wrapper.get("utf8_bom") else "utf-8")
        digest = hashlib.sha256(data).hexdigest()
        if digest != wrapper["sha256"] or path.name != digest + ".json":
            raise ValueError("PUBLIC_SNAPSHOT_DIGEST_MISMATCH")
        records.extend(
            import_metadata(
                data,
                wrapper["provider"],
                retrieved_at=datetime.fromisoformat(wrapper["retrieved_at"]),
                provenance=wrapper["provenance"],
                public_provenance_checked=True,
            )
        )
        if len(records) > 10_000:
            raise ValueError("PUBLIC_CACHE_RECORD_LIMIT")
    return LocalResearchCache(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--public-provenance-reviewed", action="store_true")
    args = parser.parse_args()
    try:
        if args.source.is_symlink() or args.source.stat().st_size > 8_000_000:
            raise ValueError("SNAPSHOT_INPUT_DENIED")
        result = store_snapshot(
            args.store,
            args.source.read_bytes(),
            args.provider,
            reviewer=args.reviewer,
            provenance=args.provenance,
            public_provenance_checked=args.public_provenance_reviewed,
        )
        print(json.dumps(result))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        print('{"status":"PUBLIC_METADATA_IMPORT_REJECTED"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
