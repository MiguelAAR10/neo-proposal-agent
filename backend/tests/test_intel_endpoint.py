import asyncio
import importlib.util
import sys
import unittest
from pathlib import Path

from fastapi import HTTPException

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.api.intel import create_human_insight, get_company_profile  # noqa: E402
from src.models.human_insight import (  # noqa: E402
    CompanyProfileStored,
    HumanInsightCreate,
    ParsedHumanInsight,
    StructuredInsightItem,
)
from src.repositories.sqlite_repositories import SQLiteHumanInsightRepository  # noqa: E402
from src.services.errors import InsightParseError  # noqa: E402

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None


@unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy no disponible en este entorno")
class IntelEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = SQLiteHumanInsightRepository("sqlite:///:memory:")
        self.parser = lambda _: ParsedHumanInsight(
            department="Operaciones",
            sentiment="Riesgo",
            structured_payload=[
                StructuredInsightItem(
                    category="pain_points",
                    value="Sobrecostos operativos",
                    confidence=0.9,
                ),
                StructuredInsightItem(
                    category="decision_makers",
                    value="Gerencia de operaciones",
                    confidence=0.85,
                ),
                StructuredInsightItem(
                    category="sentiment",
                    value="Riesgo",
                    confidence=0.9,
                ),
            ],
        )

    def test_create_human_insight_contract_and_idempotency(self) -> None:
        payload = HumanInsightCreate(
            author="Carlos Ruiz",
            text="El gerente de operaciones teme sobrecostos y pide ROI en 3 meses.",
            source="chat_form",
        )

        async def run():
            first = await create_human_insight(
                company_id="bcp",
                payload=payload,
                repository=self.repo,
                parser=self.parser,
            )
            second = await create_human_insight(
                company_id="bcp",
                payload=payload,
                repository=self.repo,
                parser=self.parser,
            )
            return first, second

        first_payload, second_payload = asyncio.run(run())
        self.assertEqual(first_payload["status"], "success")
        self.assertEqual(first_payload["company_id"], "BCP")
        self.assertEqual(first_payload["author"], "Carlos Ruiz")
        self.assertIn("department", first_payload)
        self.assertIn("sentiment", first_payload)
        self.assertEqual(len(first_payload["structured_payload"]), 3)
        self.assertEqual(second_payload["insight_id"], first_payload["insight_id"])

    def test_returns_typed_error_when_parser_fails(self) -> None:
        def _failing_parser(_: str):
            raise InsightParseError("no se pudo parsear")

        payload = HumanInsightCreate(
            author="Ana Silva",
            text="Texto de prueba para parser.",
            source="chat_form",
        )

        async def run() -> None:
            await create_human_insight(
                company_id="bcp",
                payload=payload,
                repository=self.repo,
                parser=_failing_parser,
            )

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(run())

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(ctx.exception.detail["code"], "INSIGHT_PARSE_FAILED")

    def test_get_company_profile_contract_refresh_false(self) -> None:
        class _ProfileRepo:
            def get_profile(self, *, company_id: str, area: str):
                return CompanyProfileStored(
                    company_id=company_id,
                    area=area,
                    profile_payload={"empresa": company_id, "resumen_departamentos": {"departments": []}},
                    updated_at="2026-03-02T10:00:00+00:00",
                )

        async def run() -> dict:
            return await get_company_profile(
                company_id="bcp",
                area="Operaciones",
                refresh=False,
                repository=_ProfileRepo(),
            )

        body = asyncio.run(run())
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["company_id"], "BCP")
        self.assertEqual(body["area"], "Operaciones")
        self.assertIn("profile_payload", body)

    def test_get_company_profile_not_found(self) -> None:
        class _EmptyProfileRepo:
            def get_profile(self, *, company_id: str, area: str):
                return None

        async def run() -> None:
            await get_company_profile(
                company_id="bcp",
                refresh=False,
                repository=_EmptyProfileRepo(),
            )

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(run())

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail["code"], "PROFILE_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
