# Handoff Rotation Protocol

Issue: #8

## Purpose

Handoff rotation prevents a long-running agent thread from becoming the only
place where work state exists. When a thread approaches context risk, ownership
changes, or recovery needs a cleaner execution surface, the active owner writes
a compact handoff manifest and starts the replacement from explicit facts.

This protocol defines the checklist and prompt shape only. It does not create a
real replacement thread and does not implement a full recovery runtime.

## Authority

The replacement thread may recover from:

- the state root directory named in the manifest;
- the handoff manifest itself;
- live git and GitHub facts verified at takeover time;
- artifact and report locators referenced by the manifest.

The replacement thread must not recover from:

- retired thread history;
- old thread transcripts;
- memory-only completion claims;
- inline large artifacts pasted into chat.

If the manifest and live facts disagree, live facts and repository state win,
and the replacement owner must record the mismatch before continuing.

## Rotation Triggers

Rotate before the thread becomes unsafe to continue:

- context budget is near the configured limit;
- the next prompt would require a large inline payload;
- the active owner changes;
- recovery needs to rebuild from facts after drift;
- evidence cannot be safely consumed in the current thread.

Rotation is a control-plane action. It is not proof that the task is complete.

## Handoff Checklist

Before asking a replacement thread to continue, the current owner records:

- goal and bounded scope;
- state root locator;
- branch, head SHA, workspace, and issue/PR locators;
- evidence locators and consumed status;
- explicit next owner and next action;
- out-of-scope items and prohibitions;
- reason for rotation.

The checklist belongs in a manifest that conforms to
`schemas/v1/handoff-manifest.schema.json`.

## Replacement Prompt

The replacement prompt should use `templates/handoff-replacement.md`. It should
carry only compact locators and decisions. Large logs, diffs, reports, review
records, or old thread turns must be written to artifacts and referenced by
path or URL.

## Recovery Rules

The replacement owner starts by reading the manifest and state root, then
verifies live git and GitHub facts. It may use the retired thread only as
non-authoritative orientation when a human supplies a small quote. It must not
treat retired thread content as a state database.

Missing facts are blockers. The replacement owner should ask for the missing
locator or regenerate the fact from live sources instead of guessing from
conversation memory.

## Non-Goals

This protocol does not:

- create a scheduler, watcher, worker, or replacement thread;
- install automations;
- write Loom `.loom/` state;
- implement recovery runtime behavior;
- replace git, GitHub, CI, review, or merge gates.
