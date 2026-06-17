# ADR 0005: Subagent worker_lite Provider

## Status

Accepted.

## Covers

- Issue: #87
- Date: 2026-06-17

## Context

M7 introduces a lighter execution provider for `worker_lite`. The experiment on
2026-06-17 showed that a spawned subagent returns an `agent_id` that can be used
as a `read_thread.threadId` locator for reading the subagent thread summary.
The same observation did not prove that `read_thread` exposes the full `/goal`
state object or the complete delegated objective.

This means subagents can reduce main-thread noise and perform bounded work, but
their final answer is not a control-plane fact. LoopEngineer still needs an
assignment contract, a locator-backed report, and explicit report consumption
before any state transition.

## Decision

`worker_lite` supports three providers:

```text
direct | subagent | thread
```

- `direct`: current agent completes a single-owner bounded scope.
- `subagent`: a short, low-risk, isolated, bounded execution provider with an
  explicit assignment and report contract.
- `thread`: a formal worker thread for long-running, high-risk, shared-contract,
  recovery-sensitive, gate-heavy, or worktree-backed work.

Subagent assignment records `agent_id` and `thread_id` explicitly. They may be
the same value when the host exposes the subagent id as a readable thread id.
The assignment and report locator are the consumption basis; the subagent final
answer is auxiliary evidence only.

## Consequences

- Subagents must not own shared channels, state transitions, gates, merge,
  release, closeout, external writes, or recovery authority.
- Provider selection can be recommended deterministically, but it does not spawn
  subagents, workers, schedulers, or watchers.
- Subagent report eligibility must fail closed when instruction binding, report
  locator, changed path scope, validation result, or forbidden authority claims
  are missing or invalid.
- `consume_report` may check a subagent assignment before writing a receipt, but
  it remains outside the runtime-neutral engine capability set because it writes
  a local artifact.
