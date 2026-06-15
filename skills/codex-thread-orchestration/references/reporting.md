# Reporting Protocol

scheduler-readable reporting 是硬要求，但 report 的完整内容不得通过线程正文传递。默认先写 artifact，再传 locator。

## Delivery Priority / 投递优先级

使用当前可用的最强投递路径：

1. worker/scheduler 将完整 report 写入 `report_output_path`。
2. 可用 `send_message_to_thread` 时，向具体 `report_to_thread_id` 发送 locator-only notice。
3. 没有跨线程发送工具时，在当前可达 channel 输出 locator-only fallback notice。
4. 没有可写 `report_output_path` 时，输出 `report-path-missing` blocker；禁止把完整 report 粘进线程正文。

允许的跨线程正文只包含：

```text
Scheduler Report Notice:
- report_id:
- report_path:
- state_root:
- unit_id:
- state:
- head:
- base:
- next_owner:
- next_action:
```

禁止在 `<codex_delegation>`、`Scheduler Report:`、thread preview、普通 final response 或 correction 正文中传完整 report、完整 validation log、完整 gate output、完整 shell output、完整 dispatch table。

scheduler 必须提供具体 `scheduler_thread_id`、`report_to_thread_id`、`instruction_id`、`orchestration_state_root`、`report_output_path`、`report_size_budget` 和 `do_not_read_retired_thread_turns: true`。如果缺失，worker 在 worksite/goal self-check 后写 `routing-missing` artifact，并发送 locator-only notice 后等待 correction。

## Required Report Nodes / 必要回报节点

worker 必须在这些节点写完整 report artifact，并发送 locator-only notice：

- worksite 和 goal self-check 完成。
- 收到 initial/correction/recovery/replacement 指令后的 `instruction_ack`。
- 指令缺少必需 routing 或 carrier 字段时的 `routing-missing`。
- PR/task 创建或更新，且 head/body/payload metadata readback 完成。
- hosted checks pending、in progress、pass、fail，并在 fail 时完成 root-cause classification。
- 进入 `waiting-scheduler-gate`。
- blocker 需要 scheduler decision。
- 标记 goal `blocked` 前。
- 标记 goal `complete` 前。
- final scope completion。

scheduler 在改变 table state、运行 high-cost gate、恢复 blocked/complete worker、关闭 batch 或声明 Top Goal complete 前，必须读取并消费 `report_path`。scheduler 消费 report 后必须写 `report_consumed` artifact；没有 receipt 的 report 不得驱动 table transition。

## Report Locator Schema / 回报定位结构

跨线程消息、fallback notice、heartbeat prompt 和短摘要使用这个形状：

```text
report_locator:
- report_id: <worker_id-report-YYYYMMDDHHMM or equivalent>
- report_path: <orchestration_state_root>/reports/<report_id>.json
- state_root: <orchestration_state_root>
- unit_id: <issue / PR / task / N/A>
- state: <confirming | routing-missing | active | waiting-hosted | waiting-scheduler-gate | stopped_at_waiting_scheduler_gate | waiting-scheduler | waiting-on-worker | pending-materialization-stalled | worker-stalled | worker-stalled/abandoned | replacement-planned | replacement-active | scheduler-takeover-active | takeover-escalated | recovered-waiting-scheduler-gate | blocked | complete>
- head: <head_sha or N/A>
- base: <base_sha or N/A>
- next_owner: <scheduler | worker | replacement | external>
- next_action: <exact action or waiting reason>
```

Locator notice 目标 `<=4KB`。需要更多信息时读取 `report_path`，不要回读线程正文。

## Report Artifact Schema / 完整回报结构

完整 report 写入 JSON artifact，至少包含：

```text
report:
- report_id:
- report_type: instruction_ack | startup | correction_result | waiting_scheduler_gate | blocker | final | routing_missing | recovery | hosted_update | gate_readiness
- report_for_instruction_id:
- writer_role: worker
- worker_id:
- worker_thread_id:
- scheduler_thread_id:
- report_to_thread_id:
- unit_id:
- state:
- instruction_ack:
  - accepted: yes | no | N/A
  - missing_fields:
  - objective_digest:
- objective_digest:
- goal_status:
- gate_state:
- worksite:
- branch:
- head:
- base:
- merge_base:
- pr_or_task:
- issue_state:
- validation:
  - commands:
  - result:
  - summary:
  - artifact_paths:
- hosted_checks:
  - state:
  - run_ids:
  - classification:
- head_bound_artifacts_refreshed:
- gate_failure_ledger:
- invariant_checklist:
- fail_closed_matrix_coverage:
- unverifiable_invariants:
- admission_style_valid_true_path_audited:
- root_cause_correction_completed:
- blocker:
- risks:
- next_owner:
- next_scheduler_action:
- next_worker_action:
- created_at:
```

大于预算的 evidence、validation output、gate output、shell output 和 thread readback 必须写 `artifact_paths`，report 内只保留摘要、path、run_id 和结论。

## Instruction Ack / 指令确认

worker 收到任何 initial/correction/recovery/replacement prompt 后，必须先写 ACK artifact：

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
- gate_state:
- first_action:
- missing_fields: <none or list>
```

`accepted=yes` 只表示 worker 已收到并接受该指令，不表示任务完成。`accepted=no` 或 `missing_fields` 非空时，worker 状态为 `routing-missing` 或 `waiting-scheduler`，不得开始实施。

## Report Consumed Receipt / 回报消费回执

scheduler 消费 worker report 后，在 `orchestration_state_root/consumption/` 写：

```text
report_consumed:
- worker_id:
- worker_thread_id:
- report_id:
- report_path:
- report_for_instruction_id:
- report_state:
- consumed_at:
- consumed_by_thread_id:
- table_updated: yes | no
- state_file_updated:
- next_owner:
```

没有 `report_consumed` 时，不得把 worker report 当作已更新 fact table。旧 report 与新 report 冲突时，以项目事实源 + 最新已消费 report artifact 为准；旧 heartbeat summary 和 thread preview 不能覆盖。

## Scheduler Decision Request / 请求调度决策

worker 需要 scheduler 判断时，完整 blocker evidence 写入 report artifact；跨线程只发 locator notice。artifact 必须包含：

```text
scheduler_decision_needed:
- blocker:
- evidence_summary:
- evidence_artifact_paths:
- why_outside_my_scope:
- proposed_next_action:
- current_goal_status:
```

如果没有该决策就不能继续有意义推进，发送 locator notice 后 block current goal。

## Complete Before Report Is Invalid / 未回报不得完成

worker 在生成完整 report artifact 且发送 locator notice 前，不得将 goal 标记为 complete。report 至少包含：

- PR/task URL 或等价 carrier。
- head/base。
- validation commands、result、artifact paths。
- hosted checks 和 run ids。
- gate owner 和 gate status。
- issue/task state。
- final worktree status。
- remaining risks，或明确 none。

scheduler 消费该 report artifact 前，不得把 worker 视为 complete。

## Fallback / 兜底

fallback 只能输出 short notice：

```text
Scheduler Report Notice:
- report_id:
- report_path:
- state_root:
- unit_id:
- state:
- head:
- base:
- next_owner:
- next_action:
```

如果无法写入 `report_path`：

```text
Scheduler Report Notice:
- state: report-path-missing
- state_root:
- unit_id:
- blocker: report_output_path unavailable
- next_owner: scheduler
- next_action: resend instruction with writable report_output_path
```

不要输出 `<codex_delegation>` envelope。不要输出完整 `Scheduler Report:` block。不要用 `read_thread` 从 fallback 正文恢复完整状态。
