#!/usr/bin/env bash
set -euo pipefail

goal="${1:-}"
rounds="${ROUNDS:-1}"

if [[ -z "$goal" ]]; then
  echo "Usage: $0 \"task goal\"" >&2
  echo "Optional: ROUNDS=2 $0 \"task goal\"" >&2
  exit 1
fi

if ! [[ "$rounds" =~ ^[1-9][0-9]*$ ]]; then
  echo "ROUNDS must be a positive integer" >&2
  exit 1
fi

cat <<EOF
# plan-go Execution Spec

## Objective
$goal

## Plan Gate
- Read the repository instructions, task-board entry, and registered plan.
- Confirm the plan is Aligned and execution is allowed.
- Treat that registered aligned plan as the goal source and implementation facts as owned by the target repository.
- If the gate fails, route to task-plan or stop for alignment before substantive work.
- Record goal tooling as an object with a non-empty runtime, 'used=true', and 'mechanism=task-board-plan' when the registered task/plan is the goal.
- Use 'mechanism=native-goal+task-board-plan' only when a native runtime goal mirrors that registered task/plan.
- Keep 'task_id' as the auditable registered goal identifier; the runtime name does not imply native goal usage.
- Reject chat-only, verbal, or arbitrary goal-mechanism claims.

## Acceptance Checks
- The requested outcome exists and matches the registered plan and constraints.
- Registered acceptance checks pass at the selected feedback-loop depth.
- Executor and evaluator were independent agents when independent agent tools were available.
- No blocking, important, or missing-evidence evaluator findings remain.
- Reproducible evidence and residual risk are recorded.
- Once the registered acceptance conditions are satisfied, stop instead of pursuing optional improvements.

## Role Independence Policy
- Main orchestrates and integrates: confirm the goal, hand off prompts, integrate accepted output, run mechanical checks, record evidence, and choose routes.
- Executor produces the smallest sufficient change and reports artifacts, commands/results, validation entry points, and uncertainties.
- Executor artifacts must identify either a safe existing repository-relative 'local_path' or an HTTP(S) 'external_url'; bare strings are not evidence.
- Evaluator pressure-tests the result against the original goal and reports categorized findings with evidence.
- Main must not claim executor or evaluator output as its own.
- If independent agent tools are available, use separate executor and evaluator agents. Main-thread implementation plus self-review is not a complete adversarial loop.
- Record distinct, auditable executor and evaluator agent identifiers in every round.

## Loop
1. An independent executor produces the smallest sufficient solution or artifact.
2. An independent evaluator attacks the result with real checks where possible.
3. Main routes confirmed in-scope findings to an executor fix pass, integrates accepted output, and runs mechanical checks.
4. Evaluator performs a targeted re-evaluation when important findings or risk justify it.
5. Stop after $rounds evaluator round(s), unless new blocking evidence makes another round useful.
6. Record out-of-scope findings as follow-up work or residual risk. Expand scope only when they directly block delivery or expose a safety or data-loss risk, and record the reason.

## Executor Prompt
You are the executor. Complete this objective:

$goal

Follow the registered aligned plan and target-repository rules. Edit or produce artifacts directly when appropriate. Do not expand beyond In scope; report other findings as follow-up work unless they directly block delivery or expose a safety or data-loss risk. Do not revert unrelated changes.
Return only: files/artifacts changed, commands run with results, validation entry points, and uncertainties. Do not judge final completeness.

## Evaluator Prompt
You are the evaluator. Find problems; do not praise.

Original objective:
$goal

Re-read the registered plan and inspect the result against its scope, constraints, and acceptance checks. Look for bugs, missing requirements, weak evidence, integration failures, edge cases, and requirement drift. Mark out-of-scope findings as follow-up work or residual risk unless they directly block delivery or expose a safety or data-loss risk. Run real checks when possible.
Return only: blocking issues, important issues, missing evidence, and residual risk. If there is no issue, say "no issue" and name the evidence checked.

## Reproducible Evidence
- Command or entry point:
- Environment:
- Key input:
- Expected result:
- Actual result:
- Artifact path (when available):
- Check status (must be PASS for completion):
- Executor/evaluator independence:
- Evaluator findings and fix status:
- Residual risk:
EOF
