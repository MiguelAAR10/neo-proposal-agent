from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    gemini_api_key: str | None = None
    gemini_embedding_model: str = "models/text-embedding-004"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings to avoid repeated environment parsing."""
    return Settings()
