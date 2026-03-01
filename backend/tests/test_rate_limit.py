import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.services.rate_limit import RateLimiter  # noqa: E402


class RateLimitTests(unittest.TestCase):
    def test_blocks_after_limit_and_recovers_after_window(self) -> None:
        limiter = RateLimiter(redis_url=None)
        first = limiter.check("k1", limit=2, window_sec=1)
        second = limiter.check("k1", limit=2, window_sec=1)
        third = limiter.check("k1", limit=2, window_sec=1)

        self.assertTrue(first.allowed)
        self.assertTrue(second.allowed)
        self.assertFalse(third.allowed)
        self.assertGreaterEqual(third.retry_after_sec, 1)

        time.sleep(1.05)
        fourth = limiter.check("k1", limit=2, window_sec=1)
        self.assertTrue(fourth.allowed)

    def test_falls_back_to_memory_when_redis_bootstrap_fails(self) -> None:
        with patch("src.services.rate_limit.redis.from_url", side_effect=RuntimeError("redis down")):
            limiter = RateLimiter(redis_url="redis://localhost:6379")

        a = limiter.check("k2", limit=1, window_sec=2)
        b = limiter.check("k2", limit=1, window_sec=2)
        self.assertTrue(a.allowed)
        self.assertFalse(b.allowed)


if __name__ == "__main__":
    unittest.main()
