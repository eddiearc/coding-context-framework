#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import yaml


VALID_GOAL_STATUSES = {"active", "complete", "blocked"}
VALID_ROUTES = {"continue", "complete", "blocked"}
FINDING_KEYS = ("blocking", "important", "missing_evidence", "residual_risk")
REPOSITORY = Path(__file__).resolve().parents[4]
BOARD_PATH = REPOSITORY / "tasks" / "board.yaml"
VALID_GOAL_MECHANISMS = {
    "task-board-plan",
    "native-goal+task-board-plan",
}
CONTRADICTORY_PASS_PATTERN = re.compile(
    r"(?:^|[^a-z])(?:failed|not[\s_-]*run|error|skip(?:ped)?)(?:$|[^a-z])",
    re.IGNORECASE,
)


def evidence_template(objective, task_id, plan, runtime, goal_mechanism):
    return {
        "goal": {
            "objective": objective,
            "status": "active",
            "task_id": task_id,
            "plan_path": plan["path"],
            "plan_status": plan["status"],
            "execution": plan["execution"],
            "tooling": {
                "runtime": runtime,
                "mechanism": goal_mechanism,
                "used": True,
            },
        },
        "independence": {
            "subagent_tools_available": False,
            "roles_simulated": False,
            "complete_adversarial_loop": False,
            "statement": "",
        },
        "recorder": {
            "role": "main",
            "produced_executor_output": False,
            "produced_evaluator_output": False,
        },
        "rounds": [
            {
                "executor": {
                    "agent_id": "",
                    "summary": "",
                    "artifacts": [],
                    "checks": [],
                    "uncertainties": [],
                },
                "evaluator": {
                    "agent_id": "",
                    "findings": {
                        "blocking": [],
                        "important": [],
                        "missing_evidence": [],
                        "residual_risk": [],
                    },
                    "checks": [],
                },
                "route": "continue",
            }
        ],
        "acceptance": [],
    }


def is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def has_evidence_content(value):
    if isinstance(value, str):
        return is_nonempty_string(value)
    if isinstance(value, dict):
        return bool(value) and any(has_evidence_content(item) for item in value.values())
    if isinstance(value, list):
        return bool(value) and any(has_evidence_content(item) for item in value)
    return False


def repository_path(value, *, must_exist=False):
    if not is_nonempty_string(value) or "\\" in value:
        return None
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    root = REPOSITORY.resolve()
    candidate = (root / Path(*relative.parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if must_exist and not candidate.is_file():
        return None
    return candidate


def load_board(errors):
    try:
        payload = yaml.safe_load(BOARD_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"registered task board is unavailable: {exc}")
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("tasks"), list):
        errors.append("registered task board must contain a tasks list")
        return None
    return payload


def find_registered_task(errors, task_id):
    board = load_board(errors)
    if board is None:
        return None
    matches = [task for task in board["tasks"] if task.get("id") == task_id]
    if len(matches) != 1:
        errors.append(f"goal.task_id must identify exactly one registered task: {task_id!r}")
        return None
    return matches[0]


def validate_plan_document(errors, plan_path):
    path = repository_path(plan_path, must_exist=True)
    if path is None:
        errors.append("goal.plan_path must be a safe existing repository-relative file")
        return
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"goal.plan_path cannot be read: {exc}")
        return
    if re.search(r"^Status:\s*Aligned\s*$", content, re.IGNORECASE | re.MULTILINE) is None:
        errors.append("goal.plan_path must declare Status: Aligned")
    if re.search(r"^Execution:\s*Allowed\b", content, re.IGNORECASE | re.MULTILINE) is None:
        errors.append("goal.plan_path must declare Execution: Allowed")


