# Subagent Boundaries

Issues: #17, #87

Subagents can reduce main-thread noise, but they are bounded helpers. They do
not replace LoopEngineer's thread communication control plane.

## Control Plane

Thread communication owns the control plane:

- objective and scope assignment;
- scheduler and watcher instruction IDs;
- report locators and report consumption;
- shared lane grants, waits, releases, and recovery;
- review, merge, release, closeout, and state transitions;
- final evidence readback and next owner/action.

## Subagent Role

Use subagents for bounded assistance:

- isolated read-only exploration;
- scoped implementation with disjoint file ownership;
- local test, log, or CI failure analysis;
- focused review of safety, correctness, test, performance, or maintainability
  risks;
- mechanical inventory or summary work that would pollute the main thread.

Each subagent assignment must state the goal, input locator, read range, write
ownership, forbidden scope, validation expectation, conflict handling, and
output format.

For `worker_lite`, a subagent can be selected as an execution provider when the
task is short, low risk, isolated, bounded, and useful to run outside the main
thread. The provider contract is:

- assignment records `unit_id`, `instruction_id`, `agent_id`, `thread_id`,
  objective digest, allowed read/write paths, forbidden scope, expected report
  type, report output path, validation expectation, next owner, and next action;
- `agent_id` and `thread_id` may be the same value when the host exposes the
  subagent id as a readable thread locator;
- report consumption uses the assignment and report locator, not the subagent
  final answer alone;
- changed paths and validation results must be checked before a completed
  subagent report can drive any control-plane update.

## Prohibitions

Subagents must not own:

- shared channels or lane locks;
- scheduler pool, watcher pool, or coordination unit state;
- report consumption or state transitions;
- review approval, guardian, merge, release, or closeout;
- external permissions, deployment, payment, or production write actions;
- recovery authority for retired, abandoned, or `systemError` thread history.

Escalate from subagent provider to formal thread worker when the work needs
shared contract ownership, external writes, independent branch/worktree state,
long-running recovery, formal gates, merge-ready, release, closeout, or strict
state replay.

Subagent output is evidence for the main agent or scheduler to review. It is
not itself a state transition, merge-ready decision, or closeout proof.

## Completion Rule

The main agent remains accountable for integrating subagent results, validating
current repository state, updating authoritative carriers, and reporting final
evidence. If a subagent result conflicts with live facts, live repository and
host readback wins.
