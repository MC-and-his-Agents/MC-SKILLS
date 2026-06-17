# Architecture Decision Records

This index tracks LoopEngineer architecture decisions that affect repository
boundaries, plugin shape, skill boundaries, and context safety priority.

| ADR | Status | Covers | Decision |
| --- | --- | --- | --- |
| [0001 Repository Boundary and MVP](0001-repository-boundary-and-mvp.md) | Accepted | #1 | LoopEngineer proceeds as an independent Codex plugin repository with MC-SKILLS as read-only provenance only. |
| [0002 Plugin and Skill Boundaries](0002-plugin-and-skill-boundaries.md) | Accepted | #4 | LoopEngineer remains a plugin-oriented control plane; core heavy skills stay separate and modular. |
| [0003 Context Safety First](0003-context-safety-first.md) | Accepted | #4 | Context safety is the first runtime safety layer; routing follows; heavy orchestration, MCP, and hooks are deferred. |
| [0004 Runtime-Neutral Loop Engine Interface](0004-runtime-neutral-engine-interface.md) | Accepted | #28 | M6 exposes a CLI/JSON engine contract first; MCP and host hooks are optional adapters only. |
| [0005 Subagent worker_lite Provider](0005-subagent-worker-lite-provider.md) | Accepted | #87 | `worker_lite` supports `direct`, `subagent`, and `thread` providers while preserving LoopEngineer control-plane boundaries. |

## Rules

- ADRs record decisions that constrain later issues and PRs.
- ADRs should link the issue that required the decision.
- A superseding ADR must point back to the replaced decision.
- Large background notes belong in separate artifacts or docs, not inline in the ADR.
