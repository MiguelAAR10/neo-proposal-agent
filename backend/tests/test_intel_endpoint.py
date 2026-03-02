import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.api.intel import create_human_insight  # noqa: E402
from src.models.human_insight import HumanInsightCreate, HumanInsightStored, StructuredInsightItem  # noqa: E402


class IntelEndpointTests(unittest.TestCase):
    def test_create_human_insight_contract(self) -> None:
        payload = HumanInsightCreate(
            seller_id="seller-1",
            text="El gerente de operaciones teme sobrecostos y pide ROI en 3 meses.",
            source="chat_form",
        )
        parsed = [
            StructuredInsightItem(category="pain_points", value="Temor a sobrecostos", confidence=0.8),
            StructuredInsightItem(category="decision_makers", value="Gerente de Operaciones", confidence=0.9),
            StructuredInsightItem(category="sentiment", value="negative", confidence=0.75),
        ]
        stored = HumanInsightStored(
            id="insight-1",
            company_id="BCP",
            seller_id="seller-1",
            raw_text=payload.text,
            structured_payload=parsed,
            source="chat_form",
            created_at="2026-03-02T12:00:00+00:00",
            parser_version="v1",
        )

        async def run() -> dict:
            with patch("src.api.intel.parse_sales_insight_text", return_value=parsed):
                with patch("src.api.intel.human_insight_repository.save", return_value=stored):
                    return await create_human_insight("bcp", payload)

        result = asyncio.run(run())
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["company_id"], "BCP")
        self.assertEqual(result["insight_id"], "insight-1")
        self.assertEqual(len(result["structured_payload"]), 3)


if __name__ == "__main__":
    unittest.main()
