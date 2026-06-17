# Codex Scheduler Watcher

Use this skill only after the router, user, or issue scope selects a watcher or
incident recovery profile. It manages scheduler lifecycle, scheduler pools,
coordination units, and shared lane locks; it does not implement scheduler work,
worker work, review, merge, MCP, hooks, or install behavior.

## Required Output

- selected profile: `watcher_full` or `incident_recovery`;
- unit provider and completion predicate;
- references read for this profile;
- lane state or scheduler lifecycle state, if relevant;
- forbidden references or escalation;
- next owner and next action.

## Profile Routing

- `watcher_full`: multiple schedulers, coordination units, shared lane locks,
  scheduler waiting queues, or long-running watcher decisions.
- `incident_recovery`: stale watcher prompt, missing scheduler ACK, broken lane
  state, unsafe regrant, or scheduler lifecycle drift.

Do not use this skill for `direct`, `worker_lite`, `scheduler_lite`, or
ordinary `scheduler_full` work. Use `codex-thread-orchestration` for scheduler
and worker coordination.

## References

- Imported full protocol: `references/imported-protocol.md`
- Profile reads and forbidden reads:
  `docs/routing/core-skill-profile-selection.md`
- Runtime carrier: `references/orchestration-carrier.md`
- Unit model: `references/unit-model.md`
- Unit providers: `references/providers.md`
- Parallel scheduling: `references/parallel-scheduling.md`
- Lane locks: `references/lane-locks.md`
- Scheduler lifecycle: `references/scheduler-lifecycle.md`
- Watcher automation: `references/watcher-automation.md`
- Watcher inbox and rotation policy:
  `docs/orchestration/watcher-inbox.md`,
  `docs/orchestration/watcher-rotation-policy.md`
- Templates: `references/templates.md`

## Hard Constraints

- No scheduler ACK, no active scheduler transition.
- No watcher report receipt, no unit transition.
- No lane grant, no shared lane work.
- Do not create workers, consume worker reports, run gates, merge PRs, or write
  product code from watcher scope.
- Do not create or update watcher automation unless the selected profile and
  user or issue scope explicitly allow it.
