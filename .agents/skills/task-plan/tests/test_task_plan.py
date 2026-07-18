"""Contract tests for the repository-local task-plan skill and checker."""

import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / ".agents/skills/task-plan/SKILL.md"
CHECKER = ROOT / ".agents/skills/task-plan/scripts/check-task-plan.sh"
README = ROOT / "README.md"


LAYERS = (
    ("Unit", "Yes", "python3 -m unittest", "Pure rules", "Runtime wiring"),
    (
        "Component / Module",
        "No",
        "Skip: no component boundary",
        "Omission is explicit",
        "Module regressions",
    ),
    (
        "Contract",
        "Yes",
        "Validate task schema",
        "Stable document contract",
        "External behavior",
    ),
    (
        "Mock E2E",
        "No",
        "Skip: no browser flow",
        "Omission is explicit",
        "Browser regressions",
    ),
    (
        "Real API / CLI",
        "Yes",
        "Run the checker CLI",
        "Public CLI behavior",
        "Hosted environments",
    ),
    (
        "Real Backend E2E",
        "No",
        "Skip: no backend",
        "Omission is explicit",
        "Backend integration",
    ),
    (
        "Evidence / Demo",
        "Yes",
        "Save test output",
        "Reviewable validation",
        "Future environment drift",
    ),
)


def make_plan(status="Aligned", execution="Allowed"):
    rows = "\n".join(f"| {' | '.join(row)} |" for row in LAYERS)
    plan = textwrap.dedent(
        f"""\
        # EXAMPLE-001 Task Plan
        Date: 2026-01-01

        ## Plan Status

        Status: {status}
        Execution: {execution}. Follow the registered task before implementation.

        ## Goal / Scope

        Define a synthetic example-api change.

        ## Context Sources Checked

        - AGENTS.md
        - ARCHITECTURE.md

        ## Alignment Status

        Status: {status}

        ## Human Alignment Log

        Alignment loop was skipped because this is a checker fixture.

        ## Task / Worktree / Branch Plan

        - Task: EXAMPLE-001
        - Workspace: /workspace/project

        ## Contract / Behavior

        - Keep inputs and outputs deterministic.

        ## Validation Plan

        Test Boundary: repository-local CLI and plan document
        Why this boundary: It covers the reusable public contract.
        Why not narrower: Unit-only checks miss CLI exit behavior.
        Why not broader: The task has no hosted service.
        Dependencies: Bash, awk, and Python 3 for the test suite.
        Command: python3 -m unittest discover -s .agents/skills/task-plan/tests -v
        Expected RED: Tests fail while the checker and skill are absent.
        Expected GREEN: All task-plan contract tests pass.
        Missing evidence policy: Record concrete failures and recovery paths.
        Minimum attempts before accepting missing evidence: 2
        Covered layers: Unit, Contract, Real API / CLI, Evidence / Demo.
        Entry / Command / Artifact per layer: See the table below.
        Omitted layers with reasons / risks: See rows marked No.

        | Layer | Required | Entry / Command / Artifact | Proves | Does not prove / Risk |
        | --- | --- | --- | --- | --- |
        @@LAYER_ROWS@@

        ## Evidence Plan

        - Preserve command output.

        ## Risks / Open Questions

        - None for this synthetic fixture.

        ## Implementation Recommendation

        - Use the repository's documented implementation workflow.
        """
    )
    return plan.replace("@@LAYER_ROWS@@", rows)


def make_feedback_loop_plan():
    return make_plan().replace(
        "Covered layers: Unit, Contract, Real API / CLI, Evidence / Demo.\n"
        "Entry / Command / Artifact per layer: See the table below.\n"
        "Omitted layers with reasons / risks: See rows marked No.\n\n"
        "| Layer | Required | Entry / Command / Artifact | Proves | Does not prove / Risk |\n"
        "| --- | --- | --- | --- | --- |\n"
        + "\n".join(f"| {' | '.join(row)} |" for row in LAYERS),
        "Selected feedback loops: Unit / Module tests, structural checks, Real CLI / Workflow.\n"
        "Entry / Command / Artifact per feedback loop: See the table below.\n"
        "Residual risks: Hosted API behavior is outside this task.\n\n"
        "| Feedback loop | Entry / Command / Artifact | Proves | Does not prove / Risk |\n"
        "| --- | --- | --- | --- |\n"
        "| Unit / Module tests | python3 -m unittest | Local rules | Runtime wiring |\n"
        "| structural checks | Validate task schema | Stable structure | Hosted behavior |\n"
        "| Real CLI / Workflow | Run the checker CLI | Public CLI behavior | External APIs |",
    )


