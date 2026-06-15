# Scheduler Heartbeat

用 heartbeat automation 保持 scheduler 活性，避免创建长期 scheduler goal。heartbeat 是唤醒清单，不是状态数据库。

语言规则：heartbeat prompt 的自然语言默认写中文；字段名、状态枚举、命令、日志和结构化键保持英文机器可读。

## When To Use / 何时使用

scheduler 需要跨 hosted checks、gate waits、merge、dependencies 或 closeout 协调 worker 时，创建或更新 heartbeat。Top Goal 完成，或不再需要定时唤醒时，删除 heartbeat。

默认 heartbeat 间隔为 15 分钟。创建 automation 时使用等价于 `FREQ=MINUTELY;INTERVAL=15` 的 schedule；除非用户明确要求，或目标系统有更严格的时效约束，不要缩短为更高频轮询。

不要把完整 dispatch table、worker report、thread preview、gate output 或 shell output 塞进 heartbeat。完整状态保留在 `orchestration_state_root/state/*.json`，完整 report 保留在 `orchestration_state_root/reports/*.json`，大型输出保留在 `artifacts/`。

推荐 automation 参数：

```text
kind: heartbeat
destination: thread
rrule: FREQ=MINUTELY;INTERVAL=15
status: ACTIVE
prompt: <locator-first heartbeat prompt, <=8KB>
```

创建或更新 heartbeat 后，必须 read back automation target，确认 `target_thread_id == scheduler_thread_id`。heartbeat 不得挂到 worker、watcher、retired thread 或其他非 scheduler thread；发现挂错时，立即修正或删除错误 automation，不继续调度。

## Prompt Budget / 提示预算

- `heartbeat_prompt_budget: <=8KB`
- `report_size_budget: <=4KB` for locator notice
- `cross_thread_message_budget: <=2KB`

超过预算的事实必须写入 state/report/artifact 文件，然后在 prompt 中只保留 locator。无法写入 `orchestration_state_root` 时，heartbeat 必须输出 `global_blocker` 或 `tool_blocker`，不得把完整状态临时粘进 prompt。

## Compact Prompt Skeleton / 压缩 Prompt 骨架

```text
你是 scheduler thread。不要创建 scheduler active goal。

orchestration:
- orchestration_state_root: /Users/<username>/orchestration/<project>/<round-or-unit>
- dispatch_table_path: <state_root>/state/dispatch-table.json
- recovery_index_path: <state_root>/state/recovery-index.json
- report_inbox_glob: <state_root>/reports/*.json
- consumption_path: <state_root>/consumption/
- artifact_root: <state_root>/artifacts/
- heartbeat_prompt_budget: <=8KB
- report_size_budget: <=4KB
- cross_thread_message_budget: <=2KB
- do_not_read_retired_thread_turns: true

Top Goal:
<完成条件，必须包含 merge/readback/closeout；不能只写 implementation done>

Current locators to consume:
- report_id:
  report_path:
  worker_id:
  state:
  head:
  base:
  next_owner:
  next_action:

State files to read:
- dispatch_table_path
- recovery_index_path
- relevant project truth locators: <PR/issue/repo carrier paths or URLs>

Hard forbidden actions:
- 不读取 retired/systemError/abandoned thread turns。
- 不用 list_threads/read_thread 重建状态。
- 不把完整 dispatch table、report、thread preview、gate output 或 shell output 写入 prompt 或跨线程正文。
- 没有 scheduler-owned side effect 时，不把 next_owner=scheduler 当作 valid_wait。

Heartbeat Action:
1. 读取 dispatch_table_path、recovery_index_path 和待消费 report locator。
2. 对新 report_path 写 consumption record，再更新 dispatch table。
3. 优先处理 waiting-scheduler-gate / stopped_at_waiting_scheduler_gate 的 scheduler-owned gate queue。
4. 更新 Gate Failure Ledger；如果命中 same_class_semantic_boundary_repetition，设置 gate_retry_blocked，发送 root-cause correction，不得继续 high-cost gate。
5. 如果 worker blocked，分类 root cause，并发送精确 correction、root-cause correction 或 new objective。
6. 如果当前 batch 已完成且 readback 干净，创建下一个 dependency-ready worker。
7. 如果 recovery/checkpoint prompt 已过期且没有 report locator 或事实变化，标记 worker-stalled 并选择 replacement/takeover。
8. 如果 pending worktree 短轮询后没有 readable live thread/worksite，标记 pending-materialization-stalled 并 recreate/recover；不要等完整 heartbeat。
9. 如果 instruction-sent-awaiting-ack 到本轮仍无 ack locator，resend/correct routing/recover；不得标记 active。
10. 如果 prompt stale、预算超限或 target_thread_id 不是 scheduler_thread_id，先更新 automation，再继续调度。
11. 最后 readback issue / PR / main 或等价项目事实源。

Heartbeat Decision:
- heartbeat_decision: action_taken | valid_wait | global_blocker
- action_taken: <create_thread | send_message_to_thread | run_scheduler_gate | controlled_merge_readback | mark_worker_stalled | create_replacement_worker | update_heartbeat | consume_report | none>
- valid_wait_reason: <same hosted run / active worker recent locator / external bounded wait / N/A>
- effective_progress_subject: <worker thread/run/PR/head/report_path or N/A>
- global_blocker: <classification or N/A>
- next_owner:
- next_action_by:
- next_decision_at:
```

