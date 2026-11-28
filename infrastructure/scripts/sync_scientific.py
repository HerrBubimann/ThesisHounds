"""Public-only operator downloader. No backend imports, document inputs, API keys or arbitrary URL.

Run in the separate compose.scientific-sync.yaml environment, never the private runtime.
Only the fixed public DBLP teaching subset is supported; acquisition does not activate data.
"""

import argparse
import hashlib
import ipaddress
import json
import os
import re
import shutil
import socket
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx

DATASETS = {"dblp-attention-example": "https://dblp.org/rec/conf/nips/VaswaniSPUJGKP17.xml"}
MAX_BYTES = 1_000_000


class PublicSyncTransport(httpx.BaseTransport):
    def __init__(self):
        self.transport = httpx.HTTPTransport(retries=0, trust_env=False, verify=True)

    def handle_request(self, request):
        if request.method != "GET" or str(request.url) not in DATASETS.values():
            raise ValueError("PUBLIC_SYNC_TARGET_DENIED")
        addresses = {
            row[4][0] for row in socket.getaddrinfo(request.url.host, 443, type=socket.SOCK_STREAM)
        }
        if not addresses or not all(ipaddress.ip_address(a).is_global for a in addresses):
            raise ValueError("PUBLIC_SYNC_DNS_DENIED")
        request.extensions["sni_hostname"] = request.url.host
        request.url = request.url.copy_with(host=sorted(addresses)[0])
        return self.transport.handle_request(request)

    def close(self):
        self.transport.close()


def sync_subset(
    root,
    dataset,
    expected_sha256,
    *,
    version,
    public_provenance_reviewed=False,
    transport=None,
    now=time.time,
):
    if dataset not in DATASETS or not public_provenance_reviewed:
        raise ValueError("PUBLIC_SYNC_REVIEW_REQUIRED")
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256) or not re.fullmatch(
        r"[a-z0-9_-]{1,80}", version
    ):
        raise ValueError("PUBLIC_SYNC_DIGEST_OR_VERSION_DENIED")
    root = Path(root).absolute()
    repository = Path(__file__).resolve().parents[2]
    if not (repository / "pyproject.toml").is_file():
        repository = Path("/app")  # Separate container layout; never stage inside the app image.
    if root.resolve().is_relative_to(repository) or any(
        p.is_symlink() for p in (root, *root.parents)
    ):
        raise ValueError("PUBLIC_SYNC_STORAGE_BOUNDARY")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if any(p.is_symlink() or not p.is_file() for p in root.iterdir()):
        raise ValueError("PUBLIC_SYNC_STORAGE_BOUNDARY")
    if sum(p.stat().st_size for p in root.iterdir()) + MAX_BYTES > 16_000_000:
        raise ValueError("PUBLIC_SYNC_STORAGE_LIMIT")
    if shutil.disk_usage(root).free < MAX_BYTES * 2:
        raise ValueError("PUBLIC_SYNC_FREE_SPACE_LIMIT")
    part, state_path = root / (dataset + ".part"), root / (dataset + ".state.json")
    target = root / (version + ".xml")
    if target.exists():
        raise ValueError("PUBLIC_SYNC_VERSION_EXISTS")
    lock = root / ".sync.lock"
    descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        state = json.loads(state_path.read_text("utf-8")) if state_path.exists() else {}
        if now() < state.get("next_request_at", 0):
            raise ValueError("PUBLIC_SYNC_RATE_LIMIT")
        if state.get("sha256") not in {None, expected_sha256}:
            raise ValueError("PUBLIC_SYNC_RESUME_IDENTITY_MISMATCH")
        size = part.stat().st_size if part.exists() else 0
        if size > MAX_BYTES:
            raise ValueError("PUBLIC_SYNC_SIZE_LIMIT")
        headers = {"User-Agent": "ThesisHounds-PublicSubset/0.2", "Accept-Encoding": "identity"}
        if size:
            if not state.get("etag") or state["etag"].startswith("W/"):
                raise ValueError("PUBLIC_SYNC_RESUME_REQUIRES_STRONG_ETAG")
            headers.update(Range=f"bytes={size}-", **{"If-Range": state["etag"]})
        state.update(sha256=expected_sha256, next_request_at=now() + 3)
        state_path.write_text(json.dumps(state), "utf-8")
        with httpx.Client(
            transport=transport or PublicSyncTransport(),
            trust_env=False,
            follow_redirects=False,
            timeout=20,
        ) as client:
            with client.stream("GET", DATASETS[dataset], headers=headers) as response:
                if response.status_code == 429:
                    delay = response.headers.get("Retry-After", "60")
                    state["next_request_at"] = now() + max(3, int(delay) if delay.isdigit() else 60)
                    state_path.write_text(json.dumps(state), "utf-8")
                    raise ValueError("PUBLIC_SYNC_RATE_LIMIT")
                if response.status_code not in ({206} if size else {200}):
                    raise ValueError("PUBLIC_SYNC_HTTP_OR_RANGE_DENIED")
                if size and (
                    response.headers.get("ETag") != state["etag"]
                    or not response.headers.get("Content-Range", "").startswith(f"bytes {size}-")
                ):
                    raise ValueError("PUBLIC_SYNC_RESUME_IDENTITY_MISMATCH")
                state["etag"] = response.headers.get("ETag", "")
                modified = response.headers.get("Last-Modified")
                try:
                    state["source_updated_at"] = (
                        parsedate_to_datetime(modified).isoformat() if modified else None
                    )
                except (ValueError, TypeError, OverflowError):
                    state["source_updated_at"] = None
                state_path.write_text(json.dumps(state), "utf-8")
                with part.open("ab" if size else "wb") as stream:
                    for chunk in response.iter_raw():
                        size += len(chunk)
                        if size > MAX_BYTES:
                            raise ValueError("PUBLIC_SYNC_SIZE_LIMIT")
                        stream.write(chunk)
        digest = hashlib.sha256(part.read_bytes()).hexdigest()
        if digest != expected_sha256:
            raise ValueError("PUBLIC_SYNC_DIGEST_MISMATCH")
        # Original bytes are retained. The offline importer validates XML before activation.
        os.replace(part, target)
        manifest = {
            "provider": "dblp",
            "source": DATASETS[dataset],
            "version": version,
            "sha256": digest,
            "license_id": "CC0-1.0",
            "bytes": size,
            "updated_at": state.get("source_updated_at"),
            "downloaded_at": datetime.now(UTC).isoformat(),
            "extent": "ONE_PUBLIC_RECORD",
            "classification": "PUBLIC",
            "activation": "OFFLINE_REVIEW_REQUIRED",
        }
        temp = root / (version + ".manifest.tmp")
        temp.write_text(json.dumps(manifest), "utf-8")
        os.replace(temp, root / (version + ".manifest.json"))
        return manifest
    finally:
        os.close(descriptor)
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=sorted(DATASETS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--public-provenance-reviewed", action="store_true")
    args = parser.parse_args()
    try:
        result = sync_subset(
            args.output,
            args.dataset,
            args.sha256,
            version=args.version,
            public_provenance_reviewed=args.public_provenance_reviewed,
        )
        print(json.dumps({"status": "PUBLIC_SUBSET_DOWNLOADED", "bytes": result["bytes"]}))
        return 0
    except (OSError, ValueError, httpx.HTTPError):
        print('{"status":"PUBLIC_SYNC_REJECTED"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
