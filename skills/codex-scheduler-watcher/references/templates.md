# Templates / 模板

## Unit Graph / 调度单元图

```text
unit_graph:
- unit_id:
  unit_type:
  title:
  source_locator:
  upstream_source_locator:
  dependencies:
  downstream_units:
  owned_paths:
  owned_carriers:
  shared_contracts:
  merge_lane:
  completion_predicate:
  state:
  scheduler_thread_id:
  scheduler_heartbeat_id:
  next_owner:
  next_action:
```

## Parallel Decision / 并行决策

```text
parallel_decision:
- candidate_units:
- dependency_status:
- ownership_isolation:
- shared_contract_status:
- gate_capacity:
- merge_lane_plan:
- heartbeat_observability:
- recovery_capacity:
- decision: start_parallel | keep_serial | defer
- reason:
```

## Provider Gap / 来源不足报告

```text
provider_gap:
- attempted_provider:
- missing_facts:
- why_completion_predicate_cannot_be_proven:
- minimum_user_input_needed:
- recommended_next_step: provide_facts | run_separate_discovery
```

## Scheduler Initial Prompt / Scheduler 初始提示

```text
你是 <project/unit> 的 scheduler thread。

必须读取并遵守 $codex-thread-orchestration。
不要创建长期 scheduler active goal，除非用户明确要求。
只处理本 coordination unit，不处理其他 unit。

unit:
- unit_id:
- unit_type:
- title:
- source_locator:
- upstream_source_locator:
- completion_predicate:

scheduler_thread_id:
watcher_thread_id:
report_to_watcher:

dependencies:
owned_paths:
owned_carriers:
shared_contracts:
merge_lane:
forbidden_scope:

first required response:
1. 读取 repo/host live facts。
2. 输出 dispatch table。
3. 创建 scheduler heartbeat，并 read back target。
4. 只创建 dependency-ready worker。
5. 所有 worker objective 必须包含 scheduler_thread_id、report_to_thread_id、instruction_id、expected_report_type。
```

## Watcher Heartbeat Prompt / Watcher 唤醒提示

```text
你是 meta-scheduler watcher。不要调度 worker，不要运行 gate，不要 merge。

watcher_goal:
- 维护 coordination unit graph。
- 维护 scheduler pool。
- 在安全并行时创建多个 scheduler。
- 在 scheduler complete/stalled/missing 时切换、替换或通知用户。

watcher_cadence_reason:

unit_graph:
<压缩 unit graph>

scheduler_pool:
<压缩 scheduler pool>

parallel_policy:
- 默认串行；证明独立后并行。
- 不使用固定 scheduler 数量上限。
- 新增 scheduler 前必须证明 isolation、capacity、observability。

misroute_policy:
- worker report 到 watcher 时，不消费，只转发给 scheduler。

next wakeup actions:
1. 读取 active scheduler reports / heartbeat targets。
2. 读取 live unit completion facts。
3. 更新 scheduler pool。
4. 判断 ready units 是否可并行启动。
5. 创建/替换/退休 scheduler，或记录 valid_wait/global_blocker。

Watcher Decision:
- watcher_decision: action_taken | valid_wait | notify_user | global_blocker | complete
- action_taken:
- valid_wait_reason:
- scheduler_pool_subject:
- global_blocker:
- notify_user:
- next_owner:
- next_action_by:
- next_decision_at:
```

## Replacement Scheduler Prompt / 替换 Scheduler 提示

```text
你是 replacement scheduler thread。

replacement_reason:
abandoned_scheduler_thread_id:
unit_id:
unit_title:

live_facts:
- issues:
- PRs:
- branch/base/head:
- repo_carrier:
- scheduler_reports:

allowed_scope:
- 恢复并完成本 unit 的 scheduler duties。
- 读取 current facts，重建 dispatch table。
- 必要时恢复 worker/gate/merge/readback。

forbidden_scope:
- 不处理其他 units。
- 不消费 watcher 误收的 worker report，除非通过 scheduler report protocol。
- 不扩展 completion predicate。

必须读取 $codex-thread-orchestration，并创建自己的 scheduler heartbeat。
```

## Watcher Readback Report / Watcher 读回报告

```text
Watcher Report:
- report_id:
- watcher_thread_id:
- unit_graph_version:
- scheduler_pool_version:
- active_schedulers:
- completed_units:
- blocked_units:
- stale_or_missing_schedulers:
- parallel_decision:
- action_taken:
- next_owner:
- next_action:
```
