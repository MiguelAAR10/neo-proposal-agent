import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.services.search_service import _EMBED_CACHE, _build_search_payload, _cache_get, _cache_set


class SearchServicePayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        _EMBED_CACHE.clear()

    def test_both_switch_segments_and_sets_top_match_global(self) -> None:
        raw_results = [
            {
                "id": "AI-001",
                "tipo": "AI",
                "titulo": "AI top",
                "problema": "p",
                "solucion": "s",
                "score": 0.94,
                "url_slide": "https://example.com/ai",
            },
            {
                "id": "NEO-001",
                "tipo": "NEO",
                "titulo": "Neo second",
                "problema": "p",
                "solucion": "s",
                "score": 0.80,
                "url_slide": "https://example.com/neo",
            },
        ]

        payload = _build_search_payload(
            problema="test",
            switch="both",
            raw_results=raw_results,
            latencia_ms=120,
        )

        self.assertEqual(payload["switch_usado"], "both")
        self.assertEqual(payload["neo_cases"][0]["id"], "NEO-001")
        self.assertEqual(payload["ai_cases"][0]["id"], "AI-001")
        self.assertEqual(payload["casos"][0]["id"], "NEO-001")
        self.assertIn("top_match_global", payload)
        self.assertEqual(payload["top_match_global"]["id"], "AI-001")

    def test_neo_switch_returns_only_neo_cases(self) -> None:
        raw_results = [
            {
                "id": "NEO-010",
                "tipo": "NEO",
                "titulo": "Neo",
                "problema": "p",
                "solucion": "s",
                "score": 0.77,
                "url_slide": "https://example.com/neo",
            }
        ]

        payload = _build_search_payload(
            problema="neo",
            switch="neo",
            raw_results=raw_results,
            latencia_ms=80,
        )

        self.assertEqual(len(payload["neo_cases"]), 1)
        self.assertEqual(len(payload["ai_cases"]), 0)
        self.assertEqual(payload["total"], 1)
        self.assertNotIn("top_match_global", payload)

    def test_local_cache_normalizes_query(self) -> None:
        _cache_set("  Mejorar   scoring  ", [0.1, 0.2, 0.3])
        got = _cache_get("mejorar scoring")
        self.assertEqual(got, [0.1, 0.2, 0.3])


if __name__ == "__main__":
    unittest.main()
