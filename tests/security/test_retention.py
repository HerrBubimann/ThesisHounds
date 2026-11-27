import os
from uuid import uuid4

import pytest
from app.security.retention_service import purge_orphan_documents
from app.services.document_store import DocumentStore


def test_orphan_sweep_only_deletes_expired_uuid_json_documents(tmp_path):
    store = DocumentStore(tmp_path)
    old, fresh = str(uuid4()), str(uuid4())
    store.create_demo(old)
    store.create_demo(fresh)
    os.utime(store.path(old), (10, 10))
    (tmp_path / "operator-config.json").write_text("synthetic", "utf-8")
    assert purge_orphan_documents(tmp_path, 100, clock=200) == 1
    assert not store.path(old).exists() and store.path(fresh).exists()
    assert (tmp_path / "operator-config.json").exists()


def test_invalid_ids_and_retention_fail_closed(tmp_path):
    with pytest.raises(ValueError):
        DocumentStore(tmp_path).path("../../other")
    with pytest.raises(ValueError):
        purge_orphan_documents(tmp_path, 0)
    assert purge_orphan_documents(tmp_path / "absent", 100) == 0
