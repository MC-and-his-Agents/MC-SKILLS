# ADR 0004: Runtime-Neutral Loop Engine Interface

## Status

Accepted.

## Covers

- Issue: #28
- Date: 2026-06-16

## Context

M6 originally deferred optional MCP and hooks until context safety, routing,
schemas, scripts, audit, and coordination cost were stable enough to expose.
After M5, LoopEngineer has deterministic local scripts and JSON output for loop
judgment work. Loom remains the runtime owner for execution, recovery, review,
merge-ready, closeout, and `.loom` facts.

If M6 starts with MCP or hooks as the product surface, LoopEngineer can be
misread as a second runtime or lifecycle system. That would conflict with the
repository boundary and Loom integration boundary.

## Decision

M6 uses a runtime-neutral CLI/JSON Loop Engine contract as the first product
surface.

Implementation priority is:

```text
Context safety first.
Router second.
Heavy orchestration later.
CLI/JSON engine contract before adapters.
MCP and host hooks as optional adapters only.
```

The first engine contract exposes deterministic judgment capabilities:

- context guard;
- structure validation;
- state digest;
- loop audit;
- coordination cost;
- session preflight or admission reminder.

MCP is an optional adapter over the CLI/JSON contract. Session hooks, if
provided, are host integration examples that call preflight or admission
reminder. They do not define a hook system.

`engineContractVersion` is the CLI/JSON engine contract compatibility boundary.
`adapterContractVersion` remains the external adapter compatibility boundary.

## Consequences

- #28 must define the engine contract boundary before wrapper or adapter work.
- #82 owns the unified CLI/JSON entrypoint.
- #30 owns preflight or admission reminder, not lifecycle hooks.
- #29 owns an optional MCP adapter that wraps the CLI/JSON contract.
- `consume_report` stays outside the first engine contract because it writes a
  local receipt.
- LoopEngineer does not create workers, schedulers, watchers, automations,
  issues, PRs, gates, merges, releases, or Loom `.loom` facts.
