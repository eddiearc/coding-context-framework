from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SKILL_ROOT = ROOT / ".agents" / "skills" / "task-board"


class ContractFilesTest(unittest.TestCase):
    def test_required_task_board_files_exist(self) -> None:
        expected = [
            ROOT / "tasks" / "board.yaml",
            ROOT / "tasks" / "task.schema.json",
            ROOT / "scripts" / "task",
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "scripts" / "task",
        ]
        for path in expected:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertTrue(path.is_file(), f"missing contract file: {path.relative_to(ROOT)}")

    def test_schema_uses_generic_requirement_refs(self) -> None:
        schema_path = ROOT / "tasks" / "task.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        task = schema["$defs"]["task"]

        self.assertIn("requirement_refs", task["required"])
        refs = task["properties"]["requirement_refs"]
        self.assertEqual(refs["type"], "array")
        self.assertTrue(refs["uniqueItems"])
        self.assertEqual(refs["items"]["type"], "string")
        self.assertEqual(refs["items"]["minLength"], 1)

        retired_field = "requirement" + "_" + "rows"
        retired_flag = "--requirement" + "-" + "row"
        owned_files = [
            schema_path,
            ROOT / "tasks" / "board.yaml",
            ROOT / "scripts" / "task",
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "scripts" / "task",
        ]
        for path in owned_files:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn(retired_field, text)
                self.assertNotIn(retired_flag, text)


if __name__ == "__main__":
    unittest.main()
