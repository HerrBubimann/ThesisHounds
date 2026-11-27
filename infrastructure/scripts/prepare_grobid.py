"""Prepare an operator-provided GROBID config without external consolidation credentials."""

import argparse
from pathlib import Path

import yaml


def secure_config(source: dict) -> dict:
    # Copy by serializing safe primitives; the full upstream model configuration is retained.
    result = yaml.safe_load(yaml.safe_dump(source))
    grobid = result["grobid"]
    # This path is a dedicated container tmpfs, owned by UID 10001, mode 1770.
    grobid["temp"] = "/tmp"  # nosec B108
    grobid["concurrency"] = 1
    grobid["consolidation"] = {
        "service": "glutton",
        "glutton": {"url": "http://127.0.0.1:9", "timeoutSec": 1},
        "crossref": {"mailto": None, "token": None, "timeoutSec": 1},
    }
    grobid["proxy"] = {"host": None, "port": None}
    grobid["corsAllowedOrigins"] = ""
    grobid.setdefault("pdf", {}).setdefault("pdfalto", {}).update(memoryLimitMb=2048, timeoutSec=60)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve() or args.output.exists():
        raise ValueError("OUTPUT_MUST_BE_NEW")
    data = args.source.read_bytes()
    if len(data) > 1_000_000:
        raise ValueError("CONFIG_TOO_LARGE")
    prepared = secure_config(yaml.safe_load(data))
    with args.output.open("x", encoding="utf-8") as stream:
        yaml.safe_dump(prepared, stream, sort_keys=False)
    print("GROBID_CONFIGURATION_PREPARED_NOT_DEPLOYED")


if __name__ == "__main__":
    main()
