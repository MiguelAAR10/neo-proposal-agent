import os
import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import Settings  # noqa: E402


class SettingsTests(unittest.TestCase):
    def test_allowed_origins_parsing(self) -> None:
        s = Settings(
            allowed_origins_raw="http://localhost:3000, https://app.neo.com ",
            app_env="development",
        )
        self.assertEqual(
            s.allowed_origins,
            ["http://localhost:3000", "https://app.neo.com"],
        )

    def test_non_local_env_detection(self) -> None:
        self.assertTrue(Settings(app_env="production").is_non_local_env)
        self.assertTrue(Settings(app_env="staging").is_non_local_env)
        self.assertFalse(Settings(app_env="development").is_non_local_env)


if __name__ == "__main__":
    unittest.main()

