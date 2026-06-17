# LoopEngineer Roadmap

LoopEngineer is an independent agent loop control-plane plugin. The roadmap is
ordered to keep context safety and routing stable before heavier orchestration.

Priority order:

```text
Context safety first.
Router second.
Heavy orchestration later.
CLI/JSON engine contract before adapters.
MCP and host hooks as optional adapters only.
```

## Milestones

| Milestone | Focus | Representative issues | Notes |
| --- | --- | --- | --- |
| M0 | Repository baseline and architecture decisions | #1, #2, #3, #4, #31 | Confirm boundaries, README, roadmap, ADR index, and collaboration templates. |
| M1 | Context safety minimum version | #5, #6, #7, #8, #9, #32 | Define budgets, guards, no-inline policy, handoff, and context safety skill. |
| M2 | Plugin skeleton and lightweight routing | #10, #11, #12, #33 | Add plugin structure and route work without triggering heavy protocols. |
| M3 | Protocol profiles and skill refactor | #13, #14, #15, #16, #17, #34 | Import and split core skills with provenance and profile selection. |
| M4 | Deterministic scripts and structure definitions | #18, #19, #20, #21, #22, #35, #46 | Add schemas, validation, state digest, and report consumption scripts. |
| M5 | Loop audit, cost control, and watcher policy | #23, #24, #25, #26, #27, #36 | Completed in `v0.4.0`: audit, coordination cost, watcher inbox, lazy channels, and watcher rotation policy. |
| M6 | Runtime-neutral Loop Engine interface | #28, #82, #30, #29, #81, #37 | Define the CLI/JSON engine contract first; add MCP only as an optional adapter. |
| M7 | Subagent worker_lite provider | #87, #88, #89, #90, #91, #92, #93, #94, #95 | Completed in `v0.6.0`: provider matrix, assignment/report contract, deterministic checks, and compatibility closeout. |
| Loom integration | External plugin integration | #38, #39, #40, #41 | Define adapter boundaries before any install or register action. |
| Release planning | Manual release process | #47 | Keep release evidence and compatibility fields explicit; see `docs/releases/v0.1.0.md`. |

## Current Scope

The current baseline establishes:

- LoopEngineer as a standalone Codex plugin repository;
- MC-SKILLS as read-only provenance, not runtime dependency;
- Loom as an optional external integration through an adapter contract;
- context safety as the first runtime layer;
- routing as the next layer after context safety;
- heavy orchestration, optional adapters, hooks, and Loom adapter actions as later work.

## Non-Goals

Current baseline work does not:

- import core skills;
- implement scripts or schemas;
- create watcher, scheduler, or worker threads;
- replace GitHub, git, CI, review engines, or worktrees;
- write Loom `.loom/` state;
- add MCP servers, lifecycle hooks, apps, or marketplace entries.

## Issue Closeout

Parent issues are closed only after their child issue scope is complete. For
example, #31 remains open until all M0 child issues, including #3, have landed.