def validate_registered_goal(errors, goal):
    if not isinstance(goal, dict):
        return
    task_id = goal.get("task_id")
    if not is_nonempty_string(task_id):
        errors.append("goal.task_id is required")
        return

    plan_path = goal.get("plan_path")
    if repository_path(plan_path) is None:
        errors.append("goal.plan_path must be a safe repository-relative path")
    if goal.get("plan_status") != "aligned":
        errors.append("goal.plan_status must be aligned")
    if goal.get("execution") != "allowed":
        errors.append("goal.execution must be allowed")

    legacy_fields = {"codex_goal_used", "goal_mechanism"}.intersection(goal)
    if legacy_fields:
        errors.append(
            "goal contains legacy tooling fields; use only goal.tooling with "
            "runtime, mechanism, and used"
        )
    tooling = goal.get("tooling")
    if not require_object(errors, tooling, "goal.tooling"):
        tooling = {}
    expected_tooling_fields = {"runtime", "mechanism", "used"}
    if set(tooling) != expected_tooling_fields:
        errors.append("goal.tooling must contain exactly runtime, mechanism, and used")
    if not is_nonempty_string(tooling.get("runtime")):
        errors.append("goal.tooling.runtime is required")
    mechanism = tooling.get("mechanism")
    if mechanism not in VALID_GOAL_MECHANISMS:
        allowed = ", ".join(sorted(VALID_GOAL_MECHANISMS))
        errors.append(f"goal.tooling.mechanism must be one of: {allowed}")
    if tooling.get("used") is not True:
        errors.append("goal.tooling.used must be true")

    task = find_registered_task(errors, task_id)
    if task is None:
        return
    registered_plan = task.get("plan")
    if not isinstance(registered_plan, dict):
        errors.append("goal.task_id must reference a task with a registered plan")
        return
    comparisons = (
        ("plan_path", "path"),
        ("plan_status", "status"),
        ("execution", "execution"),
    )
    for goal_field, plan_field in comparisons:
        if goal.get(goal_field) != registered_plan.get(plan_field):
            errors.append(f"goal.{goal_field} must match the registered task plan")
    if registered_plan.get("status") != "aligned":
        errors.append("registered task plan status must be aligned")
    if registered_plan.get("execution") != "allowed":
        errors.append("registered task plan execution must be allowed")
    validate_plan_document(errors, registered_plan.get("path"))


def require_object(errors, value, path):
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object")
        return False
    return True


def require_list(errors, value, path):
    if not isinstance(value, list):
        errors.append(f"{path} must be a list")
        return False
    return True


def require_nonempty_evidence_list(errors, value, path):
    if not require_list(errors, value, path):
        return
    if not value:
        errors.append(f"{path} must contain complete evidence")
        return
    for index, item in enumerate(value):
        if not has_evidence_content(item):
            errors.append(f"{path}[{index}] must contain complete evidence")


def require_structured_entries(errors, value, path, required_fields):
    if not require_list(errors, value, path):
        return
    for index, item in enumerate(value):
        item_path = f"{path}[{index}]"
        if not require_object(errors, item, item_path):
            continue
        for field in required_fields:
            if not is_nonempty_string(item.get(field)):
                errors.append(f"{item_path}.{field} is required")


def validate_executor(errors, value, path):
    if not require_object(errors, value, path):
        return
    if not isinstance(value.get("agent_id"), str):
        errors.append(f"{path}.agent_id must be a string")
    if not isinstance(value.get("summary"), str):
        errors.append(f"{path}.summary must be a string")
    artifacts = value.get("artifacts")
    if require_list(errors, artifacts, f"{path}.artifacts"):
        for index, artifact in enumerate(artifacts):
            validate_artifact(errors, artifact, f"{path}.artifacts[{index}]")
    require_structured_entries(errors, value.get("checks"), f"{path}.checks", ("name", "result"))
    require_list(errors, value.get("uncertainties"), f"{path}.uncertainties")


def validate_findings(errors, value, path):
    if not require_object(errors, value, path):
        return
    for key in FINDING_KEYS:
        require_structured_entries(errors, value.get(key), f"{path}.{key}", ("summary",))


def validate_evaluator(errors, value, path):
    if not require_object(errors, value, path):
        return
    if not isinstance(value.get("agent_id"), str):
        errors.append(f"{path}.agent_id must be a string")
    validate_findings(errors, value.get("findings"), f"{path}.findings")
    require_structured_entries(errors, value.get("checks"), f"{path}.checks", ("name", "result"))


def finding_count(findings, key):
    value = findings.get(key) if isinstance(findings, dict) else None
    return len(value) if isinstance(value, list) else 0


def validate_independent_agent_ids(errors, executor, evaluator, path):
    executor_id = executor.get("agent_id") if isinstance(executor, dict) else None
    evaluator_id = evaluator.get("agent_id") if isinstance(evaluator, dict) else None
    for role, agent_id in (("executor", executor_id), ("evaluator", evaluator_id)):
        if not is_nonempty_string(agent_id):
            errors.append(f"{path}.{role}.agent_id is required for a complete adversarial loop")
        elif agent_id.strip().lower() == "main":
            errors.append(f"{path}.{role}.agent_id must not be main")
    if (
        is_nonempty_string(executor_id)
        and is_nonempty_string(evaluator_id)
        and executor_id.strip().casefold() == evaluator_id.strip().casefold()
    ):
        errors.append(f"{path} executor/evaluator agent_id values must be distinct")


def require_passing_checks(errors, value, path):
    if not isinstance(value, list):
        return
    for index, check in enumerate(value):
        if isinstance(check, dict) and check.get("result") != "PASS":
            errors.append(f"{path}[{index}].result=PASS is required for completion")


