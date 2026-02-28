import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.tools.qdrant_tool import QdrantConnection  # noqa: E402


class LinkStatusTests(unittest.TestCase):
    @patch("src.tools.qdrant_tool.requests.head")
    def test_verified_for_200(self, mock_head) -> None:
        mock_head.return_value.status_code = 200
        self.assertEqual(
            QdrantConnection._classify_link_status("https://example.com/ok"),
            "verified",
        )

    @patch("src.tools.qdrant_tool.requests.head")
    def test_inaccessible_for_404(self, mock_head) -> None:
        mock_head.return_value.status_code = 404
        self.assertEqual(
            QdrantConnection._classify_link_status("https://example.com/missing"),
            "inaccessible",
        )


if __name__ == "__main__":
    unittest.main()

