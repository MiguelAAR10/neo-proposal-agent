from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Deque


def _percentile(values: list[int], pct: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    idx = int((len(ordered) - 1) * pct)
    return ordered[idx]


@dataclass
class SearchMetricsStore:
    """In-memory operational metrics for search SLA tracking."""

    max_samples: int = 1000
    latencies_ms: Deque[int] = field(default_factory=lambda: deque(maxlen=1000))
    embedding_ms: Deque[int] = field(default_factory=lambda: deque(maxlen=1000))
    qdrant_ms: Deque[int] = field(default_factory=lambda: deque(maxlen=1000))
    cache_hits: int = 0
    cache_misses: int = 0
    error_counter: Counter = field(default_factory=Counter)

    def __post_init__(self) -> None:
        self.latencies_ms = deque(maxlen=self.max_samples)
        self.embedding_ms = deque(maxlen=self.max_samples)
        self.qdrant_ms = deque(maxlen=self.max_samples)

    def record_success(
        self,
        total_ms: int,
        embedding_ms: int | None,
        qdrant_ms: int | None,
        cache_hit: bool | None,
    ) -> None:
        self.latencies_ms.append(max(0, int(total_ms)))
        if embedding_ms is not None:
            self.embedding_ms.append(max(0, int(embedding_ms)))
        if qdrant_ms is not None:
            self.qdrant_ms.append(max(0, int(qdrant_ms)))
        if cache_hit is True:
            self.cache_hits += 1
        elif cache_hit is False:
            self.cache_misses += 1

    def record_error(self, code: str) -> None:
        self.error_counter[code] += 1

    def snapshot(self) -> dict:
        lat = list(self.latencies_ms)
        emb = list(self.embedding_ms)
        qdr = list(self.qdrant_ms)
        total_cache = self.cache_hits + self.cache_misses
        cache_hit_rate = (self.cache_hits / total_cache) if total_cache > 0 else 0.0

        return {
            "window_samples": len(lat),
            "latency_ms": {
                "p50": _percentile(lat, 0.50),
                "p95": _percentile(lat, 0.95),
                "p99": _percentile(lat, 0.99),
            },
            "embedding_ms": {
                "p50": _percentile(emb, 0.50),
                "p95": _percentile(emb, 0.95),
            },
            "qdrant_ms": {
                "p50": _percentile(qdr, 0.50),
                "p95": _percentile(qdr, 0.95),
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": round(cache_hit_rate, 4),
            },
            "errors": dict(self.error_counter),
        }


search_metrics = SearchMetricsStore()

