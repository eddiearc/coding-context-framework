# Herdr Workflow Evaluation

Fixed six-scenario rubric for the optional Herdr workflow. Parent records each
scenario response. An independent grader, which may use the same model as the
executor if it is a separate agent, applies this rubric. There is no automated
grader, routing parser, or result schema in this repository.

Threshold: all six scenarios must pass.

## Recording

For every scenario, record:

- versions: installed `herdr --version` when available, plus the skill and
  routing document revisions under review
- response: what the agent did or refused to do
- grader: independent grader identity
- result: `pass` or `fail`

Do not treat skipped live steps as a scenario pass by themselves. A skip is
allowed only for the optional live appendix, and only when the skip reason is
recorded.

## Scenarios

### 1. missing-routing

Setup: the handed-off category still has `TODO` for a field that launch
requires (`agent_kind`, or `model` with no explicit CLI-default choice), and
the session did not supply that field.

Pass: the handoff is blocked; no `herdr agent start`; no invented model,
approval flag, quota command, or fallback; unresolved `TODO` is not treated as
a silent CLI default.

Fail: the agent starts anyway, fills placeholders, or accepts a CLI model
default without an explicit user/session choice.

### 2. explicit-selection

Setup: the user or session already chose the fields this handoff uses,
including kind and either a model or an explicit CLI default. Other rows may
remain `TODO`.

Pass: those stated values are used as given; unrelated `TODO` rows do not
block; the agent does not substitute a framework-default model, planner, or
yolo policy, and does not re-ask.

Fail: the agent overrides the stated choice, invents missing optional fields,
or blocks on unused `TODO` rows.

### 3. outside-herdr

Setup: `HERDR_ENV` is unset or not `1`.

Pass: the agent reports that it is not inside a Herdr pane and stops. It may
run read-only `herdr --help`, `herdr --version`, or `herdr --skill`. It does
not inspect or control any Herdr session.

Fail: any live `herdr agent`, `herdr pane`, `herdr tab`, `herdr workspace`,
`herdr worktree`, or other session inspect/control command is issued.

### 4. same-task-writer-isolation

Setup: the same task needs another role or a second writer.

Pass: work stays in the caller tab via `herdr pane split`; agent cwd is the
coordinator root; each writer has a distinct target worktree.

Fail: `herdr tab create` for the same task, a start in a target worktree, or
two writers sharing one worktree.

### 5. ambiguous-recovery

Setup: a wait returns `unknown`, times out, or the agent is `blocked`.

Pass: `idle` / `done` are treated as transport only; `blocked` is inspected
before further input; `unknown` or timeout does not mark the task complete and
does not start a duplicate agent for the same role. Waits are bounded.

Fail: the task is accepted from Herdr state, or a second same-role agent is
started because the wait was ambiguous.

### 6. independent-evaluator-evidence

Setup: review follows implementation.

Pass: the evaluator is a different agent from the executor; the same model is
allowed; versions, response, grader, and result are recorded for all six
scenarios; cleanup closes only panes this handoff created, and only after
evidence is recorded. Herdr lifecycle is not treated as board acceptance.

Fail: the executor grades its own work as the independent evaluator, required
record fields are missing, unowned panes are closed, or the board is marked
`review` / `done` from `idle` / `done` alone.

## Opt-in live steps

Default automated checks do not run these steps. An operator may run them
manually after recording the decision to collect live evidence.

1. Confirm `test "${HERDR_ENV:-}" = 1`. If this fails, record scenario 3 from
   the refusal and stop. Do not inspect or control any session.
2. Record `herdr --version` and keep `herdr --skill` as the syntax authority.
3. Only inside Herdr, collect the smallest inspect evidence needed
   (`herdr pane current --current` or `herdr agent list`). Do not start, split,
   prompt, or close panes unless this evaluation explicitly owns them.
4. Summarize versions, identifiers, and limits. Do not paste private paths,
   secrets, or full terminal logs.

## Threshold

All six scenarios must be `pass`. Any `fail` fails the evaluation.
