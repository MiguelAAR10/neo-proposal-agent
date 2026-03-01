import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.services.prioritized_clients import (  # noqa: E402
    get_prioritized_clients_catalog,
    get_prioritized_client_context,
    is_prioritized_client,
    normalize_company_name,
)


class PrioritizedClientsTests(unittest.TestCase):
    def test_normalize_company_name_handles_accents_and_spaces(self) -> None:
        self.assertEqual(normalize_company_name("  Pacífico  "), "PACIFICO")

    def test_is_prioritized_client_true_for_known_top12(self) -> None:
        self.assertTrue(is_prioritized_client("Interbank"))
        self.assertTrue(is_prioritized_client("plaza vea"))

    def test_get_prioritized_client_context_returns_business_context(self) -> None:
        context = get_prioritized_client_context("BCP")
        self.assertEqual(context["client_name"], "BCP")
        self.assertIn("priorities", context)
        self.assertIn("constraints", context)
        self.assertTrue(str(context.get("logo_path", "")).startswith("/logos/companies/"))

    def test_catalog_includes_logo_and_brand_fields(self) -> None:
        catalog = get_prioritized_clients_catalog()
        bcp = next((item for item in catalog if item["name"] == "BCP"), None)
        self.assertIsNotNone(bcp)
        assert bcp is not None
        self.assertIn("logo_path", bcp)
        self.assertIn("brand_color", bcp)


if __name__ == "__main__":
    unittest.main()
