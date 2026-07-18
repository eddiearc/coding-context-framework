import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[2]
CLI = ROOT / "scripts" / "loop-evidence"
SPEC = ROOT / "scripts" / "loop_spec.sh"
SKILL = ROOT / "SKILL.md"
OPENAI_YAML = ROOT / "agents" / "openai.yaml"
LICENSE = ROOT / "LICENSE"
TASK_ID = "example.plan-go-validation"
PLAN_PATH = "docs/exec-plans/active/example.plan-go-validation.md"
_WORKSPACE = None


def _checked_run(*command, cwd):
    result = subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return result


def setUpModule():
    global REPOSITORY, ROOT, CLI, SPEC, SKILL, OPENAI_YAML, LICENSE, _WORKSPACE

    source_repository = REPOSITORY
    _WORKSPACE = tempfile.TemporaryDirectory()
    workspace = Path(_WORKSPACE.name) / "framework fixture"
    _checked_run(source_repository / "init.sh", "--target", workspace, cwd=source_repository)

    plan_path = workspace / PLAN_PATH
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan = (workspace / "docs/exec-plans/_template.md").read_text(encoding="utf-8")
    plan = plan.replace("# <Task ID> Task Plan", "# Example Plan Go Validation Plan")
    plan = plan.replace(
        "Status: Draft - waiting for user alignment", "Status: Aligned"
    )
    plan = plan.replace(
        "Execution: Blocked. Do not begin implementation while questions remain.",
        "Execution: Allowed. This fixture is limited to a temporary workspace.",
    )
    plan_path.write_text(plan, encoding="utf-8")

    _checked_run(
        workspace / "scripts/task",
        "add-task",
        "--id",
        TASK_ID,
        "--title",
        "Generic plan-go validation",
        "--domain",
        "general",
        "--repo",
        "context-repository",
        "--status",
        "backlog",
        cwd=workspace,
    )
    _checked_run(
        workspace / ".agents/skills/task-plan/scripts/check-task-plan.sh",
        plan_path,
        cwd=workspace,
    )
    _checked_run(
        workspace / "scripts/task",
        "register-plan",
        plan_path,
        "--id",
        TASK_ID,
        "--domain",
        "general",
        "--repo",
        "context-repository",
        cwd=workspace,
    )

    REPOSITORY = workspace
    ROOT = workspace / ".agents/skills/plan-go"
    CLI = ROOT / "scripts/loop-evidence"
    SPEC = ROOT / "scripts/loop_spec.sh"
    SKILL = ROOT / "SKILL.md"
    OPENAI_YAML = ROOT / "agents/openai.yaml"
    LICENSE = ROOT / "LICENSE"


def tearDownModule():
    if _WORKSPACE is not None:
        _WORKSPACE.cleanup()


