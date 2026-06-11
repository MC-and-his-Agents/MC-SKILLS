# Reporting Protocol

scheduler-readable reporting 是硬要求。只在 worker thread 内写“完成了”不够，除非 scheduler 能通过 thread readback 消费。

## Delivery Priority / 投递优先级

使用当前可用的最强投递路径：

1. worker thread 可用 `send_message_to_thread` 时，发送给具体 `scheduler_thread_id`。
2. 没有跨线程发送工具时，在关键节点或 final response 输出 `<codex_delegation>` envelope。
3. 两者都不可用时，输出以 `Scheduler Report:` 开头的机器可读 block。

scheduler 必须提供具体 `scheduler_thread_id`、`report_to_thread_id` 和 `instruction_id`。如果缺失，worker 在 worksite/goal self-check 后回报 `routing-missing` 并等待 correction。

## Required Report Nodes / 必要回报节点

worker 必须在这些节点回报：

- worksite 和 goal self-check 完成。
- 收到 initial/correction/recovery/replacement 指令后的 `instruction_ack`。
- 指令缺少 `scheduler_thread_id`、`report_to_thread_id`、`instruction_id` 或 `expected_report_type` 时的 `routing-missing`。
- PR/task 创建或更新，且 head/body/payload metadata readback 完成。
- hosted checks pending 或 in progress。
- hosted checks pass。
- hosted checks fail，并完成 root-cause classification。
- 进入 `waiting-scheduler-gate`。
- blocker 需要 scheduler decision。
- 标记 goal `blocked` 前。
- 标记 goal `complete` 前。
- final scope completion。

scheduler 在改变 table state、运行 high-cost gate、恢复 blocked/complete worker、关闭 batch 或声明 Top Goal complete 前，必须读取并消费 report。
scheduler 消费 report 后必须记录 `report_consumed`；没有 receipt 的 report 不得驱动 table transition。

## Minimal Report Schema / 最小回报结构

在 `send_message_to_thread`、delegation envelope 或 fallback report 中使用这个形状：

```text
Worker: <worker_id>
Thread: <worker_thread_id>
Title: <standard title>
Unit: <issue / PR / task / N/A>
State: <confirming | instruction-sent-awaiting-ack | routing-missing | active | waiting-hosted | waiting-scheduler-gate | stopped_at_waiting_scheduler_gate | waiting-scheduler | waiting-on-worker | pending-materialization-stalled | worker-stalled | worker-stalled/abandoned | replacement-planned | replacement-active | scheduler-takeover-active | takeover-escalated | recovered-waiting-scheduler-gate | blocked | complete>
instruction_id: <id or N/A>
supersedes_instruction_id: <id or N/A>
report_id: <worker_id-report-YYYYMMDDHHMM or equivalent>
report_for_instruction_id: <instruction_id or N/A>
instruction_ack: <accepted | rejected | N/A>
objective_digest: <short digest or N/A>
worker_state: <same state vocabulary>
goal_status: <unknown | active | blocked | complete | N/A>
gate_state: <not-ready | waiting-scheduler-gate | ready-for-scheduler | authorized | passed | failed | N/A>
Objective: <exact objective or short id>
Worksite: <path>
Branch: <branch>
Head: <head_sha>
Base: <base_sha>
Merge base: <merge_base>
PR/Task: <url or N/A>
Issue state: <state or N/A>
Validation: <commands and pass/fail summary>
Hosted checks: <pending/pass/fail with run ids if available>
hosted_failure_classification: <carrier drift | shadow drift | review stale | PR metadata drift | host stale run | code semantic failure | N/A>
head_bound_artifacts_refreshed: <yes | no | N/A>
pending_materialization_status: <N/A | pending | materialized | pending-materialization-stalled>
heartbeat_decision: <N/A | action_taken | valid_wait | global_blocker>
action_taken: <N/A | create_thread | send_message_to_thread | run_scheduler_gate | controlled_merge_readback | mark_worker_stalled | create_replacement_worker | update_heartbeat | other>
valid_wait_reason: <N/A | same_hosted_run | active_worker_recent_output | external_bounded_wait>
effective_progress_subject: <thread/run/PR/head or N/A>
Event: <replacement-worker-created | scheduler-controlled-takeover | takeover-escalated | worker-stalled-abandoned | N/A>
Gate owner: <scheduler | worker-authorized>
Gate status: <not-ready | ready-for-scheduler | authorized | passed | failed | N/A>
Gate Failure Ledger: <N/A or compact pr/head/attempts/repetition/escalation summary>
Invariant checklist: <complete | partial | N/A>
Fail-closed matrix coverage: <positive paths / negative cases / gaps / N/A>
Unverifiable invariants: <none or list with owner>
Admission-style valid=true path audited: <yes | no | N/A>
Root-cause correction completed: <yes | no | N/A>
Blocker: <none or classified root cause>
Next owner: <scheduler | worker | replacement | external>
Next scheduler action: <exact action needed>
Next worker action: <exact action or waiting>
Risks: <remaining risk or none>
```

