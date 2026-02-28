import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.services.metrics import SearchMetricsStore  # noqa: E402


class MetricsStoreTests(unittest.TestCase):
    def test_snapshot_percentiles_and_cache(self) -> None:
        store = SearchMetricsStore(max_samples=20)
        for i in range(1, 11):
            store.record_success(
                total_ms=i * 100,
                embedding_ms=i * 10,
                qdrant_ms=i * 5,
                cache_hit=(i % 2 == 0),
            )
        snap = store.snapshot()

        self.assertEqual(snap["window_samples"], 10)
        self.assertGreaterEqual(snap["latency_ms"]["p95"], snap["latency_ms"]["p50"])
        self.assertEqual(snap["cache"]["hits"], 5)
        self.assertEqual(snap["cache"]["misses"], 5)

    def test_error_counter(self) -> None:
        store = SearchMetricsStore(max_samples=10)
        store.record_error("EXTERNAL_TIMEOUT")
        store.record_error("EXTERNAL_TIMEOUT")
        store.record_error("UNHANDLED_ERROR")
        snap = store.snapshot()
        self.assertEqual(snap["errors"]["EXTERNAL_TIMEOUT"], 2)
        self.assertEqual(snap["errors"]["UNHANDLED_ERROR"], 1)


if __name__ == "__main__":
    unittest.main()

