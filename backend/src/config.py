from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection_cases: str = "neo_cases_v1"
    qdrant_collection_profiles: str = "neo_profiles_v1"
    qdrant_vector_size: int = 3072
    sqlite_db_url: str | None = None
    sqlite_db_path: str = str(Path(__file__).resolve().parents[1] / "data" / "intel.sqlite3")
    intel_summary_insights_limit: int = 5
    
    redis_url: str = "redis://localhost:6379"
    
    gemini_api_key: str | None = None
    gemini_chat_model: str = "gemini-2.0-flash"
    gemini_embedding_model: str = "models/gemini-embedding-001"
    tavily_api_key: str | None = None
    perplexity_api_key: str | None = None
    firecrawl_api_key: str | None = None
    radar_use_live_tools: bool = False
    radar_tool_timeout_sec: float = 8.0
    admin_token: str | None = None
    app_env: str = "development"
    allowed_origins_raw: str = "http://localhost:3000,http://127.0.0.1:3000"
    chat_audit_max_events: int = 2000
    chat_audit_retention_days: int = 7
    chat_audit_redis_key: str = "ops:chat_audit:v1"
    chat_alert_min_events: int = 20
    chat_alert_block_rate_warning: float = 0.20
    chat_alert_block_rate_critical: float = 0.35
    chat_alert_no_case_usage_warning: float = 0.40
    chat_alert_company_concentration_warning: float = 0.75
    rate_limit_window_sec: int = 60
    rate_limit_start_per_window: int = 20
    rate_limit_select_per_window: int = 30
    rate_limit_refine_per_window: int = 40
    rate_limit_chat_per_window: int = 60
    rate_limit_redis_key_prefix: str = "ops:rate_limit:v1"
    session_funnel_redis_key: str = "ops:session_funnel:v1"

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
