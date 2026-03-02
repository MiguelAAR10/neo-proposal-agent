import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.agent.nodes import update_summary_node  # noqa: E402
from src.models.human_insight import HumanInsightStored, StructuredInsightItem  # noqa: E402


class UpdateSummaryNodeTests(unittest.TestCase):
    def test_merges_recent_human_insights_into_profile(self) -> None:
        base_state = {
            "empresa": "BCP",
            "area": "Operaciones",
            "perfil_cliente": {
                "empresa": "BCP",
                "area": "Operaciones",
                "objetivos": ["eficiencia"],
                "pain_points": ["Procesos manuales"],
            },
            "inteligencia_sector": {
                "source": "web_scraper_v1",
                "industria": "Banca",
                "area": "Operaciones",
            },
            "error": "",
        }
        recent = [
            HumanInsightStored(
                id="h1",
                company_id="BCP",
                seller_id="s-1",
                raw_text="texto",
                source="sales_form",
                created_at="2026-03-02T12:00:00+00:00",
                structured_payload=[
                    StructuredInsightItem(category="pain_points", value="Temor a sobrecostos", confidence=0.7),
                    StructuredInsightItem(category="decision_makers", value="Gerente Operaciones", confidence=0.9),
                    StructuredInsightItem(category="sentiment", value="negative", confidence=0.8),
                ],
                parser_version="v1",
            )
        ]

        class _InsightRepo:
            def list_recent(self, *, company_id: str, limit: int = 5):
                return recent

        class _ProfileRepo:
            def upsert_profile(self, *, company_id: str, area: str, profile_payload: dict):
                return None

        with patch("src.agent.nodes.human_insight_repository", new=_InsightRepo()):
            with patch("src.agent.nodes.company_profile_repository", new=_ProfileRepo()):
                result = update_summary_node(base_state)

        perfil = result["perfil_cliente"]
        self.assertIn("Temor a sobrecostos", perfil["pain_points"])
        self.assertEqual(perfil["decision_makers"], ["Gerente Operaciones"])
        self.assertEqual(perfil["sentimiento_comercial"], "negative")
        self.assertEqual(perfil["intel_sources"]["human_insights_count"], 1)
        self.assertEqual(len(result["human_insights"]), 1)


if __name__ == "__main__":
    unittest.main()
