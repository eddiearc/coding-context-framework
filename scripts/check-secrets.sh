#!/usr/bin/env bash
set -euo pipefail

PINNED_VERSION="8.24.2"
ROOT="."

if [[ "${1:-}" == "--root" ]]; then
  if [[ $# -ne 2 ]]; then
    echo "usage: $0 [--root PATH]" >&2
    exit 2
  fi
  ROOT="$2"
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--root PATH]" >&2
  exit 2
fi

if ! command -v gitleaks >/dev/null 2>&1; then
  echo "secret check failed: Gitleaks v$PINNED_VERSION is required" >&2
  exit 2
fi

actual_version="$(gitleaks version 2>/dev/null || true)"
if [[ "$actual_version" != *"$PINNED_VERSION"* ]]; then
  echo "secret check failed: expected Gitleaks v$PINNED_VERSION, got $actual_version" >&2
  exit 2
fi

gitleaks dir "$ROOT" --no-banner --redact --exit-code 1
