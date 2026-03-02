import importlib.util
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.api.intel import get_human_insight_repository, get_insight_parser  # noqa: E402
from src.api.main import app  # noqa: E402
from src.repositories.sqlite_repositories import SQLiteHumanInsightRepository  # noqa: E402
from src.services.errors import InsightParseError  # noqa: E402

HAS_SQLALCHEMY = importlib.util.find_spec("sqlalchemy") is not None

@unittest.skipUnless(HAS_SQLALCHEMY, "SQLAlchemy no disponible en este entorno")
class IntelEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = SQLiteHumanInsightRepository("sqlite:///:memory:")
        app.dependency_overrides[get_human_insight_repository] = lambda: self.repo
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.client.close()

    def test_create_human_insight_contract_and_idempotency(self) -> None:
        body = {
            "seller_id": "seller-1",
            "text": "El gerente de operaciones teme sobrecostos y pide ROI en 3 meses.",
            "source": "chat_form",
        }
        first = self.client.post("/intel/company/bcp/insights", json=body)
        self.assertEqual(first.status_code, 200)
        first_payload = first.json()
        self.assertEqual(first_payload["status"], "success")
        self.assertEqual(first_payload["company_id"], "BCP")
        self.assertEqual(len(first_payload["structured_payload"]), 3)

        second = self.client.post("/intel/company/bcp/insights", json=body)
        self.assertEqual(second.status_code, 200)
        second_payload = second.json()
        self.assertEqual(second_payload["insight_id"], first_payload["insight_id"])

    def test_returns_typed_error_when_parser_fails(self) -> None:
        def _failing_parser(_: str):
            raise InsightParseError("no se pudo parsear")

        app.dependency_overrides[get_insight_parser] = lambda: _failing_parser
        response = self.client.post(
            "/intel/company/bcp/insights",
            json={
                "seller_id": "seller-2",
                "text": "Texto de prueba para parser.",
                "source": "chat_form",
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"]["code"], "INSIGHT_PARSE_FAILED")


if __name__ == "__main__":
    unittest.main()
