# Scheduler Lifecycle / 调度器生命周期

## Scheduler States / 调度器状态

```text
scheduler_state:
- planned
- ready
- scheduler-instruction-sent-awaiting-ack
- scheduler-routing-missing
- scheduler-active
- scheduler-blocked
- scheduler-stalled
- scheduler-complete
- closeout-needed
- replacement-planned
- replacement-active
- retired
```

这些是 watcher table states，不是 scheduler 内部 worker states。

## Creation Rules / 创建规则

创建 scheduler 前必须有：

- unit id/title/type。
- completion predicate。
- constraints 和 forbidden scope。
- dependencies、dependency edges、downstream units、unblocked scope 和 blocked scope。
- owned paths/carriers/contracts。
- merge lane plan。
- scheduler model/reasoning policy。
- watcher thread id 和 `report_to_watcher_thread_id`。
- 唯一 `watcher_instruction_id`，格式建议 `<unit-id>-scheduler-<YYYYMMDDHHMM>`。
- `expected_scheduler_report_type` 和 `ack_deadline_or_next_wakeup_decision`。
- 要求 scheduler 读取 `$codex-thread-orchestration`。
- 要求 scheduler 创建自己的 scheduler heartbeat。

创建 scheduler 后必须 read back：

- scheduler_thread_id。
- scheduler title。
- `scheduler_ack` 或 routing-missing report。
- scheduler heartbeat id 和 target。
- scheduler startup dispatch table。
- scheduler 是否只处理 assigned unit。
- scheduler 是否只处理 watcher 授权的 unblocked scope，并排除 blocked scope。

创建请求发出后，scheduler pool 先标记 `scheduler-instruction-sent-awaiting-ack`。收到 `scheduler_ack` 前，不得标记 `scheduler-active`，不得把“thread 已创建”当成“scheduler 已理解并开始执行”。如果下一次 watcher wakeup 仍无 ACK，必须重发/修正路由、创建 replacement scheduler，或记录真实 tool/global blocker。

## Watcher-Scheduler Message Contract / 调度线程通信契约

所有需要 scheduler 行动的 initial、replacement、correction prompt 都必须包含：

```text
watcher_instruction_id:
supersedes_watcher_instruction_id: <id or N/A>
watcher_thread_id:
scheduler_thread_id: <known id or scheduler fills in scheduler_ack>
report_to_watcher_thread_id:
expected_scheduler_report_type:
ack_deadline_or_next_wakeup_decision:
```

scheduler 首次回应必须包含：

```text
scheduler_ack:
- scheduler_thread_id:
- watcher_thread_id:
- report_to_watcher_thread_id:
- watcher_instruction_id:
- accepted: yes|no
- routing_ok: yes|no
- effective_unit_id:
- first_action:
```

如果缺少 `watcher_thread_id`、`report_to_watcher_thread_id`、`watcher_instruction_id` 或 `expected_scheduler_report_type`，scheduler 必须回报 `scheduler-routing-missing`，不要创建 worker 或进入 active 调度。

## Scheduler Report Consumption / 调度回报消费

watcher 读取 scheduler report 后，必须在 watcher thread、scheduler pool 或 unit graph 中记录：

```text
watcher_report_consumed:
- watcher_thread_id:
- scheduler_thread_id:
- scheduler_report_id:
- report_for_watcher_instruction_id:
- report_state:
- consumed_at:
- pool_updated: yes|no
- unit_state_transition:
- next_owner:
```

没有 `watcher_report_consumed` 时，不得把 scheduler report 视为已经驱动 scheduler pool 或 unit state transition。若 report 缺 `scheduler_report_id` 或 `report_for_watcher_instruction_id`，watcher 可以消费 live facts，但必须标记 `report_id_missing`，并在下一条 correction 中要求 scheduler 补齐。

## Replacement Scheduler / 替换调度器

当 scheduler thread 缺失、不可读、长期无有效 heartbeat、反复 status-only、或无法恢复时，watcher 可以创建 replacement scheduler。

replacement objective 必须包含：

- abandoned scheduler thread id。
- replacement reason。
- unit id 和 completion predicate。
- dependency edges、unblocked scope、blocked scope。
- live readback facts。
- allowed scheduler scope。
- forbidden scope。
- current branch/PR/issue/repo carrier facts。
- recovery boundary：replacement scheduler 不接管其他 units。

原 scheduler 标记为 `scheduler-stalled` 或 `retired`，不得继续作为有效 scheduler 消费。

## Blocked Scheduler / 阻塞调度器

如果 scheduler 报 global blocker，watcher 不要替它解决 worker/gate 细节。watcher 只判断：

- blocker 是否属于该 unit。
- blocker 是否只阻塞 unit 的 scoped subset。
- blocker 是否需要用户决策。
- blocker 是否阻塞 downstream units。
- 是否可以启动不依赖该 blocker 的其他 scheduler。
- 是否需要把当前 unit 拆成 blocked_scope 和 unblocked_scope 后继续推进。

## Complete Scheduler / 完成调度器

scheduler 报 complete 后，watcher 必须独立 read back completion predicate。只有 scheduler final report 和 live/repo facts 对齐，unit 才能转为 complete。

完成后动作：

- 更新 unit state。
- 清理或退休 scheduler heartbeat。
- 解锁 downstream units。
- 解锁只消费该 unit completion predicate 的 blocked scope。
- 判断是否创建下一批 scheduler。
- 若需要 fan-in closeout，创建 closeout scheduler，而不是 watcher 自己 closeout。
