---
name: herdr-workflow
description: "Optional Herdr handoff for repository-local task work. Use when the user wants Herdr to start, prompt, recover, or collect results from another agent. Requires user-owned docs/agent-routing.md. CLI syntax comes from herdr --skill. Requires HERDR_ENV=1 before any live inspect or control."
---

# Herdr Workflow

Optional coordination helper. Task board, plans, and evidence stay on
`scripts/task`. This skill does not schedule work, complete tasks from Herdr
state, or add a runtime adapter.

Users without Herdr keep the rest of the framework. If Herdr is unused, stop
after reading this paragraph.

## Authority

Installed CLI syntax is authoritative. Read-only discovery may run without a
Herdr pane:

```bash
herdr --skill
herdr --help
herdr --version
```

Do not run bare `herdr` for discovery; it launches or attaches the TUI. Copy
flags and identifiers from those sources and from JSON responses. Do not invent
subcommands.

## Environment guard

Check this before any live inspect or control, including `herdr agent`,
`herdr pane`, `herdr tab`, `herdr workspace`, `herdr worktree`, and any other
command that talks to a live session:

```bash
test "${HERDR_ENV:-}" = 1
```

If the check fails, report that this process is not inside a Herdr pane and
stop. Do not inspect or control any Herdr session from outside Herdr.

After the guard passes, print installed groups only as needed:

```bash
herdr agent
herdr pane
```

## User-owned routing

Read `docs/agent-routing.md` plus any explicit choice already stated in the
current session.

- Honor explicit user or session values for the current handoff. Do not re-ask.
- Do not execute `TODO` or other placeholders. Do not invent a model, planner,
  approval flag, quota command, or fallback.
- Before `herdr agent start`, the current handoff must have an explicit
  `agent_kind` and an explicit model decision: a chosen model, or an explicit
  user/session choice to use the installed CLI default. An unresolved model
  `TODO` is not permission to accept a silent CLI default.
- Resolve only the other fields that this handoff actually uses. Unrelated
  `TODO` rows do not block other work.
- If a field required by this handoff is missing and the session did not supply
  it, block only that handoff and report the missing field.
- There is no mandatory planner, model, or yolo/auto-approve policy.
- Planning is proportional. Skip a planning handoff when the user did not ask
  for one and the task does not need it.
- Independent executor and evaluator agents may share a model.

## Workflow

1. Intake: `scripts/task list --tree` and `scripts/task show <task-id>`. Register
   a task before starting agents when none exists. Record the Herdr agent name
   in task notes or evidence.
2. Implementation handoff requires an aligned plan that is already registered
   on the task board. If that plan is missing, route to task-plan or stop. Do
   not start an implementation agent from chat history alone.
3. Map a short unique agent name to that task id. Names must match
   `[a-z][a-z0-9_-]{0,31}` and stay unique among live agents.
4. Stay in the caller tab for the same task. Split a sibling pane; do not
   `herdr tab create` for the same task, the same planning/implementation/review
   loop, or a continuation of an existing conversation.
5. Keep agent cwd at the coordinator repository root (the process `$PWD` unless
   the user named another coordinator). Do not start the agent in a target
   worktree, a throwaway checkout, or `/tmp`.
6. Give each writer its own target-repository git worktree. Do not point two
   writers at the same worktree.
7. After routing is ready and `HERDR_ENV=1`, split, start, prompt, wait, and
   read using installed syntax. Use one start. Pass native arguments after `--`
   only when the user or session supplied them:

   ```bash
   herdr pane layout --pane "$HERDR_PANE_ID"
   herdr pane split --current --direction right --cwd "$PWD" --no-focus
   herdr agent start <name> --kind <kind> --pane <returned-pane-id> -- <agent-args...>
   herdr agent prompt <name> "<work>" --wait --timeout 120000
   herdr agent get <name>
   herdr agent read <name> --source recent-unwrapped --lines 120
   ```

   Read the new pane id from `.result.pane.pane_id`. Use `--direction down` when
   the caller pane is narrow or tall. Every wait must be bounded (`--timeout`).
   Add model, thinking, or approval flags only when routing or the session set
   them, including an explicit CLI-default model choice.
8. Collect results after `idle` or `done`, and inspect immediately on
   `blocked`. Register evidence with `scripts/task` when the board should
   change. After evidence is recorded, close only panes this handoff created.

## Recovery

- `idle` and `done` are transport lifecycle states. They do not accept a task
  or prove completion.
- `blocked` requires `herdr agent get` and `herdr agent read` before further
  input.
- `unknown` and wait timeouts do not prove completion and do not justify
  starting a second agent for the same role.
- Do not treat a failed wait as a reason to duplicate startup. Inspect, then
  continue the existing agent or record a blocker.
- Task status changes stay serialized through `scripts/task` and need real
  validation or evidence.

## Evidence and review

- Prompt, wait, and read. Do not leave a started agent uncollected.
- Record command versions, agent names, and transcript or result references
  without private paths or raw secrets.
- An independent evaluator must be a separate agent from the executor. The same
  model is allowed.
- Herdr state is not task acceptance. Board `review` / `done` still require
  evidence.

## Scenario evaluation

The fixed six-scenario rubric is
`.agents/skills/herdr-workflow/references/evaluation.md`. Parent records
scenario responses. An independent grader applies the rubric. Live Herdr steps
are manual and opt-in. Default automated checks do not drive a session.

## Out of scope

Automatic scheduling, a new task schema, a routing parser, an automated grader,
provider rankings, mandatory models, universal yolo, and completing tasks from
Herdr lifecycle alone.
