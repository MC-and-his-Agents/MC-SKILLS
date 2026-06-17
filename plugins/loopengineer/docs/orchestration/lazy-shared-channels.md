# Lazy Shared Channel Policy

Issue: #24

Shared channels protect state that more than one scheduler could change, but a
loop should not pay full watcher and channel-table cost before shared work is
actually requested. This policy defines the lightest sufficient channel mode.

## Modes

| Mode | Use when | Required state |
| --- | --- | --- |
| `disabled` | The task is single-owner and does not touch shared facts, review records, gates, merge, or contracts. | No channel table is required. |
| `declared-forbidden-scope` | Work can start, but some shared paths or actions are explicitly forbidden until later grant. | Prompt or dispatch state names the forbidden scope and allowed non-channel work. |
| `active-locking` | A scheduler requests access to shared state, a shared gate, merge, review carrier, or contract surface. | Watcher-owned channel state, waiting queue, and release evidence are required. |

## Default Decision

Start in `disabled` unless the issue, route profile, or implementation plan has
a concrete shared-state signal. Move to `declared-forbidden-scope` when work can
proceed safely without the shared resource, but the prompt must prevent drift
into it. Move to `active-locking` only when a scheduler actually needs shared
access.

Implementation preparation alone does not require a full shared channel table.
Examples include local fixtures, read-only inventory, branch setup, isolated
docs, or code that cannot touch shared carriers before review.

## Active Locking Triggers

Enter `active-locking` before any scheduler:

- writes shared fact-chain, status, bootstrap, or shadow carrier state;
- updates current-item review records or review finding disposition;
- runs a shared high-cost gate;
- performs controlled merge or post-merge readback;
- changes schema, API, parser, release, or protocol contracts used by another
  scheduler;
- requests a path already named in another scheduler's forbidden or granted
  scope.

## Safety Rules

- No channel grant means no shared write, shared gate, merge, or contract
  action.
- Forbidden scope must name the paths or actions that are blocked before grant.
- Allowed non-channel work must be narrow enough for a scheduler to keep moving
  without weakening the lock.
- A release claim is not enough to free a channel; release evidence must prove
  the owner no longer touches the channel scope.
- If the loop cannot prove whether work is shared, choose
  `declared-forbidden-scope` and ask the scheduler to report the missing facts.

## Evidence Shape

For `disabled`, record only the routing reason when the task could otherwise
look shared.

For `declared-forbidden-scope`, include:

```text
channel_mode: declared-forbidden-scope
forbidden_until_grant:
allowed_non_channel_work:
next_owner:
next_action:
```

For `active-locking`, use the v1 channel structures:

- `loopengineer.channelState`
- `loopengineer.waitingQueue`
- `loopengineer.channelEvent`
- `loopengineer.watcherDecision`

These structures stay in files. Cross-thread messages carry locators and a
compact next owner/action only.

## Non-Goals

This policy does not implement a channel runtime, create watcher automation,
create scheduler threads, or weaken shared resource safety.
