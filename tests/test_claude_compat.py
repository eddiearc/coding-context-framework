from __future__ import annotations

import os
import unittest

from tests.helpers import REPOSITORY


class ClaudeCompatibilityTests(unittest.TestCase):
    def test_project_instructions_import_agents(self) -> None:
        self.assertEqual("@AGENTS.md\n", (REPOSITORY / "CLAUDE.md").read_text())

    def test_project_skills_link_to_canonical_agent_skills(self) -> None:
        for name in ("task-board", "task-plan", "plan-go", "herdr-workflow"):
            with self.subTest(name=name):
                link = REPOSITORY / ".claude/skills" / name
                canonical = REPOSITORY / ".agents/skills" / name
                self.assertTrue(link.is_symlink())
                self.assertEqual(f"../../.agents/skills/{name}", os.readlink(link))
                self.assertEqual(canonical.resolve(), link.resolve(strict=True))


if __name__ == "__main__":
    unittest.main()