## Update Rules / 更新规则

每次 batch merge、closeout、worker retirement、major blocker classification 或 dependency unlock 后，重写 heartbeat prompt，但只更新 locator、checklist 和预算字段。

保留：

- `orchestration_state_root` 和 state/report/artifact paths。
- 当前需要消费的 report locators，通常 1-4 个。
- 当前 scheduler-owned gate queue 的 locator。
- recovery/checkpoint prompt 的 sent_at、expected_report_type、target head/base、report_output_path 和下一次 heartbeat 决策。
- shared contract/schema/metadata ownership locator。
- gate owner 和 forbidden scope expansion。
- Gate Failure Ledger locator，尤其是同一 PR/helper/admission path 的 repeated semantic boundary failure。

completed、retired、stalled-replaced worker 移入 `dispatch-table.json` 的 terminal/recovery section；不要继续作为 current scheduling subjects。heartbeat prompt 只保留 terminal locator 或 none。

heartbeat prompt 过期、超过预算或挂错 target 时，先更新或删除 automation，再继续。不要让旧 prompt 持续唤醒旧 batch、旧 worker id 或已退休 thread。

## Heartbeat Action Rules / 唤醒动作规则

每次 wakeup：

1. 判断 Top Goal 是否 complete。若 complete，输出 final summary 并删除不必要 heartbeat。
2. 若 incomplete，读取 state files 和 report locators，判断是否至少有一个 worker 在有效推进。
3. worker 等待同一 hosted run 时，只记录 scheduler judgment 和 run locator，避免 fake messages 或不必要 reruns。
4. worker 回报 `waiting-scheduler-gate` 且 `next_owner=scheduler` 后，改为 `stopped_at_waiting_scheduler_gate`，scheduler 必须运行或授权 next gate，不再等待 worker。
5. 如果存在未消费的 scheduler-owned gate queue 或 `gate_retry_blocked`，不得对另一个 active worker 直接返回 `valid_wait`，除非明确记录合法延后原因。
6. worker 处于 `worker-stalled` 时，不再重复 stale readback；默认创建 replacement worker，只允许短程 scheduler takeover 确认现场。
7. recovery/checkpoint prompt 后仍无 report locator 或项目事实无变化时，立即升级 `worker-stalled`。
8. scheduler 处于 `scheduler-takeover-active` 且需要 commit/push/hosted checks/完整验证/语义修复时，提示 role drift，改为 `takeover-escalated` 并创建 replacement worker。
9. 创建 worker 返回 `pendingWorktreeId` 后，立即短轮询确认 live thread/worksite/startup locator。未物化时标记 `pending-materialization-stalled`，并重建/恢复 worker 或记录真实 tool/global blocker。
10. worker 处于 `instruction-sent-awaiting-ack` 时，下一次 heartbeat 必须读 ACK locator；没有 ACK 就纠正路由、重发、创建 replacement 或分类 blocker，不得称 worker active。
11. 所有 worker idle/blocked/waiting 且 Top Goal incomplete 时，选择最高优先级 blocker 并行动。
12. worker 必须行动时，使用 cross-thread messaging，但消息只包含 exact instruction、carrier fields 和 locator/budget，不包含完整历史。
13. 恢复 blocked/complete worker 时，发送 new exact objective，并要求 `create_goal` + `get_goal` self-check + report artifact。
14. 不要写一个看起来像 worker 已收到的 scheduler-thread reply。

## Turn Completion Contract / 唤醒收尾契约

Top Goal incomplete 时，heartbeat turn 的 final response 不能只是状态摘要。必须输出并满足：

```text
Heartbeat Decision:
- heartbeat_decision: action_taken | valid_wait | global_blocker
- action_taken:
- valid_wait_reason:
- effective_progress_subject:
- global_blocker:
- next_owner:
- next_action_by:
- next_decision_at:
```

有效 `action_taken` 必须是已经发生的调度 side effect：创建/恢复 worker、发送 worker 指令、运行/授权 gate、标记 stalled、创建 replacement、controlled merge/readback、消费 report artifact、修正 heartbeat target 或更新过期 heartbeat。只写“下一步要做”不算。

有效 `valid_wait` 必须证明等待对象仍在推进：active worker 最近有 report locator、同一 hosted run 仍在运行、外部锁/权限/队列处于有界等待。`pendingWorktreeId`、未 ACK 的 `instruction-sent-awaiting-ack`、旧 heartbeat summary、已停在 `waiting-scheduler-gate` 的 worker、`worker-stalled` worker 都不是合法等待对象。

No self-owned next action, no stop：

- `next_owner=scheduler` 或 `next_action_by=scheduler` 时，本轮必须先执行对应 scheduler side effect，再输出 Heartbeat Decision。
- 只写 `next_scheduler_action`、`next_owner=scheduler` 或“下一步由 scheduler 执行”不构成 `action_taken`。
- 当前 scheduler 自己要执行的动作不能作为 `valid_wait`；如果工具、权限、环境或外部状态阻止执行，必须分类为 blocker。

如果无法行动也无法合法等待，必须记录 `global_blocker` 和解除条件。否则该 heartbeat 是 scheduler 空转，应立即纠正。
