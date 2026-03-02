from __future__ import annotations

from typing import NotRequired, TypedDict


class RadarState(TypedDict):
    industry_target: str
    raw_signals: list[str]
    critical_triggers_found: list[str]
    industry_radiography: dict
    force_mock_tools: NotRequired[bool]
    signals_structured: NotRequired[list[dict]]
    trigger_objects: NotRequired[list[dict]]
    error: NotRequired[str]
