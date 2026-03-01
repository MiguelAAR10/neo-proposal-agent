import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.services.chat_alerts import ChatAlertThresholds, build_chat_alerts  # noqa: E402


class ChatAlertsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.thresholds = ChatAlertThresholds(
            min_events=10,
            block_rate_warning=0.2,
            block_rate_critical=0.35,
            no_case_usage_warning=0.4,
            company_concentration_warning=0.75,
        )

    def test_low_sample_returns_info(self) -> None:
        out = build_chat_alerts(
            {
                "window_events": 3,
                "guardrail_block_rate": 0.5,
                "no_case_usage_rate": 0.9,
                "top_company_share": 1.0,
            },
            self.thresholds,
        )
        self.assertEqual(out["severity"], "info")
        self.assertFalse(out["ready_for_strict_alerting"])
        self.assertIn("recommended_actions", out)
        self.assertGreaterEqual(len(out["recommended_actions"]), 1)
        self.assertIn("playbook_hint", out["alerts"][0])
        self.assertIn("owner", out["alerts"][0])
        self.assertIn("priority", out["alerts"][0])

    def test_critical_block_rate(self) -> None:
        out = build_chat_alerts(
            {
                "window_events": 20,
                "guardrail_block_rate": 0.5,
                "no_case_usage_rate": 0.1,
                "top_company_share": 0.3,
            },
            self.thresholds,
        )
        self.assertEqual(out["severity"], "critical")
        self.assertTrue(any(a["code"] == "HIGH_GUARDRAIL_BLOCK_RATE" for a in out["alerts"]))
        critical = [a for a in out["alerts"] if a["code"] == "HIGH_GUARDRAIL_BLOCK_RATE"][0]
        self.assertEqual(critical["priority"], "p0")
        self.assertIn("playbook_hint", critical)

    def test_warning_mix(self) -> None:
        out = build_chat_alerts(
            {
                "window_events": 30,
                "guardrail_block_rate": 0.22,
                "no_case_usage_rate": 0.5,
                "top_company_share": 0.8,
            },
            self.thresholds,
        )
        self.assertEqual(out["severity"], "warning")
        codes = {a["code"] for a in out["alerts"]}
        self.assertIn("ELEVATED_GUARDRAIL_BLOCK_RATE", codes)
        self.assertIn("LOW_CASE_GROUNDING", codes)
        self.assertIn("HIGH_COMPANY_CONCENTRATION", codes)
        self.assertGreaterEqual(len(out["recommended_actions"]), 2)


if __name__ == "__main__":
    unittest.main()
