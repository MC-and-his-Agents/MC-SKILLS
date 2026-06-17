# Heavy Skill Trigger Policy

Issue: #12

Heavy orchestration protocols are explicit-only. Low-risk tasks must not
implicitly load or start full scheduler, watcher, worker-pool, MCP, hook, or
automation behavior.

## Current Control

LoopEngineer imports the core orchestration skills, but their heavy protocol
content is explicit-only. The repository exposes short entrypoints, and full
protocol references are read only after router, user, or issue scope selects a
matching profile.

The current plugin manifest does not define a stable field for disabling
implicit skill triggers. Do not invent one. Until such a host contract exists,
control is enforced by:

- keeping short skill entrypoints separate from heavy references;
- requiring the router to recommend escalation before any heavy protocol is
  selected;
- treating watcher behavior as unavailable to direct and lightweight tasks.

## Explicit Trigger Rule

Future heavy skills must require an explicit user, issue, or router decision.
They must not be selected only because a task is important, long, or asks for
care.

Heavy profiles require concrete signals:

- `scheduler_full`: multiple workers, strict gates, shared contracts, or
  release-sensitive validation;
- `watcher_full`: multiple schedulers, shared lanes, long-running observation,
  repeated gate drift, or cross-workstream state;
- `incident_recovery`: stale facts, polluted context, failed handoff,
  conflicting state, or repeated unclassified failures.

## Watcher Restrictions

Watcher behavior must not be:

- directly executed by a low-risk task;
- triggered by `direct`, `worker_lite`, or `scheduler_lite` routing alone;
- used as a substitute for ownership, tests, review, or merge gates;
- started before context safety and routing facts are explicit.

## Non-Triggers

The following are not enough to start heavy protocols:

- a normal test or review is needed;
- the task is important but single-scope;
- documentation, schema, or policy work is bounded;
- the user asks for thoroughness without multi-owner or shared-state signals;
- a lightweight context guard or handoff check is sufficient.

## Non-Goals

This policy does not implement routing logic, create runtime hooks, add MCP
servers, start watcher threads, or install automations.
