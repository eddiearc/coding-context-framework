#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)"
SKIP_SECRETS=0
if [[ "${1:-}" == "--skip-secrets" && $# -eq 1 ]]; then
  SKIP_SECRETS=1
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--skip-secrets]" >&2
  exit 2
fi

cd "$ROOT"
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m unittest discover -s .agents/skills/task-board/tests -p 'test_*.py' -v
python3 -m unittest discover -s .agents/skills/task-plan/tests -p 'test_*.py' -v
scripts/check-context.sh
scripts/check-publication.sh
if [[ "$SKIP_SECRETS" -eq 0 ]]; then
  scripts/check-secrets.sh
fi
