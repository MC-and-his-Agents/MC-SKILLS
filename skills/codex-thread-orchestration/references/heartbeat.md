# Scheduler Heartbeat

用 heartbeat automation 保持 scheduler 活性，避免创建长期 scheduler goal。

语言规则：heartbeat prompt 的自然语言默认写中文；字段名、状态枚举、命令、日志和结构化键保持英文机器可读。

## When To Use / 何时使用

scheduler 需要跨 hosted checks、gate waits、merge、dependencies 或 closeout 协调 worker 时，创建或更新 heartbeat。Top Goal 完成，或不再需要定时唤醒时，删除 heartbeat。

默认 heartbeat 间隔为 15 分钟。创建 automation 时使用等价于 `FREQ=MINUTELY;INTERVAL=15` 的 schedule；除非用户明确要求，或目标系统有更严格的时效约束，不要缩短为更高频轮询。

不要把完整 dispatch table 塞进 heartbeat。heartbeat 只保留下一次唤醒必须消费的事实；完整表保留在 scheduler thread、issue/PR comment、project carrier 或其他权威记录中。

推荐 automation 参数：

```text
kind: heartbeat
destination: thread
rrule: FREQ=MINUTELY;INTERVAL=15
status: ACTIVE
prompt: <compact heartbeat prompt>
```

创建或更新 heartbeat 后，必须 read back automation target，确认 `target_thread_id == scheduler_thread_id`。heartbeat 不得挂到 worker、watcher、retired thread 或其他非 scheduler thread；发现挂错时，立即修正或删除错误 automation，不继续调度。

## Compact Prompt Skeleton / 压缩 Prompt 骨架

```text
你是 scheduler thread。不要创建 scheduler active goal。

Top Goal:
<完成条件，必须包含 merge/readback/closeout；不能只写 implementation done>

Global Gate:
- gate_owner:
- high-cost gate owner:
- live / integration / release gate default:
- forbidden scope expansion:

Batch Plan:
- current batch:
- later batches:
- closeout conditions:

Dependency / Ownership:
- shared shape owner:
- blocker dependencies:
- downstream consumers:
- schema / contract / metadata that must not be duplicated:

Current Workers:
<only instruction-sent-awaiting-ack / routing-missing / active / waiting-hosted / stopped_at_waiting_scheduler_gate / waiting-scheduler / waiting-on-worker / pending-materialization-stalled / worker-stalled / worker-stalled/abandoned / replacement-planned / replacement-active / scheduler-takeover-active / takeover-escalated / recovered-waiting-scheduler-gate / blocked>
- worker_id:
- thread_id:
- pending_worktree_id:
- last_instruction_id:
- awaiting_ack_for:
- last_report_id:
- last_report_consumed_at:
- issue / PR / task:
- branch / worksite:
- head / base:
- merge_base:
- PR number/state/head/base:
- issue state:
- state:
- blocker:
- recovery_prompt: <sent_at / expected_report_type / target head/base / expiry decision>
- last_readback_at:
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
<只列未启动事项和启动条件>

Completed Readback:
<merged / closed / readback facts，每项一行压缩记录>

Heartbeat Action:
1. 读取 worker report / PR / issue / task / base state。
2. 如果 worker 处于 waiting-scheduler-gate，scheduler 运行或授权准确的 next gate。
3. 如果当前 batch 已完成且 readback 干净，创建下一个 dependency-ready worker。
4. 如果 worker blocked，分类 root cause，并发送精确 correction 或 new objective。
5. 如果 recovery/checkpoint prompt 已过期且没有 report 或事实变化，标记 worker-stalled 并选择 replacement/takeover。
6. 如果 pending worktree 短轮询后没有 readable thread/worksite，标记 pending-materialization-stalled 并 recreate/recover；不要等完整 heartbeat。
7. 如果 instruction-sent-awaiting-ack 到本轮仍无 ack，resend/correct routing/recover；不得标记 active。
8. 如果 prompt stale 或 target_thread_id 不是 scheduler_thread_id，先更新 automation，再继续调度。
9. 最后 readback issue / PR / main 或等价 target state。

Heartbeat Decision:
- heartbeat_decision: action_taken | valid_wait | global_blocker
- action_taken: <create_thread | send_message_to_thread | run_scheduler_gate | controlled_merge_readback | mark_worker_stalled | create_replacement_worker | update_heartbeat | none>
- valid_wait_reason: <same hosted run / active worker recent output / external bounded wait / N/A>
- effective_progress_subject: <worker thread/run/PR/head or N/A>
- global_blocker: <classification or N/A>
- next_owner:
- next_action_by:
- next_decision_at:
```

