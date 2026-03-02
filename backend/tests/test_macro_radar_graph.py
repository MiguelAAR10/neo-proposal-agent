import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.intel_pipeline.orchestrator.macro_radar_graph import run_macro_radar_sync  # noqa: E402


class MacroRadarGraphTests(unittest.TestCase):
    def test_runs_and_persists_industry_radiography(self) -> None:
        class _FakeRepo:
            def __init__(self) -> None:
                self.saved: dict = {}

            def upsert_radiography(self, *, industry_target: str, profile_payload: dict, triggers_payload: list[dict]):
                self.saved = {
                    "industry_target": industry_target,
                    "profile_payload": profile_payload,
                    "triggers_payload": triggers_payload,
                    "updated_at": "2026-03-02T16:30:00+00:00",
                }
                return type("Stored", (), self.saved)()

        fake_repo = _FakeRepo()
        with patch("src.intel_pipeline.orchestrator.nodes.industry_radar_repository", new=fake_repo):
            result = run_macro_radar_sync(industry_target="Banca", force_mock_tools=True)

        self.assertFalse(result.get("error"))
        self.assertEqual(result["industry_target"], "Banca")
        self.assertGreater(len(result["raw_signals"]), 0)
        self.assertGreater(len(result["critical_triggers_found"]), 0)
        self.assertIn("executive_summary", result["industry_radiography"])
        self.assertEqual(fake_repo.saved["industry_target"], "Banca")


if __name__ == "__main__":
    unittest.main()
