#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 --target PATH" >&2
}

if [[ $# -ne 2 || "$1" != "--target" || -z "$2" ]]; then
  usage
  exit 2
fi

SOURCE_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
TARGET="$2"

if [[ -e "$TARGET" && ! -d "$TARGET" ]]; then
  echo "initialization failed: target is not a directory: $TARGET" >&2
  exit 1
fi

mkdir -p -- "$TARGET"
TARGET="$(CDPATH= cd -- "$TARGET" && pwd -P)"

STAGING="$(mktemp -d "${TMPDIR:-/tmp}/coding-context-framework-init.XXXXXX")"
trap 'rm -rf -- "$STAGING"' EXIT

files=(
  AGENTS.md
  CLAUDE.md
  ARCHITECTURE.md
  VERSION
  scripts/task
  tasks/board.yaml
  tasks/task.schema.json
  tests/__init__.py
  tests/helpers.py
  tests/test_claude_compat.py
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
  .agents/skills/herdr-workflow/SKILL.md
  .agents/skills/herdr-workflow/references/evaluation.md
  docs/domains/index.md
  docs/domains/general.md
  docs/design-docs/layered-testing-practice.md
  docs/exec-plans/_template.md
  docs/generated/evidence/templates/evidence-manifest.yaml
  docs/generated/evidence/templates/integration-cases.md
  docs/generated/evidence/templates/validation-report.md
  docs/agent-routing.md
)

claude_skills=(task-board task-plan plan-go herdr-workflow)

for relative in "${files[@]}"; do
  source_file="$SOURCE_ROOT/$relative"
  if [[ ! -f "$source_file" ]]; then
    echo "initialization failed: source file is missing: $relative" >&2
    exit 1
  fi
  mkdir -p -- "$STAGING/$(dirname -- "$relative")"
  cp -- "$source_file" "$STAGING/$relative"
done

conflicts=()
migrate_legacy_claude_md=false
migrate_legacy_claude_skills=false

if [[ -L "$TARGET/CLAUDE.md" && "$(readlink "$TARGET/CLAUDE.md")" == "AGENTS.md" ]]; then
  migrate_legacy_claude_md=true
fi

if [[ -L "$TARGET/.claude/skills" ]]; then
  if [[ "$(readlink "$TARGET/.claude/skills")" == "../.agents/skills" ]]; then
    migrate_legacy_claude_skills=true
  else
    conflicts+=(".claude/skills")
  fi
elif [[ -e "$TARGET/.claude/skills" && ! -d "$TARGET/.claude/skills" ]]; then
  conflicts+=(".claude/skills")
fi

for relative in "${files[@]}"; do
  destination="$TARGET/$relative"
  if [[ "$relative" == "CLAUDE.md" && "$migrate_legacy_claude_md" == true ]]; then
    continue
  fi
  if [[ -e "$destination" || -L "$destination" ]]; then
    if [[ ! -f "$destination" ]] || ! cmp -s -- "$STAGING/$relative" "$destination"; then
      conflicts+=("$relative")
    fi
  fi
done

if [[ "$migrate_legacy_claude_skills" != true ]]; then
  for name in "${claude_skills[@]}"; do
    relative=".claude/skills/$name"
    destination="$TARGET/$relative"
    expected_target="../../.agents/skills/$name"
    if [[ -L "$destination" ]]; then
      if [[ "$(readlink "$destination")" != "$expected_target" ]]; then
        conflicts+=("$relative")
      fi
    elif [[ -e "$destination" ]]; then
      conflicts+=("$relative")
    fi
  done
fi

if (( ${#conflicts[@]} > 0 )); then
  echo "initialization failed: refusing to overwrite changed files:" >&2
  for relative in "${conflicts[@]}"; do
    echo "  $relative" >&2
  done
  exit 1
fi

for relative in "${files[@]}"; do
  destination="$TARGET/$relative"
  if [[ "$relative" == "CLAUDE.md" && "$migrate_legacy_claude_md" == true ]]; then
    unlink "$destination"
  fi
  if [[ ! -e "$destination" ]]; then
    mkdir -p -- "$(dirname -- "$destination")"
    cp -- "$STAGING/$relative" "$destination"
  fi
done

if [[ "$migrate_legacy_claude_skills" == true ]]; then
  unlink "$TARGET/.claude/skills"
fi
mkdir -p -- "$TARGET/.claude/skills"
for name in "${claude_skills[@]}"; do
  destination="$TARGET/.claude/skills/$name"
  if [[ ! -e "$destination" && ! -L "$destination" ]]; then
    ln -s "../../.agents/skills/$name" "$destination"
  fi
done

chmod +x \
  "$TARGET/scripts/task" \
  "$TARGET/.agents/skills/task-board/scripts/task" \
  "$TARGET/.agents/skills/task-plan/scripts/check-task-plan.sh" \
  "$TARGET/.agents/skills/plan-go/scripts/loop-evidence" \
  "$TARGET/.agents/skills/plan-go/scripts/loop_evidence.py" \
  "$TARGET/.agents/skills/plan-go/scripts/loop_spec.sh"

echo "initialized Coding Context Framework in $TARGET"
