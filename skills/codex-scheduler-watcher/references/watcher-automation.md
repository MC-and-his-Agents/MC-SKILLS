# Watcher Automation / 调度线程编排自动化

## Purpose / 用途

watcher automation 用于定时唤醒 meta-scheduler watcher，维护 scheduler pool、unit cursor、candidate pool、lane lock table 和 waiting queue。它不是 scheduler heartbeat。

watcher wakeup 只做 scheduler lifecycle 判断：

- scheduler 是否存在。
- scheduler 是否 ACK 了最新 `watcher_instruction_id`。
- scheduler heartbeat 是否挂对线程。
- scheduler 是否 active、blocked、stalled 或 complete。
- scheduler report 是否已被 watcher 消费并更新 pool。
- lane request / release / scheduler blocked update 是否已被 watcher 消费。
- lane_lock_table、waiting_queue 和 release predicates 是否最新。
- 是否有 unit ready 可以创建 scheduler。
- 是否需要通知用户。

## Target And Prompt Readback / 目标和提示读回

创建或更新 watcher automation 后必须 read back：

- automation id。
- target_thread_id。
- schedule。
- status。
- prompt 中的 current unit graph / scheduler pool / lane_lock_table / waiting_queue 是否最新。

如果 watcher heartbeat 挂错线程，先修正，不继续创建 scheduler。

## Schedule / 频率选择

不要硬编码统一频率。根据 unit cadence、scheduler pool 风险和 shared lane contention 选择：

- idle / long-running watcher：低频。
- active scheduler pool：10-15 分钟。
- active shared lane contention 或 waiting queue：5-10 分钟。
- scheduler replacement/recovery 期间：5-10 分钟。
- 用户明确要求时按用户要求。

频率选择必须写进 watcher prompt 的 `watcher_cadence_reason`。

如果 live facts、scheduler reports、lane table、waiting queue 和 release predicates 都没有变化，heartbeat 应输出 `DONT_NOTIFY`，不要打扰用户。提高 cadence 只表示需要更快读回 lane/recovery 状态，不表示可以扩容 scheduler pool。

示例：

```text
rrule = "FREQ=MINUTELY;INTERVAL=10"
watcher_cadence_reason: active scheduler pool with shared lane locks and waiting queue; 10m cadence balances lane release latency and readback cost.
```

## Watcher Decision Contract / 编排决策契约

每次 wakeup 必须输出：

```text
Watcher Decision:
- watcher_decision: action_taken | valid_wait | DONT_NOTIFY | notify_user | global_blocker | complete
- action_taken:
- valid_wait_reason:
- scheduler_pool_subject:
- scheduler_pool_readback:
- lane_lock_table_readback:
- lane_requests_consumed:
- lane_grants_issued:
- lane_waits_issued:
- lane_releases_consumed:
- waiting_queue:
- unacked_scheduler_instructions:
- scheduler_reports_consumed:
- candidate_parallel_decision:
- candidate_scheduler_created:
- awaiting_ack_recovery_decision:
- stalled_recovery_decision:
- duplicate_guard:
- capacity_decision:
- completion_predicate_readback:
- successor_unlock_decision:
- global_blocker:
- notify_user:
- next_owner:
- next_action_by:
- next_decision_at:
- human_summary:
  - 当前目标状态：
  - 当前 active schedulers：
  - lane lock / waiting queue 状态：
  - 本轮 watcher 做了什么：
  - 对用户/项目的影响：
  - 下一步 owner 和动作：
```

有效 `action_taken` 包括：

- 创建 scheduler。
- 创建 replacement scheduler。
- 更新 watcher prompt。
- 更新 scheduler pool。
- 更新 candidate pool。
- 更新 lane lock table。
- 消费 lane_request / lane_release / scheduler_blocked_update。
- 发出 lane_grant / lane_wait / lane_denied。
- 释放 lane 或将 stale owner 标记为 lane-blocked。
- 记录 `watcher_report_consumed`。
- 转发误发 worker report 给 scheduler。
- 标记 scheduler complete/stalled/retired。
- 切换 unit cursor。

有效 `valid_wait` 必须证明至少一个 scheduler 仍在有效推进，或 watcher 正在等待明确外部事实、lane owner、hosted run、release predicate readback。旧 watcher summary、未 ACK 的 scheduler instruction、未消费的 scheduler report、未消费的 lane request、不可读 scheduler、无 heartbeat target readback 都不是合法等待对象。

如果 `next_owner=watcher` 或 `next_action_by=watcher`，本轮不能只输出 summary、pool 或 next_action 后停止。watcher 必须先执行真实 side effect；无法执行时分类为 `global_blocker`、`tool_blocker`、`permission_blocker` 或 `external_wait`。

## ACK And Report Freshness / ACK 与回报新鲜度

每次 wakeup 必须先检查：

- latest `watcher_instruction_id` 是否已有 `scheduler_ack`。
- `scheduler_ack.watcher_thread_id` 和 `report_to_watcher_thread_id` 是否等于当前 watcher thread。
- 是否存在比 watcher prompt 更新的 scheduler report。
- scheduler report 是否已记录 `watcher_report_consumed`。
- 是否存在未消费的 lane_request、lane_release 或 scheduler_blocked_update。
- lane_lock_table 是否仍引用 stale owner、旧 PR head/base 或已 terminal 的 release predicate。
- scheduler pool 是否仍引用旧 `scheduler_report_id`、旧 head/base 或旧 heartbeat target。

如果 scheduler 未 ACK，状态保持 `scheduler-instruction-sent-awaiting-ack`，本轮只能修正路由、重发指令、创建 replacement scheduler，或记录 global blocker。不得把它写成 `scheduler-active`。

如果 scheduler report 或 lane-level report 未消费，必须先记录对应 consumed event，并更新 scheduler pool、lane_lock_table 或 waiting_queue，再判断 unit state、parallel decision、lane grant/release 或 replacement。旧 watcher prompt 不得覆盖更新的 scheduler/lane report。

## Misrouted Worker Reports / 误路由的 Worker 回报

如果 worker report 到达 watcher：

1. 不消费 worker report。
2. 查找对应 scheduler_thread_id 或 unit scheduler。
3. 原样转发给 scheduler。
4. 要求 scheduler 修正 worker `report_to_thread_id`。
5. watcher 只记录 routing incident，不更新 unit completion。

## Stale Prompt Rules / 过期提示规则

每次生成 watcher prompt 前检查：

- scheduler pool 是否有新 scheduler、新 heartbeat 或 retired scheduler。
- unit graph 是否有新增/完成/deferred units。
- lane_lock_table 或 waiting_queue 是否有 grant、wait、release、stale owner 或 queue 顺序变化。
- live issue/PR/project/repo carrier 是否已变化。
- completion predicate 是否仍适用。

发现 prompt stale 时先更新 automation，再继续判断。不要让旧 prompt 持续创建旧 scheduler 或等待已完成 unit。
