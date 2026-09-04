---
name: task-board
description: Maintain the repository-native Coding Context Framework task board, plan links, evidence, notes, and task hierarchy.
---

# Task Board

Use `scripts/task` from the repository root. The CLI stores all state in
`tasks/board.yaml`; it has no network, database, hosted synchronization, or
runtime-specific integration.

## Safe workflow

1. Run `scripts/task validate` before relying on board state.
2. Capture unplanned work with `add-task`.
3. Register an aligned or explicitly blocked Markdown plan with
   `register-plan` before execution.
4. Keep status, notes, evidence, and parent-child links current.
5. Run `scripts/task validate` after manual board edits.

Mutations are atomic. Paths stored in the board must be repository-relative,
must exist, and must not escape through `..` or symlinks.

## Commands

```text
scripts/task validate
scripts/task list [--status STATUS] [--format table|yaml|json] [--tree]
scripts/task show TASK_ID [--format yaml|json]
scripts/task add-task --id ID --title TITLE --domain DOMAIN [options]
scripts/task set-title TASK_ID TITLE
scripts/task register-plan PLAN --id ID --domain DOMAIN --repo REPO [options]
scripts/task set-status TASK_ID STATUS
scripts/task set-plan-metadata TASK_ID PLAN [routing options]
scripts/task add-note TASK_ID NOTE
scripts/task remove-note TASK_ID NOTE
scripts/task add-evidence TASK_ID --type TYPE --status STATUS --summary TEXT [--path PATH]
scripts/task link-sub-task PARENT_TASK_ID CHILD_TASK_ID
scripts/task unlink-sub-task PARENT_TASK_ID CHILD_TASK_ID
```

Every subcommand also accepts `--board PATH`. Use `--requirement-ref` more than
once to associate generic requirement IDs, document anchors, or external
references with a task.

Example intake:

```bash
scripts/task add-task \
  --id example.first-task \
  --title "Describe the task" \
  --domain general \
  --repo context-repository \
  --requirement-ref REQ-001
```

## Plan metadata contract

A registered Markdown plan must contain:

```markdown
## Plan Status

Status: Aligned

Execution: Allowed for this task.
```

The other supported pair is `Draft - waiting for user alignment` with an
`Execution:` value beginning with `Blocked`. Draft plans require the board task
to be blocked. `set-plan-metadata` preserves routing values when their options
are omitted; use the explicit `--clear-*` flags to remove them.

## Hierarchy contract

`sub_tasks` is a forest: a child has at most one parent, every child ID exists,
and self-links and cycles are invalid. Use the link commands rather than editing
the relationship manually.

## Evidence contract

Tasks in `review` or `done` need at least one evidence entry. Evidence paths are
optional so external or local-only results can be summarized without publishing
private locations. Never place credentials, tokens, private hostnames, or
sensitive personal data in task text or evidence summaries.
