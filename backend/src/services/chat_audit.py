from __future__ import annotations

import json
from collections import Counter
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Deque, Literal

import redis

from src.config import get_settings


def _parse_ts_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


@dataclass
class ChatAuditStore:
    max_events: int = 2000
    retention_days: int = 7
    redis_url: str | None = None
    redis_key: str = "ops:chat_audit:v1"
    events: Deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=2000))
    _redis_client: redis.Redis | None = field(default=None, init=False)
    _redis_unavailable: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.events = deque(maxlen=self.max_events)
        if self.redis_url:
            self._bootstrap_redis()

    def _bootstrap_redis(self) -> None:
        if self._redis_unavailable or not self.redis_url:
            return
        try:
            client = redis.from_url(
                self.redis_url,
                socket_timeout=0.2,
                socket_connect_timeout=0.2,
                decode_responses=True,
            )
            client.ping()
            self._redis_client = client
        except Exception:
            self._redis_unavailable = True
            self._redis_client = None

    def _build_event(
        self,
        *,
        thread_id: str,
        empresa: str | None,
        status: str,
        guardrail_code: str,
        used_case_ids: list[str],
        message: str,
    ) -> dict[str, Any]:
        preview = " ".join((message or "").strip().split())[:140]
        return {
            "ts_utc": datetime.now(timezone.utc).isoformat(),
            "thread_id": thread_id,
            "empresa": (empresa or "").strip() or "N/A",
            "status": status,
            "guardrail_code": guardrail_code,
            "used_case_ids": list(used_case_ids),
            "used_case_count": len(used_case_ids),
            "message_preview": preview,
        }

    def _retention_cutoff(self) -> datetime:
        days = max(1, int(self.retention_days))
        return datetime.now(timezone.utc) - timedelta(days=days)

    def _filter_retention(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cutoff = self._retention_cutoff()
        kept: list[dict[str, Any]] = []
        for row in rows:
            ts = _parse_ts_utc(str(row.get("ts_utc") or ""))
            if ts is None:
                continue
            if ts >= cutoff:
                kept.append(row)
        return kept

    def _record_redis_event(self, event: dict[str, Any]) -> None:
        if self._redis_client is None:
            return
        try:
            payload = json.dumps(event, ensure_ascii=True)
            self._redis_client.rpush(self.redis_key, payload)
            self._redis_client.ltrim(self.redis_key, -self.max_events, -1)
        except Exception:
            # degradar graceful a memoria si redis falla en runtime
            self._redis_unavailable = True
            self._redis_client = None

    def _load_redis_events(self) -> list[dict[str, Any]] | None:
        if self._redis_client is None:
            return None
        try:
            raw_rows = self._redis_client.lrange(self.redis_key, -self.max_events, -1)
            parsed: list[dict[str, Any]] = []
            for raw in raw_rows:
                try:
                    item = json.loads(raw)
                    if isinstance(item, dict):
                        parsed.append(item)
                except Exception:
                    continue
            return parsed
        except Exception:
            self._redis_unavailable = True
            self._redis_client = None
            return None

    def record_event(
        self,
        *,
        thread_id: str,
        empresa: str | None,
        status: str,
        guardrail_code: str,
        used_case_ids: list[str],
        message: str,
    ) -> None:
        event = self._build_event(
            thread_id=thread_id,
            empresa=empresa,
            status=status,
            guardrail_code=guardrail_code,
            used_case_ids=used_case_ids,
            message=message,
        )
        self.events.append(event)
        self._record_redis_event(event)

    def _get_retained_rows(self) -> tuple[str, list[dict[str, Any]]]:
        rows = self._load_redis_events()
        source = "redis" if rows is not None else "memory"
        if rows is None:
            rows = list(self.events)
        rows = self._filter_retention(rows)
        return source, rows

    @staticmethod
    def _bucket_start(ts: datetime, bucket: Literal["hour", "day"]) -> datetime:
        if bucket == "day":
            return ts.replace(hour=0, minute=0, second=0, microsecond=0)
        return ts.replace(minute=0, second=0, microsecond=0)

    def _compute_analytics_from_rows(self, source: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(rows)
        blocked = sum(1 for row in rows if row.get("status") == "guardrail_blocked")
        ok = sum(1 for row in rows if row.get("status") == "ok")
        block_rate = (blocked / total) if total > 0 else 0.0
        ok_without_cases = sum(
            1 for row in rows if row.get("status") == "ok" and int(row.get("used_case_count") or 0) == 0
        )
        no_case_usage_rate = (ok_without_cases / ok) if ok > 0 else 0.0

        guardrail_counter: Counter[str] = Counter()
        case_counter: Counter[str] = Counter()
        thread_counter: Counter[str] = Counter()
        company_counter: Counter[str] = Counter()

        for row in rows:
            code = str(row.get("guardrail_code") or "UNKNOWN")
            guardrail_counter[code] += 1
            thread_counter[str(row.get("thread_id") or "unknown")] += 1
            company_counter[str(row.get("empresa") or "N/A")] += 1
            for case_id in row.get("used_case_ids", []) or []:
                case_counter[str(case_id)] += 1

        top_company = company_counter.most_common(1)
        top_company_share = (top_company[0][1] / total) if (total > 0 and top_company) else 0.0

        return {
            "source": source,
            "retention_days": max(1, int(self.retention_days)),
            "window_events": total,
            "status_counts": {"ok": ok, "guardrail_blocked": blocked},
            "guardrail_block_rate": round(block_rate, 4),
            "no_case_usage_rate": round(no_case_usage_rate, 4),
            "top_company_share": round(top_company_share, 4),
            "top_guardrail_codes": guardrail_counter.most_common(5),
            "top_case_ids": case_counter.most_common(10),
            "top_threads": thread_counter.most_common(10),
            "top_companies": company_counter.most_common(10),
        }

    def snapshot(self, limit: int = 100, status: str | None = None) -> dict[str, Any]:
        safe_limit = max(1, min(int(limit), 500))
        source, rows = self._get_retained_rows()

        total_retained = len(rows)
        if status:
            rows = [row for row in rows if row.get("status") == status]

        selected = rows[-safe_limit:]
        return {
            "source": source,
            "retention_days": max(1, int(self.retention_days)),
            "total_events": total_retained,
            "filtered_events": len(rows),
            "returned": len(selected),
            "items": selected,
        }

    def analytics(self, status: str | None = None) -> dict[str, Any]:
        source, rows = self._get_retained_rows()
        if status:
            rows = [row for row in rows if row.get("status") == status]
        return self._compute_analytics_from_rows(source, rows)

    def analytics_history(
        self,
        *,
        bucket: Literal["hour", "day"] = "hour",
        limit_buckets: int = 48,
        status: str | None = None,
    ) -> dict[str, Any]:
        safe_limit = max(1, min(int(limit_buckets), 720))
        source, rows = self._get_retained_rows()
        if status:
            rows = [row for row in rows if row.get("status") == status]

        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            ts = _parse_ts_utc(str(row.get("ts_utc") or ""))
            if ts is None:
                continue
            key = self._bucket_start(ts, bucket).isoformat()
            grouped.setdefault(key, []).append(row)

        keys = sorted(grouped.keys())
        selected_keys = keys[-safe_limit:]
        series: list[dict[str, Any]] = []
        for key in selected_keys:
            metrics = self._compute_analytics_from_rows(source, grouped[key])
            series.append({"bucket_start_utc": key, "metrics": metrics})

        return {
            "source": source,
            "bucket": bucket,
            "returned_buckets": len(series),
            "series": series,
        }


_settings = get_settings()
chat_audit_store = ChatAuditStore(
    max_events=_settings.chat_audit_max_events,
    retention_days=_settings.chat_audit_retention_days,
    redis_url=_settings.redis_url,
    redis_key=_settings.chat_audit_redis_key,
)
