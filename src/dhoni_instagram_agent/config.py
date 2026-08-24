"""Typed, environment-aware application configuration."""

from __future__ import annotations

from typing import Literal
from urllib.parse import quote

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = "INFO"

    # Database
    #
    # Production can provide DATABASE_URL directly.
    # Local development/tests can continue using the legacy POSTGRES_* settings.
    database_url_env: SecretStr | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
    )

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "dhoni_agent"
    postgres_user: str | None = None
    postgres_password: SecretStr | None = None

    # LLM providers
    gemini_api_key: SecretStr = SecretStr("")
    openai_api_key: SecretStr = SecretStr("")
    anthropic_api_key: SecretStr = SecretStr("")

    # Instagram
    instagram_access_token: SecretStr = SecretStr("")
    instagram_business_account_id: str = ""

    # Embeddings / generation
    embedding_model: str = "gemini-embedding-2"
    embedding_dimension: int = 768
    generation_model: str = "gemini-3.7-flash"
    generation_fallback_model: str = "gemini-3.6-flash"

    # Optional local Ollama support retained for development compatibility.
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"

    @property
    def database_url(self) -> str:
        """Return explicit DATABASE_URL or build the local PostgreSQL URL."""
        if self.database_url_env is not None:
            return self.database_url_env.get_secret_value()

        if self.postgres_user is None or self.postgres_password is None:
            raise ValueError(
                "DATABASE_URL is not set and POSTGRES_USER/POSTGRES_PASSWORD "
                "are required to build the local database URL."
            )

        user = quote(self.postgres_user, safe="")
        password = quote(
            self.postgres_password.get_secret_value(),
            safe="",
        )

        return (
            f"postgresql://{user}:{password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )
