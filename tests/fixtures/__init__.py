"""Shared synthetic test fixtures. Never place real theses or personal data here."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"

# Synthetic Ollama model entry used by HTTP-level mocks.
MODEL = {"name": "qwen3:8b", "size": 5000000000, "digest": "test-digest"}
