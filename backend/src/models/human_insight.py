from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


InsightCategory = Literal["pain_points", "decision_makers", "sentiment"]


class StructuredInsightItem(BaseModel):
    category: InsightCategory
    value: str = Field(..., min_length=1, max_length=500)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class HumanInsightCreate(BaseModel):
    seller_id: str = Field(..., min_length=2, max_length=100)
    text: str = Field(..., min_length=10, max_length=4000)
    source: str = Field(default="sales_form", min_length=2, max_length=50)

    @field_validator("source", mode="before")
    @classmethod
    def _normalize_source(cls, value: str) -> str:
        return str(value).strip().lower()


class HumanInsightStored(BaseModel):
    id: str
    company_id: str
    seller_id: str
    raw_text: str
    structured_payload: list[StructuredInsightItem]
    source: str
    created_at: str
    parser_version: str = "v1"


class CompanyProfileStored(BaseModel):
    company_id: str
    area: str
    profile_payload: dict
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
