#!/usr/bin/env bash
# Narrow CLI fallback for test-target-finder.
# Reads changed files from arguments, stdin, or git diff against HEAD, then calls
# `codegraph affected --stdin --json`.

set -euo pipefail

PROJECT_DIR="."
DEPTH=""
FILTER=""

usage() {
  cat <<'USAGE'
Usage: codegraph-affected.sh [--project PATH] [--depth N] [--filter GLOB] [FILE...]

Inputs:
  FILE...        Changed files. If omitted, reads stdin. If stdin is empty and
                 git is available, falls back to `git diff --name-only HEAD`.

Output:
  JSON from `codegraph affected --stdin --json`.
USAGE
}

files=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --project|-p)
      PROJECT_DIR="${2:?missing project path}"
      shift 2
      ;;
    --depth|-d)
      DEPTH="${2:?missing depth}"
      shift 2
      ;;
    --filter|-f)
      FILTER="${2:?missing filter}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do
        files+=("$1")
        shift
      done
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      files+=("$1")
      shift
      ;;
  esac
done

if ! command -v codegraph >/dev/null 2>&1; then
  echo "codegraph CLI is not installed. Install @colbymchenry/codegraph first." >&2
  exit 127
fi

if [ ! -d "$PROJECT_DIR/.codegraph" ]; then
  echo "CodeGraph index not found at $PROJECT_DIR/.codegraph. Run 'codegraph init -i' first." >&2
  exit 3
fi

input=""
if [ "${#files[@]}" -gt 0 ]; then
  input="$(printf '%s\n' "${files[@]}")"
elif [ ! -t 0 ]; then
  input="$(cat)"
fi

if [ -z "$(printf '%s' "$input" | tr -d '[:space:]')" ] && command -v git >/dev/null 2>&1; then
  if git -C "$PROJECT_DIR" rev-parse --show-toplevel >/dev/null 2>&1; then
    input="$(git -C "$PROJECT_DIR" diff --name-only HEAD)"
  fi
fi

if [ -z "$(printf '%s' "$input" | tr -d '[:space:]')" ]; then
  echo "No changed files provided. Pass files as arguments, pipe file names, or run inside a git repo with changes." >&2
  exit 4
fi

cmd=(codegraph affected --path "$PROJECT_DIR" --stdin --json)
if [ -n "$DEPTH" ]; then
  cmd+=(--depth "$DEPTH")
fi
if [ -n "$FILTER" ]; then
  cmd+=(--filter "$FILTER")
fi

printf '%s\n' "$input" | "${cmd[@]}"