def validate_artifact(errors, artifact, path):
    if not isinstance(artifact, dict):
        errors.append(f"{path} must explicitly identify local_path or external_url")
        return
    artifact_type = artifact.get("type")
    if artifact_type == "local_path":
        local_path = artifact.get("path")
        if repository_path(local_path, must_exist=True) is None:
            errors.append(f"{path}.path must be a safe existing repository-relative file")
    elif artifact_type == "external_url":
        url = artifact.get("url")
        parsed = urlparse(url) if is_nonempty_string(url) else None
        if parsed is None or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"{path}.url must be an http(s) external URL")
    else:
        errors.append(f"{path}.type must be local_path or external_url")


def validate_acceptance(errors, acceptance):
    if not isinstance(acceptance, list):
        return
    if not acceptance:
        errors.append("acceptance must contain reproducible evidence")
        return
    for index, item in enumerate(acceptance):
        path = f"acceptance[{index}]"
        if not require_object(errors, item, path):
            continue
        if not (is_nonempty_string(item.get("entry_point")) or is_nonempty_string(item.get("command"))):
            errors.append(f"{path}.entry_point or command is required")
        for field in ("environment", "key_input", "expected", "actual"):
            if not is_nonempty_string(item.get(field)):
                errors.append(f"{path}.{field} is required")
        if item.get("status") != "PASS":
            errors.append(f"{path}.status must be PASS")
        actual = item.get("actual")
        if is_nonempty_string(actual) and CONTRADICTORY_PASS_PATTERN.search(actual):
            errors.append(f"{path}.actual contradicts status=PASS")
        if "artifact" in item:
            validate_artifact(errors, item.get("artifact"), f"{path}.artifact")