## Update Rules / 更新规则

每次 batch merge、closeout、worker retirement、major blocker classification 或 dependency unlock 后，重写 heartbeat prompt。

保留：

- active/waiting/blocked workers，通常 1-4 个。
- 每个 current worker 的 next scheduler action。
- 只有 worker 需要实际消息时，才保留 next worker action。
- recovery/checkpoint prompt 的 sent_at、expected_report_type、target head/base 和下一次 heartbeat 决策。
- 生成 heartbeat 前必须检查是否存在更新的 worker report、PR head/base/state、issue state、main merge commit/readback、repo carrier state；发现 stale 内容时先修正 prompt，不继续调度。
- shared contract/schema/metadata ownership。
- gate owner 和 forbidden scope expansion。

completed、retired、stalled-replaced worker 移入 `Completed Readback` 或 recovery readback；不要继续作为 current scheduling subjects。

heartbeat prompt 过期或挂错 target 时，先更新或删除 automation，再继续。不要让旧 prompt 持续唤醒旧 batch、旧 worker id 或已退休 thread。

## Heartbeat Action Rules / 唤醒动作规则

每次 wakeup：

1. 判断 Top Goal 是否 complete。若 complete，输出 final summary 并删除不必要 heartbeat。
2. 若 incomplete，判断是否至少有一个 worker 在有效推进。
3. worker 等待同一 hosted run 时，只记录 scheduler judgment，避免 fake messages 或不必要 reruns。
4. worker 回报 `waiting-scheduler-gate` 且 `next_owner=scheduler` 时，改为 `stopped_at_waiting_scheduler_gate`，scheduler 必须运行或授权 next gate，不再等待 worker。
5. worker 处于 `worker-stalled` 时，不再重复 stale readback；默认创建 replacement worker，只允许短程 scheduler takeover 确认现场。
6. recovery/checkpoint prompt 后仍无 report 或事实无变化时，立即升级 `worker-stalled`。
7. scheduler 处于 `scheduler-takeover-active` 且需要 commit/push/hosted checks/完整验证/语义修复时，提示 role drift，改为 `takeover-escalated` 并创建 replacement worker。
8. 创建 worker 返回 `pendingWorktreeId` 后，立即短轮询确认 thread/worksite/startup report。未物化时标记 `pending-materialization-stalled`，并重建/恢复 worker 或记录真实 tool/global blocker。
9. worker 处于 `instruction-sent-awaiting-ack` 时，下一次 heartbeat 必须读 ACK；没有 ACK 就纠正路由、重发、创建 replacement 或分类 blocker，不得称 worker active。
10. 所有 worker idle/blocked/waiting 且 Top Goal incomplete 时，选择最高优先级 blocker 并行动。
11. worker 必须行动时，使用 cross-thread messaging。
12. 恢复 blocked/complete worker 时，发送 new exact objective，并要求 `create_goal` + `get_goal` self-check。
13. 不要写一个看起来像 worker 已收到的 scheduler-thread reply。

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

有效 `action_taken` 必须是已经发生的调度 side effect：创建/恢复 worker、发送 worker 指令、运行/授权 gate、标记 stalled、创建 replacement、controlled merge/readback、修正 heartbeat target 或更新过期 heartbeat。只写“下一步要做”不算。

有效 `valid_wait` 必须证明等待对象仍在推进：active worker 最近有输出、同一 hosted run 仍在运行、外部锁/权限/队列处于有界等待。`pendingWorktreeId`、未 ACK 的 `instruction-sent-awaiting-ack`、旧 heartbeat summary、已停在 `waiting-scheduler-gate` 的 worker、`worker-stalled` worker 都不是合法等待对象。

No self-owned next action, no stop：

- `next_owner=scheduler` 或 `next_action_by=scheduler` 时，本轮必须先执行对应 scheduler side effect，再输出 Heartbeat Decision。
- 只写 `next_scheduler_action`、`next_owner=scheduler` 或“下一步由 scheduler 执行”不构成 `action_taken`。
- 当前 scheduler 自己要执行的动作不能作为 `valid_wait`；如果工具、权限、环境或外部状态阻止执行，必须分类为 blocker。

如果无法行动也无法合法等待，必须记录 `global_blocker` 和解除条件。否则该 heartbeat 是 scheduler 空转，应立即纠正。
