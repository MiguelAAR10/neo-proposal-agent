from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import redis

from src.config import get_settings


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after_sec: int = 0


class RateLimiter:
    """
    Fixed-window rate limiter with Redis persistence and in-memory fallback.
    """

    def __init__(self, redis_url: str | None = None, redis_key_prefix: str = "ops:rate_limit:v1") -> None:
        self._redis_url = redis_url
        self._redis_key_prefix = redis_key_prefix
        self._redis_client: redis.Redis | None = None
        self._redis_unavailable = False
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[float, int]] = {}
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

    def _check_memory(self, key: str, limit: int, window_sec: int) -> RateLimitResult:
        now = time.time()
        with self._lock:
            started, count = self._buckets.get(key, (now, 0))
            if (now - started) >= window_sec:
                started, count = now, 0

            if count >= limit:
                retry_after = max(1, int(window_sec - (now - started)))
                return RateLimitResult(allowed=False, retry_after_sec=retry_after)

            self._buckets[key] = (started, count + 1)
            return RateLimitResult(allowed=True, retry_after_sec=0)

    def _check_redis(self, key: str, limit: int, window_sec: int) -> RateLimitResult | None:
        if self._redis_client is None:
            return None
        try:
            now = int(time.time())
            bucket = now // window_sec
            redis_key = f"{self._redis_key_prefix}:{key}:{bucket}"

            pipe = self._redis_client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, window_sec + 2)
            value, _ = pipe.execute()
            current = int(value)

            if current <= limit:
                return RateLimitResult(allowed=True, retry_after_sec=0)

            retry_after = max(1, window_sec - (now % window_sec))
            return RateLimitResult(allowed=False, retry_after_sec=retry_after)
        except Exception:
            self._redis_unavailable = True
            self._redis_client = None
            return None

    def check(self, key: str, limit: int, window_sec: int) -> RateLimitResult:
        safe_limit = max(1, int(limit))
        safe_window = max(1, int(window_sec))
        redis_result = self._check_redis(key=key, limit=safe_limit, window_sec=safe_window)
        if redis_result is not None:
            return redis_result
        return self._check_memory(key=key, limit=safe_limit, window_sec=safe_window)


_settings = get_settings()
rate_limiter = RateLimiter(
    redis_url=_settings.redis_url,
    redis_key_prefix=_settings.rate_limit_redis_key_prefix,
)