def validate_evidence(payload):
    errors = []

    if not require_object(errors, payload, "evidence"):
        return errors

    goal = payload.get("goal")
    if require_object(errors, goal, "goal"):
        if not is_nonempty_string(goal.get("objective")):
            errors.append("goal.objective is required")
        if goal.get("status") not in VALID_GOAL_STATUSES:
            errors.append("goal.status must be active, complete, or blocked")
        validate_registered_goal(errors, goal)

    independence = payload.get("independence")
    if require_object(errors, independence, "independence"):
        if not isinstance(independence.get("subagent_tools_available"), bool):
            errors.append("independence.subagent_tools_available must be a boolean")
        if not isinstance(independence.get("roles_simulated"), bool):
            errors.append("independence.roles_simulated must be a boolean")
        if not isinstance(independence.get("complete_adversarial_loop"), bool):
            errors.append("independence.complete_adversarial_loop must be a boolean")
        if (
            independence.get("subagent_tools_available") is False
            and independence.get("complete_adversarial_loop") is not False
        ):
            errors.append(
                "independence.complete_adversarial_loop must be false when "
                "subagent_tools_available is false"
            )
        if independence.get("roles_simulated") is True:
            statement = independence.get("statement", "")
            if independence.get("complete_adversarial_loop") is not False or (
                "not a complete adversarial loop" not in statement.lower()
            ):
                errors.append(
                    "simulated roles must state this was not a complete adversarial loop"
                )

    recorder = payload.get("recorder")
    if require_object(errors, recorder, "recorder"):
        if recorder.get("role") != "main":
            errors.append("recorder.role must be main")
        if recorder.get("produced_executor_output") is not False:
            errors.append("recorder must not produce executor output")
        if recorder.get("produced_evaluator_output") is not False:
            errors.append("recorder must not produce evaluator output")

    rounds = payload.get("rounds")
    complete_route_indexes = []
    if require_list(errors, rounds, "rounds"):
        if not rounds:
            errors.append("rounds must contain at least one round")
        for index, round_payload in enumerate(rounds):
            round_path = f"rounds[{index}]"
            if not require_object(errors, round_payload, round_path):
                continue

            executor = round_payload.get("executor")
            if "executor" not in round_payload:
                errors.append(f"{round_path}.executor is required")
            else:
                validate_executor(errors, executor, f"{round_path}.executor")

            evaluator = round_payload.get("evaluator")
            if "evaluator" not in round_payload:
                errors.append(f"{round_path}.evaluator is required")
                findings = None
            else:
                validate_evaluator(errors, evaluator, f"{round_path}.evaluator")
                findings = evaluator.get("findings") if isinstance(evaluator, dict) else None

            if (
                isinstance(independence, dict)
                and independence.get("complete_adversarial_loop") is True
            ):
                validate_independent_agent_ids(errors, executor, evaluator, round_path)

            route = round_payload.get("route")
            if route not in VALID_ROUTES:
                errors.append(f"{round_path}.route must be continue, complete, or blocked")
            elif route == "complete":
                complete_route_indexes.append(index)
            if finding_count(findings, "blocking") or finding_count(findings, "important"):
                if route not in {"continue", "blocked"}:
                    errors.append(
                        f"{round_path}.route must be continue or blocked when "
                        "blocking or important findings remain"
                    )

    acceptance = payload.get("acceptance")
    require_list(errors, acceptance, "acceptance")

    goal_status = goal.get("status") if isinstance(goal, dict) else None
    if isinstance(rounds, list) and rounds:
        final_round = rounds[-1] if isinstance(rounds[-1], dict) else {}
        final_route = final_round.get("route")
        for index in complete_route_indexes:
            if index != len(rounds) - 1:
                errors.append(
                    f"rounds[{index}].route=complete must only appear on the final round"
                )
        if complete_route_indexes and goal_status != "complete":
            errors.append("route=complete requires goal.status=complete")
        if goal_status == "complete" and final_route != "complete":
            errors.append("goal.status=complete requires final route to be complete")
        completion_claimed = goal_status == "complete" or final_route == "complete"
    else:
        completion_claimed = goal_status == "complete"

    if completion_claimed and isinstance(rounds, list) and rounds:
        final_round = rounds[-1] if isinstance(rounds[-1], dict) else {}
        final_evaluator = final_round.get("evaluator")
        final_findings = (
            final_evaluator.get("findings") if isinstance(final_evaluator, dict) else None
        )
        final_executor = final_round.get("executor")
        if isinstance(final_executor, dict):
            if not is_nonempty_string(final_executor.get("summary")):
                errors.append(
                    "goal.status=complete requires complete evidence in final executor summary"
                )
            require_nonempty_evidence_list(
                errors,
                final_executor.get("artifacts"),
                "rounds[-1].executor.artifacts",
            )
            require_nonempty_evidence_list(
                errors,
                final_executor.get("checks"),
                "rounds[-1].executor.checks",
            )
            require_passing_checks(
                errors,
                final_executor.get("checks"),
                "rounds[-1].executor.checks",
            )
        if isinstance(final_evaluator, dict):
            require_nonempty_evidence_list(
                errors,
                final_evaluator.get("checks"),
                "rounds[-1].evaluator.checks",
            )
            require_passing_checks(
                errors,
                final_evaluator.get("checks"),
                "rounds[-1].evaluator.checks",
            )
        if finding_count(final_findings, "blocking") or finding_count(final_findings, "important"):
            errors.append(
                "goal.status=complete requires no final blocking or important findings"
            )
        if finding_count(final_findings, "missing_evidence"):
            errors.append(
                "goal.status=complete requires no final missing evidence findings"
            )
        if not finding_count(final_findings, "residual_risk"):
            errors.append("goal.status=complete requires an explicit final residual risk entry")
        if isinstance(independence, dict) and independence.get("complete_adversarial_loop") is not True:
            errors.append(
                "goal.status=complete requires independence.complete_adversarial_loop=true"
            )
        validate_acceptance(errors, acceptance)

    return errors


def load_json(path):
    if path == "-":
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def cmd_init(args):
    errors = []
    task = find_registered_task(errors, args.task_id)
    plan = task.get("plan") if isinstance(task, dict) else None
    if not isinstance(plan, dict):
        errors.append("task must have a registered plan")
    else:
        if plan.get("status") != "aligned":
            errors.append("registered task plan status must be aligned")
        if plan.get("execution") != "allowed":
            errors.append("registered task plan execution must be allowed")
        validate_plan_document(errors, plan.get("path"))
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    json.dump(
        evidence_template(
            args.objective,
            args.task_id,
            plan,
            args.runtime,
            args.goal_mechanism,
        ),
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_validate(args):
    try:
        payload = load_json(args.path)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid JSON evidence: {exc}", file=sys.stderr)
        return 1

    errors = validate_evidence(payload)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print("valid")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="loop-evidence")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="write a v1 evidence template")
    init_parser.add_argument("--task-id", required=True, help="registered task-board id")
    init_parser.add_argument(
        "--runtime",
        required=True,
        help="agent runtime recording the registered goal, for example codex",
    )
    init_parser.add_argument(
        "--goal-mechanism",
        required=True,
        choices=sorted(VALID_GOAL_MECHANISMS),
        help=(
            "goal source: registered task/plan only, or a native runtime goal "
            "mirrored to the registered task/plan"
        ),
    )
    init_parser.add_argument("objective")
    init_parser.set_defaults(func=cmd_init)

    validate_parser = subparsers.add_parser("validate", help="validate a v1 evidence file")
    validate_parser.add_argument("path", help="path to evidence JSON, or '-' to read stdin")
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
