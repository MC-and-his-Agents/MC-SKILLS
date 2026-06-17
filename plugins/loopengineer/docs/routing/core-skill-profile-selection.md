# Core Skill Profile Selection

Issues: #15, #16, #34

Core orchestration skills are imported but explicit-only. Select the lightest
sufficient profile before reading heavy references.

## Profile Reads

| Profile | Skill | Required reads | Forbidden reads |
| --- | --- | --- | --- |
| `direct` | none | `docs/routing/route-profiles.md`, `docs/routing/trigger-matrix.md` | All `codex-thread-orchestration` and `codex-scheduler-watcher` references |
| `worker_lite` | `codex-thread-orchestration` | `references/worker.md`, `references/reporting.md`, `references/orchestration-carrier.md`; for provider choice also read `docs/routing/route-profiles.md` | Watcher references; scheduler gate/closeout references unless requested by scheduler |
| `scheduler_lite` | `codex-thread-orchestration` | `references/scheduler.md`, `references/reporting.md`, `references/orchestration-carrier.md` | Watcher references; `references/gates-and-closeout.md` unless gates are in scope |
| `scheduler_full` | `codex-thread-orchestration` | `references/imported-protocol.md`, `references/scheduler.md`, `references/reporting.md`, `references/gates-and-closeout.md`, `references/templates.md` | Watcher references unless shared lanes or multiple schedulers are in scope |
| `watcher_full` | `codex-scheduler-watcher` | `references/imported-protocol.md`, `references/unit-model.md`, `references/providers.md`, `references/lane-locks.md`, `references/scheduler-lifecycle.md`, `references/parallel-scheduling.md` | Worker references and scheduler implementation details except scheduler prompt handoff requirements |
| `incident_recovery` | selected by failure locus | Read the owning skill's `references/imported-protocol.md`, carrier, reporting, lifecycle, and templates needed to restore facts | Unrelated role references, retired thread turns, and any merge/release action without explicit authorization |

## Selection Rules

- `direct` work must not load either core orchestration skill.
- `worker_lite` is for one bounded worker scope with scheduler-readable reports.
  It may use `direct`, `subagent`, or `thread`; subagent is only a bounded
  execution provider and never owns state transition, gate, merge, release, or
  closeout.
- `scheduler_lite` is for one scheduler coordinating a small number of scopes
  without shared lanes or high-cost gates.
- `scheduler_full` is for dependency tracking, worker replacement, report
  consumption, gate ownership, or closeout.
- `watcher_full` is for multiple schedulers, shared lane locks, scheduler pools,
  candidate graphs, or watcher lifecycle decisions.
- `incident_recovery` follows the broken state owner: worker/scheduler failures
  use `codex-thread-orchestration`; watcher/lane/scheduler-pool failures use
  `codex-scheduler-watcher`.

## Completion Proof

Profile selection does not weaken completion proof. State transitions still
require ACKs, locator-backed reports, consumption receipts, current head/base
readback where applicable, and explicit next owner/action.
