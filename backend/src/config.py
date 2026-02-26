from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection_cases: str = "neo_cases_v1"
    qdrant_collection_profiles: str = "neo_profiles_v1"
    
    redis_url: str = "redis://localhost:6379"
    
    gemini_api_key: str | None = None
    gemini_embedding_model: str = "models/gemini-embedding-001"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings to avoid repeated environment parsing."""
    return Settings()
