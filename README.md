# MCSKILLS

This repository collects Codex skills and Codex plugins.

[中文版](./README.zh-CN.md)

## Skills

Standalone skills live under `skills/`. They are kept as lightweight reusable
assets and are not listed in the plugin marketplace.

- [write-follow-goal](./skills/write-follow-goal/SKILL.md) - Draft and refine durable `/goal` instructions.
- [code-smell-decision](./skills/code-smell-decision/SKILL.md) - Discover code smells, collect engineering evidence, and decide whether to fix, defer, track as debt, accept, or escalate.

## Plugins

Installable plugins live under `plugins/`. Repo marketplace metadata is defined
in [`.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json).

- [codegraph-intelligence](./plugins/codegraph-intelligence/README.md) - CodeGraph-backed workflows for code exploration, impact analysis, refactoring and review.

## Notes

- Keep this README as a lightweight navigation page as new skills are added.
- Future standalone skills should live under `skills/`.
- Future installable plugins should live under `plugins/` and be added to the marketplace only when their plugin metadata is ready.
