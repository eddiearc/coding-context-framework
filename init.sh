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
  ARCHITECTURE.md
  VERSION
  scripts/task
  tasks/board.yaml
  tasks/task.schema.json
  .agents/skills/task-board/SKILL.md
  .agents/skills/task-board/scripts/task
  .agents/skills/task-plan/SKILL.md
  .agents/skills/task-plan/scripts/check-task-plan.sh
  docs/domains/index.md
  docs/domains/general.md
  docs/design-docs/layered-testing-practice.md
  docs/generated/evidence/templates/evidence-manifest.yaml
  docs/generated/evidence/templates/integration-cases.md
  docs/generated/evidence/templates/validation-report.md
)

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
for relative in "${files[@]}"; do
  destination="$TARGET/$relative"
  if [[ -e "$destination" || -L "$destination" ]]; then
    if [[ ! -f "$destination" ]] || ! cmp -s -- "$STAGING/$relative" "$destination"; then
      conflicts+=("$relative")
    fi
  fi
done

if (( ${#conflicts[@]} > 0 )); then
  echo "initialization failed: refusing to overwrite changed files:" >&2
  for relative in "${conflicts[@]}"; do
    echo "  $relative" >&2
  done
  exit 1
fi

for relative in "${files[@]}"; do
  destination="$TARGET/$relative"
  if [[ ! -e "$destination" ]]; then
    mkdir -p -- "$(dirname -- "$destination")"
    cp -- "$STAGING/$relative" "$destination"
  fi
done

chmod +x \
  "$TARGET/scripts/task" \
  "$TARGET/.agents/skills/task-board/scripts/task" \
  "$TARGET/.agents/skills/task-plan/scripts/check-task-plan.sh"

echo "initialized Coding Context Framework in $TARGET"
