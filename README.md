# MCSKILLS

This repository collects Codex skills and Codex plugins.

[中文版](./README.zh-CN.md)

## Skills

Standalone skills live under `skills/`. They are kept as lightweight reusable
assets and are not listed in the plugin marketplace.

- [write-a-goal](./skills/write-a-goal/SKILL.md) - Draft, refine, or set durable Codex goals.
- [code-smell-decision](./skills/code-smell-decision/SKILL.md) - Discover code smells, collect engineering evidence, and decide whether to fix, defer, track as debt, accept, or escalate.
- [codex-thread-orchestration](./skills/codex-thread-orchestration/SKILL.md) - Coordinate scheduler/worker Codex threads for scoped execution, reporting, gates, and closeout.
- [codex-scheduler-watcher](./skills/codex-scheduler-watcher/SKILL.md) - Create meta-scheduler watcher automations that maintain coordination units, scheduler pools, and scheduler lifecycle without taking over worker or gate execution.

## Local Source Checkout Sync

For maintainers working from this local source checkout, changes merged to `main`
can be exposed to the local Codex runtime with symlinks:

```bash
./scripts/install-local-skills.sh <skill-name>
```

This is a developer convenience for local source iteration, not the default
installation path for general users. The script links selected
`skills/*/SKILL.md` directories into `~/.codex/skills/<skill-name>` and validates
the installed paths. Omit `<skill-name>` only when every local skill is ready to
be linked.

## Plugins

Installable plugins live under `plugins/`. Repo marketplace metadata is defined
in [`.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json).

- [codegraph-intelligence](./plugins/codegraph-intelligence/README.md) - CodeGraph-backed workflows for code exploration, impact analysis, refactoring and review.

## Notes

- Keep this README as a lightweight navigation page as new skills are added.
- Future standalone skills should live under `skills/`.
- Future installable plugins should live under `plugins/` and be added to the marketplace only when their plugin metadata is ready.
