from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


RadarSignalType = Literal["market_trend", "regulatory", "financial_ticker", "analyst_report"]
TriggerType = Literal["new_law", "stock_drop", "analyst_alert", "budget_shift", "other"]
TriggerSeverity = Literal["high", "medium", "low"]


class RadarRunRequest(BaseModel):
    industry_target: str = Field(..., min_length=2, max_length=100)
    force_mock_tools: bool = False

    @field_validator("industry_target")
    @classmethod
    def _normalize_industry(cls, value: str) -> str:
        cleaned = " ".join(str(value).split())
        if not cleaned:
            raise ValueError("industry_target vacio")
        return cleaned


class RadarSignal(BaseModel):
    source: str = Field(..., min_length=2, max_length=80)
    signal_type: RadarSignalType
    content: str = Field(..., min_length=8, max_length=2000)
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    captured_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IndustryTrigger(BaseModel):
    trigger_type: TriggerType
    title: str = Field(..., min_length=4, max_length=180)
    rationale: str = Field(..., min_length=8, max_length=400)
    severity: TriggerSeverity = "medium"
    evidence: str = Field(..., min_length=8, max_length=500)


class IndustryRadiography(BaseModel):
    industry_target: str = Field(..., min_length=2, max_length=100)
    executive_summary: str = Field(..., min_length=16, max_length=1200)
    critical_triggers: list[IndustryTrigger] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    sources_checked: list[str] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IndustryRadiographyStored(BaseModel):
    industry_target: str
    profile_payload: dict
    triggers_payload: list[dict]
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
