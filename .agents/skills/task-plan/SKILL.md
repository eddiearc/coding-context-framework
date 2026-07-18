---
name: task-plan
description: Create or review repository-local task intake and alignment plans before implementation. Use when work needs explicit scope, contracts, human alignment, task/worktree routing, layered validation, or an evidence plan.
---

# Task Plan

Create or review one decision-ready plan under `docs/exec-plans/active/`. Keep
task state in the repository task board and change it through `scripts/task`; do
not edit the board by hand. Do not implement product code, deploy, publish, or
change repository policy while using this skill.

## Workflow

1. Read `AGENTS.md`, `ARCHITECTURE.md`, the relevant task-board entry, the
   repository's layered-validation guidance, and directly relevant contracts.
2. Capture unplanned future work with `scripts/task add-task` as `backlog`, or
   as `blocked` when a concrete blocker is known. Use `--requirement-ref` for
   requirement links when they exist.
3. For complex or multi-step work, ask one unresolved, high-leverage question at a time.
   Explain why it matters, recommend an answer, and wait for the user response.
4. Record only questions actually asked and answers actually received in the
   `Human Alignment Log`. Mark an assumption as user-authorized only when the
   user explicitly authorizes it. For trivial work, record why the loop was
   skipped.
5. Write the plan with the exact structure below, then run:

   ```bash
   .agents/skills/task-plan/scripts/check-task-plan.sh docs/exec-plans/active/<plan>.md
   ```

6. Register the plan through `scripts/task register-plan`. An aligned plan is
   not executable until registered. A draft may be registered only as blocked.

## Plan Status

Make `Plan Status` the first level-two heading and place it within the first
eight lines, after the title and optional date.

Use exactly one of these pairs:

```markdown
## Plan Status

Status: Aligned
Execution: Allowed. Begin only after the plan is registered in the task board.
```

```markdown
## Plan Status

Status: Draft - waiting for user alignment
Execution: Blocked. Do not begin implementation while questions remain.
```

Repeat the same `Status:` value under `Alignment Status`. Aligned means scope,
contract, validation boundary, major risks, and implementation routing have no
blocking alignment questions. Draft means the unanswered questions remain
listed in the plan.

## Required Plan Structure

Use these level-two headings exactly once and in this order. Additional detail
may use level-three or deeper headings.

1. `Plan Status`
2. `Goal / Scope`
3. `Context Sources Checked`
4. `Alignment Status`
5. `Human Alignment Log`
6. `Task / Worktree / Branch Plan`
7. `Contract / Behavior`
8. `Validation Plan`
9. `Evidence Plan`
10. `Risks / Open Questions`
11. `Implementation Recommendation`

## Validation Contract

Put each common label and its value on one line inside `Validation Plan`:

- `Test Boundary:`
- `Why this boundary:`
- `Why not narrower:`
- `Why not broader:`
- `Dependencies:`
- `Command:`
- `Expected RED:`
- `Expected GREEN:`
- `Missing evidence policy:`
- `Minimum attempts before accepting missing evidence:`

Set `Minimum attempts before accepting missing evidence:` to an integer of at
least `2`. Each failed attempt must record its entry point, environment, concrete
blocker, and recovery path. Missing evidence is not accepted by default.

New plans then use these labels:

- `Selected feedback loops:`
- `Entry / Command / Artifact per feedback loop:`
- `Residual risks:`

Select the smallest effective feedback loop for the task. Allowed rows are
`Unit / Module tests`, `evals`, `structural checks`, `Mock E2E`, `Real CLI /
Workflow`, and `Real API E2E`. `Selected feedback loops:` is a comma-separated
list of those exact names and must match the table rows exactly. Include at
least one row, use every selected row at most once, and fill every cell with
meaningful content. The table must contain exactly one Markdown separator row
and tables inside fenced code blocks do not satisfy the contract.

`Evidence / Demo` is not a feedback loop or test layer. Record reproducible
evidence and recorded demos under `Evidence Plan`; they do not upgrade the
underlying validation depth.

Add exactly this table inside `Validation Plan`:

```markdown
| Feedback loop | Entry / Command / Artifact | Proves | Does not prove / Risk |
| --- | --- | --- | --- |
| Unit / Module tests | concrete entry | concrete claim | residual risk |
| structural checks | concrete entry | concrete claim | residual risk |
| Real CLI / Workflow | concrete entry | concrete claim | residual risk |
```

The checker continues to accept already-registered active plans that use the
legacy labels and seven-row table below. Do not use this legacy form for new
plans:

```markdown
| Layer | Required | Entry / Command / Artifact | Proves | Does not prove / Risk |
| --- | --- | --- | --- | --- |
| Unit | Yes or No | concrete entry or skip reason | concrete claim | residual risk |
| Component / Module | Yes or No | concrete entry or skip reason | concrete claim | residual risk |
| Contract | Yes or No | concrete entry or skip reason | concrete claim | residual risk |
| Mock E2E | Yes or No | concrete entry or skip reason | concrete claim | residual risk |
| Real API / CLI | Yes or No | concrete entry or skip reason | concrete claim | residual risk |
| Real Backend E2E | Yes or No | concrete entry or skip reason | concrete claim | residual risk |
| Evidence / Demo | Yes or No | concrete entry or skip reason | concrete claim | residual risk |
```

In a legacy plan, replace `Yes or No` with exactly `Yes` or `No`. Fill all cells
with meaningful content. For an omitted layer, use `No`, name the skip entry or
reason, and state the residual risk; do not use placeholders such as `TBD` or
`N/A`.

## Execution Boundary

The plan defines scope, contracts, validation, evidence, and routing. The
executor follows the repository's documented implementation and review process.
If required validation cannot run in the current environment, record the
limitation and recovery path instead of claiming it passed.

Keep delivery boundaries in the existing `Goal / Scope` content and registered
acceptance conditions; do not add plan sections or fields solely for scope
control. Treat findings outside `In scope` as follow-up work unless they directly
block the registered delivery or expose a safety or data-loss risk. Record the
reason before expanding scope, and re-align when that expansion changes the
agreed outcome or risk.

The checker validates document structure, not whether human alignment truly
occurred or whether evidence claims are accurate. Review those semantics before
registering the plan.
