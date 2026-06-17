# Route Profiles

Issue: #11

LoopEngineer routes each task to the lightest sufficient profile. The router
chooses; it does not execute orchestration.

## Profiles

| Profile | Use when | Output owner |
| --- | --- | --- |
| `direct` | One owner can complete the work without delegation, shared state, or gate-heavy review. | current agent |
| `worker_lite` | Work is bounded to one scope and benefits from a worker-style objective, but does not need scheduling. Provider is `direct`, `subagent`, or `thread`. | worker |
| `scheduler_lite` | A small set of independent tasks needs ordering, ownership, or report consumption. | scheduler |
| `scheduler_full` | Multiple workers, strict gates, or cross-module contracts need explicit coordination. | scheduler |
| `watcher_full` | Multiple schedulers, shared lanes, long-running observation, or repeated gate drift must be coordinated. | watcher |
| `incident_recovery` | The loop is broken, bloated, inconsistent, or cannot recover from current facts. | recovery owner |

## Router Output

The router response should include:

- recommended profile;
- one-sentence reason;
- next owner;
- next action;
- explicit prohibitions, such as not starting watcher behavior for a low-risk task.

For `worker_lite`, the router should also include a provider recommendation:

| Provider | Use when | Must escalate when |
| --- | --- | --- |
| `direct` | One current owner can complete the bounded scope without delegation or isolation. | Work needs independent execution, worksite isolation, or recovery. |
| `subagent` | Short, low-risk, isolated work is clear enough to delegate and return through assignment/report consumption. | Work touches shared contracts, external writes, gates, merge, release, closeout, strict recovery, or long-running state. |
| `thread` | Formal worker worksite, branch/worktree isolation, high-cost gates, recovery, or long-running ownership is required. | Do not downshift after these signals appear. |

## Boundaries

The router must not:

- create workers, schedulers, watchers, automations, hooks, or MCP calls;
- import heavy orchestration skills;
- treat chat history as authoritative state;
- bypass context safety for large messages.
