# Watcher Inbox

Issue: #26

The watcher inbox is the first file a watcher should read before loading full
scheduler pools, channel tables, reports, or event artifacts. It keeps watcher
wakeups compact and makes the next required action visible without using thread
history as a state database.

## Structure

The v1 structure is `loopengineer.watcherInbox`, defined in
`schemas/v1/watcher-inbox.schema.json`.

It carries:

- source locators used to generate the inbox;
- compact counts for unread or stale work;
- unconsumed scheduler report locators;
- unconsumed channel event locators;
- unacknowledged scheduler instructions;
- stale scheduler heartbeat targets;
- stale channel owners;
- candidate units;
- required next actions.

The inbox does not replace the scheduler pool, channel state, waiting queue,
channel events, watcher decisions, or report artifacts. It points to them.

## Read Order

Watcher wakeups should read in this order:

1. watcher inbox or state digest;
2. only the source locators named by the inbox;
3. full report, channel, or pool artifacts only when the inbox requires them;
4. live host facts only when needed to resolve a stale target, release
   predicate, or external wait.

If the inbox says `next_action.owner=watcher`, the watcher must either perform a
real watcher-owned action or classify a blocker. It must not stop at a status
summary.

## Inbox Generation

Inbox generation is deterministic and local. It may be produced by a watcher,
scheduler, or future script, but it must not create automations, grant channels,
merge PRs, or update external systems.

The inbox should be regenerated after:

- scheduler report receipt;
- channel request, grant, wait, denial, or release;
- scheduler instruction send;
- heartbeat target readback;
- stale owner classification;
- unit readiness change.

## Context Safety

The inbox is a summary surface. It must not inline complete reports, complete
channel tables, complete scheduler pools, full logs, thread previews, or gate
output. Those bodies stay in artifacts, and the inbox stores locators.

## Non-Goals

This design does not implement a watcher runtime, create watcher automation,
create scheduler threads, expose MCP, install hooks, or weaken channel grants.
