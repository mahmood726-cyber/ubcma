from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "e156-submission" / "config.json"
README_PATH = REPO_ROOT / "README.md"


class PortabilityContractTests(unittest.TestCase):
    def test_submission_config_uses_repo_relative_root(self) -> None:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["path"], "..")
        self.assertEqual((CONFIG_PATH.parent / payload["path"]).resolve(), REPO_ROOT.resolve())

    def test_release_surface_has_no_hardcoded_ubcma_root(self) -> None:
        for path in (CONFIG_PATH, README_PATH):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(r"C:\ubcma", text, path.as_posix())
            self.assertNotIn("C:/ubcma", text, path.as_posix())


if __name__ == "__main__":
    unittest.main()
