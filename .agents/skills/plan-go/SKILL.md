---
name: plan-go
description: "Execute a registered aligned task plan through an independent executor/evaluator feedback loop and finish with reproducible evidence."
---

# Go!

## Overview

Turn an aligned repository plan into a closed execution loop:

`goal -> executor -> evaluator -> fix loop -> reproducible evidence -> done`

Use the registered task-board entry and its aligned plan as the preferred goal source. The plan defines scope, constraints, acceptance checks, evidence requirements, and the stop condition; the target repository remains the implementation fact source.

## Entry Gate

Before substantive execution:

1. Read the repository instructions, task-board entry, and registered plan.
2. Confirm that the plan is registered, `Aligned`, and allowed to execute.
3. If there is no registered aligned plan, route the work to the repository-local `task-plan` skill or stop for alignment. Do not invent an execution goal from chat history.
4. Record structured goal tooling with a non-empty runtime, `used=true`, and exactly `task-board-plan` when the registered task/plan is the goal, or `native-goal+task-board-plan` when native goal tooling mirrors it. The registered `task_id` remains the auditable goal identifier; a runtime name alone never claims native goal tooling.

A todo list or an unregistered draft is not an execution goal.

## Loop Contract

1. Define the checkable goal from the registered aligned plan: objective, constraints, acceptance checks, evidence, and stop condition.
2. Assign `executor` to make the smallest sufficient implementation or artifact change. The executor reports changed files, commands and results, validation entry points, and uncertainties; it does not judge final completeness.
3. Assign `evaluator` to pressure-test the result against the original goal. The evaluator reports only blocking issues, important issues, missing evidence, and residual risk, backed by real checks where possible.
4. Keep `main` as orchestrator and integrator: it confirms the goal, creates role handoffs, integrates accepted executor output, runs mechanical checks, records evidence, and chooses the next route.
5. Compare each finding with the registered `In scope`, `Out of scope`, and acceptance conditions. Route confirmed in-scope blocking or important findings to an executor fix pass, then ask an evaluator for targeted re-evaluation.
6. Run one evaluator round by default. Run a second when the first finds important issues or the risk justifies it. Continue past two only when new blocking evidence appears and another pass is likely to improve the result.
7. Record out-of-scope findings as follow-up work or residual risk instead of fixing them. Expand scope only when a finding directly blocks the registered delivery or exposes a safety or data-loss risk; record the reason and re-align if the agreed outcome or risk changes.
8. Complete and stop when acceptance checks pass; no in-scope blocking, important, or missing-evidence findings remain; reproducible evidence is recorded; and residual risk is explicit.

## Role Independence

- When independent agent tools are available, executor and evaluator must be separate agents. Main-thread implementation plus self-review is not a complete adversarial loop.
- `executor` owns production only. It must not make the final completion judgment.
- `evaluator` owns evaluation only. It must not quietly repair the artifact it is judging.
- `main` may apply patches, resolve integration conflicts, run formatters and tests, and wire accepted output into the workspace. It must not claim executor or evaluator output as its own.
- Give each role one responsibility and one expected output. Split broad work rather than combining implementation, evaluation, and planning.
- If independent agent tools are unavailable, disclose that limitation. Separate passes may help, but evidence must set `complete_adversarial_loop` to `false` and must not claim completion under this skill.

## Repository-Relative Drivers

From the coordination repository root, generate role prompts with:

```bash
.agents/skills/plan-go/scripts/loop_spec.sh "Execute the registered aligned plan"
```

Set an explicit evaluator-round target when warranted:

```bash
ROUNDS=2 .agents/skills/plan-go/scripts/loop_spec.sh "Execute the registered aligned plan"
```

Create and validate an evidence packet with:

```bash
.agents/skills/plan-go/scripts/loop-evidence init \
  --task-id TASK_ID \
  --runtime codex \
  --goal-mechanism native-goal+task-board-plan \
  "Execute the registered aligned plan" > evidence.json
.agents/skills/plan-go/scripts/loop-evidence validate evidence.json
.agents/skills/plan-go/scripts/loop-evidence init \
  --task-id TASK_ID \
  --runtime codex \
  --goal-mechanism native-goal+task-board-plan \
  "Execute the registered aligned plan" \
  | .agents/skills/plan-go/scripts/loop-evidence validate -
```

These commands are repository relative so the workflow does not depend on a user-home skill installation.

## Evidence Contract

The main/orchestrator records evidence; the validator does not create goals, spawn agents, or execute the plan. The packet contains:

- `goal`: objective, `active|complete|blocked` status, registered `task_id`, safe repository-relative `plan_path`, `plan_status=aligned`, `execution=allowed`, and a `tooling` object containing non-empty `runtime`, allowlisted `mechanism`, and `used=true`. The mechanism is exactly `task-board-plan` or `native-goal+task-board-plan`. Legacy or mixed top-level tooling fields are invalid. The validator cross-checks task and plan fields against `tasks/board.yaml` and the plan document.
- `independence`: whether independent agent tools were available, whether roles were simulated, and whether the full adversarial loop was completed.
- `recorder`: `main`, which must not claim executor or evaluator output.
- `rounds`: distinct auditable executor/evaluator `agent_id` values, structured role output, evaluator checks and findings, and a `continue|complete|blocked` route. Every executor artifact is explicitly typed as a safe existing repository-relative `local_path` or an HTTP(S) `external_url`; bare artifact strings are invalid.
- `acceptance`: structured reproducible evidence for every completion claim. Each entry uses `entry_point` or `command`, `environment`, `key_input`, `expected`, `actual`, and `status=PASS`. An optional artifact is explicitly typed as a safe existing `local_path` or an HTTP(S) `external_url`.

Reproducible evidence records the command or entry point, environment, key input, expected result, actual result, and artifact path when available. Recorded demos are evidence, but do not upgrade the validation depth they demonstrate.

`route=complete` may appear only on the final round and requires `goal.status=complete`. Completion is rejected when final blocking, important, or missing-evidence findings remain; a final check result is anything other than `PASS`; acceptance `status=PASS` contradicts an `actual` value such as `FAILED`, `NOT RUN`, `ERROR`, or `SKIP`; structured acceptance evidence is incomplete; residual risk is not explicitly recorded; or executor/evaluator identities are blank, equal, or `main`.

## Prompts

Executor contract:

```text
Complete the objective with the smallest sufficient change. Do not expand beyond In scope; report other findings as follow-up work unless they directly block delivery or expose a safety or data-loss risk. Return only: files/artifacts changed, commands run with results, validation entry points, and uncertainties. Do not judge final completeness.
```

Evaluator contract:

```text
Find problems. Do not praise. Re-read the original objective and evaluate the result with real checks where possible. Mark out-of-scope findings as follow-up work or residual risk unless they directly block delivery or expose a safety or data-loss risk. Report only blocking issues, important issues, missing evidence, and residual risk. If there is no issue, say "no issue" and name the evidence checked.
```

## Stop Conditions

- `complete`: all registered acceptance checks pass; no blocking, important, or missing-evidence findings remain; evidence is reproducible; and residual risk is stated.
- `continue`: concrete blocking, important, or missing-evidence findings have an authorized fix path.
- `blocked`: the plan cannot proceed within current authority or a required dependency remains unavailable; record the blocker, attempts, recovery path, and residual risk.

Once the registered acceptance conditions are satisfied, stop. Do not continue merely because another review or improvement is possible. Do not finish with verbal confidence alone.
