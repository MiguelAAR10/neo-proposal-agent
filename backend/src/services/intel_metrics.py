from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class IntelMetricsStore:
    _lock: Lock = field(default_factory=Lock)
    _parse_ms: list[int] = field(default_factory=list)
    _store_ms: list[int] = field(default_factory=list)
    _success: int = 0
    _errors: Counter[str] = field(default_factory=Counter)
    _max_samples: int = 1000

    def _append_sample(self, values: list[int], value: int) -> None:
        values.append(max(0, int(value)))
        if len(values) > self._max_samples:
            del values[0 : len(values) - self._max_samples]

    def record_success(self, *, parse_ms: int, store_ms: int) -> None:
        with self._lock:
            self._success += 1
            self._append_sample(self._parse_ms, parse_ms)
            self._append_sample(self._store_ms, store_ms)

    def record_error(self, code: str) -> None:
        with self._lock:
            self._errors[str(code or "UNKNOWN")] += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            parse_ms = list(self._parse_ms)
            store_ms = list(self._store_ms)
            return {
                "success_total": self._success,
                "error_total": int(sum(self._errors.values())),
                "errors_by_code": dict(self._errors),
                "parse_ms": _build_metric(parse_ms),
                "store_ms": _build_metric(store_ms),
            }


def _build_metric(values: list[int]) -> dict[str, float | int]:
    if not values:
        return {"count": 0, "avg": 0.0, "max": 0}
    return {
        "count": len(values),
        "avg": round(sum(values) / len(values), 2),
        "max": max(values),
    }


intel_metrics = IntelMetricsStore()
