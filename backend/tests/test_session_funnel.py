import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.services.session_funnel import SessionFunnelStore  # noqa: E402


class SessionFunnelStoreTests(unittest.TestCase):
    def test_summary_contract(self) -> None:
        store = SessionFunnelStore(max_sessions=10)
        store.record_start("t1", "BCP", "Operaciones", total_cases=3)
        store.record_select("t1", selected_count=2, completed=True)
        store.record_chat("t1", "ok")
        store.record_chat("t1", "guardrail_blocked")
        store.record_refine("t1")

        summary = store.summary()
        self.assertEqual(summary["source"], "memory")
        self.assertEqual(summary["window_sessions"], 1)
        self.assertEqual(summary["sessions_with_cases"], 1)
        self.assertEqual(summary["sessions_selected"], 1)
        self.assertEqual(summary["sessions_completed"], 1)
        self.assertEqual(summary["sessions_refined"], 1)
        self.assertEqual(summary["chat_interactions"], 2)
        self.assertEqual(summary["guardrail_blocked_interactions"], 1)

    def test_fallback_to_memory_when_redis_fails(self) -> None:
        with patch("src.services.session_funnel.redis.from_url", side_effect=RuntimeError("redis down")):
            store = SessionFunnelStore(max_sessions=10, redis_url="redis://localhost:6379")
        store.record_start("t2", "Alicorp", "Operaciones", total_cases=2)
        snap = store.snapshot(limit=10)
        self.assertEqual(snap["source"], "memory")
        self.assertEqual(snap["returned"], 1)

    def test_snapshot_filters_and_pagination(self) -> None:
        store = SessionFunnelStore(max_sessions=10)
        store.record_start("t1", "BCP", "Operaciones", total_cases=2)
        store.record_select("t1", selected_count=1, completed=True)
        store.record_start("t2", "Alicorp", "Marketing", total_cases=1)

        # Force old timestamp for t2 to test time filter.
        old_ts = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        store._items["t2"].last_update_utc = old_ts  # noqa: SLF001

        page1 = store.snapshot(limit=1, offset=0, company="bcp")
        self.assertEqual(page1["total_filtered"], 1)
        self.assertEqual(page1["returned"], 1)
        self.assertEqual(page1["items"][0]["empresa"], "BCP")

        filtered_time = store.snapshot(limit=10, offset=0, updated_after_utc=(datetime.now(timezone.utc) - timedelta(hours=24)).isoformat())
        self.assertEqual(filtered_time["total_filtered"], 1)
        self.assertEqual(filtered_time["items"][0]["thread_id"], "t1")

        completed = store.snapshot(limit=10, offset=0, completed_only=True)
        self.assertEqual(completed["total_filtered"], 1)
        self.assertTrue(completed["items"][0]["proposal_generated"])

    def test_snapshot_sorting(self) -> None:
        store = SessionFunnelStore(max_sessions=10)
        store.record_start("t1", "BCP", "Operaciones", total_cases=1)
        store.record_start("t2", "Alicorp", "Operaciones", total_cases=5)
        snap = store.snapshot(limit=10, offset=0, sort_by="total_cases", sort_dir="desc")
        self.assertEqual(snap["items"][0]["thread_id"], "t2")

    def test_history_contract(self) -> None:
        store = SessionFunnelStore(max_sessions=10)
        store.record_start("t1", "BCP", "Operaciones", total_cases=2)
        store.record_select("t1", selected_count=1, completed=True)
        history = store.history(bucket="hour", limit_buckets=24)
        self.assertEqual(history["bucket"], "hour")
        self.assertGreaterEqual(history["returned_buckets"], 1)
        self.assertIn("metrics", history["series"][-1])


if __name__ == "__main__":
    unittest.main()
