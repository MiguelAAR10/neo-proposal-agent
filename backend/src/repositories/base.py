from __future__ import annotations

from abc import ABC, abstractmethod

from src.models.human_insight import CompanyProfileStored, HumanInsightStored, StructuredInsightItem


class HumanInsightRepository(ABC):
    @abstractmethod
    def save(
        self,
        *,
        company_id: str,
        author: str,
        department: str,
        sentiment: str,
        raw_text: str,
        structured_payload: list[StructuredInsightItem],
        source: str,
        parser_version: str = "v1",
    ) -> HumanInsightStored:
        raise NotImplementedError

    @abstractmethod
    def list_recent(self, *, company_id: str, limit: int = 5) -> list[HumanInsightStored]:
        raise NotImplementedError


class CompanyProfileRepository(ABC):
    @abstractmethod
    def get_profile(self, *, company_id: str, area: str) -> CompanyProfileStored | None:
        raise NotImplementedError

    @abstractmethod
    def upsert_profile(self, *, company_id: str, area: str, profile_payload: dict) -> CompanyProfileStored:
        raise NotImplementedError
