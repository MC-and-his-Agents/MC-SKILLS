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

## Recovery Checkpoint Record / 恢复检查点记录

```text
recovery_prompt:
- worker_id:
- thread_id:
- sent_at:
- expected_report_type: <worksite/head report | rebase result | metadata repair readback | validation result>
- target_head:
- target_base:
- target_pr_or_task:
- next_heartbeat_decision: if no scheduler-readable report or no fact change, mark worker-stalled
```

## Replacement Worker Prompt / 替换 Worker Prompt

```text
Worker identity:
- worker id: <replacement id>
- replaces worker id/thread_id: <stalled worker>
- scheduler_thread_id: <scheduler thread id>
- title: [<Project/Round>][<replacement id>][Recovery][<PR/Task>] <short task>

Objective:
"<exact recovery objective: rebase / metadata repair / validation / PR body readback / push only>"

Boundaries:
- state starts as replacement-planned, then replacement-active after worksite + goal self-check
- allowed write paths:
- forbidden: expand original scope, run guardian/formal review/controlled merge, modify unrelated units
- gate_owner: scheduler

Report `recovered-waiting-scheduler-gate` when recovery is complete, head/base/body are read back, and hosted checks are green.
```

## Scheduler Takeover Report / Scheduler 接管回报

```text
Scheduler Report:
State: scheduler-controlled-takeover
Original worker: <worker_id / thread_id>
Reason: worker-stalled
Concurrent writes: <none confirmed>
Worktree status: <clean, no rebase/merge/cherry-pick>
Branch/head/PR alignment: <branch / head / base / PR>
Recovery scope: <rebase / metadata repair / validation / push only>
Validation: <commands and result>
PR body readback: <aligned / mismatch>
Hosted checks: <green / pending / failed>
Next scheduler action: <run scheduler-owned gate | create replacement | classify blocker>
```

## Fact Table Readback / 事实表读回

```text
Scheduler Fact Table:
- worker_id:
- thread_id:
- worksite:
- branch:
- base_sha:
- merge_base:
- current_head_sha:
- PR number/state/head/base:
- issue state:
- worker_state:
- next_owner:
- next_action:
- blocker_classification:
- last_readback_at:
- fact_source_priority: live host/local git readback > repo carrier current files > newest scheduler-authored state > newest worker report > older heartbeat summary
```

## Head-Bound Artifact Refresh Report / Head 绑定刷新回报

```text
Scheduler Report:
State: recovered-waiting-scheduler-gate
Head: <current_head_sha>
Base: <base_sha>
PR headRefOid: <readback oid>
PR body machine carrier head_sha: <readback sha>
PR metadata preflight: <pass/fail>
compare-body: <pass/fail>
review artifact stale: <yes/no>
hosted gate stale-run: <yes/no>
head_bound_artifacts_refreshed: <yes/no>
Next scheduler action: <run scheduler-owned gate | refresh artifacts | classify blocker>
```

## Hosted Failure Classification / Hosted 失败分类

```text
Scheduler Report:
State: <waiting-scheduler | scheduler-controlled-takeover>
Hosted checks: <failed check/run id>
hosted_failure_classification: <carrier drift | shadow drift | review stale | PR metadata drift | host stale run | code semantic failure>
Evidence:
- local validation:
- PR/body/head readback:
- repo carrier/shadow readback:
- review artifact head:
Next scheduler action: <repair | rerun after repair | replacement worker | takeover>
Rerun allowed before classification: no
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
