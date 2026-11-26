"""Validated environment configuration; no prompt or response persistence."""

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, HttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    deployment_mode: Literal["local", "university"] = "local"
    ollama_base_url: HttpUrl = HttpUrl("http://ollama:11434")
    university_ollama_hosts: list[str] = Field(default_factory=list)
    ollama_ca_file: Path | None = None
    ollama_auth_token: SecretStr | None = None
    enable_public_research: bool = False
    enable_internal_research: bool = False
    enable_ai_scoring: bool = False
    max_concurrent_model_requests: int = Field(default=1, ge=1, le=4)
    llm_model: str = Field(
        default="qwen3:8b",
        min_length=1,
        max_length=200,
        validation_alias=AliasChoices("ollama_default_model", "llm_model"),
    )
    llm_connect_timeout: float = Field(default=5, gt=0, le=60)
    llm_status_timeout: float = Field(default=10, gt=0, le=60)
    llm_chat_timeout: float = Field(
        default=300,
        gt=0,
        le=1800,
        validation_alias=AliasChoices("ollama_request_timeout", "llm_chat_timeout"),
    )
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

    @model_validator(mode="after")
    def require_internal_ollama(self) -> "Settings":
        value = self.ollama_base_url
        local = value.host in {"ollama", "localhost", "127.0.0.1", "::1"}
        approved_university = (
            self.deployment_mode == "university"
            and value.host in self.university_ollama_hosts
            and value.scheme == "https"
        )
        if (
            not (local or approved_university)
            or (self.deployment_mode == "local" and value.scheme != "http")
            or value.username
            or value.password
            or value.path not in {None, "/"}
            or value.query
            or value.fragment
        ):
            raise ValueError("Use local HTTP or an explicitly approved university HTTPS host.")
        if self.ollama_auth_token and value.scheme != "https":
            raise ValueError("Authentication requires verified HTTPS.")
        # These switches cannot activate unfinished or unapproved egress/scoring paths.
        if self.enable_public_research or self.enable_ai_scoring:
            raise ValueError("Public research and AI scoring are not released in this MVP.")
        return self
