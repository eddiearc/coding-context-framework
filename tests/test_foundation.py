from __future__ import annotations

import unittest
from pathlib import Path

from tests.helpers import REPOSITORY


class FoundationTests(unittest.TestCase):
    def test_context_foundation_exists(self) -> None:
        required = (
            "README.md",
            "LICENSE",
            "VERSION",
            "AGENTS.md",
            "ARCHITECTURE.md",
            "init.sh",
            ".gitignore",
        )
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((REPOSITORY / relative).is_file())

    def test_version_is_consistent(self) -> None:
        self.assertEqual("0.1.0", (REPOSITORY / "VERSION").read_text().strip())
        readme = (REPOSITORY / "README.md").read_text()
        self.assertIn("v0.1.0", readme)

    def test_license_is_mit(self) -> None:
        license_text = (REPOSITORY / "LICENSE").read_text()
        self.assertIn("MIT License", license_text)
        self.assertIn("Permission is hereby granted", license_text)

    def test_readme_describes_context_workspace(self) -> None:
        readme = (REPOSITORY / "README.md").read_text()
        self.assertIn("Coding Context Framework", readme)
        self.assertIn("Git-backed", readme)
        self.assertIn("MIT", readme)

    def test_scripts_are_executable(self) -> None:
        for relative in (
            "init.sh",
            "scripts/check-context.sh",
            "scripts/check-publication.sh",
            "scripts/check-secrets.sh",
            "scripts/check-all.sh",
        ):
            path = REPOSITORY / relative
            with self.subTest(relative=relative):
                self.assertTrue(path.is_file())
                self.assertTrue(path.stat().st_mode & 0o111)


if __name__ == "__main__":
    unittest.main()
