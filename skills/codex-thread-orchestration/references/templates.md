# Templates

语言规则：模板里的自然语言默认写中文；字段名、状态枚举、工具名、命令和日志保持英文机器可读。复制模板时不要把整段回报改成英文。

## Worker Initial Prompt / Worker 初始 Prompt

```text
Worker 身份:
- worker id: <Tn>
- worker_thread_id: <worker-thread-id if known>
- scheduler_thread_id: <concrete scheduler thread id>
- report_to_thread_id: <scheduler_thread_id>
- instruction_id: <Tn-initial-YYYYMMDDHHMM>
- supersedes_instruction_id: N/A
- expected_report_type: instruction_ack_then_startup_report
- report_deadline_or_next_heartbeat_decision: <if no ack/report by next heartbeat, treat as instruction unacknowledged>
- title: [<Project/Round>][<Tn>][<units>][<PR/Task>] <short task>
- model/reasoning: <default gpt-5.5 + high for complex/high-risk/shared-contract/gate work; lower only for low-risk read-only or mechanical work>

目标:
"<exact objective>"

分配现场:
- project/root: <project-root for repository identity only>
- worker worksite: <actual worker cwd, or ask worker to read back cwd first>
- assigned branch: <branch>
- base: <base branch/ref>
- related units: <PRs/issues/tasks>
- allowed write paths:
- forbidden paths/actions:
- gate_owner: scheduler | worker-authorized

第一步:
只读确认 worksite、branch、HEAD、base、status、PR/task metadata 和 issue/task state。如果 Codex-managed worker worksite 处于 detached at base/main，这可能是正常初始化状态；只有本 prompt 明确授权时，才在 worker worksite 内切换到 assigned branch。

如果 worksite 一致，用上面的 exact objective 创建 goal，立即运行 get_goal，并把 objective/status 回报给 scheduler_thread_id。
首个 report 必须包含 `instruction_ack`，以及 `instruction_id`、`report_id`、`worker_state`、`goal_status` 和 `gate_state`。

不要写入 project/root main worktree。不要扩大 scope。除非 scheduler 针对当前 head 明确授权，不要运行 guardian/formal review/controlled merge/closeout。
```

## Scheduler Correction Prompt / Scheduler 纠偏 Prompt

```text
<Worker id>, scheduler decision:
instruction_id: <worker-id-correction-YYYYMMDDHHMM>
supersedes_instruction_id: <prior instruction id or N/A>
scheduler_thread_id: <scheduler thread id>
report_to_thread_id: <scheduler_thread_id>
expected_report_type: instruction_ack_then_correction_result
report_deadline_or_next_heartbeat_decision: <if no ack/report by next heartbeat, mark instruction unacknowledged and recover>
Current state: <state>
纠偏目标/边界:
- <specific correction>

执行:
- <allowed actions>

禁止:
- <forbidden actions>

回报内容:
- instruction_ack:
- worksite/head:
- validation:
- metadata/readback:
- report_id:
- report_for_instruction_id:
- blocker or next scheduler action:
```

## Recovery Prompt For Blocked/Complete Goal / 恢复 Prompt

```text
instruction_id: <worker-id-recovery-YYYYMMDDHHMM>
supersedes_instruction_id: <prior instruction id or N/A>
scheduler_thread_id: <scheduler thread id>
report_to_thread_id: <scheduler_thread_id>
expected_report_type: instruction_ack_then_new_goal_report
report_deadline_or_next_heartbeat_decision: <if no ack/report by next heartbeat, mark worker-stalled or create replacement>

你的 previous goal 已经 blocked/complete。goal API 不能恢复或编辑它。
请用下面的 exact objective 创建新 goal：
"<new exact objective>"

创建后运行 get_goal，并把 objective/status 回报给 report_to_thread_id。回报必须包含 `instruction_ack`、`report_id`、`report_for_instruction_id`、`worker_state`、`goal_status` 和 `gate_state`。不要把旧 goal 当作 active。
```

## Recovery Checkpoint Record / 恢复检查点记录

```text
recovery_prompt:
- worker_id:
- thread_id:
- instruction_id:
- supersedes_instruction_id:
- sent_at:
- expected_report_type: <worksite/head report | rebase result | metadata repair readback | validation result>
- target_head:
- target_base:
- target_pr_or_task:
- next_heartbeat_decision: if no scheduler-readable report or no fact change, mark worker-stalled
```

## Replacement Worker Prompt / 替换 Worker Prompt

