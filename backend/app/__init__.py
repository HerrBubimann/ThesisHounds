"""Disable optional exporters before importing orchestration/model libraries."""

import os

for _name in ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2", "HF_HUB_ENABLE_HF_TRANSFER"):
    os.environ[_name] = "false"
for _name in (
    "HF_HUB_OFFLINE",
    "TRANSFORMERS_OFFLINE",
    "HF_HUB_DISABLE_TELEMETRY",
    "DO_NOT_TRACK",
):
    os.environ[_name] = "1"
os.environ["OTEL_SDK_DISABLED"] = "true"
