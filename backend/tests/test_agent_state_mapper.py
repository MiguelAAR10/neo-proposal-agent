import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.api.deps import map_state_response


class AgentStateMapperTests(unittest.TestCase):
    def test_maps_defaults_and_auto_status(self) -> None:
        state = {
            "empresa": "BCP",
            "area": "Operaciones",
            "problema": "Reducir tiempos",
            "casos_encontrados": [],
            "casos_seleccionados_ids": [],
        }

        response = map_state_response("thread-1", state)

        self.assertEqual(response.thread_id, "thread-1")
        self.assertEqual(response.empresa, "BCP")
        self.assertEqual(response.status, "awaiting_selection")
        self.assertEqual(response.neo_cases, [])
        self.assertEqual(response.ai_cases, [])
        self.assertEqual(response.human_insights, [])

    def test_status_completed_when_proposal_exists(self) -> None:
        state = {
            "empresa": "Alicorp",
            "area": "TI",
            "problema": "Automatizar reportes",
            "casos_encontrados": [],
            "casos_seleccionados_ids": ["NEO-1"],
            "propuesta_final": "Texto final",
        }

        response = map_state_response("thread-2", state)
        self.assertEqual(response.status, "completed")

    def test_maps_human_insights_when_present(self) -> None:
        state = {
            "empresa": "BCP",
            "area": "Operaciones",
            "problema": "Reducir tiempos",
            "casos_encontrados": [],
            "casos_seleccionados_ids": [],
            "human_insights": [{"id": "h-1", "author": "Carlos Ruiz", "department": "TI"}],
        }
        response = map_state_response("thread-3", state)
        self.assertEqual(len(response.human_insights), 1)
        self.assertEqual(response.human_insights[0]["id"], "h-1")


if __name__ == "__main__":
    unittest.main()
