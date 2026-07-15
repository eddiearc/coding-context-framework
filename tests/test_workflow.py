from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPOSITORY, run


def aligned_plan() -> str:
    return """# Example Workflow Plan

Date: 2026-01-01

## Plan Status

Status: Aligned
Execution: Allowed. This fixture is limited to a temporary workspace.

## Goal / Scope

Exercise the complete local task lifecycle.

## Context Sources Checked

- AGENTS.md
- ARCHITECTURE.md

## Alignment Status

Status: Aligned

## Human Alignment Log

Alignment loop was skipped because this is a deterministic test fixture.

## Task / Worktree / Branch Plan

- Task: example.workflow
- Repository: context-repository
- Worktree: temporary workspace

## Contract / Behavior

- Persist task, plan, status, and evidence transitions atomically.

## Validation Plan

Test Boundary: initialized repository-local CLI lifecycle
Why this boundary: It covers the public wrappers and persisted board state.
Why not narrower: Direct module tests miss initialization and wrapper routing.
Why not broader: The framework has no hosted service or UI.
Dependencies: Bash, Python 3, and PyYAML.
Command: python3 -m unittest tests.test_workflow -v
Expected RED: The lifecycle fails when framework wiring is incomplete.
Expected GREEN: The final task is in review with an aligned plan and evidence.
Missing evidence policy: Record concrete failures and retry through the same public entrypoints.
Minimum attempts before accepting missing evidence: 2
Covered layers: Unit, Contract, Real API / CLI, Evidence / Demo.
Entry / Command / Artifact per layer: See the table below.
Omitted layers with reasons / risks: No UI, component service, or real backend exists.

| Layer | Required | Entry / Command / Artifact | Proves | Does not prove / Risk |
| --- | --- | --- | --- | --- |
| Unit | Yes | Repository unit suites | Local rules | External integration |
| Component / Module | No | Skip because no service component exists | Omission is explicit | Future services need coverage |
| Contract | Yes | Task board validation | Persisted contract | Hosted behavior |
| Mock E2E | No | Skip because no UI workflow exists | Omission is explicit | Future UI behavior |
| Real API / CLI | Yes | Temporary initialized CLI lifecycle | Public local wiring | External APIs |
| Real Backend E2E | No | Skip because no backend exists | No backend claim | Distributed behavior |
| Evidence / Demo | Yes | Test command result | Reproducible local evidence | Independent audit |

## Evidence Plan

- Preserve unittest result and final JSON assertions.

## Risks / Open Questions

- Concurrent CLI writers remain outside this test.

## Implementation Recommendation

- Keep the fixture temporary and exercise only public entrypoints.
"""


class LocalWorkflowTests(unittest.TestCase):
    def test_initialized_workspace_supports_task_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "coding context"
            initialized = run(REPOSITORY / "init.sh", "--target", workspace)
            self.assertEqual(0, initialized.returncode, initialized.stderr)

            added = run(
                workspace / "scripts/task",
                "add-task",
                "--id",
                "example.workflow",
                "--title",
                "Temporary local workflow",
                "--domain",
                "general",
                "--repo",
                "context-repository",
                "--status",
                "backlog",
                "--requirement-ref",
                "REQ-001",
                cwd=workspace,
            )
            self.assertEqual(0, added.returncode, added.stderr)

            plan_dir = workspace / "docs/exec-plans/active"
            plan_dir.mkdir(parents=True)
            plan = plan_dir / "example.workflow.md"
            plan.write_text(aligned_plan(), encoding="utf-8")

            checked = run(
                workspace / ".agents/skills/task-plan/scripts/check-task-plan.sh",
                plan,
                cwd=workspace,
            )
            self.assertEqual(0, checked.returncode, checked.stderr)

            registered = run(
                workspace / "scripts/task",
                "register-plan",
                plan,
                "--id",
                "example.workflow",
                "--domain",
                "general",
                "--repo",
                "context-repository",
                cwd=workspace,
            )
            self.assertEqual(0, registered.returncode, registered.stderr)

            active = run(
                workspace / "scripts/task",
                "set-status",
                "example.workflow",
                "active",
                cwd=workspace,
            )
            self.assertEqual(0, active.returncode, active.stderr)

            evidence = run(
                workspace / "scripts/task",
                "add-evidence",
                "example.workflow",
                "--type",
                "local-cli",
                "--path",
                "docs/exec-plans/active/example.workflow.md",
                "--status",
                "pass",
                "--summary",
                "Temporary local lifecycle completed.",
                cwd=workspace,
            )
            self.assertEqual(0, evidence.returncode, evidence.stderr)

            review = run(
                workspace / "scripts/task",
                "set-status",
                "example.workflow",
                "review",
                cwd=workspace,
            )
            self.assertEqual(0, review.returncode, review.stderr)

            validated = run(workspace / "scripts/task", "validate", cwd=workspace)
            self.assertEqual(0, validated.returncode, validated.stderr)

            shown = run(
                workspace / "scripts/task",
                "show",
                "example.workflow",
                "--format",
                "json",
                cwd=workspace,
            )
            self.assertEqual(0, shown.returncode, shown.stderr)
            task = json.loads(shown.stdout)
            self.assertEqual("review", task["status"])
            self.assertEqual("aligned", task["plan"]["status"])
            self.assertEqual(1, len(task["evidence"]))


if __name__ == "__main__":
    unittest.main()
