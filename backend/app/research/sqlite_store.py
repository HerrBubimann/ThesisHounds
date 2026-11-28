"""Versioned PUBLIC metadata storage underneath the existing snapshot/cache contract."""

import hashlib
import json
import os
import re
import shutil
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.research.provider_registry import LocalResearchCache, MetadataRecord

MAX_STORE_BYTES = 256_000_000
MAX_DATABASE_BYTES = 96_000_000
VERSION = re.compile(r"[a-z0-9][a-z0-9_-]{0,79}")


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def query_records(database, sql, values):
    # Only fixed SQL statements are supplied by LocalResearchCache; terms are parameters.
    with closing(
        sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    ) as db:
        db.execute("PRAGMA trusted_schema=OFF")
        db.execute("PRAGMA query_only=ON")
        return [MetadataRecord.model_validate_json(row[0]) for row in db.execute(sql, values)]


def _version(root, version):
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("SNAPSHOT_VERSION_DENIED")
    path = root / "versions" / version
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("SNAPSHOT_STORAGE_BOUNDARY")
    return path


def _manifest(root, version):
    path = _version(root, version)
    manifest_path, database = path / "manifest.json", path / "metadata.sqlite"
    if any(p.is_symlink() or not p.is_file() for p in (manifest_path, database)):
        raise ValueError("SNAPSHOT_VERSION_FILES_DENIED")
    if manifest_path.stat().st_size > 64000 or database.stat().st_size > MAX_DATABASE_BYTES:
        raise ValueError("SNAPSHOT_VERSION_SIZE_LIMIT")
    value = json.loads(manifest_path.read_text("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("SNAPSHOT_MANIFEST_INVALID")
    if (
        (value.get("kind"), value.get("classification"), value.get("version"))
        != ("REVIEWED_PUBLIC_SQLITE_METADATA", "PUBLIC", version)
        or not value.get("reviewer")
        or not value.get("license_id")
    ):
        raise ValueError("PUBLIC_SNAPSHOT_PROVENANCE_REQUIRED")
    if value.get("updated_at") is not None:
        stamp = datetime.fromisoformat(value["updated_at"])
        if stamp.tzinfo is None or stamp > datetime.now(UTC):
            raise ValueError("SNAPSHOT_TIMESTAMP_DENIED")
    if file_digest(database) != value["database_sha256"]:
        raise ValueError("PUBLIC_SNAPSHOT_DIGEST_MISMATCH")
    return value


def activate_version(root, version):
    """Atomic activation/rollback; existing cache instances stay pinned to their version."""
    from app.research.snapshot_store import checked_root

    root = checked_root(Path(root))
    value = _manifest(root, version)
    pointer = {
        "version": version,
        "manifest_sha256": file_digest(_version(root, version) / "manifest.json"),
    }
    temp = root / (".current-" + uuid4().hex)
    try:
        with temp.open("x", encoding="utf-8") as stream:
            json.dump(pointer, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, root / "CURRENT.json")
    finally:
        temp.unlink(missing_ok=True)
    return value


def load_versioned_cache(root):
    pointer = root / "CURRENT.json"
    if pointer.is_symlink() or not pointer.is_file() or pointer.stat().st_size > 4096:
        raise ValueError("SNAPSHOT_POINTER_DENIED")
    selection = json.loads(pointer.read_text("utf-8"))
    value = _manifest(root, selection["version"])
    path = _version(root, selection["version"])
    if file_digest(path / "manifest.json") != selection["manifest_sha256"]:
        raise ValueError("SNAPSHOT_MANIFEST_DIGEST_MISMATCH")
    return LocalResearchCache(database=path / "metadata.sqlite", manifest=value)


def install_version(
    root,
    records,
    *,
    version,
    source_sha256,
    provenance,
    reviewer,
    license_id,
    updated_at,
    public_provenance_checked=False,
):
    from app.research.snapshot_store import checked_root

    root = checked_root(Path(root))
    target = _version(root, version)
    if not public_provenance_checked or not reviewer or not provenance or not license_id:
        raise ValueError("PUBLIC_SNAPSHOT_REVIEW_REQUIRED")
    if not re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        raise ValueError("SNAPSHOT_SOURCE_DIGEST_REQUIRED")
    if updated_at is not None and (updated_at.tzinfo is None or updated_at > datetime.now(UTC)):
        raise ValueError("SNAPSHOT_TIMESTAMP_DENIED")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    paths = list(root.rglob("*"))
    if any(p.is_symlink() for p in paths):
        raise ValueError("SNAPSHOT_STORAGE_BOUNDARY")
    used = sum(p.stat().st_size for p in paths if p.is_file())
    if used + MAX_DATABASE_BYTES > MAX_STORE_BYTES:
        raise ValueError("SNAPSHOT_STORAGE_LIMIT")
    if target.exists() or len(list((root / "versions").glob("*"))) >= 8:
        raise ValueError("SNAPSHOT_VERSION_EXISTS_OR_LIMIT")
    lock = root / ".import.lock"
    descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    stage = root / (".stage-" + uuid4().hex)
    try:
        stage.mkdir(mode=0o700)
        database = stage / "metadata.sqlite"
        with closing(sqlite3.connect(database)) as db, db:
            db.execute("PRAGMA page_size=4096")
            db.execute("PRAGMA max_page_count=" + str(MAX_DATABASE_BYTES // 4096))
            db.execute("PRAGMA cache_size=-4096")
            db.execute(
                "CREATE TABLE records (id INTEGER PRIMARY KEY, doi TEXT, isbn TEXT, "
                "provider TEXT, provider_id TEXT, year INTEGER, source_type TEXT, record_json TEXT)"
            )
            db.execute("CREATE INDEX doi_idx ON records(doi)")
            db.execute("CREATE INDEX isbn_idx ON records(isbn)")
            db.execute("CREATE VIRTUAL TABLE records_fts USING fts5(title, authors)")
            count, providers, source_snapshots = 0, set(), set()
            release_dois, selections = set(), set()
            for record in records:
                record = MetadataRecord.model_validate(record.model_dump())
                count += 1
                if count > 100_000 or not (record.doi or record.isbn or record.provider_id):
                    raise ValueError("SNAPSHOT_RECORD_LIMIT_OR_ID_MISSING")
                providers.add(record.provider)
                source_snapshots.add(record.snapshot_sha256)
                if record.source_release_doi:
                    release_dois.add(record.source_release_doi)
                if record.selection_sha256:
                    selections.add(record.selection_sha256)
                record.snapshot_version = version
                db.execute(
                    "INSERT INTO records VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        count,
                        record.doi,
                        record.isbn,
                        record.provider,
                        record.provider_id,
                        record.year,
                        record.source_type,
                        record.model_dump_json(),
                    ),
                )
                db.execute(
                    "INSERT INTO records_fts(rowid,title,authors) VALUES (?, ?, ?)",
                    (count, record.title, " ".join(record.authors)),
                )
            if not count:
                raise ValueError("SNAPSHOT_EMPTY_IMPORT")
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("SNAPSHOT_DATABASE_INVALID")
        manifest = {
            "kind": "REVIEWED_PUBLIC_SQLITE_METADATA",
            "classification": "PUBLIC",
            "version": version,
            "source_sha256": source_sha256,
            "database_sha256": file_digest(database),
            "license_id": license_id,
            "record_count": count,
            "source_snapshots": sorted(source_snapshots),
            "source_release_dois": sorted(release_dois),
            "selection_sha256": sorted(selections),
            "providers": sorted(providers),
            "provenance": provenance,
            "reviewer": reviewer,
            "updated_at": updated_at.isoformat() if updated_at is not None else None,
            "imported_at": datetime.now(UTC).isoformat(),
            "sqlite_version": sqlite3.sqlite_version,
        }
        (stage / "manifest.json").write_text(json.dumps(manifest), "utf-8")
        target.parent.mkdir(exist_ok=True, mode=0o700)
        stage.rename(target)
        activate_version(root, version)
        return manifest
    finally:
        os.close(descriptor)
        lock.unlink(missing_ok=True)
        # Only this import's generated staging directory is eligible for cleanup.
        if stage.exists() and stage.resolve().is_relative_to(root.resolve()):
            shutil.rmtree(stage)
