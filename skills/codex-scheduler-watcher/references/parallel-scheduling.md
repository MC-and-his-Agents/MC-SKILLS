# Parallel Scheduling / 并行调度判断

## Principle / 原则

不设置固定 scheduler 数量上限。并发量由 candidate scope readiness、hard dependency consumption、ownership isolation、gate pressure、merge lane、heartbeat observability 和 recovery capacity 决定。

核心规则：

```text
默认串行；分类 dependency edge 并证明候选 scope 可启动后并行。
不要求 unit 完全独立；未满足 hard dependency 只阻塞消费它的 scoped subset。
无法证明 dependency type、blocked scope、isolation、capacity 或 observability 时保持串行。
```

## Parallel Decision / 并行决策

每次扩容 scheduler pool 前，输出可审计判断：

```text
parallel_decision:
- candidate_units:
- candidate_scopes:
- dependency_status:
- dependency_edges:
- unblocked_scope:
- blocked_scope:
- ownership_isolation:
- shared_contract_status:
- gate_capacity:
- merge_lane_plan:
- heartbeat_observability:
- recovery_capacity:
- decision: start_parallel | keep_serial | defer
- reason:
```

## 可以启动并行的信号

可以并行创建 scheduler 的信号：

- 候选 scope 不消费未满足的 hard dependency。
- unit 仍有未满足 hard dependency 时，`blocked_scope` 与 `unblocked_scope` 已明确，且 scheduler objective 排除 blocked scope。
- 软依赖和 convergence 依赖已分类，并有后续 readback、refresh 或 fan-in plan。
- write paths、branch、PR、worktree 隔离。
- 不共享未冻结 schema、contract、metadata carrier、status/shadow truth。
- shared contract 或前置 shape owner 已 merged/readback。
- 每个 unit 有独立 completion predicate。
- 每个 scheduler 有独立 thread id 和 heartbeat id。
- hosted checks、review、merge gate 不争用同一资源。
- merge lane plan 明确，必要时允许实现并行、merge 串行。
- watcher 能在一次 heartbeat 内准确 read back 每个 active scheduler 的状态。

## 必须保持串行的信号

必须降低并发或串行的信号：

- dependency source 不清楚，无法判断 hard/soft/convergence。
- 未满足 hard dependency 覆盖整个候选 scope。
- 无法说明 blocked scope、unblocked scope、owner unit 或 readiness predicate。
- 多个 units 写同一 carrier/status/shadow/progress 文件。
- 多个 units 共享未冻结 schema、fixture naming、API contract 或 parser。
- merge 顺序会改变后续 base/head/review artifact。
- high-cost gate 已排队、频繁失败或外部服务不稳定。
- watcher heartbeat prompt 已经无法准确表达 active scheduler pool。
- 任一 scheduler 进入 `scheduler-stalled`、replacement、takeover、dirty metadata recovery。
- watcher 无法读到 scheduler thread、heartbeat target 或 final report。
- GitHub/API/CI readback 不可靠，无法证明事实优先级。

## Merge Lane / 合并通道

可以并行 implementation scheduler，但 merge/readback 可能需要串行。

merge lane plan 必须说明：

- 哪些 scheduler 可以同时实现。
- 哪些 scheduler 只允许处理 unblocked scope。
- 哪些 PR 必须按顺序 merge。
- base/main 前进后，哪些 scheduler 必须 rebase 或 refresh head-bound artifacts。
- fan-in closeout 由哪个 scheduler 执行，或是否需要新 closeout scheduler。

## Recovery Capacity / 恢复容量

并发不是只看 ready units，也看 watcher 是否能处理异常。

如果新增 scheduler 后，watcher 无法在下一次 wakeup 内完成以下动作，不要扩容：

- 读取每个 active scheduler 状态。
- 识别 missing/stalled scheduler。
- 确认 heartbeat target。
- 跟踪每个 scheduler 的 next owner。
- 在 scheduler blocked/stalled 时创建 replacement 或通知用户。
