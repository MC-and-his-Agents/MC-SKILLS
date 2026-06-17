# Routing Trigger Matrix

Issue: #11

Use the lowest matching profile. Escalate only when the task has a concrete
signal that the lower profile cannot handle.

| Signal | Profile |
| --- | --- |
| Single small edit, answer, check, or local decision | `direct` |
| One bounded implementation or investigation scope | `worker_lite` |
| Two or more independent low-risk tasks that need ownership tracking | `scheduler_lite` |
| Multiple workers, shared contract changes, strict review gates, or release-sensitive validation | `scheduler_full` |
| Multiple schedulers, shared lane locks, long-running monitors, repeated gate drift, or cross-workstream state | `watcher_full` |
| Stale facts, polluted context, failed handoff, conflicting state, or repeated unclassified failures | `incident_recovery` |

## Default Decisions

- Prefer `direct` for single-owner work.
- Prefer `worker_lite` for one bounded delegated scope.
- Inside `worker_lite`, prefer `direct` for single-owner work, `subagent` for
  short low-risk isolated bounded work, and `thread` for long-running,
  recovery-sensitive, gate-heavy, shared-contract, external-write, or worktree
  work.
- Prefer `scheduler_lite` before `scheduler_full` unless strict gates or shared
  contracts require stronger coordination.
- Prefer `incident_recovery` when current state cannot be trusted.

## Non-Triggers

These signals alone do not justify heavy orchestration:

- task is important but single-scope;
- user asks for care or thoroughness;
- a normal test run is needed;
- documentation or schema work is small and bounded;
- context safety can be handled by the context guard and handoff manifest.
