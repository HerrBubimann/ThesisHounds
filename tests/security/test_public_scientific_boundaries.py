import hashlib
import json

import httpx
import pytest
import yaml

from infrastructure.scripts.sync_scientific import DATASETS, PublicSyncTransport, sync_subset
from infrastructure.scripts.validate_docker import check_public_sync
from tests.fixtures import ROOT

DATA = b"<dblp><article key='synthetic'><title>Public test</title></article></dblp>"
DIGEST = hashlib.sha256(DATA).hexdigest()


def test_public_sync_resumes_only_same_pinned_representation_and_keeps_manifest(tmp_path):
    dataset = next(iter(DATASETS))
    root = tmp_path / "sync"
    root.mkdir()
    (root / (dataset + ".part")).write_bytes(DATA[:10])
    (root / (dataset + ".state.json")).write_text(
        json.dumps(
            {
                "etag": '"synthetic-v1"',
                "sha256": DIGEST,
            }
        )
    )

    def handler(request):
        assert str(request.url) == DATASETS[dataset]
        assert (
            request.headers["Range"] == "bytes=10-"
            and request.headers["If-Range"] == '"synthetic-v1"'
        )
        return httpx.Response(
            206,
            stream=httpx.ByteStream(DATA[10:]),
            headers={
                "ETag": '"synthetic-v1"',
                "Content-Range": f"bytes 10-{len(DATA) - 1}/{len(DATA)}",
            },
        )

    manifest = sync_subset(
        root,
        dataset,
        DIGEST,
        version="test-v1",
        public_provenance_reviewed=True,
        transport=httpx.MockTransport(handler),
    )
    assert (root / "test-v1.xml").read_bytes() == DATA and manifest["sha256"] == DIGEST
    assert manifest["activation"] == "OFFLINE_REVIEW_REQUIRED"
    assert (root / "test-v1.manifest.json").is_file()


@pytest.mark.parametrize(
    "status,headers",
    [(302, {"Location": "https://example.invalid"}), (429, {"Retry-After": "3600"}), (200, {})],
)
def test_sync_rejects_redirects_rate_limit_or_wrong_checksum_without_activation(
    tmp_path, status, headers
):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, stream=httpx.ByteStream(DATA), headers=headers)

    root = tmp_path / "sync"
    with pytest.raises(ValueError):
        sync_subset(
            root,
            next(iter(DATASETS)),
            "b" * 64,
            version="v1",
            public_provenance_reviewed=True,
            transport=httpx.MockTransport(handler),
        )
    assert len(calls) == 1 and not (root / "v1.manifest.json").exists()


def test_sync_never_accepts_document_derived_query_arbitrary_url_or_repository_storage(tmp_path):
    for root, dataset in [
        (tmp_path / "cache", "private-document-doi"),
        (ROOT / ".runtime/cache", next(iter(DATASETS))),
    ]:
        with pytest.raises(ValueError):
            sync_subset(root, dataset, DIGEST, version="test", public_provenance_reviewed=True)
    compose = yaml.safe_load((ROOT / "compose.scientific-sync.yaml").read_text("utf-8"))
    service = compose["services"]["public-sync"]
    assert service["networks"] == ["public_scientific_sync"]
    assert len(service["volumes"]) == 2 and not any(
        "documents" in mount or "secrets" in mount or "config:" in mount
        for mount in service["volumes"]
    )
    script = (ROOT / "infrastructure/scripts/sync_scientific.py").read_text("utf-8")
    assert "from app." not in script and "import app." not in script


def test_sync_network_target_and_dns_pins_cannot_reach_private_runtime(monkeypatch):
    transport = PublicSyncTransport()
    try:
        with pytest.raises(ValueError, match="TARGET"):
            transport.handle_request(httpx.Request("GET", "http://127.0.0.1/private"))
        monkeypatch.setattr(
            "socket.getaddrinfo", lambda *a, **k: [(None, None, None, None, ("127.0.0.1", 443))]
        )
        with pytest.raises(ValueError, match="DNS"):
            transport.handle_request(httpx.Request("GET", next(iter(DATASETS.values()))))
    finally:
        transport.close()


def test_sync_compose_gate_rejects_private_network_mount_or_privilege():
    import copy

    config = yaml.safe_load((ROOT / "compose.scientific-sync.yaml").read_text("utf-8"))
    service = config["services"]["public-sync"]
    service["networks"] = {name: {} for name in service["networks"]}
    service["volumes"] = [
        {
            "source": str(ROOT / "infrastructure/scripts/sync_scientific.py"),
            "target": "/opt/public-tools/sync_scientific.py",
            "read_only": True,
            "type": "bind",
        },
        {"source": "public_metadata_staging", "target": "/public-staging", "type": "volume"},
    ]
    assert not check_public_sync(config)
    for mutation in (
        lambda c: c["services"]["public-sync"].update(networks={"inference": {}}),
        lambda c: c["services"]["public-sync"].update(privileged=True),
        lambda c: c["services"]["public-sync"]["volumes"].append(
            {"target": "/private", "type": "bind"}
        ),
        lambda c: c["services"]["public-sync"]["environment"].update(API_KEY="SYNTHETIC"),
    ):
        changed = copy.deepcopy(config)
        mutation(changed)
        assert check_public_sync(changed)
