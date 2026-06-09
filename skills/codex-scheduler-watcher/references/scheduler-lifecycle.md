# Scheduler Lifecycle / 调度器生命周期

## Scheduler States / 调度器状态

```text
scheduler_state:
- planned
- ready
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
- dependencies 和 downstream units。
- owned paths/carriers/contracts。
- merge lane plan。
- scheduler model/reasoning policy。
- watcher thread id 或 watcher report path。
- 要求 scheduler 读取 `$codex-thread-orchestration`。
- 要求 scheduler 创建自己的 scheduler heartbeat。

创建 scheduler 后必须 read back：

- scheduler_thread_id。
- scheduler title。
- scheduler heartbeat id 和 target。
- scheduler startup dispatch table。
- scheduler 是否只处理 assigned unit。

## Replacement Scheduler / 替换调度器

当 scheduler thread 缺失、不可读、长期无有效 heartbeat、反复 status-only、或无法恢复时，watcher 可以创建 replacement scheduler。

replacement objective 必须包含：

- abandoned scheduler thread id。
- replacement reason。
- unit id 和 completion predicate。
- live readback facts。
- allowed scheduler scope。
- forbidden scope。
- current branch/PR/issue/repo carrier facts。
- recovery boundary：replacement scheduler 不接管其他 units。

原 scheduler 标记为 `scheduler-stalled` 或 `retired`，不得继续作为有效 scheduler 消费。

## Blocked Scheduler / 阻塞调度器

如果 scheduler 报 global blocker，watcher 不要替它解决 worker/gate 细节。watcher 只判断：

- blocker 是否属于该 unit。
- blocker 是否需要用户决策。
- blocker 是否阻塞 downstream units。
- 是否可以启动不依赖该 blocker 的其他 scheduler。

## Complete Scheduler / 完成调度器

scheduler 报 complete 后，watcher 必须独立 read back completion predicate。只有 scheduler final report 和 live/repo facts 对齐，unit 才能转为 complete。

完成后动作：

- 更新 unit state。
- 清理或退休 scheduler heartbeat。
- 解锁 downstream units。
- 判断是否创建下一批 scheduler。
- 若需要 fan-in closeout，创建 closeout scheduler，而不是 watcher 自己 closeout。
