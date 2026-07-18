#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd -P)"

if [[ "${1:-}" == "--root" ]]; then
  if [[ $# -ne 2 ]]; then
    echo "usage: $0 [--root PATH]" >&2
    exit 2
  fi
  ROOT="$(CDPATH= cd -- "$2" && pwd -P)"
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--root PATH]" >&2
  exit 2
fi

required=(
  README.md
  AGENTS.md
  ARCHITECTURE.md
  VERSION
  tasks/board.yaml
  tasks/task.schema.json
  scripts/task
  .agents/skills/task-board/SKILL.md
  .agents/skills/task-board/scripts/task
  .agents/skills/task-plan/SKILL.md
  .agents/skills/task-plan/scripts/check-task-plan.sh
  .agents/skills/plan-go/SKILL.md
  .agents/skills/plan-go/agents/openai.yaml
  .agents/skills/plan-go/LICENSE
  .agents/skills/plan-go/scripts/loop-evidence
  .agents/skills/plan-go/scripts/loop_evidence.py
  .agents/skills/plan-go/scripts/loop_spec.sh
  docs/domains/index.md
  docs/domains/general.md
  docs/design-docs/layered-testing-practice.md
  docs/generated/evidence/templates/validation-report.md
)

for relative in "${required[@]}"; do
  if [[ ! -f "$ROOT/$relative" ]]; then
    echo "context check failed: missing $relative" >&2
    exit 1
  fi
done

if [[ "$(tr -d '[:space:]' < "$ROOT/VERSION")" != "0.1.0" ]]; then
  echo "context check failed: VERSION must be 0.1.0" >&2
  exit 1
fi

python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError as error:
    raise SystemExit("context check failed: install requirements-dev.txt") from error

root = Path(sys.argv[1])
with (root / "tasks/task.schema.json").open() as stream:
    schema = json.load(stream)
if "requirement_refs" not in schema["$defs"]["task"]["required"]:
    raise SystemExit("context check failed: schema must require requirement_refs")

with (root / "tasks/board.yaml").open() as stream:
    board = yaml.safe_load(stream)
if not isinstance(board, dict):
    raise SystemExit("context check failed: root board must be a mapping")
if board.get("tasks") != []:
    raise SystemExit("context check failed: root board must start without real tasks")
PY

"$ROOT/scripts/task" validate
for plan in "$ROOT"/docs/exec-plans/active/*.md; do
  [[ -e "$plan" ]] || continue
  "$ROOT/.agents/skills/task-plan/scripts/check-task-plan.sh" "$plan"
done

for script in "$ROOT"/init.sh "$ROOT"/scripts/*.sh "$ROOT"/.agents/skills/*/scripts/*; do
  [[ -f "$script" ]] || continue
  case "$script" in
    *.sh) bash -n "$script" ;;
  esac
done

grep -Fq '.agents/skills/task-board/scripts/task' "$ROOT/scripts/task" || {
  echo "context check failed: scripts/task must wrap the task-board skill CLI" >&2
  exit 1
}

legacy_key='requirement''_rows'
legacy_flag='--requirement''-row'
if rg -n "$legacy_key|$legacy_flag" \
  "$ROOT/tasks" "$ROOT/scripts/task" "$ROOT/.agents/skills"; then
  echo "context check failed: legacy requirement-row vocabulary remains" >&2
  exit 1
fi

echo "context check passed"
