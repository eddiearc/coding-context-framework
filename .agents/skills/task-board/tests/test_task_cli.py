from __future__ import annotations

import contextlib
import copy
import importlib.machinery
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / ".agents" / "skills" / "task-board" / "scripts" / "task"


def load_cli():
    if not SCRIPT.is_file():
        raise AssertionError(f"task CLI implementation is missing: {SCRIPT.relative_to(ROOT)}")
    loader = importlib.machinery.SourceFileLoader("coding_context_framework_task_cli", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class TaskCliTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cli = load_cli()

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name).resolve()
        (self.root / "tasks").mkdir()
        (self.root / "docs" / "plans").mkdir(parents=True)
        (self.root / "artifacts").mkdir()
        (self.root / "checkouts" / "example-api").mkdir(parents=True)
        (self.root / "AGENTS.md").write_text("# Synthetic fixture\n", encoding="utf-8")
        (self.root / "artifacts" / "result.txt").write_text("pass\n", encoding="utf-8")
        self.board_path = self.root / "tasks" / "board.yaml"
        self.write_board(self.empty_board())
        self.cli.repo_root = lambda: self.root
        self.cli.default_board_path = lambda: self.board_path

    @staticmethod
    def timestamp() -> str:
        return "2026-01-01T00:00:00Z"

    def empty_board(self) -> dict:
        timestamp = self.timestamp()
        return {
            "schema_version": 1,
            "schema_ref": "tasks/task.schema.json",
            "updated_at": timestamp,
            "status_vocab": sorted(self.cli.KNOWN_STATUSES),
            "domains": [
                {
                    "id": "shop",
                    "title": "Example Domain",
                    "status": "active",
                    "repos": [
                        {
                            "id": "example-api",
                            "name": "Example API",
                            "checkout": "checkouts/example-api",
                            "base_branch": "main",
                        }
                    ],
                    "context_docs": [],
                    "notes": [],
                    "updated_at": timestamp,
                }
            ],
            "tasks": [],
        }

    def write_board(self, board: dict) -> None:
        self.board_path.write_text(
            yaml.safe_dump(board, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    def read_board(self) -> dict:
        return yaml.safe_load(self.board_path.read_text(encoding="utf-8"))

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = self.cli.main([*args, "--board", str(self.board_path)])
        return result, stdout.getvalue(), stderr.getvalue()

    def make_plan(
        self,
        name: str,
        *,
        status: str = "Aligned",
        execution: str = "Allowed for this synthetic task.",
        title: str = "Synthetic checkout plan",
    ) -> Path:
        path = self.root / "docs" / "plans" / name
        path.write_text(
            f"# {title}\n\n"
            "## Plan Status\n\n"
            f"Status: {status}\n\n"
            f"Execution: {execution}\n\n"
            "## Goal / Scope\n\nSynthetic fixture.\n",
            encoding="utf-8",
        )
        return path

    def add_task(self, task_id: str, *, status: str = "backlog") -> None:
        result, _stdout, stderr = self.run_cli(
            "add-task",
            "--id",
            task_id,
            "--title",
            f"Task {task_id}",
            "--domain",
            "shop",
            "--repo",
            "example-api",
            "--status",
            status,
        )
        self.assertEqual(result, 0, stderr)

    def register_aligned(self, task_id: str, name: str = "aligned.md") -> Path:
        plan = self.make_plan(name)
        result, _stdout, stderr = self.run_cli(
            "register-plan",
            str(plan),
            "--id",
            task_id,
            "--domain",
            "shop",
            "--repo",
            "example-api",
        )
        self.assertEqual(result, 0, stderr)
        return plan

    def task(self, task_id: str) -> dict:
        return next(task for task in self.read_board()["tasks"] if task["id"] == task_id)

    def test_validate_list_show_add_task_and_requirement_refs(self) -> None:
        result, stdout, stderr = self.run_cli("validate")
        self.assertEqual(result, 0, stderr)
        self.assertIn("valid board", stdout)

        result, stdout, stderr = self.run_cli("list", "--format", "json")
        self.assertEqual(result, 0, stderr)
        self.assertEqual(json.loads(stdout), [])

        result, stdout, stderr = self.run_cli(
            "add-task",
            "--id",
            "example.checkout",
            "--title",
            "Add checkout",
            "--domain",
            "shop",
            "--repo",
            "example-api",
            "--requirement-ref",
            "REQ-001",
            "--requirement-ref",
            "docs/spec.md#checkout",
        )
        self.assertEqual(result, 0, stderr)
        self.assertIn("added: example.checkout", stdout)

        result, stdout, stderr = self.run_cli("show", "example.checkout", "--format", "json")
        self.assertEqual(result, 0, stderr)
        shown = json.loads(stdout)
        self.assertEqual(shown["requirement_refs"], ["REQ-001", "docs/spec.md#checkout"])
        self.assertEqual(shown["plan"]["path"], None)

        result, stdout, stderr = self.run_cli("list", "--format", "yaml")
        self.assertEqual(result, 0, stderr)
        self.assertEqual(yaml.safe_load(stdout)[0]["id"], "example.checkout")

        result, stdout, stderr = self.run_cli("list", "--status", "backlog")
        self.assertEqual(result, 0, stderr)
        self.assertIn("example.checkout", stdout)

        result, _stdout, stderr = self.run_cli("show", "missing.task", "--format", "json")
        self.assertEqual(result, 1)
        self.assertIn("task not found", stderr)

    def test_add_note_evidence_and_status_transitions_are_idempotent(self) -> None:
        self.register_aligned("example.release")

        for _ in range(2):
            result, _stdout, stderr = self.run_cli(
                "add-note", "example.release", "Synthetic review note."
            )
            self.assertEqual(result, 0, stderr)
        self.assertEqual(self.task("example.release")["notes"], ["Synthetic review note."])

        evidence_args = (
            "add-evidence",
            "example.release",
            "--type",
            "local-cli",
            "--path",
            "artifacts/result.txt",
            "--status",
            "pass",
            "--summary",
            "Synthetic CLI passed.",
        )
        for _ in range(2):
            result, _stdout, stderr = self.run_cli(*evidence_args)
            self.assertEqual(result, 0, stderr)
        self.assertEqual(len(self.task("example.release")["evidence"]), 1)

        result, _stdout, stderr = self.run_cli("set-status", "example.release", "review")
        self.assertEqual(result, 0, stderr)
        result, stdout, stderr = self.run_cli("set-status", "example.release", "review")
        self.assertEqual(result, 0, stderr)
        self.assertIn("unchanged", stdout)
        result, _stdout, stderr = self.run_cli("set-status", "example.release", "done")
        self.assertEqual(result, 0, stderr)
        self.assertEqual(self.task("example.release")["status"], "done")

    def test_status_failure_and_blocked_intake_are_atomic(self) -> None:
        self.add_task("example.unplanned")
        before = self.board_path.read_bytes()
        result, _stdout, stderr = self.run_cli("set-status", "example.unplanned", "review")
        self.assertEqual(result, 1)
        self.assertIn("would make board invalid", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

        result, _stdout, stderr = self.run_cli(
            "add-task",
            "--id",
            "example.blocked",
            "--title",
            "Blocked intake",
            "--domain",
            "shop",
            "--status",
            "blocked",
        )
        self.assertEqual(result, 0, stderr)
        self.assertTrue(self.task("example.blocked")["notes"])

    def test_register_plan_creates_and_attaches_with_strict_pairing(self) -> None:
        aligned = self.make_plan("register.md", title="Checkout registration")
        result, _stdout, stderr = self.run_cli(
            "register-plan",
            str(aligned),
            "--id",
            "example.registered",
            "--domain",
            "shop",
            "--repo",
            "example-api",
            "--requirement-ref",
            "REQ-001",
            "--branch",
            "feature/checkout",
            "--worktree",
            "checkouts/example-api",
            "--base-branch",
            "example-api=main",
        )
        self.assertEqual(result, 0, stderr)
        task = self.task("example.registered")
        self.assertEqual(task["title"], "Checkout registration")
        self.assertEqual(task["status"], "ready")
        self.assertEqual(task["requirement_refs"], ["REQ-001"])
        self.assertEqual(task["plan"]["status"], "aligned")
        self.assertEqual(task["plan"]["execution"], "allowed")

        before = self.board_path.read_bytes()
        result, _stdout, stderr = self.run_cli(
            "register-plan",
            str(aligned),
            "--id",
            "example.registered",
            "--domain",
            "shop",
            "--repo",
            "example-api",
        )
        self.assertEqual(result, 1)
        self.assertIn("already has a plan", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

        self.add_task("example.existing")
        attach = self.make_plan("attach.md")
        result, _stdout, stderr = self.run_cli(
            "register-plan",
            str(attach),
            "--id",
            "example.existing",
            "--domain",
            "shop",
            "--repo",
            "example-api",
            "--requirement-ref",
            "REQ-002",
            "--requirement-ref",
            "REQ-002",
        )
        self.assertEqual(result, 0, stderr)
        self.assertEqual(self.task("example.existing")["requirement_refs"], ["REQ-002"])

        draft = self.make_plan(
            "draft.md",
            status="Draft - waiting for user alignment",
            execution="Blocked until alignment.",
        )
        before = self.board_path.read_bytes()
        result, _stdout, stderr = self.run_cli(
            "register-plan",
            str(draft),
            "--id",
            "example.invalid-draft",
            "--domain",
            "shop",
            "--repo",
            "example-api",
            "--status",
            "ready",
        )
        self.assertEqual(result, 1)
        self.assertIn("draft plan requires task status", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

        mismatch = self.make_plan("mismatch.md", execution="Blocked unexpectedly.")
        result, _stdout, stderr = self.run_cli(
            "register-plan",
            str(mismatch),
            "--id",
            "example.mismatch",
            "--domain",
            "shop",
            "--repo",
            "example-api",
        )
        self.assertEqual(result, 1)
        self.assertIn("Execution", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

    def test_set_plan_metadata_preserves_clears_and_fails_atomically(self) -> None:
        old = self.make_plan("old.md")
        result, _stdout, stderr = self.run_cli(
            "register-plan",
            str(old),
            "--id",
            "example.metadata",
            "--domain",
            "shop",
            "--repo",
            "example-api",
            "--note",
            "May wait for alignment.",
            "--branch",
            "feature/old",
            "--worktree",
            "checkouts/example-api",
            "--base-branch",
            "example-api=main",
        )
        self.assertEqual(result, 0, stderr)

        new = self.make_plan("new.md")
        result, _stdout, stderr = self.run_cli(
            "set-plan-metadata", "example.metadata", str(new)
        )
        self.assertEqual(result, 0, stderr)
        self.assertEqual(self.task("example.metadata")["plan"]["branch"], "feature/old")

        result, _stdout, stderr = self.run_cli(
            "set-plan-metadata",
            "example.metadata",
            str(new),
            "--branch",
            "feature/new",
            "--worktree",
            "checkouts/example-api",
            "--base-branch",
            "example-api=main",
        )
        self.assertEqual(result, 0, stderr)
        self.assertEqual(self.task("example.metadata")["plan"]["branch"], "feature/new")

        result, _stdout, stderr = self.run_cli(
            "set-plan-metadata",
            "example.metadata",
            str(new),
            "--clear-branch",
            "--clear-worktrees",
            "--clear-base-branches",
        )
        self.assertEqual(result, 0, stderr)
        plan = self.task("example.metadata")["plan"]
        self.assertIsNone(plan["branch"])
        self.assertEqual(plan["worktrees"], [])
        self.assertEqual(plan["base_branches"], {})

        before = self.board_path.read_bytes()
        missing = self.root / "docs" / "plans" / "missing.md"
        result, _stdout, stderr = self.run_cli(
            "set-plan-metadata", "example.metadata", str(missing)
        )
        self.assertEqual(result, 1)
        self.assertIn("plan file not found", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

        result, _stdout, stderr = self.run_cli(
            "set-plan-metadata",
            "example.metadata",
            str(new),
            "--base-branch",
            "unknown-repo=main",
        )
        self.assertEqual(result, 1)
        self.assertIn("not listed in task.repos", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

        draft = self.make_plan(
            "metadata-draft.md",
            status="Draft - waiting for user alignment",
            execution="Blocked until alignment.",
        )
        result, _stdout, stderr = self.run_cli(
            "set-plan-metadata", "example.metadata", str(draft)
        )
        self.assertEqual(result, 1)
        self.assertIn("draft plan requires task status", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

        result, _stdout, stderr = self.run_cli(
            "set-plan-metadata",
            "example.metadata",
            str(draft),
            "--task-status",
            "blocked",
        )
        self.assertEqual(result, 0, stderr)
        self.assertEqual(self.task("example.metadata")["status"], "blocked")

    def test_link_unlink_tree_and_hierarchy_invariants(self) -> None:
        for task_id in ("example.parent", "example.child", "example.other"):
            self.add_task(task_id)

        result, _stdout, stderr = self.run_cli(
            "link-sub-task", "example.parent", "example.child"
        )
        self.assertEqual(result, 0, stderr)
        result, stdout, stderr = self.run_cli("list", "--tree")
        self.assertEqual(result, 0, stderr)
        self.assertIn("↳ example.child", stdout)

        before = self.board_path.read_bytes()
        result, _stdout, stderr = self.run_cli(
            "link-sub-task", "example.other", "example.child"
        )
        self.assertEqual(result, 1)
        self.assertIn("already belongs to parent", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

        result, _stdout, stderr = self.run_cli(
            "link-sub-task", "example.child", "example.parent"
        )
        self.assertEqual(result, 1)
        self.assertIn("cycle", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

        result, _stdout, stderr = self.run_cli(
            "link-sub-task", "example.parent", "example.parent"
        )
        self.assertEqual(result, 1)
        self.assertIn("own sub-task", stderr)

        result, _stdout, stderr = self.run_cli(
            "unlink-sub-task", "example.parent", "example.child"
        )
        self.assertEqual(result, 0, stderr)
        result, stdout, stderr = self.run_cli(
            "unlink-sub-task", "example.parent", "example.child"
        )
        self.assertEqual(result, 0, stderr)
        self.assertIn("unchanged", stdout)

        board = self.read_board()
        by_id = {task["id"]: task for task in board["tasks"]}
        by_id["example.parent"]["sub_tasks"] = ["example.missing"]
        errors = self.cli.validate_board(board)[2]
        self.assertTrue(any("unknown sub-task" in error for error in errors), errors)

        cycle_board = copy.deepcopy(board)
        cycle_by_id = {task["id"]: task for task in cycle_board["tasks"]}
        cycle_by_id["example.parent"]["sub_tasks"] = ["example.child"]
        cycle_by_id["example.child"]["sub_tasks"] = ["example.parent"]
        errors = self.cli.validate_board(cycle_board)[2]
        self.assertTrue(any("cycle" in error for error in errors), errors)

    def test_repository_paths_cannot_escape_and_fail_without_writes(self) -> None:
        outside_dir = Path(self.tempdir.name).parent
        outside = outside_dir / "outside-task-board-fixture.txt"
        outside.write_text("outside\n", encoding="utf-8")
        self.addCleanup(outside.unlink, missing_ok=True)

        before = self.board_path.read_bytes()
        result, _stdout, stderr = self.run_cli(
            "add-task",
            "--id",
            "example.escape",
            "--title",
            "Escape attempt",
            "--domain",
            "shop",
            "--context-doc",
            f"{outside}=must stay local",
        )
        self.assertEqual(result, 1)
        self.assertIn("repository-relative", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

        symlink = self.root / "artifacts" / "escape.txt"
        symlink.symlink_to(outside)
        result, _stdout, stderr = self.run_cli(
            "add-task",
            "--id",
            "example.symlink",
            "--title",
            "Symlink escape",
            "--domain",
            "shop",
            "--context-doc",
            "artifacts/escape.txt=must stay local",
        )
        self.assertEqual(result, 1)
        self.assertIn("escapes repository root", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)

        self.add_task("example.evidence-path")
        before = self.board_path.read_bytes()
        result, _stdout, stderr = self.run_cli(
            "add-evidence",
            "example.evidence-path",
            "--type",
            "local",
            "--path",
            str(outside),
            "--status",
            "pass",
            "--summary",
            "Must reject an outside path.",
        )
        self.assertEqual(result, 1)
        self.assertIn("repository-relative", stderr)
        self.assertEqual(self.board_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
