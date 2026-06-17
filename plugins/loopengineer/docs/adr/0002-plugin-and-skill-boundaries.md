# ADR 0002: Plugin and Skill Boundaries

## Status

Accepted.

## Covers

- Issue: #4
- Date: 2026-06-15

## Context

LoopEngineer needs a stable boundary before adding plugin metadata or importing
skills. Without this boundary, later work could accidentally turn LoopEngineer
into a Loom scenario skill, collapse several heavy protocols into one prompt, or
make old MC-SKILLS paths part of runtime behavior.

## Decision

LoopEngineer is a Codex plugin-oriented control-plane package.

It must not become:

- a Loom scenario skill;
- a Loom repo companion;
- a replacement for GitHub, git, CI, review engines, or worktrees;
- a runtime wrapper around MC-SKILLS;
- a single monolithic prompt that combines all loop protocols.

Skill boundaries:

- lightweight routing remains separate from context safety;
- thread orchestration remains separate from scheduler/watcher behavior;
- loop audit remains separate from execution;
- heavy protocols are kept in modular references rather than copied into short
  entrypoints;
- low-risk work should not implicitly trigger watcher or scheduler protocols.

## Consequences

- The plugin skeleton may expose `skills/`, but it must not claim hooks, MCP
  servers, apps, or marketplace entries before those surfaces exist.
- Future skill import issues should create short entries and referenced protocol
  documents instead of one large merged skill.
- Loom integration must use an explicit adapter contract and must not write
  `.loom/` state directly.
