"""Validated application settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from ``OPSGRAPH_`` environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="OPSGRAPH_",
        env_file=".env",
        extra="ignore",
    )

    profile: Literal["test", "local", "aws-demo"] = "local"
    model_provider: Literal["fake", "ollama", "bedrock"] = "fake"
    database_url: str = "sqlite+pysqlite:///:memory:"
    max_tool_calls: int = Field(default=6, ge=1, le=6)
    local_admin_token: str = Field(default="local-development-only", min_length=8)
    sqlite_database_path: Path | None = None
    max_upload_bytes: int = Field(default=2_000_000, ge=1, le=10_000_000)
    max_pdf_pages: int = Field(default=20, ge=1, le=100)
    response_cache_seconds: int = Field(default=300, ge=0, le=3_600)
    telemetry_enabled: bool = False
    telemetry_exporter: Literal["console", "otlp"] = "console"
    telemetry_service_name: str = "opsgraph-api"
    otel_exporter_otlp_endpoint: str = "http://127.0.0.1:4318/v1/traces"
    evaluation_report_path: Path | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:4b"
    aws_region: str = "ap-southeast-2"
    bedrock_model_id: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one validated settings instance per process."""

    return Settings()
