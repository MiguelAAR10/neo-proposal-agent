from __future__ import annotations

from typing import Any, Callable

from src.config import get_settings
from src.repositories.sqlite_repositories import (
    SQLiteCompanyProfileRepository,
    SQLiteHumanInsightRepository,
    SQLiteIndustryRadarRepository,
)


def _get_database_url_or_path() -> str:
    settings = get_settings()
    return settings.sqlite_db_url or settings.sqlite_db_path


class _LazyRepositoryProxy:
    def __init__(self, factory: Callable[[], Any]) -> None:
        self._factory = factory
        self._target: Any | None = None

    def _resolve(self) -> Any:
        if self._target is None:
            self._target = self._factory()
        return self._target

    def __getattr__(self, item: str) -> Any:
        return getattr(self._resolve(), item)


human_insight_repository = _LazyRepositoryProxy(
    lambda: SQLiteHumanInsightRepository(_get_database_url_or_path())
)
company_profile_repository = _LazyRepositoryProxy(
    lambda: SQLiteCompanyProfileRepository(_get_database_url_or_path())
)
industry_radar_repository = _LazyRepositoryProxy(
    lambda: SQLiteIndustryRadarRepository(_get_database_url_or_path())
)
