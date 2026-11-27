"""Offline operator import of explicitly public institutional sources; no production activation."""

import argparse
import json
from pathlib import Path

import yaml

from app.knowledge.importer import ImportAuthority, KnowledgeStore, safe_yaml
from app.knowledge.schemas import SourceDocument
from app.security.audit_service import disable_content_logging


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("metadata", type=Path, help="Reviewed source metadata JSON/YAML")
    parser.add_argument(
        "--store", type=Path, required=True, help="Dedicated directory OUTSIDE repository"
    )
    parser.add_argument(
        "--curator", required=True, help="Operator identifier, no university role assertion"
    )
    parser.add_argument("--public-provenance-reviewed", action="store_true")
    args = parser.parse_args()
    disable_content_logging()
    try:
        if (
            not args.public_provenance_reviewed
            or args.source.is_symlink()
            or args.metadata.is_symlink()
        ):
            raise ValueError("IMPORT_NOT_AUTHORIZED")
        if args.metadata.stat().st_size > 65536 or args.source.stat().st_size > 8_000_000:
            raise ValueError("IMPORT_TOO_LARGE")
        metadata = SourceDocument.model_validate(safe_yaml(args.metadata.read_text("utf-8-sig")))
        result = KnowledgeStore(args.store).import_public(
            args.source.read_bytes(),
            args.source.suffix,
            metadata,
            ImportAuthority(args.curator, curator=True, public_provenance_checked=True),
        )
        print(
            json.dumps(
                {
                    "status": "CANDIDATE_IMPORTED",
                    "sha256": result["sha256"],
                    "release": "CANDIDATE",
                    "warnings": result["warnings"],
                }
            )
        )
        return 0
    except (OSError, ValueError, KeyError, RecursionError, yaml.YAMLError):
        # No filenames, imported text or validation inputs in general console logs.
        print('{"status":"IMPORT_REJECTED"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
