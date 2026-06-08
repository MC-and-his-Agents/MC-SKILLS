# Scheduler Heartbeat

用 heartbeat automation 保持 scheduler 活性，避免创建长期 scheduler goal。

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
You are the scheduler thread. Do not create a scheduler active goal.

Top Goal:
<completion criteria, including merge/readback/closeout; not only implementation done>

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
<only active / waiting-hosted / stopped_at_waiting_scheduler_gate / waiting-scheduler / waiting-on-worker / worker-stalled / replacement-planned / replacement-active / scheduler-controlled-takeover / recovered-waiting-scheduler-gate / blocked>
- worker_id:
- thread_id:
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

Planned But Not Started:
<only unstarted items and start conditions>

Completed Readback:
<merged / closed / readback facts, one compact line each>

Heartbeat Action:
1. Read worker reports / PR / issue / task / base state.
2. If a worker is waiting-scheduler-gate, scheduler runs or authorizes the exact next gate.
3. If the current batch is complete and readback is clean, create the next dependency-ready worker.
4. If a worker is blocked, classify root cause and send a precise correction or new objective.
5. If a recovery/checkpoint prompt expired with no report or no fact change, mark worker-stalled and choose replacement/takeover.
6. If this prompt is stale or target_thread_id is not scheduler_thread_id, update the automation before further scheduling.
7. Final readback issue / PR / main or equivalent target state.
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
5. worker 处于 `worker-stalled` 时，不再重复 stale readback；创建 replacement worker 或执行 scheduler controlled takeover。
6. recovery/checkpoint prompt 后仍无 report 或事实无变化时，立即升级 `worker-stalled`。
7. 所有 worker idle/blocked/waiting 且 Top Goal incomplete 时，选择最高优先级 blocker 并行动。
8. worker 必须行动时，使用 cross-thread messaging。
9. 恢复 blocked/complete worker 时，发送 new exact objective，并要求 `create_goal` + `get_goal` self-check。
10. 不要写一个看起来像 worker 已收到的 scheduler-thread reply。
