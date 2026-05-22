#!/usr/bin/env bash
# SessionStart check for CodeGraph CLI and the current project's index.
# It prints status only; it never runs indexing on its own.

set -e

echo "[CodeGraph Intelligence] Checking CodeGraph availability..."

if ! command -v codegraph >/dev/null 2>&1; then
  echo "[CodeGraph Intelligence] CodeGraph CLI is not installed. Install it with 'npm install -g @colbymchenry/codegraph' or run 'npx @colbymchenry/codegraph'."
  exit 0
fi

PROJECT_DIR="${1:-${CODEX_CWD:-${CODEX_WORKSPACE_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}}}"

if command -v git >/dev/null 2>&1 && git -C "$PROJECT_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
  PROJECT_DIR="$(git -C "$PROJECT_DIR" rev-parse --show-toplevel)"
fi

if [ ! -d "$PROJECT_DIR/.codegraph" ]; then
  echo "[CodeGraph Intelligence] No .codegraph index found at $PROJECT_DIR. Initialize it with 'codegraph init -i' from the project root."
  exit 0
fi

status_output=$(codegraph status "$PROJECT_DIR" 2>&1 || true)

printf '[CodeGraph Intelligence] CodeGraph status for %s:\n%s\n' "$PROJECT_DIR" "$status_output"
