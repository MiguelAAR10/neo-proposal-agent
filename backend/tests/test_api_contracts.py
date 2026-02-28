import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.api.main import SearchRequest, api_search, get_agent_state  # noqa: E402
from src.services.errors import ExternalDependencyTimeout  # noqa: E402


class ApiContractTests(unittest.TestCase):
    def test_api_search_success_contract(self) -> None:
        payload = {
            "status": "success",
            "problema_user": "mejorar scoring",
            "switch_usado": "both",
            "total": 1,
            "latencia_ms": 123,
            "neo_cases": [],
            "ai_cases": [],
            "casos": [],
        }

        async def run() -> dict:
            with patch("src.api.main.search_cases_with_sla", new=AsyncMock(return_value=payload)):
                return await api_search(SearchRequest(problema="mejorar scoring con IA", switch="both"))

        result = asyncio.run(run())
        self.assertEqual(result["status"], "success")
        self.assertIn("casos", result)
        self.assertIn("total", result)

    def test_api_search_timeout_contract(self) -> None:
        async def run() -> None:
            with patch(
                "src.api.main.search_cases_with_sla",
                new=AsyncMock(side_effect=ExternalDependencyTimeout("Gemini", 2.0)),
            ):
                await api_search(SearchRequest(problema="mejorar scoring con IA", switch="both"))

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(run())

        exc = ctx.exception
        self.assertEqual(exc.status_code, 504)
        self.assertEqual(exc.detail["code"], "EXTERNAL_TIMEOUT")
        self.assertIn("Gemini", exc.detail["message"])

    def test_get_agent_state_not_found_contract(self) -> None:
        async def run() -> None:
            with patch("src.api.main.graph.aget_state", new=AsyncMock(return_value=type("S", (), {"values": None})())):
                await get_agent_state("thread-x")

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(run())

        exc = ctx.exception
        self.assertEqual(exc.status_code, 404)
        self.assertEqual(exc.detail["code"], "SESSION_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()

