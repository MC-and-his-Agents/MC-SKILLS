#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/install-local-skills.sh [--dry-run] [skill-name ...]

Developer-only helper for a local MCSKILLS source checkout.
Install repository skills into $CODEX_HOME/skills as top-level symlinks.
When skill names are provided, install only those skills.
This is not the default installation path for general MCSKILLS users.

Safety checks:
- must run from the MCSKILLS main branch
- worktree must be clean
- existing non-symlink skill directories are replaced only when identical to source
- installed skills are validated after linking

Environment:
- CODEX_HOME defaults to ~/.codex
- SKILL_VALIDATOR defaults to ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py
USAGE
}

dry_run=0
requested_skills=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      requested_skills+=("$1")
      shift
      ;;
  esac
done

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

branch="$(git branch --show-current)"
if [[ "$branch" != "main" ]]; then
  echo "refusing to install skills from branch '$branch'; switch to main first" >&2
  exit 1
fi

if [[ -n "$(git status --short)" ]]; then
  echo "refusing to install skills from a dirty worktree" >&2
  git status --short >&2
  exit 1
fi

codex_home="${CODEX_HOME:-$HOME/.codex}"
install_root="$codex_home/skills"
validator="${SKILL_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"

if [[ ! -d "$install_root" ]]; then
  echo "missing install root: $install_root" >&2
  exit 1
fi

if [[ ! -f "$validator" ]]; then
  echo "missing skill validator: $validator" >&2
  exit 1
fi

run() {
  if [[ "$dry_run" -eq 1 ]]; then
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

installed=0
for skill_dir in "$repo_root"/skills/*; do
  [[ -d "$skill_dir" ]] || continue
  [[ -f "$skill_dir/SKILL.md" ]] || continue

  skill_name="$(basename "$skill_dir")"
  if [[ "$skill_name" == ".system" ]]; then
    continue
  fi

  if [[ "${#requested_skills[@]}" -gt 0 ]]; then
    found=0
    for requested in "${requested_skills[@]}"; do
      if [[ "$skill_name" == "$requested" ]]; then
        found=1
        break
      fi
    done
    if [[ "$found" -eq 0 ]]; then
      continue
    fi
  fi

  target="$install_root/$skill_name"

  echo "installing skill: $skill_name"
  python3 "$validator" "$skill_dir"

  if [[ -L "$target" ]]; then
    current_target="$(readlink "$target")"
    if [[ "$current_target" == "$skill_dir" ]]; then
      echo "  already linked: $target -> $skill_dir"
    else
      echo "  updating symlink: $target -> $skill_dir"
      run ln -sfn "$skill_dir" "$target"
    fi
  elif [[ -e "$target" ]]; then
    if [[ -d "$target" ]] && diff -qr "$skill_dir" "$target" >/dev/null; then
      echo "  replacing identical installed directory with symlink"
      run rm -rf "$target"
      run ln -s "$skill_dir" "$target"
    else
      echo "  refusing to replace non-identical installed path: $target" >&2
      echo "  resolve the diff manually, then rerun this script" >&2
      exit 1
    fi
  else
    echo "  creating symlink: $target -> $skill_dir"
    run ln -s "$skill_dir" "$target"
  fi

  if [[ "$dry_run" -eq 0 ]]; then
    python3 "$validator" "$target"
  fi

  installed=$((installed + 1))
done

if [[ "$installed" -eq 0 ]]; then
  if [[ "${#requested_skills[@]}" -gt 0 ]]; then
    echo "no requested skills found under $repo_root/skills: ${requested_skills[*]}" >&2
  else
    echo "no skills found under $repo_root/skills" >&2
  fi
  exit 1
fi

echo "installed $installed skill(s) into $install_root"
