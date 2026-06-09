# Watcher Automation / 调度线程编排自动化

## Purpose / 用途

watcher automation 用于定时唤醒 meta-scheduler watcher，维护 scheduler pool 和 unit cursor。它不是 scheduler heartbeat。

watcher wakeup 只做 scheduler lifecycle 判断：

- scheduler 是否存在。
- scheduler 是否 ACK 了最新 `watcher_instruction_id`。
- scheduler heartbeat 是否挂对线程。
- scheduler 是否 active、blocked、stalled 或 complete。
- scheduler report 是否已被 watcher 消费并更新 pool。
- 是否有 unit ready 可以创建 scheduler。
- 是否需要通知用户。

## Target And Prompt Readback / 目标和提示读回

创建或更新 watcher automation 后必须 read back：

- automation id。
- target_thread_id。
- schedule。
- status。
- prompt 中的 current unit graph / scheduler pool 是否最新。

如果 watcher heartbeat 挂错线程，先修正，不继续创建 scheduler。

## Schedule / 频率选择

不要硬编码统一频率。根据 unit cadence 和 scheduler pool 风险选择：

- 低风险长期 watcher：低频。
- active scheduler pool：中频。
- scheduler replacement/recovery 期间：临时提高频率。
- 用户明确要求时按用户要求。

频率选择必须写进 watcher prompt 的 `watcher_cadence_reason`。

## Watcher Decision Contract / 编排决策契约

每次 wakeup 必须输出：

```text
Watcher Decision:
- watcher_decision: action_taken | valid_wait | notify_user | global_blocker | complete
- action_taken:
- valid_wait_reason:
- scheduler_pool_subject:
- unacked_scheduler_instructions:
- scheduler_reports_consumed:
- global_blocker:
- notify_user:
- next_owner:
- next_action_by:
- next_decision_at:
```

有效 `action_taken` 包括：

- 创建 scheduler。
- 创建 replacement scheduler。
- 更新 watcher prompt。
- 更新 scheduler pool。
- 记录 `watcher_report_consumed`。
- 转发误发 worker report 给 scheduler。
- 标记 scheduler complete/stalled/retired。
- 切换 unit cursor。

有效 `valid_wait` 必须证明至少一个 scheduler 仍在有效推进，或 watcher 正在等待明确外部事实。旧 watcher summary、未 ACK 的 scheduler instruction、未消费的 scheduler report、不可读 scheduler、无 heartbeat target readback 都不是合法等待对象。

## ACK And Report Freshness / ACK 与回报新鲜度

每次 wakeup 必须先检查：

- latest `watcher_instruction_id` 是否已有 `scheduler_ack`。
- `scheduler_ack.watcher_thread_id` 和 `report_to_watcher_thread_id` 是否等于当前 watcher thread。
- 是否存在比 watcher prompt 更新的 scheduler report。
- scheduler report 是否已记录 `watcher_report_consumed`。
- scheduler pool 是否仍引用旧 `scheduler_report_id`、旧 head/base 或旧 heartbeat target。

如果 scheduler 未 ACK，状态保持 `scheduler-instruction-sent-awaiting-ack`，本轮只能修正路由、重发指令、创建 replacement scheduler，或记录 global blocker。不得把它写成 `scheduler-active`。

如果 scheduler report 未消费，必须先记录 `watcher_report_consumed` 并更新 scheduler pool，再判断 unit state、parallel decision 或 replacement。旧 watcher prompt 不得覆盖更新的 scheduler report。

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
- live issue/PR/project/repo carrier 是否已变化。
- completion predicate 是否仍适用。

发现 prompt stale 时先更新 automation，再继续判断。不要让旧 prompt 持续创建旧 scheduler 或等待已完成 unit。