```text
Worker 身份:
- worker id: <replacement id>
- replaces worker id/thread_id: <stalled worker>
- scheduler_thread_id: <scheduler thread id>
- report_to_thread_id: <scheduler_thread_id>
- instruction_id: <replacement-id-recovery-YYYYMMDDHHMM>
- supersedes_instruction_id: <stalled worker instruction id or N/A>
- expected_report_type: instruction_ack_then_recovered_waiting_scheduler_gate
- report_deadline_or_next_heartbeat_decision: <if no ack/report by next heartbeat, classify replacement startup failure>
- title: [<Project/Round>][<replacement id>][Recovery][<PR/Task>] <short task>

目标:
"<exact recovery objective: rebase / metadata repair / validation / PR body readback / push only>"

恢复上下文:
- stalled_worker_id:
- stalled_worker_thread_id:
- recovery_reason:
- branch:
- worksite:
- base:
- head:

边界:
- state starts as replacement-planned, then replacement-active after worksite + goal self-check
- allowed write paths:
- forbidden: expand original scope, run guardian/formal review/controlled merge, modify unrelated units
- validation requirements:
- gate_owner: scheduler

恢复完成、head/base/body 已 read back 且 hosted checks green 后，回报 `recovered-waiting-scheduler-gate`。
每个 report 都必须包含 `report_id` 和 `report_for_instruction_id`。
```

## Instruction Ack / 指令 ACK

```text
Scheduler Report:
Worker: <worker_id>
Thread: <worker_thread_id>
State: <confirming | routing-missing | active>
instruction_ack:
- received_from_scheduler_thread_id:
- report_to_thread_id:
- instruction_id:
- supersedes_instruction_id:
- accepted: yes | no
- objective_digest:
- worker_state:
- goal_status:
- gate_state:
- first_action:
- missing_fields: <none or list>
report_id: <worker-id-ack-YYYYMMDDHHMM>
report_for_instruction_id: <instruction_id>
Next scheduler action: <consume ack | send routing correction>
```

## Report Consumed Receipt / 回报消费回执

```text
Scheduler Report:
report_consumed:
- worker_id:
- worker_thread_id:
- report_id:
- report_for_instruction_id:
- report_state:
- consumed_at:
- table_updated: yes | no
- next_owner:
```

## Routing Missing Report / 路由缺失回报

```text
Scheduler Report:
Worker: <worker_id>
State: routing-missing
instruction_ack:
- instruction_id: <missing or value>
- accepted: no
- missing_fields: <scheduler_thread_id | report_to_thread_id | instruction_id | expected_report_type>
report_id:
worker_state: waiting-scheduler
goal_status: <N/A | active | blocked>
gate_state: N/A
Next scheduler action: resend correction with required routing fields
Next worker action: waiting
```

## Pending Materialization Stalled Record / Worker 物化失败记录

```text
Scheduler Report:
State: pending-materialization-stalled
pending_materialization_status: pending-materialization-stalled
请求创建的 worker:
- worker_id:
- pending_worktree_id:
- title:
- branch:
- base:
已尝试 readback:
- thread search:
- worksite search:
- branch/head:
- startup report:
原因: short readback 后没有 readable worker thread/worksite
Heartbeat Decision:
- heartbeat_decision: action_taken | global_blocker
- action_taken: create_thread | create_replacement_worker | update_heartbeat | none
- global_blocker: <tool unavailable / permission / environment / N/A>
Next scheduler action: <recreate worker | recover worker | report tool blocker>
```

## Scheduler Takeover Report / Scheduler 接管回报

```text
Scheduler Report:
State: scheduler-takeover-active
Event: scheduler-controlled-takeover
原 worker: <worker_id / thread_id>
原因: worker-stalled
并发写入: <none confirmed>
Worktree status: <clean, no rebase/merge/cherry-pick>
Branch/head/PR alignment: <branch / head / base / PR>
恢复范围: <short readback / tiny mechanical state repair / replacement preparation only>
Validation: <commands and result>
PR body readback: <aligned / mismatch>
Hosted checks: <green / pending / failed>
Next scheduler action: <run scheduler-owned gate | create replacement | classify blocker>
```

## Scheduler Takeover Abort / Escalation Report / 接管中止回报

```text
Scheduler Report:
State: takeover-escalated
Event: takeover-escalated
原 worker: <worker_id / thread_id>
升级触发条件: <needs commit | needs push | needs hosted checks wait | needs full validation | needs semantic fix | exceeds one short step>
已完成的 scheduler readback:
- PR/head/worktree:
- concurrent writes:
- worktree clean:
Next scheduler action: create replacement worker
Scheduler role restored: yes
```

