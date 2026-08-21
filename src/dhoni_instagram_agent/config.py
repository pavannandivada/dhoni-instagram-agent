"""Typed, environment-only application configuration."""

from __future__ import annotations

from typing import Literal
from urllib.parse import quote

from pydantic import SecretStr
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

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "dhoni_agent"
    postgres_user: str
    postgres_password: SecretStr

    gemini_api_key: SecretStr
    openai_api_key: SecretStr
    anthropic_api_key: SecretStr
    instagram_access_token: SecretStr
    instagram_business_account_id: str

    embedding_model: str = "gemini-embedding-2"
    embedding_dimension: int = 768

    generation_model: str = "gemini-3.7-flash"
    generation_fallback_model: str = "gemini-3.6-flash"
    
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"

    @property
    def database_url(self) -> str:
        """Build a connection URL."""

        user = quote(self.postgres_user, safe="")
        password = quote(
            self.postgres_password.get_secret_value(),
            safe="",
        )

        return (
            f"postgresql://{user}:{password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )
