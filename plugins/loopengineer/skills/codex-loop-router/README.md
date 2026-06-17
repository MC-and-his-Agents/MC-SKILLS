# Codex Loop Router

Use this skill to choose the lightest sufficient LoopEngineer execution profile.
It selects a profile and explains the next owner/action; it does not execute
worker, scheduler, watcher, hook, MCP, or automation behavior.

## Required Output

- recommended profile;
- reason for the recommendation;
- prohibited escalation, if any;
- next owner;
- next action.

## Profiles

- `direct`
- `worker_lite`
- `scheduler_lite`
- `scheduler_full`
- `watcher_full`
- `incident_recovery`

## References

- Profile definitions: `docs/routing/route-profiles.md`
- Trigger matrix: `docs/routing/trigger-matrix.md`
- Heavy trigger policy: `docs/routing/heavy-trigger-policy.md`
- Context budget: `docs/context-safety/context-budget.md`
- No-inline policy: `docs/context-safety/no-inline-large-artifacts.md`

## Hard Constraints

- Do not start orchestration from this skill.
- Do not create workers when `direct` is enough.
- Do not start a scheduler when `worker_lite` is enough.
- Do not start a watcher when routing or scheduling is enough.
- Do not bypass context safety checks for large prompts or handoffs.