## Worker Stalled Abandoned Record / 卡死 Worker 废弃记录

```text
Scheduler Report:
State: worker-stalled/abandoned
Event: worker-stalled-abandoned
Worker: <worker_id>
Thread: <thread_id>
最后已知 worksite:
最后已知 branch/head/base:
PR/task:
stall evidence:
- latest turn inProgress with no output:
- PR/head/base/updated_at stale:
- worktree old head while base/main advanced:
Replacement:
- replacement_worker_id:
- replacement_thread_id:
Current scheduler action: waiting for replacement report
```

## Fact Table Readback / 事实表读回

```text
Scheduler Fact Table:
- worker_id:
- thread_id:
- pending_worktree_id:
- last_instruction_id:
- awaiting_ack_for:
- last_report_id:
- last_report_consumed_at:
- worksite:
- branch:
- base_sha:
- merge_base:
- current_head_sha:
- PR number/state/head/base:
- issue state:
- worker_state:
- goal_status:
- gate_state:
- next_owner:
- next_action:
- blocker_classification:
- last_readback_at:
- pending_materialization_status:
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
State: <waiting-scheduler | scheduler-takeover-active | takeover-escalated>
Hosted checks: <failed check/run id>
hosted_failure_classification: <carrier drift | shadow drift | review stale | PR metadata drift | host stale run | code semantic failure>
证据:
- local validation:
- PR/body/head readback:
- repo carrier/shadow readback:
- review artifact head:
Next scheduler action: <repair | rerun after repair | replacement worker | takeover>
分类前允许 rerun: no
```

## Delegation Fallback / 委派兜底

```xml
<codex_delegation>
  <source_thread_id><worker_thread_id or worker_id></source_thread_id>
  <input>
  Worker: <worker_id>
  Unit: <issue / PR / task>
  State: <confirming | routing-missing | active | waiting-hosted | waiting-scheduler-gate | blocked | complete>
  instruction_id: <id or N/A>
  report_id: <id>
  report_for_instruction_id: <id or N/A>
  worker_state: <state>
  goal_status: <unknown/active/blocked/complete/N/A>
  gate_state: <state/N/A>
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
instruction_id: <id>
report_id: <id>
report_for_instruction_id: <id>
worker_state: waiting-scheduler-gate
goal_status: active
gate_state: ready-for-scheduler
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
你是 scheduler thread。不要创建 scheduler active goal。

Top Goal:
<completion criteria，必须包含 merge/readback/closeout>

Current Workers:
- worker_id:
- thread_id:
- pending_worktree_id:
- last_instruction_id:
- awaiting_ack_for:
- last_report_id:
- last_report_consumed_at:
- branch / worksite:
- head / base:
- state:
- blocker:
- next_scheduler_action:
- next_worker_action:

Facts Consumed Before This Heartbeat:
- worker_reports:
- live_pr_or_task_readback:
- local_git_readback:
- issue_state:
- repo_carrier_state:
- stale_heartbeat_corrected: yes|no

Planned But Not Started:
<未启动事项和启动条件>

Completed Readback:
<merged/closed/readback facts>

Heartbeat Action:
1. 读取 worker reports 和 host state。
2. 如果 worker 处于 waiting-scheduler-gate，运行或授权准确的 next gate。
3. 如果 blocked，分类 root cause，并发送 correction 或 new objective。
4. 如果当前 batch 已完成，创建下一个 dependency-ready worker。
5. 如果 pending worktree 短轮询后没有 readable thread/worksite，标记 pending-materialization-stalled 并 recreate/recover。
6. 如果 instruction-sent-awaiting-ack 到本轮仍无 ack，resend/correct routing/recover；不得标记 active。
7. 如果 prompt stale，先更新 automation，再继续调度。

Heartbeat Decision:
- heartbeat_decision: action_taken | valid_wait | global_blocker
- action_taken: <create_thread | send_message_to_thread | run_scheduler_gate | controlled_merge_readback | mark_worker_stalled | create_replacement_worker | update_heartbeat | none>
- valid_wait_reason: <same_hosted_run | active_worker_recent_output | external_bounded_wait | N/A>
- effective_progress_subject: <worker thread/run/PR/head or N/A>
- global_blocker: <classification or N/A>
- next_owner:
- next_action_by:
- next_decision_at:
```
