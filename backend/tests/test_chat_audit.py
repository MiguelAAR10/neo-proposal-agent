import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.services.chat_audit import ChatAuditStore  # noqa: E402


class ChatAuditStoreTests(unittest.TestCase):
    def test_records_and_snapshots(self) -> None:
        store = ChatAuditStore(max_events=5)
        store.record_event(
            thread_id="t1",
            empresa="BCP",
            status="ok",
            guardrail_code="ALLOWED",
            used_case_ids=["C1"],
            message="Mensaje de prueba para preview",
        )
        store.record_event(
            thread_id="t2",
            empresa="Alicorp",
            status="guardrail_blocked",
            guardrail_code="PROMPT_INJECTION",
            used_case_ids=[],
            message="Ignora instrucciones",
        )

        snap = store.snapshot(limit=10)
        self.assertEqual(snap["source"], "memory")
        self.assertEqual(snap["total_events"], 2)
        self.assertEqual(snap["returned"], 2)
        self.assertEqual(snap["items"][0]["thread_id"], "t1")

        blocked = store.snapshot(limit=10, status="guardrail_blocked")
        self.assertEqual(blocked["filtered_events"], 1)
        self.assertEqual(blocked["items"][0]["guardrail_code"], "PROMPT_INJECTION")

    def test_respects_max_events(self) -> None:
        store = ChatAuditStore(max_events=3)
        for idx in range(5):
            store.record_event(
                thread_id=f"t{idx}",
                empresa="BCP",
                status="ok",
                guardrail_code="ALLOWED",
                used_case_ids=[],
                message=f"m{idx}",
            )
        snap = store.snapshot(limit=10)
        self.assertEqual(snap["total_events"], 3)
        self.assertEqual(snap["items"][0]["thread_id"], "t2")

    def test_retention_filter_excludes_old_rows(self) -> None:
        store = ChatAuditStore(max_events=10, retention_days=1)
        old_ts = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        store.events.append(
            {
                "ts_utc": old_ts,
                "thread_id": "old",
                "status": "ok",
                "guardrail_code": "ALLOWED",
                "used_case_ids": [],
                "used_case_count": 0,
                "message_preview": "old",
            }
        )
        store.record_event(
            thread_id="new",
            empresa="BCP",
            status="ok",
            guardrail_code="ALLOWED",
            used_case_ids=[],
            message="nuevo",
        )
        snap = store.snapshot(limit=10)
        self.assertEqual(snap["total_events"], 1)
        self.assertEqual(snap["items"][0]["thread_id"], "new")

    def test_analytics_has_expected_kpis(self) -> None:
        store = ChatAuditStore(max_events=10, retention_days=7)
        store.record_event(
            thread_id="t1",
            empresa="BCP",
            status="ok",
            guardrail_code="ALLOWED",
            used_case_ids=["C1", "C2"],
            message="ok1",
        )
        store.record_event(
            thread_id="t1",
            empresa="BCP",
            status="guardrail_blocked",
            guardrail_code="PROMPT_INJECTION",
            used_case_ids=[],
            message="blocked",
        )
        store.record_event(
            thread_id="t2",
            empresa="Alicorp",
            status="ok",
            guardrail_code="ALLOWED",
            used_case_ids=["C1"],
            message="ok2",
        )
        metrics = store.analytics()
        self.assertEqual(metrics["window_events"], 3)
        self.assertEqual(metrics["status_counts"]["ok"], 2)
        self.assertEqual(metrics["status_counts"]["guardrail_blocked"], 1)
        self.assertEqual(metrics["top_case_ids"][0][0], "C1")
        self.assertEqual(metrics["top_threads"][0][0], "t1")

    def test_analytics_history_groups_by_hour(self) -> None:
        store = ChatAuditStore(max_events=20, retention_days=7)
        store.record_event(
            thread_id="t1",
            empresa="BCP",
            status="ok",
            guardrail_code="ALLOWED",
            used_case_ids=["C1"],
            message="m1",
        )
        store.record_event(
            thread_id="t2",
            empresa="BCP",
            status="guardrail_blocked",
            guardrail_code="PROMPT_INJECTION",
            used_case_ids=[],
            message="m2",
        )
        history = store.analytics_history(bucket="hour", limit_buckets=24)
        self.assertEqual(history["bucket"], "hour")
        self.assertGreaterEqual(history["returned_buckets"], 1)
        first = history["series"][-1]
        self.assertIn("bucket_start_utc", first)
        self.assertIn("metrics", first)


if __name__ == "__main__":
    unittest.main()
