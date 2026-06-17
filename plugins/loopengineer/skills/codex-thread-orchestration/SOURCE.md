# Source Provenance

Issue: #13

This skill was imported from the legacy MC-SKILLS repository as a read-only
source. LoopEngineer must not depend on that path at runtime.

## Source

- Source repository: `https://github.com/MC-and-his-Agents/MC-SKILLS.git`
- Source checkout: `/Users/mc/dev/MC-SKILLS`
- Source path: `skills/codex-thread-orchestration/`
- Local source path used for import: `../MC-SKILLS/skills/codex-thread-orchestration/`
- Source commit: `4495346edbe459ec914e657cd82ec13ad18fbd7c`
- Source commit date: `2026-06-15T11:14:03+08:00`
- Source commit subject: `[codex] 将本地编排 SKILL 改为 carrier 驱动 (#20)`
- Target path: `skills/codex-thread-orchestration/`
- Target repository commit at import: `11298ed809a1c83b2a1a18e96d9098b600b0bd12`
- Imported on: `2026-06-15`

## Imported Files

- `references/imported-protocol.md` from legacy `SKILL.md`
- `README.md` as the LoopEngineer short entrypoint
- `agents/openai.yaml`
- `references/gates-and-closeout.md`
- `references/goal-lifecycle.md`
- `references/heartbeat.md`
- `references/orchestration-carrier.md`
- `references/reporting.md`
- `references/scheduler.md`
- `references/templates.md`
- `references/worker.md`

## File Mapping

- `SKILL.md` -> `references/imported-protocol.md`
- `agents/openai.yaml` -> `agents/openai.yaml`
- `references/*.md` -> `references/*.md`

## Excluded Files

- `.DS_Store`

## Boundary

The import preserves the original protocol semantics for scheduler and worker
coordination. The full imported entry lives in `references/imported-protocol.md`
so the skill `README.md` can remain a short entrypoint.

## Non-Goals

- No runtime script, MCP, hook, automation, install, or register behavior.
