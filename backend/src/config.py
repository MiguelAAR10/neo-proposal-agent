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
    admin_token: str | None = None
    app_env: str = "development"
    allowed_origins_raw: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_non_local_env(self) -> bool:
        return self.app_env.strip().lower() in {"prod", "production", "staging"}

    @property
    def allowed_origins(self) -> list[str]:
        values = [v.strip() for v in self.allowed_origins_raw.split(",") if v.strip()]
        return values or ["http://localhost:3000"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings to avoid repeated environment parsing."""
    return Settings()