## Instruction Ack / 指令确认

worker 收到任何 initial/correction/recovery/replacement prompt 后，必须先回：

```text
instruction_ack:
- received_from_scheduler_thread_id:
- report_to_thread_id:
- instruction_id:
- supersedes_instruction_id:
- accepted: yes | no
- objective_digest:
- worker_state:
- goal_status:
- first_action:
- missing_fields: <none or list>
```

`accepted=yes` 只表示 worker 已收到并接受该指令，不表示任务完成。`accepted=no` 或 `missing_fields` 非空时，worker 状态为 `routing-missing` 或 `waiting-scheduler`，不得开始实施。

## Report Consumed Receipt / 回报消费回执

scheduler 消费 worker report 后记录：

```text
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

没有 `report_consumed` 时，不得把 worker report 当作已更新 fact table。旧 report 与新 report 冲突时，以带有最新 `report_id`、当前 head/base readback 且已消费的 report 为准。

## Delegation Fallback / 委派兜底

```xml
<codex_delegation>
  <source_thread_id><worker_thread_id or worker_id></source_thread_id>
  <input>
  Worker: <worker_id>
  Unit: <issue / PR / task>
  State: <confirming | routing-missing | active | waiting-hosted | waiting-scheduler-gate | stopped_at_waiting_scheduler_gate | pending-materialization-stalled | worker-stalled | worker-stalled/abandoned | scheduler-takeover-active | takeover-escalated | recovered-waiting-scheduler-gate | blocked | complete>
  instruction_id: <id or N/A>
  report_id: <id>
  report_for_instruction_id: <id or N/A>
  instruction_ack: <accepted/rejected/N/A>
  worker_state: <state>
  goal_status: <unknown/active/blocked/complete/N/A>
  gate_state: <state/N/A>
  PR: <url or N/A>
  Head: <head_sha>
  Base: <base_sha>
  Validation: <commands and pass/fail summary>
  Hosted checks: <pending/pass/fail with run ids if available>
  hosted_failure_classification: <classification or N/A>
  head_bound_artifacts_refreshed: <yes/no/N/A>
  pending_materialization_status: <N/A/pending/materialized/pending-materialization-stalled>
  Gate owner: <scheduler | worker-authorized>
  Invariant checklist: <complete/partial/N/A>
  Fail-closed matrix coverage: <positive paths / negative cases / gaps / N/A>
  Unverifiable invariants: <none or list with owner>
  Admission-style valid=true path audited: <yes/no/N/A>
  Root-cause correction completed: <yes/no/N/A>
  Blocker: <none or root cause>
  Next scheduler action: <exact action needed>
  Next worker action: <exact action or waiting>
  </input>
</codex_delegation>
```

## Scheduler Decision Request / 请求调度决策

worker 需要 scheduler 判断时，回报：

```text
Scheduler decision needed:
- blocker:
- evidence:
- why outside my scope:
- proposed next action:
- current goal status:
```

如果没有该决策就不能继续有意义推进，发送 report 后 block current goal。

## Complete Before Report Is Invalid / 未回报不得完成

worker 在生成 scheduler-readable report 前，不得将 goal 标记为 complete。report 至少包含：

- PR/task URL 或等价 carrier。
- head/base。
- validation commands 和 result。
- hosted checks，以及可用的 run ids。
- gate owner 和 gate status。
- issue/task state。
- final worktree status。
- remaining risks，或明确 none。

scheduler 消费该 report 前，不得把 worker 视为 complete。
