# Codex Loop Audit

Use this skill before continuing a loop when scheduler, watcher, channel, or
report state may have drifted. It runs deterministic local audit checks and
explains the next owner/action. It does not recover state by itself.

## Required Output

- audit inputs and locators;
- `scripts/loop_audit.py` command or equivalent checked inputs;
- compact result status and finding count;
- human summary;
- next owner and next action.

## Checks

The audit script can detect:

- unconsumed reports;
- missing scheduler ACK consumption;
- stale heartbeat targets;
- stale channel owners;
- missing waiting recovery conditions;
- self-owned required next actions;
- completed reports without consumption receipts;
- missing channel release evidence.

## References

- Audit script: `scripts/loop_audit.py`
- Report consumption: `scripts/consume_report.py`
- Structures: `schemas/v1/report.schema.json`,
  `schemas/v1/dispatch-table.schema.json`,
  `schemas/v1/waiting-queue.schema.json`,
  `schemas/v1/channel-state.schema.json`,
  `schemas/v1/channel-event.schema.json`,
  `schemas/v1/watcher-inbox.schema.json`
- Watcher inbox: `docs/orchestration/watcher-inbox.md`
- No-inline policy: `docs/context-safety/no-inline-large-artifacts.md`

## Hard Constraints

- Do not execute recovery, gate, merge, release, MCP, hook, or automation work
  from this skill.
- Do not treat a status-only summary as progress when the audit assigns a
  required action to the current owner.
- Do not paste full reports, logs, tables, or thread history inline; cite
  locators and artifact paths.
