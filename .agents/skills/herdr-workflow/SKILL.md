---
name: herdr-workflow
description: "Optional Herdr handoff for repository-local task work. Use for useful parallel or independent work. Requires user-owned docs/agent-routing.md. CLI syntax comes from herdr --skill. Check HERDR_ENV=1 before live inspection and establish caller identity before control. Missing Herdr does not block task or plan work."
---

# Herdr Workflow

Optional coordination helper. Task board, plans, and evidence stay on
`scripts/task`. This skill does not schedule work, complete tasks from Herdr
state, or add a runtime adapter.

Users without Herdr keep the rest of the framework. If Herdr is unused, continue
task and plan work and do not issue Herdr commands.

## When to delegate

A valid Herdr context is `HERDR_ENV=1` plus a caller pane this handoff can
identify. In that context, prefer `herdr pane split` and `herdr agent start`
over a hidden or in-process subagent for work that is usefully parallel or
independent.

If Herdr is missing, the environment check fails, or the caller pane id is
missing or stale, continue task and plan work. Do not inspect or control Herdr
when `HERDR_ENV` is not `1`. A missing or stale caller does not justify
splitting a pane focused on unrelated work, and it does not justify inventing a
caller id. Host that long-running external agent with the persistent-session
fallback under Recovery.

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

If the check fails, report that this process is not inside a Herdr pane. Do not
inspect or control any Herdr session. Continue task and plan work that does not
need Herdr.

After the guard passes, print installed groups only as needed:

```bash
herdr agent
herdr pane
```

Confirm the caller pane exists before splitting. If it is missing or the
installed current-pane command reports it is gone, stop Herdr control for this
handoff and use the persistent-session fallback. Do not attach this handoff to
some other focused pane.

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
- There is no mandatory planner, model, provider, or yolo/auto-approve policy.
- The current agent writes the plan by default. Hand planning to the configured
  planning route only when complexity or missing expertise justifies another
  pass and that route is filled and useful. Do not add a pass that only rereads
  material already used. A `TODO` planning row does not block implementation.
- When `quota_check` is filled, run that exact command before launch, before
  resume, and before integrating that agent's result. Integrating means
  accepting the result into the task outcome under that route. Still read a
  started agent; do not leave it uncollected.
- Exhausted quota means the check ran and reported no remaining capacity.
  That blocks a new launch or resume of the exhausted route. It does not discard
  a transcript already produced, and it does not move that result onto another
  model. Unavailable metering means the check did not run or could not be read.
  Record the two outcomes separately. Unavailable metering is not exhaustion and
  is not a reason to switch routes or add a launch gate: continue the already
  authorized route with the unknown reading recorded, unless an existing
  explicit policy requires successful metering. When quota is exhausted, a
  filled fallback with remaining capacity may be used for a launch that has
  not started. The routing document owns this policy.
- Choose remaining capacity only among routes the user explicitly configured. A
  filled `fallback` is the only substitute, and only for the route it belongs
  to. Never invent a fallback. Do not change the review model unless that
  review route's own filled fallback, or a new explicit session choice, says so.
- Independent executor and evaluator agents may share a model.

## Workflow

1. Intake: `scripts/task list --tree` and `scripts/task show <task-id>`. Register
   a task before starting agents when none exists. Record the Herdr agent name,
   or the fallback session name, in task notes or evidence.
2. Implementation handoff requires an aligned plan that is already registered
   on the task board. If that plan is missing, route to task-plan or stop. Do
   not start an implementation agent from chat history alone. The current agent
   writes that plan unless the planning rule above calls for a handoff.
3. Map a short unique agent name to that task id. Names must match
   `[a-z][a-z0-9_-]{0,31}` and stay unique among live agents. Give every
   non-agent command pane a readable label too, using the pane label or title
   operation copied from `herdr --skill`. Do not invent that subcommand. If the
   installed CLI has none, record the label in evidence.
4. Stay in the caller tab for the same task. Split a sibling pane; do not
   `herdr tab create` for the same task, the same planning/implementation/review
   loop, or a continuation of an existing conversation.
5. Keep a flat readable layout. If more panes would be unreadable, run fewer
   at a time in that same tab; do not split merely to raise the agent count.
6. Keep agent cwd at the coordinator repository root (the process `$PWD` unless
   the user named another coordinator). Do not start the agent in a target
   worktree, a throwaway checkout, or `/tmp`.
7. Give each writer its own target-repository git worktree. Do not point two
   writers at the same worktree. Each role prompt states scope, inputs,
   expected output, and validation.
8. Resolve unsettled shared contracts before starting dependent writers.
   Once inputs are fixed, ready slices with separate write sets may start
   together, including writers that use the same settled contract. Serialize
   conflicting edits and unfinished dependencies. Keep one handoff for a small
   cohesive change.
9. After routing is ready and the Herdr context is valid, split, start, prompt,
   wait, and read using installed syntax. Use one start. Pass native arguments
   after `--` only when the user or session supplied them:

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
10. Collect results after `idle` or `done`, and inspect immediately on
    `blocked`. Run a filled `quota_check` again before integrating the result.
    Register evidence with `scripts/task` when the board should change. After
    evidence is recorded, close only panes this handoff created.

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

### Persistent session fallback

Use this when a long-running external agent has no valid Herdr caller. Create a
new tmux session owned by this task, unless the current session already named
another persistent session tool. This is not a new routing field.

Record the session name, cwd, start command, and log location in task notes or
evidence. Bound every wait. Rejoin after a timeout; do not start a second
session for the same role. Do not attach to, adopt, or kill a session this
handoff did not create. After durable evidence is recorded, clean up only
sessions this handoff created.

Help, version, and other commands that are known to finish immediately may run
directly. They do not need a persistent session.

```bash
tmux new-session -d -s <task-session-name> -c "$PWD" -- <start-command>
```

## Evidence and review

- Prompt, wait, and read. Do not leave a started agent uncollected.
- Record command versions, agent or session names, cwd, start command, log
  location, and transcript or result references without private paths or raw
  secrets.
- An independent evaluator must be a separate agent from the executor. The same
  model is allowed. The evaluator compares each added layer or mechanism with
  removing it or using a simpler alternative. Passing tests do not prove that
  layer is necessary.
- PR text follows the PR section in `AGENTS.md`.
- Herdr state is not task acceptance. Board `review` / `done` still require
  evidence.

## Scenario evaluation

The fixed six-scenario rubric is
`.agents/skills/herdr-workflow/references/evaluation.md`. Parent records
scenario responses. An independent grader applies the rubric. The written
scenarios do not require live agent side effects. Live Herdr steps are manual
and opt-in. Default automated checks do not drive a session.

## Out of scope

Automatic scheduling, a new task schema, a routing parser, an automated grader,
provider rankings, mandatory models, universal yolo or other universal approval
modes, a new routing field for the session fallback, and completing tasks from
Herdr lifecycle alone.
