"""Validated environment configuration; no prompt or response persistence."""

from pathlib import Path

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: HttpUrl = HttpUrl("http://ollama:11434")
    llm_model: str = Field(default="qwen3:8b", min_length=1, max_length=200)
    llm_connect_timeout: float = Field(default=5, gt=0, le=60)
    llm_status_timeout: float = Field(default=10, gt=0, le=60)
    llm_chat_timeout: float = Field(default=300, gt=0, le=1800)
    llm_max_tokens: int = Field(default=512, ge=1, le=4096)
    llm_context_length: int = Field(default=4096, ge=512, le=32768)
    config_dir: Path = Path(__file__).resolve().parents[2] / "config"
    document_store_dir: Path = Path(".runtime/documents")

    @field_validator("llm_model")
    @classmethod
    def require_local_model(cls, value: str) -> str:
        value = value.strip()
        if not value or "/" in value or ":cloud" in value or value.endswith("-cloud"):
            raise ValueError("Use a local model tag, for example qwen3:8b.")
        return value

    @field_validator("ollama_base_url")
    @classmethod
    def require_internal_ollama(cls, value: HttpUrl) -> HttpUrl:
        # Explicit allowlist also prevents accidental configuration of an external API.
        if (
            value.scheme != "http"
            or value.host not in {"ollama", "localhost", "127.0.0.1", "::1"}
            or value.username
            or value.password
            or value.path not in {None, "/"}
            or value.query
            or value.fragment
        ):
            raise ValueError("Ollama must use an internal or loopback HTTP address.")
        return value
