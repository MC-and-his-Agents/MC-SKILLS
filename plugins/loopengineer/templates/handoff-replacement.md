# Handoff Replacement Prompt

Use this template when a loop must rotate to a replacement thread because the
current thread is approaching context risk or ownership is changing.

Do not paste the retired thread history into the replacement thread. The
replacement thread must recover only from the state root, this handoff manifest,
current git/GitHub facts, and referenced artifacts.

```text
You are taking over a LoopEngineer-managed task.

Goal:
<one sentence goal>

Authority:
- State root: <path>
- Handoff manifest: <path>
- Live facts to verify: git branch/head, GitHub issue/PR state, referenced
  artifacts

Forbidden recovery sources:
- retired thread history
- old thread transcript
- memory-only claims
- inline large artifacts

Current state:
- Workspace: <absolute worktree path>
- Branch: <branch>
- Head SHA: <head_sha>
- Issue/PR: <locator>
- Status: <in_progress | blocked | ready_for_review | ready_for_handoff |
  complete>

Evidence locators:
- <kind>: <locator> (consumed: <true | false>)

Next owner:
<owner>

Next action:
<single concrete next action>

Instructions:
1. Read the handoff manifest and state root before continuing.
2. Verify live git and GitHub facts before trusting stale locators.
3. Consume evidence by locator; do not ask for full logs, diffs, or reports
   inline.
4. Treat the retired thread as non-authoritative context only if a human
   explicitly provides a small quote for orientation.
5. If required facts are missing, stop and request the missing locator instead
   of reconstructing state from memory.
```
