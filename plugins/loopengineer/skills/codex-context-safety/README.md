# Codex Context Safety

Use this skill before sending large prompts, cross-thread messages, heartbeat
updates, or handoff prompts.

## Role

Keep agent loop messages within explicit context budgets. If a message exceeds
the selected budget, write the large body to an artifact, send a compact
locator, or rotate to a replacement thread.

## Required Checks

1. Choose the correct profile from `schemas/v1/context-budget.default.json`.
2. Run `scripts/context_guard.py` before sending large external prompts or
   handoff messages.
3. Apply the no-inline policy for logs, diffs, reports, status tables, and old
   thread content.
4. Use the handoff manifest and replacement prompt when rotation is required.

## References

- Budget schema: `schemas/v1/context-budget.schema.json`
- Default budget: `schemas/v1/context-budget.default.json`
- Guard script: `scripts/context_guard.py`
- No-inline policy: `docs/context-safety/no-inline-large-artifacts.md`
- Handoff schema: `schemas/v1/handoff-manifest.schema.json`
- Rotation protocol: `docs/context-safety/handoff-rotation.md`
- Replacement prompt: `templates/handoff-replacement.md`

## Hard Constraints

- Do not inline full artifacts.
- Do not use old thread content as a state database.
- Do not bypass the context guard for large outgoing messages.
- Do not start watcher, scheduler, worker, hook, MCP, or Loom adapter behavior
  from this skill.
