import tempfile
import unittest
from pathlib import Path

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.models.human_insight import StructuredInsightItem  # noqa: E402
from src.repositories.sqlite_repositories import SQLiteHumanInsightRepository  # noqa: E402


class HumanInsightRepositoryTests(unittest.TestCase):
    def test_save_and_dedupe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "intel.db")
            repo = SQLiteHumanInsightRepository(db_path)
            payload = [
                StructuredInsightItem(category="pain_points", value="falta presupuesto", confidence=0.7),
                StructuredInsightItem(category="decision_makers", value="CFO", confidence=0.9),
                StructuredInsightItem(category="sentiment", value="negative", confidence=0.8),
            ]

            first = repo.save(
                company_id="BCP",
                seller_id="seller-1",
                raw_text="Cliente preocupado por presupuesto",
                structured_payload=payload,
                source="form",
            )
            second = repo.save(
                company_id="BCP",
                seller_id="seller-1",
                raw_text="Cliente preocupado por presupuesto",
                structured_payload=payload,
                source="form",
            )

            self.assertEqual(first.id, second.id)
            recent = repo.list_recent(company_id="BCP", limit=5)
            self.assertEqual(len(recent), 1)
            self.assertEqual(recent[0].structured_payload[0].category, "pain_points")


if __name__ == "__main__":
    unittest.main()
