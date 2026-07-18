from __future__ import annotations

import os
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
                "CLAUDE.md",
                "ARCHITECTURE.md",
                "VERSION",
                "scripts/task",
                "tasks/board.yaml",
                "tasks/task.schema.json",
                ".agents/skills/task-board/SKILL.md",
                ".agents/skills/task-plan/SKILL.md",
                ".agents/skills/plan-go/SKILL.md",
                ".agents/skills/plan-go/agents/openai.yaml",
                ".agents/skills/plan-go/LICENSE",
                ".agents/skills/plan-go/scripts/loop-evidence",
                ".agents/skills/plan-go/scripts/loop_evidence.py",
                ".agents/skills/plan-go/scripts/loop_spec.sh",
                "docs/design-docs/layered-testing-practice.md",
                "docs/exec-plans/_template.md",
                "docs/generated/evidence/templates/validation-report.md",
            ):
                with self.subTest(relative=relative):
                    self.assertTrue((destination / relative).is_file())

            self.assertEqual("@AGENTS.md\n", (destination / "CLAUDE.md").read_text())
            for name in ("task-board", "task-plan", "plan-go"):
                with self.subTest(claude_skill=name):
                    link = destination / ".claude/skills" / name
                    self.assertTrue(link.is_symlink())
                    self.assertEqual(
                        f"../../.agents/skills/{name}", os.readlink(link)
                    )
                    self.assertEqual(
                        (destination / ".agents/skills" / name).resolve(),
                        link.resolve(strict=True),
                    )

            for relative in (
                ".agents/skills/plan-go/scripts/loop-evidence",
                ".agents/skills/plan-go/scripts/loop_evidence.py",
                ".agents/skills/plan-go/scripts/loop_spec.sh",
            ):
                with self.subTest(executable=relative):
                    self.assertTrue((destination / relative).stat().st_mode & 0o111)

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
            for name in ("task-board", "task-plan", "plan-go"):
                self.assertEqual(
                    f"../../.agents/skills/{name}",
                    os.readlink(destination / ".claude/skills" / name),
                )

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

    def test_does_not_overwrite_a_conflicting_claude_skill_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "project"
            conflict = destination / ".claude/skills/task-plan"
            conflict.mkdir(parents=True)
            (conflict / "SKILL.md").write_text("local Claude skill\n")

            result = self.initialize(destination)

            self.assertNotEqual(0, result.returncode)
            self.assertTrue(conflict.is_dir())
            self.assertIn(".claude/skills/task-plan", result.stderr + result.stdout)

    def test_migrates_legacy_claude_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "project"
            (destination / ".claude").mkdir(parents=True)
            os.symlink("AGENTS.md", destination / "CLAUDE.md")
            os.symlink("../.agents/skills", destination / ".claude/skills")

            result = self.initialize(destination)

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse((destination / "CLAUDE.md").is_symlink())
            self.assertEqual("@AGENTS.md\n", (destination / "CLAUDE.md").read_text())
            self.assertFalse((destination / ".claude/skills").is_symlink())
            for name in ("task-board", "task-plan", "plan-go"):
                self.assertEqual(
                    f"../../.agents/skills/{name}",
                    os.readlink(destination / ".claude/skills" / name),
                )


if __name__ == "__main__":
    unittest.main()