class TaskPlanContractTests(unittest.TestCase):
    def run_checker(self, plan, *extra_args):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan with spaces.md"
            path.write_text(plan, encoding="utf-8")
            return subprocess.run(
                [str(CHECKER), str(path), *extra_args],
                text=True,
                capture_output=True,
                check=False,
            )

    def test_skill_is_public_and_documents_the_contract(self):
        content = SKILL.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")
        self.assertIn("name: task-plan", content)
        self.assertIn("check-task-plan.sh", content)
        for section in (
            "Plan Status",
            "Goal / Scope",
            "Context Sources Checked",
            "Alignment Status",
            "Human Alignment Log",
            "Task / Worktree / Branch Plan",
            "Contract / Behavior",
            "Validation Plan",
            "Evidence Plan",
            "Risks / Open Questions",
            "Implementation Recommendation",
        ):
            self.assertIn(section, content)
        self.assertIn("--requirement-ref", content)
        public_guidance = content + readme
        self.assertNotIn("非平凡", public_guidance)
        self.assertNotIn("non-trivial", public_guidance)
        self.assertIn("complex or multi-step work", content)
        self.assertIn("复杂或包含多个步骤的任务", readme)
        self.assertIn("do not add plan sections or fields solely for scope", content)
        self.assertIn("outside `In scope` as follow-up work", content)

    def test_aligned_plan_passes(self):
        result = self.run_checker(make_plan())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("task plan structure check passed", result.stdout)

    def test_draft_blocked_plan_passes(self):
        result = self.run_checker(
            make_plan("Draft - waiting for user alignment", "Blocked")
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_selectable_feedback_loop_plan_passes(self):
        result = self.run_checker(make_feedback_loop_plan())
        self.assertEqual(0, result.returncode, result.stderr)

    def test_feedback_loop_plan_does_not_require_every_category(self):
        plan = make_feedback_loop_plan().replace(
            "| Real CLI / Workflow | Run the checker CLI | Public CLI behavior | External APIs |\n",
            "",
        ).replace(
            "Selected feedback loops: Unit / Module tests, structural checks, Real CLI / Workflow.",
            "Selected feedback loops: Unit / Module tests, structural checks.",
        )
        result = self.run_checker(plan)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_feedback_loop_plan_rejects_unknown_or_duplicate_rows(self):
        unknown = make_feedback_loop_plan().replace(
            "| Real CLI / Workflow | Run the checker CLI | Public CLI behavior | External APIs |",
            "| Mystery | Save test output | Reproducible evidence | Future drift |",
        )
        self.assertEqual(1, self.run_checker(unknown).returncode)

        duplicate = make_feedback_loop_plan().replace(
            "| Real CLI / Workflow | Run the checker CLI | Public CLI behavior | External APIs |",
            "| structural checks | Save test output | Reproducible evidence | Future drift |",
        )
        self.assertEqual(1, self.run_checker(duplicate).returncode)

    def test_feedback_loop_selected_field_rejects_unknown_duplicate_and_mismatch(self):
        selected = (
            "Selected feedback loops: Unit / Module tests, structural checks, "
            "Real CLI / Workflow."
        )
        cases = {
            "unknown": "Selected feedback loops: Unit / Module tests, Mystery.",
            "duplicate": (
                "Selected feedback loops: Unit / Module tests, structural checks, "
                "structural checks, Real CLI / Workflow."
            ),
            "mismatch": (
                "Selected feedback loops: Unit / Module tests, Real CLI / Workflow."
            ),
        }
        for name, replacement in cases.items():
            with self.subTest(name=name):
                result = self.run_checker(
                    make_feedback_loop_plan().replace(selected, replacement)
                )
                self.assertEqual(1, result.returncode)

    def test_feedback_loop_rejects_evidence_only(self):
        plan = make_feedback_loop_plan().replace(
            "Selected feedback loops: Unit / Module tests, structural checks, Real CLI / Workflow.",
            "Selected feedback loops: Evidence / Demo.",
        ).replace(
            "| Unit / Module tests | python3 -m unittest | Local rules | Runtime wiring |\n"
            "| structural checks | Validate task schema | Stable structure | Hosted behavior |\n"
            "| Real CLI / Workflow | Run the checker CLI | Public CLI behavior | External APIs |",
            "| Evidence / Demo | Save test output | Reproducible evidence | Future drift |",
        )
        self.assertEqual(1, self.run_checker(plan).returncode)

    def test_validation_table_inside_fence_does_not_count(self):
        table = (
            "| Feedback loop | Entry / Command / Artifact | Proves | Does not prove / Risk |\n"
            "| --- | --- | --- | --- |\n"
            "| Unit / Module tests | python3 -m unittest | Local rules | Runtime wiring |\n"
            "| structural checks | Validate task schema | Stable structure | Hosted behavior |\n"
            "| Real CLI / Workflow | Run the checker CLI | Public CLI behavior | External APIs |"
        )
        fenced = make_feedback_loop_plan().replace(
            table, f"```markdown\n{table}\n```"
        )
        self.assertEqual(1, self.run_checker(fenced).returncode)

    def test_validation_table_requires_exactly_one_separator(self):
        separator = "| --- | --- | --- | --- |"
        missing = make_feedback_loop_plan().replace(separator + "\n", "", 1)
        duplicate = make_feedback_loop_plan().replace(
            separator, separator + "\n" + separator, 1
        )
        self.assertEqual(1, self.run_checker(missing).returncode)
        self.assertEqual(1, self.run_checker(duplicate).returncode)

    def test_usage_and_missing_file_exit_two(self):
        no_args = subprocess.run(
            [str(CHECKER)], text=True, capture_output=True, check=False
        )
        missing = subprocess.run(
            [str(CHECKER), "/workspace/project/missing.md"],
            text=True,
            capture_output=True,
            check=False,
        )
        too_many = subprocess.run(
            [str(CHECKER), "one.md", "two.md"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, no_args.returncode)
        self.assertEqual(2, missing.returncode)
        self.assertEqual(2, too_many.returncode)

    def test_invalid_plan_exits_one(self):
        result = self.run_checker("# EXAMPLE-001\n")
        self.assertEqual(1, result.returncode)
        self.assertTrue(result.stderr)

    def test_plan_status_must_be_first_and_sections_ordered(self):
        plan = make_plan().replace(
            "## Plan Status", "## Temporary\n\nIntro.\n\n## Plan Status", 1
        )
        extra_heading = self.run_checker(plan)
        self.assertEqual(1, extra_heading.returncode)

        title = "# EXAMPLE-001 Task Plan\nDate: 2026-01-01\n"
        late = make_plan().replace(
            title,
            title + "\nIntro one.\nIntro two.\nIntro three.\nIntro four.\nIntro five.\n",
            1,
        )
        self.assertEqual(1, self.run_checker(late).returncode)

        plan = make_plan()
        first = "## Context Sources Checked\n\n- AGENTS.md\n- ARCHITECTURE.md"
        second = "## Alignment Status\n\nStatus: Aligned"
        swapped = plan.replace(first, "@@FIRST@@").replace(second, first).replace(
            "@@FIRST@@", second
        )
        out_of_order = self.run_checker(swapped)
        self.assertEqual(1, out_of_order.returncode)

    def test_status_and_execution_must_match(self):
        for status, execution in (
            ("Aligned", "Blocked"),
            ("Draft - waiting for user alignment", "Allowed"),
        ):
            with self.subTest(status=status, execution=execution):
                result = self.run_checker(make_plan(status, execution))
                self.assertEqual(1, result.returncode)

    def test_validation_fields_are_non_empty_and_scoped(self):
        blank = self.run_checker(
            make_plan().replace(
                "Test Boundary: repository-local CLI and plan document",
                "Test Boundary:",
            )
        )
        self.assertEqual(1, blank.returncode)

        moved = make_plan().replace(
            "Command: python3 -m unittest discover -s .agents/skills/task-plan/tests -v\n",
            "",
        ).replace(
            "## Evidence Plan\n",
            "## Evidence Plan\n\nCommand: python3 -m unittest\n",
        )
        out_of_scope = self.run_checker(moved)
        self.assertEqual(1, out_of_scope.returncode)

    def test_minimum_attempts_is_an_integer_at_least_two(self):
        for value in ("one", "1", "2 attempts"):
            with self.subTest(value=value):
                plan = make_plan().replace(
                    "Minimum attempts before accepting missing evidence: 2",
                    f"Minimum attempts before accepting missing evidence: {value}",
                )
                self.assertEqual(1, self.run_checker(plan).returncode)

    def test_layer_table_requires_exact_meaningful_rows(self):
        missing = make_plan().replace(
            "| Contract | Yes | Validate task schema | Stable document contract | External behavior |\n",
            "",
        )
        self.assertEqual(1, self.run_checker(missing).returncode)

        placeholder = make_plan().replace(
            "| Unit | Yes | python3 -m unittest | Pure rules | Runtime wiring |",
            "| Unit | Yes | TBD | Pure rules | Runtime wiring |",
        )
        self.assertEqual(1, self.run_checker(placeholder).returncode)

        extra = make_plan().replace(
            "| Evidence / Demo | Yes | Save test output | Reviewable validation | Future environment drift |",
            "| Evidence / Demo | Yes | Save test output | Reviewable validation | Future environment drift |\n"
            "| Extra | No | Skip: unrelated | Nothing | Unchecked risk |",
        )
        self.assertEqual(1, self.run_checker(extra).returncode)

        wrong_required = make_plan().replace(
            "| Unit | Yes |", "| Unit | Maybe |", 1
        )
        self.assertEqual(1, self.run_checker(wrong_required).returncode)


if __name__ == "__main__":
    unittest.main()
