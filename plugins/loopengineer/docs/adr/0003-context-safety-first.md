# ADR 0003: Context Safety First

## Status

Accepted.

## Covers

- Issue: #4
- Date: 2026-06-15

## Context

LoopEngineer's product goal is reliable agent loops. The earliest runtime risk
is uncontrolled context growth: large logs, diffs, reports, and old thread state
can become invisible dependencies and make recovery unreliable.

## Decision

Context safety is the first runtime safety layer.

Implementation priority is:

```text
Context safety first.
Router second.
Heavy orchestration later.
MCP and hooks last.
```

Context safety owns the first minimum runtime checks:

- budget profiles;
- no-inline-large-artifact policy;
- locator-only messaging for large evidence;
- handoff and rotation requirements;
- admission checks before large prompts, cross-thread messages, and recovery
  prompts.

The router can only make good decisions after the context boundary is explicit.
Watcher, scheduler, MCP, and hook work must wait until the context safety and
routing foundations exist.

## Consequences

- M1 context safety work is a dependency for later orchestration depth.
- M2 plugin skeleton work may create directories and metadata, but it must not
  implement heavy runtime behavior.
- Future checks should fail closed when context risk cannot be classified.
