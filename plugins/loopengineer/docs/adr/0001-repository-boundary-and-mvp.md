# ADR 0001: Repository Boundary and MVP

## Status

Accepted.

## Covers

- Issue: #1
- Date: 2026-06-15

## Context

LoopEngineer is a new repository for an agent loop control-plane plugin. The
first implementation step must confirm the execution environment and repository
boundary before skills, scripts, schemas, or runtime code are introduced.

Recorded environment facts:

| Fact | Value |
| --- | --- |
| Working directory | `/Users/mc/dev/LoopEngineer` |
| Git root | `/Users/mc/dev/LoopEngineer` |
| Remote | `https://github.com/MC-and-his-Agents/LoopEngineer.git` |
| Baseline branch | `main` tracking `origin/main` |
| Baseline head | `6d6986d72811eb0ab3da68eddd7bc2402ac75dbe` |
| Baseline status | Clean worktree before this ADR branch |

## Decision

LoopEngineer proceeds as an independent Codex plugin repository.

It may use the old MC-SKILLS repository only as a read-only provenance source
when a future issue explicitly asks for skill import or semantic alignment.
MC-SKILLS is not a runtime dependency, install target, state store, or authority
for LoopEngineer behavior.

The minimum product scope is:

- define context safety, routing, evidence, audit, recovery, and coordination
  cost as LoopEngineer-owned control-plane concerns;
- preserve GitHub, git, CI, review engines, and worktrees as external sources
  of truth instead of replacing them;
- keep Loom integration optional and adapter-based;
- land context safety before lightweight routing;
- defer heavy orchestration, MCP, hooks, and Loom adapter actions until their
  later issues.

## Consequences

- README and roadmap should describe LoopEngineer as a standalone product, not
  as a migration directory for prior skills.
- Future imports from MC-SKILLS must record source path and source commit.
- This ADR does not import skills, implement plugin runtime code, or create
  watcher, scheduler, or worker threads.
