# Templates

## Worker Initial Prompt / Worker 初始 Prompt

```text
Worker identity:
- worker id: <Tn>
- worker_thread_id: <worker-thread-id if known>
- scheduler_thread_id: <concrete scheduler thread id>
- title: [<Project/Round>][<Tn>][<units>][<PR/Task>] <short task>
- model/reasoning: <default gpt-5.5 + high for complex/high-risk/shared-contract/gate work; lower only for low-risk read-only or mechanical work>

Objective:
"<exact objective>"

Assigned worksite:
- project/root: <project-root for repository identity only>
- worker worksite: <actual worker cwd, or ask worker to read back cwd first>
- assigned branch: <branch>
- base: <base branch/ref>
- related units: <PRs/issues/tasks>
- allowed write paths:
- forbidden paths/actions:
- gate_owner: scheduler | worker-authorized

First action:
Read-only confirm worksite, branch, HEAD, base, status, PR/task metadata, and issue/task state. If the Codex-managed worker worksite is detached at base/main, this may be normal; switch to the assigned branch only inside the worker worksite and only if authorized here.

If the worksite is consistent, create a goal with the exact objective above, immediately run get_goal, and report objective/status to scheduler_thread_id.

Do not write project/root main worktree. Do not expand scope. Do not run guardian/formal review/controlled merge/closeout unless explicitly authorized for the current head.
```

## Scheduler Correction Prompt / Scheduler 纠偏 Prompt

```text
<Worker id>, scheduler decision:
Current state: <state>
Correction objective/boundary:
- <specific correction>

Do:
- <allowed actions>

Do not:
- <forbidden actions>

Report back with:
- worksite/head:
- validation:
- metadata/readback:
- blocker or next scheduler action:
```

## Recovery Prompt For Blocked/Complete Goal / 恢复 Prompt

```text
Your previous goal is blocked/complete. The API cannot resume or edit it.
Create a new goal with this exact objective:
"<new exact objective>"

After creation, run get_goal and report objective/status to scheduler_thread_id. Do not treat the old goal as active.
```

## Delegation Fallback / 委派兜底

```xml
<codex_delegation>
  <source_thread_id><worker_thread_id or worker_id></source_thread_id>
  <input>
  Worker: <worker_id>
  Unit: <issue / PR / task>
  State: <active | waiting-hosted | waiting-scheduler-gate | blocked | complete>
  PR: <url or N/A>
  Head: <head_sha>
  Base: <base_sha>
  Validation: <commands and pass/fail summary>
  Hosted checks: <pending/pass/fail with run ids if available>
  Gate owner: <scheduler | worker-authorized>
  Blocker: <none or root cause>
  Next scheduler action: <exact action needed>
  Next worker action: <exact action or waiting>
  </input>
</codex_delegation>
```

## Waiting Scheduler Gate Report / 等待调度 Gate 回报

```text
Scheduler Report:
Worker: <worker_id>
State: waiting-scheduler-gate
Worksite: <path>
Branch: <branch>
Head: <head_sha>
Base: <base_sha>
PR/Task: <url>
Scope diff: <matches objective / notes>
Local validation: <commands passed>
Hosted checks: <green, run ids>
Metadata readback: <body/payload/head aligned>
Findings: <none or dispositioned>
Same-class search: <done / N/A>
Gate owner: scheduler
Next scheduler action: <run guardian / formal review / controlled merge / post-merge readback>
Next worker action: waiting
```

## Heartbeat Prompt Skeleton / Heartbeat Prompt 骨架

```text
You are the scheduler thread. Do not create a scheduler active goal.

Top Goal:
<completion criteria, including merge/readback/closeout>

Current Workers:
- worker_id:
- thread_id:
- branch / worksite:
- head / base:
- state:
- blocker:
- next_scheduler_action:
- next_worker_action:

Planned But Not Started:
<unstarted items and start conditions>

Completed Readback:
<merged/closed/readback facts>

Heartbeat Action:
1. Read worker reports and host state.
2. If waiting-scheduler-gate, run or authorize the exact next gate.
3. If blocked, classify root cause and send a correction or new objective.
4. If current batch is complete, create the next dependency-ready worker.
5. If prompt is stale, update automation before more scheduling.
```
