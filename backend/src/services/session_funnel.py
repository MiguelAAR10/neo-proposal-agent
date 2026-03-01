from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any

import redis

from src.config import get_settings


@dataclass
class SessionFunnelEvent:
    thread_id: str
    empresa: str
    area: str
    started_at_utc: str
    total_cases: int = 0
    selected_count: int = 0
    proposal_generated: bool = False
    refined_count: int = 0
    chat_count: int = 0
    guardrail_blocked_count: int = 0
    last_update_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SessionFunnelStore:
    def __init__(
        self,
        max_sessions: int = 2000,
        redis_url: str | None = None,
        redis_key: str = "ops:session_funnel:v1",
    ) -> None:
        self._max_sessions = max_sessions
        self._items: dict[str, SessionFunnelEvent] = {}
        self._lock = Lock()
        self._redis_url = redis_url
        self._redis_key = redis_key
        self._redis_data_key = f"{redis_key}:data"
        self._redis_index_key = f"{redis_key}:index"
        self._redis_client: redis.Redis | None = None
        self._redis_unavailable = False
        if self._redis_url:
            self._bootstrap_redis()

    def _bootstrap_redis(self) -> None:
        if self._redis_unavailable or not self._redis_url:
            return
        try:
            client = redis.from_url(
                self._redis_url,
                socket_timeout=0.2,
                socket_connect_timeout=0.2,
                decode_responses=True,
            )
            client.ping()
            self._redis_client = client
        except Exception:
            self._redis_unavailable = True
            self._redis_client = None

    def _ts(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _ts_epoch(self) -> float:
        return datetime.now(timezone.utc).timestamp()

    def _ensure(self, thread_id: str, empresa: str = "", area: str = "") -> SessionFunnelEvent:
        item = self._items.get(thread_id)
        if item is None:
            item = SessionFunnelEvent(
                thread_id=thread_id,
                empresa=empresa,
                area=area,
                started_at_utc=self._ts(),
            )
            self._items[thread_id] = item
            self._trim_if_needed()
        return item

    def _trim_if_needed(self) -> None:
        if len(self._items) <= self._max_sessions:
            return
        oldest_key = min(self._items, key=lambda k: self._items[k].started_at_utc)
        self._items.pop(oldest_key, None)

    def _load_redis_item(self, thread_id: str) -> SessionFunnelEvent | None:
        if self._redis_client is None:
            return None
        try:
            raw = self._redis_client.hget(self._redis_data_key, thread_id)
            if not raw:
                return None
            data = json.loads(raw)
            if not isinstance(data, dict):
                return None
            return SessionFunnelEvent(**data)
        except Exception:
            self._redis_unavailable = True
            self._redis_client = None
            return None

    def _save_redis_item(self, item: SessionFunnelEvent) -> None:
        if self._redis_client is None:
            return
        try:
            payload = json.dumps(vars(item), ensure_ascii=True)
            pipe = self._redis_client.pipeline()
            pipe.hset(self._redis_data_key, item.thread_id, payload)
            pipe.zadd(self._redis_index_key, {item.thread_id: self._ts_epoch()})
            pipe.execute()
            self._trim_redis_if_needed()
        except Exception:
            self._redis_unavailable = True
            self._redis_client = None

    def _trim_redis_if_needed(self) -> None:
        if self._redis_client is None:
            return
        try:
            size = self._redis_client.zcard(self._redis_index_key)
            overflow = int(size) - int(self._max_sessions)
            if overflow <= 0:
                return
            old_ids = self._redis_client.zrange(self._redis_index_key, 0, overflow - 1)
            if not old_ids:
                return
            pipe = self._redis_client.pipeline()
            pipe.zrem(self._redis_index_key, *old_ids)
            pipe.hdel(self._redis_data_key, *old_ids)
            pipe.execute()
        except Exception:
            self._redis_unavailable = True
            self._redis_client = None

    def _snapshot_redis(self, limit: int) -> list[dict[str, Any]] | None:
        if self._redis_client is None:
            return None
        try:
            safe_limit = max(1, int(limit))
            thread_ids = self._redis_client.zrevrange(self._redis_index_key, 0, safe_limit - 1)
            if not thread_ids:
                return []
            rows: list[dict[str, Any]] = []
            for thread_id in thread_ids:
                raw = self._redis_client.hget(self._redis_data_key, thread_id)
                if not raw:
                    continue
                item = json.loads(raw)
                if isinstance(item, dict):
                    rows.append(item)
            return rows
        except Exception:
            self._redis_unavailable = True
            self._redis_client = None
            return None

    @staticmethod
    def _to_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            return None

    def _apply_filters(
        self,
        rows: list[dict[str, Any]],
        *,
        company: str | None = None,
        updated_after_utc: str | None = None,
        completed_only: bool = False,
    ) -> list[dict[str, Any]]:
        company_norm = (company or "").strip().lower()
        cutoff = self._to_dt(updated_after_utc)
        filtered: list[dict[str, Any]] = []
        for row in rows:
            if company_norm:
                empresa = str(row.get("empresa") or "").strip().lower()
                if company_norm not in empresa:
                    continue
            if completed_only and not bool(row.get("proposal_generated", False)):
                continue
            if cutoff is not None:
                ts = self._to_dt(str(row.get("last_update_utc") or ""))
                if ts is None or ts < cutoff:
                    continue
            filtered.append(row)
        return filtered

    @staticmethod
    def _sort_rows(rows: list[dict[str, Any]], sort_by: str, sort_dir: str) -> list[dict[str, Any]]:
        reverse = str(sort_dir).lower() != "asc"
        safe_sort = str(sort_by or "last_update_utc").strip()
        allowed_numeric = {
            "total_cases",
            "selected_count",
            "refined_count",
            "chat_count",
            "guardrail_blocked_count",
        }
        allowed_text = {"empresa", "area", "thread_id", "last_update_utc"}
        allowed_bool = {"proposal_generated"}

        if safe_sort in allowed_numeric:
            return sorted(rows, key=lambda r: int(r.get(safe_sort, 0) or 0), reverse=reverse)
        if safe_sort in allowed_bool:
            return sorted(rows, key=lambda r: 1 if bool(r.get(safe_sort, False)) else 0, reverse=reverse)
        if safe_sort in allowed_text:
            return sorted(rows, key=lambda r: str(r.get(safe_sort, "") or "").lower(), reverse=reverse)
        # fallback estable por last_update
        return sorted(rows, key=lambda r: str(r.get("last_update_utc", "") or ""), reverse=True)

    def _upsert(self, thread_id: str, empresa: str = "", area: str = "") -> SessionFunnelEvent:
        # Try Redis-backed state first.
        if self._redis_client is not None:
            redis_item = self._load_redis_item(thread_id)
            if redis_item is not None:
                return redis_item
            return SessionFunnelEvent(
                thread_id=thread_id,
                empresa=empresa,
                area=area,
                started_at_utc=self._ts(),
            )
        # Fallback memory.
        return self._ensure(thread_id, empresa=empresa, area=area)

    def _persist(self, item: SessionFunnelEvent) -> None:
        if self._redis_client is not None:
            self._save_redis_item(item)
            return
        self._items[item.thread_id] = item
        self._trim_if_needed()

    def record_start(self, thread_id: str, empresa: str, area: str, total_cases: int) -> None:
        with self._lock:
            item = self._upsert(thread_id, empresa=empresa, area=area)
            item.empresa = empresa
            item.area = area
            item.total_cases = max(0, int(total_cases))
            item.last_update_utc = self._ts()
            self._persist(item)

    def record_select(self, thread_id: str, selected_count: int, completed: bool) -> None:
        with self._lock:
            item = self._upsert(thread_id)
            item.selected_count = max(0, int(selected_count))
            item.proposal_generated = bool(completed) or item.proposal_generated
            item.last_update_utc = self._ts()
            self._persist(item)

    def record_refine(self, thread_id: str) -> None:
        with self._lock:
            item = self._upsert(thread_id)
            item.refined_count += 1
            item.last_update_utc = self._ts()
            self._persist(item)

    def record_chat(self, thread_id: str, status: str) -> None:
        with self._lock:
            item = self._upsert(thread_id)
            item.chat_count += 1
            if status == "guardrail_blocked":
                item.guardrail_blocked_count += 1
            item.last_update_utc = self._ts()
            self._persist(item)

    def snapshot(
        self,
        *,
        limit: int = 200,
        offset: int = 0,
        company: str | None = None,
        updated_after_utc: str | None = None,
        completed_only: bool = False,
        sort_by: str = "last_update_utc",
        sort_dir: str = "desc",
    ) -> dict[str, Any]:
        safe_limit = max(1, int(limit))
        safe_offset = max(0, int(offset))

        rows = self._snapshot_redis(max(1, self._max_sessions))
        if rows is not None:
            filtered = self._apply_filters(
                rows,
                company=company,
                updated_after_utc=updated_after_utc,
                completed_only=completed_only,
            )
            filtered = self._sort_rows(filtered, sort_by=sort_by, sort_dir=sort_dir)
            selected = filtered[safe_offset : safe_offset + safe_limit]
            return {
                "source": "redis",
                "returned": len(selected),
                "offset": safe_offset,
                "limit": safe_limit,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
                "total_available": len(rows),
                "total_filtered": len(filtered),
                "items": selected,
            }

        with self._lock:
            mem_rows = [vars(row) for row in sorted(self._items.values(), key=lambda v: v.last_update_utc, reverse=True)]
            filtered = self._apply_filters(
                mem_rows,
                company=company,
                updated_after_utc=updated_after_utc,
                completed_only=completed_only,
            )
            filtered = self._sort_rows(filtered, sort_by=sort_by, sort_dir=sort_dir)
            selected = filtered[safe_offset : safe_offset + safe_limit]
            return {
                "source": "memory",
                "returned": len(selected),
                "offset": safe_offset,
                "limit": safe_limit,
                "sort_by": sort_by,
                "sort_dir": sort_dir,
                "total_available": len(mem_rows),
                "total_filtered": len(filtered),
                "items": selected,
            }

    def summary(
        self,
        *,
        company: str | None = None,
        updated_after_utc: str | None = None,
        completed_only: bool = False,
        sort_by: str = "last_update_utc",
        sort_dir: str = "desc",
    ) -> dict[str, Any]:
        snap = self.snapshot(
            limit=max(1, self._max_sessions),
            offset=0,
            company=company,
            updated_after_utc=updated_after_utc,
            completed_only=completed_only,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        rows = snap.get("items", [])
        started = len(rows)
        with_cases = sum(1 for r in rows if int(r.get("total_cases", 0)) > 0)
        selected = sum(1 for r in rows if int(r.get("selected_count", 0)) > 0)
        completed = sum(1 for r in rows if bool(r.get("proposal_generated", False)))
        refined = sum(1 for r in rows if int(r.get("refined_count", 0)) > 0)
        chats = sum(int(r.get("chat_count", 0)) for r in rows)
        blocked = sum(int(r.get("guardrail_blocked_count", 0)) for r in rows)
        return {
            "source": snap.get("source", "memory"),
            "window_sessions": started,
            "total_available": snap.get("total_available", started),
            "total_filtered": snap.get("total_filtered", started),
            "sessions_with_cases": with_cases,
            "sessions_selected": selected,
            "sessions_completed": completed,
            "sessions_refined": refined,
            "chat_interactions": chats,
            "guardrail_blocked_interactions": blocked,
            "rates": {
                "with_cases_over_started": round((with_cases / started), 4) if started else 0.0,
                "selected_over_started": round((selected / started), 4) if started else 0.0,
                "completed_over_started": round((completed / started), 4) if started else 0.0,
                "refined_over_completed": round((refined / completed), 4) if completed else 0.0,
            },
        }

    @staticmethod
    def _bucket_start(ts: datetime, bucket: str) -> datetime:
        if bucket == "day":
            return ts.replace(hour=0, minute=0, second=0, microsecond=0)
        return ts.replace(minute=0, second=0, microsecond=0)

    def history(
        self,
        *,
        bucket: str = "hour",
        limit_buckets: int = 48,
        company: str | None = None,
        updated_after_utc: str | None = None,
        completed_only: bool = False,
    ) -> dict[str, Any]:
        safe_bucket = "day" if bucket == "day" else "hour"
        safe_limit = max(1, min(int(limit_buckets), 720))
        snap = self.snapshot(
            limit=max(1, self._max_sessions),
            offset=0,
            company=company,
            updated_after_utc=updated_after_utc,
            completed_only=completed_only,
            sort_by="last_update_utc",
            sort_dir="asc",
        )
        rows = snap.get("items", [])
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            ts = self._to_dt(str(row.get("last_update_utc") or ""))
            if ts is None:
                continue
            key = self._bucket_start(ts, safe_bucket).isoformat()
            grouped.setdefault(key, []).append(row)

        keys = sorted(grouped.keys())[-safe_limit:]
        series: list[dict[str, Any]] = []
        for key in keys:
            bucket_rows = grouped[key]
            started = len(bucket_rows)
            completed = sum(1 for r in bucket_rows if bool(r.get("proposal_generated", False)))
            selected = sum(1 for r in bucket_rows if int(r.get("selected_count", 0)) > 0)
            with_cases = sum(1 for r in bucket_rows if int(r.get("total_cases", 0)) > 0)
            refined = sum(1 for r in bucket_rows if int(r.get("refined_count", 0)) > 0)
            chats = sum(int(r.get("chat_count", 0)) for r in bucket_rows)
            blocked = sum(int(r.get("guardrail_blocked_count", 0)) for r in bucket_rows)
            series.append(
                {
                    "bucket_start_utc": key,
                    "metrics": {
                        "started": started,
                        "with_cases": with_cases,
                        "selected": selected,
                        "completed": completed,
                        "refined": refined,
                        "chat_interactions": chats,
                        "guardrail_blocked_interactions": blocked,
                        "completed_over_started": round((completed / started), 4) if started else 0.0,
                    },
                }
            )

        return {
            "source": snap.get("source", "memory"),
            "bucket": safe_bucket,
            "returned_buckets": len(series),
            "series": series,
        }


_settings = get_settings()
session_funnel_store = SessionFunnelStore(
    max_sessions=2000,
    redis_url=_settings.redis_url,
    redis_key=_settings.session_funnel_redis_key,
)
