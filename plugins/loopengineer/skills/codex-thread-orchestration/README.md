# Codex Thread Orchestration

Use this skill only after the router, user, or issue scope selects a scheduler
or worker orchestration profile. It coordinates scheduler/worker thread
protocols; it does not manage watcher pools, shared lane locks, MCP, hooks, or
automations.

## Required Output

- detected role: `scheduler`, `worker`, or `unclear`;
- selected profile: `worker_lite`, `scheduler_lite`, `scheduler_full`, or
  `incident_recovery`;
- references read for this profile;
- forbidden references or escalation;
- next owner and next action.

## Profile Routing

- `worker_lite`: bounded delegated execution by one worker using `direct`,
  `subagent`, or `thread` provider.
- `scheduler_lite`: one scheduler tracking a small set of independent scopes.
- `scheduler_full`: scheduler-owned workers, reports, gates, closeout, or
  strict dependency handling.
- `incident_recovery`: stalled worker, stale facts, missing ACK/report, broken
  carrier, or unsafe recovery.

Do not use this skill for `direct` work. Do not start watcher behavior from this
skill.

## References

- Imported full protocol: `references/imported-protocol.md`
- Profile reads and forbidden reads:
  `docs/routing/core-skill-profile-selection.md`
- Runtime carrier: `references/orchestration-carrier.md`
- Scheduler protocol: `references/scheduler.md`
- Worker protocol: `references/worker.md`
- Reporting protocol: `references/reporting.md`
- Goal lifecycle: `references/goal-lifecycle.md`
- Heartbeat protocol: `references/heartbeat.md`
- Gates and closeout: `references/gates-and-closeout.md`
- Templates: `references/templates.md`

## Hard Constraints

- No scheduler-readable report, no complete.
- No instruction ACK, no active worker transition.
- No report consumption receipt, no fact-table transition.
- Do not use thread history as the state database.
- Do not read retired, abandoned, or `systemError` thread turns as facts.
- Do not run guardian, formal review, merge, release, or closeout unless the
  selected profile and gate owner allow it.
