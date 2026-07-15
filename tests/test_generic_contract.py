from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

from tests.helpers import REPOSITORY


class GenericAbstractionContractTests(unittest.TestCase):
    def test_repository_contains_only_generic_framework_content(self) -> None:
        forbidden = {
            "personal brand": "Id" + "an",
            "reference business": "El" + "ys",
            "extracted template": "agent" + "-work-context",
            "tutorial brand": "ac" + "me",
            "tutorial task": "TASK" + "-123",
        }
        violations: list[str] = []
        for path in REPOSITORY.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(REPOSITORY)
            if any(part in {".git", "__pycache__"} for part in relative.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for label, marker in forbidden.items():
                pattern = rf"(?<![A-Za-z0-9]){re.escape(marker)}(?![A-Za-z0-9])"
                if re.search(pattern, text, re.IGNORECASE):
                    violations.append(f"{label}: {relative}")
        self.assertEqual([], violations)

    def test_instance_and_tutorial_content_is_absent(self) -> None:
        self.assertFalse((REPOSITORY / "examples").exists())
        completed = REPOSITORY / "docs/exec-plans/completed"
        reports = REPOSITORY / "docs/generated/evidence/reports"
        self.assertEqual(
            [".gitkeep"],
            sorted(path.name for path in completed.iterdir()),
        )
        self.assertEqual(
            [".gitkeep"],
            sorted(path.name for path in reports.iterdir()),
        )

    def test_root_board_uses_generic_empty_defaults(self) -> None:
        board = yaml.safe_load(
            (REPOSITORY / "tasks/board.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual([], board["tasks"])
        self.assertEqual(["general"], [domain["id"] for domain in board["domains"]])
        self.assertEqual(
            ["context-repository"],
            [repo["id"] for repo in board["domains"][0]["repos"]],
        )

    def test_docs_use_framework_identity(self) -> None:
        readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
        self.assertIn("# Coding Context Framework", readme)
        self.assertIn("通用", readme)


if __name__ == "__main__":
    unittest.main()
