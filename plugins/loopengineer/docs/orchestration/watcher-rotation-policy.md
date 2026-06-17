# Watcher Automation And Rotation Policy

Issue: #25

Watcher automation is optional and explicit. A watcher should not depend on a
long-lived thread as its state store, and a stale prompt must be refreshed
before it can safely drive scheduler or channel decisions.

## Modes

| Mode | Use when | Behavior |
| --- | --- | --- |
| `manual-readback` | A human or scheduler only needs a one-time watcher check. | Read watcher inbox or digest once; do not create automation. |
| `scheduled-wakeup` | Active scheduler pool or shared channel state needs periodic readback. | Use a compact prompt that points at state root, inbox, budget, and forbidden actions. |
| `incident-recovery` | Watcher prompt, scheduler ACK, lane state, or lifecycle facts are stale or inconsistent. | Stop ordinary scheduling and repair state, prompt, or target binding first. |

Do not create or update watcher automation unless the selected profile and
issue or user scope explicitly allow it.

## Summary-First Read Rule

Every watcher wakeup starts from a compact source:

1. `loopengineer.watcherInbox`;
2. `state_digest.py --mode full` output;
3. specifically named source locators from the inbox or digest.

The watcher loads full scheduler pools, channel state, reports, gate output, or
live host facts only when the summary points to them. Thread history is not a
state database.

Thread history is not a state database; stale watcher prompts must not override
fresh inbox, digest, artifact, or host readback facts.

## Rotation Thresholds

Watcher prompts use the context budget profile `heartbeat_prompt` from
`schemas/v1/context-budget.default.json`:

- warn at 675 estimated tokens;
- hard limit at 900 estimated tokens;
- overflow action is `rotate_thread`.

If a watcher prompt reaches the warning threshold, compress it to locators and
summary counts before the next wakeup. If it exceeds the hard limit, rotate or
handoff before adding more state. Do not paste full reports, lane tables,
scheduler pools, thread previews, or logs into the prompt to avoid rotation.

Imported watcher protocol references also use larger byte-oriented limits for
host automation prompts. The repository-level v1 budget remains authoritative
for LoopEngineer-owned prompt admission.

## Stale Prompt Update Rules

Refresh the watcher prompt before continuing when any of these changed after
the prompt was written:

- watcher inbox id or generated time;
- scheduler pool membership or scheduler status;
- unconsumed scheduler report or channel event locator;
- waiting queue order, stale owner, or release predicate;
- heartbeat target binding;
- issue, PR, head, base, or repo carrier facts;
- completion predicate or candidate unit readiness.

The refreshed prompt should contain only state root, inbox or digest locator,
decision checklist, hard forbidden actions, budget, and next readback time.

## Valid Wakeup Outcomes

A watcher wakeup must end in one of these states:

- action taken by watcher;
- valid bounded wait with current evidence;
- no notification because no facts changed;
- user notification;
- classified blocker;
- complete.

If `next_action.owner=watcher`, the watcher must perform a watcher-owned action
or classify why it cannot. A status-only summary is not progress.

## Non-Goals

This policy does not create actual automations, scheduler threads, watcher
threads, MCP tools, hooks, merge actions, or release actions.
