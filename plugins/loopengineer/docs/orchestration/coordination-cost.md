# Coordination Cost

Issue: #27

Coordination improves safety, but every scheduler, watcher, heartbeat, report,
and cross-thread message adds control-plane cost. LoopEngineer treats that cost
as an input to routing, not as permission to skip safety.

## Inputs

The v1 cost model considers:

- control-plane tokens;
- cross-thread messages;
- report reads;
- report writes;
- heartbeat wakeups;
- recovery actions;
- worker count;
- scheduler count.

These inputs are local estimates. They do not integrate with billing systems.

## Tiers

| Recommended profile | Cost score | Use when |
| --- | --- | --- |
| `direct` | 0-9 | Single-owner work can finish without delegation. |
| `worker_lite` | 10-24 | One bounded worker-style scope is useful. |
| `scheduler_lite` | 25-49 | A small set of tasks needs ordering or report consumption. |
| `scheduler_full` | 50-79 | Multiple workers, strict gates, or shared contracts need coordination. |
| `watcher_full` | 80-119 | Multiple schedulers, shared lanes, or long-running observation need a watcher. |
| `incident_recovery` | 120+ | Recovery, repeated drift, or stale facts dominate normal scheduling. |

The score is advisory. Required safety checks, shared-channel grants, review
gates, merge controls, and release evidence cannot be bypassed because a lower
cost profile looks cheaper.

## Marginal Scheduling Cost

Adding another worker or scheduler is justified only when its expected value
exceeds its marginal cost:

- more prompts and acknowledgements;
- more report artifacts to consume;
- more heartbeat or readback obligations;
- more recovery paths if the worker or scheduler stalls;
- more shared-channel contention if it touches shared state.

Prefer direct execution or worker-lite when the task is narrow. Prefer
scheduler-lite before scheduler-full when ordering and ownership are enough.
Prefer watcher-full only when multiple schedulers or shared lanes are real.

## Script

`scripts/coordination_tax.py` calculates the v1 score and emits JSON:

```text
python3 scripts/coordination_tax.py \
  --control-plane-tokens 1200 \
  --cross-thread-messages 2 \
  --reports-read 3 \
  --reports-written 2 \
  --heartbeats 1 \
  --recovery-actions 0 \
  --workers 1 \
  --schedulers 0
```

The script is read-only. It does not create threads, modify GitHub, write git
state, update issues, or change LoopEngineer structures.

## Non-Goals

This model does not implement billing integration, automatic routing, watcher
runtime behavior, MCP, hooks, merge, or release actions.
