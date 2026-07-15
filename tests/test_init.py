from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPOSITORY, run


class InitTests(unittest.TestCase):
    def initialize(self, destination: Path):
        return run(REPOSITORY / "init.sh", "--target", destination)

    def test_initializes_an_empty_workspace_with_spaces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "fresh workspace"
            destination.mkdir()
            result = self.initialize(destination)
            self.assertEqual(0, result.returncode, result.stderr)
            for relative in (
                "AGENTS.md",
                "ARCHITECTURE.md",
                "VERSION",
                "scripts/task",
                "tasks/board.yaml",
                "tasks/task.schema.json",
                ".agents/skills/task-board/SKILL.md",
                ".agents/skills/task-plan/SKILL.md",
                "docs/design-docs/layered-testing-practice.md",
                "docs/generated/evidence/templates/validation-report.md",
            ):
                with self.subTest(relative=relative):
                    self.assertTrue((destination / relative).is_file())

            validation = run(destination / "scripts/task", "validate", cwd=destination)
            self.assertEqual(0, validation.returncode, validation.stderr)

    def test_repeated_initialization_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "project"
            destination.mkdir()
            first = self.initialize(destination)
            self.assertEqual(0, first.returncode, first.stderr)
            before = {
                path.relative_to(destination): path.read_bytes()
                for path in destination.rglob("*")
                if path.is_file()
            }
            second = self.initialize(destination)
            self.assertEqual(0, second.returncode, second.stderr)
            after = {
                path.relative_to(destination): path.read_bytes()
                for path in destination.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)

    def test_does_not_silently_overwrite_a_changed_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "project"
            destination.mkdir()
            first = self.initialize(destination)
            self.assertEqual(0, first.returncode, first.stderr)
            protected = destination / "AGENTS.md"
            marker = "synthetic local customization\n"
            protected.write_text(marker)

            second = self.initialize(destination)
            self.assertNotEqual(0, second.returncode)
            self.assertEqual(marker, protected.read_text())
            self.assertIn("AGENTS.md", second.stderr + second.stdout)


if __name__ == "__main__":
    unittest.main()
