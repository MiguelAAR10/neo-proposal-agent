import importlib.util
import unittest
from pathlib import Path

import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.models.human_insight import StructuredInsightItem  # noqa: E402
from src.repositories.sqlite_repositories import SQLiteCompanyProfileRepository, SQLiteHumanInsightRepository  # noqa: E402

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None


@unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy no disponible en este entorno")
class HumanInsightRepositoryTests(unittest.TestCase):
    def test_repository_flow_in_memory_including_idempotency(self) -> None:
        db_url = "sqlite:///:memory:"
        insight_repo = SQLiteHumanInsightRepository(db_url)
        profile_repo = SQLiteCompanyProfileRepository(db_url)
        payload = [
            StructuredInsightItem(category="pain_points", value="falta presupuesto", confidence=0.7),
            StructuredInsightItem(category="decision_makers", value="CFO", confidence=0.9),
            StructuredInsightItem(category="sentiment", value="negative", confidence=0.8),
        ]

        first = insight_repo.save(
            company_id="BCP",
            author="Carlos Ruiz",
            department="Finanzas",
            sentiment="Riesgo",
            raw_text="Cliente preocupado por presupuesto",
            structured_payload=payload,
            source="form",
        )
        second = insight_repo.save(
            company_id="BCP",
            author="Carlos Ruiz",
            department="Finanzas",
            sentiment="Riesgo",
            raw_text="Cliente preocupado por presupuesto",
            structured_payload=payload,
            source="form",
        )

        self.assertEqual(first.id, second.id)
        recent = insight_repo.list_recent(company_id="BCP", limit=5)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].structured_payload[0].category, "pain_points")
        self.assertEqual(recent[0].author, "Carlos Ruiz")
        self.assertEqual(recent[0].department, "Finanzas")
        self.assertEqual(recent[0].sentiment, "Riesgo")

        profile_repo.upsert_profile(
            company_id="BCP",
            area="Operaciones",
            profile_payload={"empresa": "BCP", "pain_points": ["Procesos manuales"]},
        )
        profile = profile_repo.get_profile(company_id="BCP", area="Operaciones")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.profile_payload["empresa"], "BCP")


if __name__ == "__main__":
    unittest.main()