def run(*command, input_text=None):
    return subprocess.run(
        [str(part) for part in command],
        cwd=REPOSITORY,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def write_json(payload):
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    with handle:
        json.dump(payload, handle)
    return Path(handle.name)


def complete_evidence():
    return {
        "goal": {
            "objective": "Execute an aligned task plan",
            "status": "complete",
            "task_id": TASK_ID,
            "plan_path": PLAN_PATH,
            "plan_status": "aligned",
            "execution": "allowed",
            "tooling": {
                "runtime": "codex",
                "mechanism": "native-goal+task-board-plan",
                "used": True,
            },
        },
        "independence": {
            "subagent_tools_available": True,
            "roles_simulated": False,
            "complete_adversarial_loop": True,
            "statement": "executor and evaluator were independent agents",
        },
        "recorder": {
            "role": "main",
            "produced_executor_output": False,
            "produced_evaluator_output": False,
        },
        "rounds": [
            {
                "executor": {
                    "agent_id": "executor-agent-1",
                    "summary": "Implemented the registered plan.",
                    "artifacts": [
                        {
                            "type": "local_path",
                            "path": ".agents/skills/plan-go/SKILL.md",
                        }
                    ],
                    "checks": [{"name": "unit tests", "result": "PASS"}],
                    "uncertainties": [],
                },
                "evaluator": {
                    "agent_id": "evaluator-agent-1",
                    "findings": {
                        "blocking": [],
                        "important": [],
                        "missing_evidence": [],
                        "residual_risk": [
                            {"summary": "Future runtime drift is not covered."}
                        ],
                    },
                    "checks": [{"name": "acceptance review", "result": "PASS"}],
                },
                "route": "complete",
            }
        ],
        "acceptance": [
            {
                "command": "python3 -m unittest discover -v",
                "environment": "initialized framework fixture",
                "key_input": "generic registered plan-go test suite",
                "expected": "all tests pass",
                "actual": "all tests passed",
                "status": "PASS",
            }
        ],
    }


class PlanGoContractTests(unittest.TestCase):
    def test_skill_contract_and_ui_metadata(self):
        skill = SKILL.read_text(encoding="utf-8")
        metadata = OPENAI_YAML.read_text(encoding="utf-8")
        self.assertIn("name: plan-go", skill)
        self.assertIn("aligned", skill.lower())
        self.assertIn("registered", skill.lower())
        self.assertIn("goal", skill.lower())
        self.assertIn("executor", skill.lower())
        self.assertIn("evaluator", skill.lower())
        self.assertIn("reproducible evidence", skill.lower())
        self.assertNotIn("explicitly accepted", skill.lower())
        self.assertIn('display_name: "Go!"', metadata)
        self.assertIn("$plan-go", metadata)

    def test_adapted_source_retains_mit_notice(self):
        notice = LICENSE.read_text(encoding="utf-8")
        self.assertIn("MIT License", notice)
        self.assertIn("loop-adversarial-engineering", notice)
        self.assertIn("eddiearc", notice.lower())

    def test_loop_spec_is_repository_relative_and_names_roles(self):
        result = run(SPEC, "Execute the plan")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Execute the plan", result.stdout)
        self.assertIn("Executor Prompt", result.stdout)
        self.assertIn("Evaluator Prompt", result.stdout)
        self.assertNotIn("~/.codex", result.stdout)

    def test_init_outputs_active_template_with_executor(self):
        result = run(
            CLI,
            "init",
            "--task-id",
            TASK_ID,
            "--goal-mechanism",
            "native-goal+task-board-plan",
            "--runtime",
            "codex",
            "Execute the plan",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("active", payload["goal"]["status"])
        self.assertNotIn("codex_goal_used", payload["goal"])
        self.assertNotIn("goal_mechanism", payload["goal"])
        self.assertEqual(TASK_ID, payload["goal"]["task_id"])
        self.assertEqual(PLAN_PATH, payload["goal"]["plan_path"])
        self.assertEqual("aligned", payload["goal"]["plan_status"])
        self.assertEqual("allowed", payload["goal"]["execution"])
        self.assertEqual(
            {
                "runtime": "codex",
                "mechanism": "native-goal+task-board-plan",
                "used": True,
            },
            payload["goal"]["tooling"],
        )
        self.assertIn("executor", payload["rounds"][0])
        self.assertNotIn("generator", payload["rounds"][0])

    def test_active_template_validates_from_stdin(self):
        initialized = run(
            CLI,
            "init",
            "--task-id",
            TASK_ID,
            "--goal-mechanism",
            "native-goal+task-board-plan",
            "--runtime",
            "codex",
            "Execute the plan",
        )
        result = run(CLI, "validate", "-", input_text=initialized.stdout)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("valid", result.stdout)

    def test_init_rejects_chat_only_objective_without_task_identity(self):
        result = run(CLI, "init", "Execute the plan")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("task-id", result.stderr)

    def test_registered_goal_gate_rejects_forged_or_missing_fields(self):
        mutations = {
            "task_id": "missing.task",
            "plan_path": "docs/exec-plans/active/forged.md",
            "plan_status": "draft",
            "execution": "blocked_until_plan",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                payload = complete_evidence()
                payload["goal"][field] = value
                result = run(CLI, "validate", write_json(payload))
                self.assertNotEqual(0, result.returncode)
                self.assertIn(field, result.stderr)

    def test_goal_mechanism_uses_strict_allowlist(self):
        for mechanism in ("chat only", "chat_history", "verbal-claim", "banana"):
            with self.subTest(mechanism=mechanism):
                payload = complete_evidence()
                payload["goal"]["tooling"]["mechanism"] = mechanism
                result = run(CLI, "validate", write_json(payload))
                self.assertNotEqual(0, result.returncode)
                self.assertIn("task-board-plan", result.stderr)

    def test_task_board_plan_does_not_claim_native_codex_goal(self):
        result = run(
            CLI,
            "init",
            "--task-id",
            TASK_ID,
            "--goal-mechanism",
            "task-board-plan",
            "--runtime",
            "codex",
            "Execute the plan",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        goal = json.loads(result.stdout)["goal"]
        self.assertNotIn("codex_goal_used", goal)
        self.assertNotIn("goal_mechanism", goal)
        self.assertEqual("task-board-plan", goal["tooling"]["mechanism"])
        self.assertTrue(goal["tooling"]["used"])

    def test_goal_tooling_rejects_missing_mixed_and_invalid_packets(self):
        payload = complete_evidence()
        del payload["goal"]["tooling"]
        missing = run(CLI, "validate", write_json(payload))
        self.assertNotEqual(0, missing.returncode)
        self.assertIn("goal.tooling", missing.stderr)

        payload = complete_evidence()
        payload["goal"]["codex_goal_used"] = True
        payload["goal"]["goal_mechanism"] = "native-goal+task-board-plan"
        mixed = run(CLI, "validate", write_json(payload))
        self.assertNotEqual(0, mixed.returncode)
        self.assertIn("legacy", mixed.stderr)

        mutations = (
            ("runtime", ""),
            ("mechanism", "banana"),
            ("used", False),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                payload = complete_evidence()
                payload["goal"]["tooling"][field] = value
                invalid = run(CLI, "validate", write_json(payload))
                self.assertNotEqual(0, invalid.returncode)
                self.assertIn(f"goal.tooling.{field}", invalid.stderr)

    def test_init_rejects_unregistered_goal_mechanism(self):
        result = run(
            CLI,
            "init",
            "--task-id",
            TASK_ID,
            "--goal-mechanism",
            "banana",
            "--runtime",
            "codex",
            "Execute the plan",
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("invalid choice", result.stderr)

    def test_registered_goal_gate_rejects_unsafe_plan_path(self):
        payload = complete_evidence()
        payload["goal"]["plan_path"] = "../outside.md"
        result = run(CLI, "validate", write_json(payload))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("repository-relative", result.stderr)

    def test_complete_evidence_validates(self):
        result = run(CLI, "validate", write_json(complete_evidence()))
        self.assertEqual(0, result.returncode, result.stderr)

    def test_completion_rejects_important_and_missing_evidence(self):
        for category in ("important", "missing_evidence"):
            with self.subTest(category=category):
                payload = complete_evidence()
                payload["rounds"][0]["evaluator"]["findings"][category] = [
                    {"summary": "unresolved finding"}
                ]
                result = run(CLI, "validate", write_json(payload))
                self.assertNotEqual(0, result.returncode)
                self.assertIn(category.replace("_", " "), result.stderr.lower())

    def test_completion_requires_independent_agents(self):
        payload = complete_evidence()
        payload["independence"]["complete_adversarial_loop"] = False
        result = run(CLI, "validate", write_json(payload))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("complete_adversarial_loop", result.stderr)

    def test_complete_loop_requires_distinct_auditable_agent_ids(self):
        mutations = (
            ("executor", "agent_id", ""),
            ("executor", "agent_id", "main"),
            ("evaluator", "agent_id", "executor-agent-1"),
        )
        for role, field, value in mutations:
            with self.subTest(role=role, value=value):
                payload = complete_evidence()
                payload["rounds"][0][role][field] = value
                result = run(CLI, "validate", write_json(payload))
                self.assertNotEqual(0, result.returncode)
                self.assertIn("agent_id", result.stderr)

    def test_completion_rejects_nonpassing_executor_or_evaluator_checks(self):
        for role in ("executor", "evaluator"):
            for forged_result in ("FAIL", "NOT RUN", "unknown"):
                with self.subTest(role=role, forged_result=forged_result):
                    payload = complete_evidence()
                    payload["rounds"][0][role]["checks"][0]["result"] = forged_result
                    result = run(CLI, "validate", write_json(payload))
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("result=PASS", result.stderr)

    def test_completion_requires_structured_passing_acceptance_evidence(self):
        invalid_acceptance = (
            "all checks passed",
            {
                "command": "python3 -m unittest",
                "environment": "worktree",
                "key_input": "suite",
                "expected": "pass",
                "actual": "not run",
                "status": "NOT RUN",
            },
            {
                "environment": "worktree",
                "key_input": "suite",
                "expected": "pass",
                "actual": "pass",
                "status": "PASS",
            },
        )
        for acceptance in invalid_acceptance:
            with self.subTest(acceptance=acceptance):
                payload = complete_evidence()
                payload["acceptance"] = [acceptance]
                result = run(CLI, "validate", write_json(payload))
                self.assertNotEqual(0, result.returncode)
                self.assertIn("acceptance", result.stderr)

    def test_completion_rejects_pass_acceptance_with_contradictory_actual(self):
        for actual in ("FAILED", "NOT RUN", "ERROR", "SKIP"):
            with self.subTest(actual=actual):
                payload = complete_evidence()
                payload["acceptance"][0]["actual"] = actual
                result = run(CLI, "validate", write_json(payload))
                self.assertNotEqual(0, result.returncode)
                self.assertIn("contradicts status=PASS", result.stderr)

    def test_executor_artifacts_must_be_structured_and_auditable(self):
        invalid_artifacts = (
            "artifact.txt",
            {"type": "local_path", "path": "missing-artifact.txt"},
            {"type": "local_path", "path": "../outside.txt"},
            {"type": "external_url", "url": "file:///tmp/forged"},
            {"type": "mystery", "path": ".agents/skills/plan-go/SKILL.md"},
        )
        for artifact in invalid_artifacts:
            with self.subTest(artifact=artifact):
                payload = complete_evidence()
                payload["rounds"][0]["executor"]["artifacts"] = [artifact]
                result = run(CLI, "validate", write_json(payload))
                self.assertNotEqual(0, result.returncode)
                self.assertIn("executor.artifacts", result.stderr)

    def test_completion_validates_optional_artifact_kind_and_local_path(self):
        for artifact in (
            {"type": "local_path", "path": "../outside.txt"},
            {"type": "external_url", "url": "file:///tmp/forged"},
            {"type": "mystery", "path": "artifact.txt"},
        ):
            with self.subTest(artifact=artifact):
                payload = complete_evidence()
                payload["acceptance"][0]["artifact"] = artifact
                result = run(CLI, "validate", write_json(payload))
                self.assertNotEqual(0, result.returncode)
                self.assertIn("artifact", result.stderr)

    def test_completion_requires_explicit_residual_risk(self):
        payload = complete_evidence()
        payload["rounds"][0]["evaluator"]["findings"]["residual_risk"] = []
        result = run(CLI, "validate", write_json(payload))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("residual risk", result.stderr.lower())

    def test_main_recorder_cannot_claim_executor_output(self):
        payload = complete_evidence()
        payload["recorder"]["produced_executor_output"] = True
        result = run(CLI, "validate", write_json(payload))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("executor output", result.stderr)

    def test_complete_route_must_be_final_and_match_goal_status(self):
        payload = complete_evidence()
        payload["goal"]["status"] = "active"
        result = run(CLI, "validate", write_json(payload))
        self.assertNotEqual(0, result.returncode)
        self.assertIn("goal.status=complete", result.stderr)

    def test_cli_resources_are_executable(self):
        self.assertTrue(os.access(CLI, os.X_OK))
        self.assertTrue(os.access(SPEC, os.X_OK))


if __name__ == "__main__":
    unittest.main()
