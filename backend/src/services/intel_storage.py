from __future__ import annotations

from src.config import get_settings
from src.repositories.sqlite_repositories import SQLiteCompanyProfileRepository, SQLiteHumanInsightRepository

_settings = get_settings()

human_insight_repository = SQLiteHumanInsightRepository(_settings.sqlite_db_path)
company_profile_repository = SQLiteCompanyProfileRepository(_settings.sqlite_db_path)
