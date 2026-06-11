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
  dependency_edges:
  downstream_units:
  candidate_ids:
  owned_paths:
  owned_carriers:
  shared_contracts:
  required_lanes:
  unblocked_scope:
  blocked_scope:
  merge_lane:
  completion_predicate:
  state:
  scheduler_thread_id:
  scheduler_heartbeat_id:
  last_watcher_instruction_id:
  awaiting_scheduler_ack_for:
  last_scheduler_report_id:
  last_scheduler_report_consumed_at:
  next_owner:
  next_action:

candidate_graph:
- candidate_id:
  unit_id:
  candidate_scope:
  candidate_type:
  required_lanes:
  forbidden_shared_paths_before_grant:
  state:
  next_owner:
  next_action:

lane_lock_table:
<compressed lane lock table>

waiting_queue:
<compressed lane waiting queue>
```

## Parallel Decision / 并行决策

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
- lane_budget:
  - implementation_only_parallel:
  - expected_lane_requests:
  - shared_lanes_required_later:
  - forbidden_shared_paths_before_grant:
  - gate_lane_plan:
  - merge_lane_plan:
  - carrier_lane_plan:
  - contract_lane_plan:
  - recovery_capacity_impact:
- heartbeat_observability:
- recovery_capacity:
- decision: start_parallel | start_parallel_implementation_only | keep_serial | defer
- reason:

human_summary:
- 当前目标状态：
- 并行判断：
- shared lane 风险：
- 本轮 watcher 结论：
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
默认用中文解释调度判断、状态摘要、blocker 和 next action；协议字段、状态枚举、命令、日志、ID 和 sha 保持原文。

unit:
- unit_id:
- unit_type:
- title:
- source_locator:
- upstream_source_locator:
- completion_predicate:

scheduler_thread_id: <created thread id if known; otherwise fill in scheduler_ack>
watcher_thread_id:
report_to_watcher_thread_id:
watcher_instruction_id:
supersedes_watcher_instruction_id: <id or N/A>
expected_scheduler_report_type:
ack_deadline_or_next_wakeup_decision:

dependencies:
dependency_edges:
unblocked_scope: <full assigned unit unless a hard dependency blocks only a scoped subset>
blocked_scope: <none unless a hard dependency blocks a scoped subset or whole unit>
owned_paths:
owned_carriers:
shared_contracts:
required_lanes:
lane_lock_table_readback:
waiting_queue_readback:
merge_lane:
forbidden_scope:
forbidden_until_dependency_ready:
forbidden_shared_paths_before_grant:
allowed_non_lane_work:

shared_lane_policy:
- 可以在 assigned scope 内做 implementation-only / non-shared branch refresh / metadata / readback / local validation。
- 写 shared lane paths、更新 shared carrier/status/shadow/current-item-bound review、运行 shared gate 或 merge 前，必须向 watcher 发送 `lane_request` 并等待 `lane_grant`。
- worker objective 必须继承 grant 前 forbidden shared paths。
- 如果被 shared lane 阻塞，回报 scheduler-level `scheduler_blocked_update` 或 `lane_request`，不要把 worker detail 发给 watcher。
- 没有 `lane_grant` 时禁止运行 shared gate、禁止 controlled merge、禁止写 shared carrier/status/shadow/review record。

first required response:
0. 输出 `scheduler_ack`，确认 watcher/scheduler 双向 thread id 和 `watcher_instruction_id`。
1. 读取 repo/host live facts。
2. 输出 dispatch table。
3. 创建 scheduler heartbeat，并 read back target。
4. 只在 unblocked_scope 内创建 dependency-ready worker；如果 blocked_scope 为 none 或空，unblocked_scope 默认为完整 assigned unit。
5. 所有 worker objective 必须包含 scheduler_thread_id、report_to_thread_id、instruction_id、expected_report_type。
6. 不得处理 blocked_scope 或 `forbidden_until_dependency_ready`，除非 watcher 发送带新 `watcher_instruction_id` 的 correction/replacement 指令。
7. 不得处理 shared lane scope，除非 watcher 已发 `lane_grant`。

human_summary:
- 当前目标状态：
- 可立即执行的非共享工作：
- grant 前禁止事项：
- 下一步 owner 和动作：
```

## Scheduler ACK / Scheduler 确认回报

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

## Scheduler-Level Report / Scheduler 级回报

```text
Scheduler Report:
- scheduler_report_id:
- report_for_watcher_instruction_id:
- scheduler_thread_id:
- watcher_thread_id:
- unit_id:
- scheduler_state: scheduler-active | scheduler-blocked | scheduler-blocked-on-lane | scheduler-waiting-lane-grant | scheduler-lane-granted | scheduler-lane-release-pending | scheduler-stalled | scheduler-complete | closeout-needed
- current_head_or_carrier:
- completion_predicate_status:
- scheduler_heartbeat_target_readback:
- lane_request:
- lane_release:
- scheduler_blocked_update:
- action_taken:
- next_owner:
- next_action:
- human_summary:
  - 当前目标状态：
  - 当前 scheduler 状态：
  - lane 需求或释放状态：
  - 本轮 scheduler 做了什么：
  - 下一步 owner 和动作：
```

## Lane-Level Messages / Lane 级消息

```text
lane_request:
- request_id:
- scheduler_thread_id:
- watcher_thread_id:
- watcher_instruction_id:
- unit_id:
- candidate_id:
- requested_lane:
- requested_paths:
- intended_action:
- current_pr:
- current_head:
- current_base:
- dependency_readback:
- why_non_lane_work_is_insufficient:
- human_summary:
  - 请求原因：
  - 非共享工作为何不足：
  - 期望 watcher 动作：

lane_grant:
- grant_id:
- lane_id:
- scheduler_thread_id:
- unit_id:
- granted_paths:
- grant_scope:
- expires_or_recheck_at:
- release_predicate:
- forbidden_scope:
- required_report_after_action:
- human_summary:
  - 授权范围：
  - 禁止事项：
  - release 条件：
  - 下一步 owner 和动作：

lane_wait:
- wait_id:
- lane_id:
- scheduler_thread_id:
- blocked_by_scheduler:
- blocked_by_pr:
- blocked_by_issue:
- resume_condition:
- allowed_non_lane_work:
- forbidden_until_grant:
- next_readback_at:
- human_summary:
  - 等待原因：
  - 当前 lane owner：
  - 允许继续的非共享工作：
  - 下一步 owner 和动作：

lane_denied:
- denial_id:
- lane_id:
- scheduler_thread_id:
- reason:
- missing_facts:
- required_correction:
- allowed_non_lane_work:
- next_owner:
- human_summary:
  - 拒绝原因：
  - 缺失事实：
  - 允许继续的非共享工作：
  - 下一步 owner 和动作：

lane_release:
- release_id:
- lane_id:
- owner_scheduler_id:
- owner_pr:
- release_evidence:
- release_predicate_status:
- next_waiting_scheduler:
- human_summary:
  - release 证据：
  - release predicate 状态：
  - 下一个等待 scheduler：
  - 下一步 owner 和动作：
```

## Watcher Heartbeat Prompt / Watcher 唤醒提示

```text
你是 meta-scheduler watcher。不要调度 worker，不要运行 gate，不要 merge。默认用中文输出自然语言说明和 human_summary；协议字段、状态枚举、命令、日志、ID 和 sha 保持原文。

watcher_goal:
- 维护 coordination unit graph。
- 维护 scheduler pool。
- 维护 candidate graph / candidate pool。
- 维护 shared lane lock table。
- 维护 scheduler waiting queue。
- 在安全并行时创建多个 scheduler。
- 在 shared lane 争用时发出 lane_grant / lane_wait / lane_denied，并验证 lane_release。
- 在 scheduler complete/stalled/missing 时切换、替换或通知用户。

watcher_cadence_reason:

unit_graph:
<压缩 unit graph>

scheduler_pool:
<压缩 scheduler pool>

candidate_graph:
<压缩 candidate graph / candidate pool>

lane_lock_table:
<压缩 lane lock table>

waiting_queue:
<压缩 scheduler waiting queue>

release_predicates:
<压缩 release predicates>

open_pr_changed_files:
<压缩 open PR changed files for lane-relevant PRs>

communication_state:
- unacked_scheduler_instructions:
- newest_scheduler_reports:
- scheduler_reports_consumed:
- lane_requests_consumed:
- lane_grants_issued:
- lane_waits_issued:
- lane_releases_consumed:
- stale_pool_entries:

parallel_policy:
- 默认串行；分类 dependency edge 并证明候选 scope 可启动后并行。
- 不要求 unit 完全独立；未满足 hard dependency 只阻塞消费它的 scoped subset。
- 不使用固定 scheduler 数量上限。
- 新增 scheduler 前必须证明 dependency type、blocked/unblocked scope、isolation、capacity、observability。
- path isolation 只证明 implementation stage；shared carrier/status/review/gate/merge/contract 阶段必须通过 lane_grant。

shared_lane_policy:
- 没有 lane_grant，scheduler 只能做 implementation-only / non-shared branch refresh / metadata / readback / local validation。
- 没有 lane_grant，scheduler 禁止写 shared carrier/status/shadow/current-item-bound review，禁止跑 shared gate，禁止 merge。
- PR merged 不自动释放 lane；release 必须通过 watcher-owned release predicate。
- lane-scoped blocker 必须进入 waiting_queue。

misroute_policy:
- worker report 到 watcher 时，不消费，只转发给 scheduler。

next wakeup actions:
1. 读取 scheduler ACK / scheduler reports / heartbeat targets。
2. 对未消费 scheduler report 记录 `watcher_report_consumed`。
3. 读取 lane_lock_table、open PR changed files、waiting_queue 和 release_predicates。
4. 消费 lane_request / lane_release / scheduler_blocked_update，并发出 lane_grant / lane_wait / lane_denied。
5. 读取 live unit completion facts。
6. 更新 scheduler pool、candidate pool、lane table 和 waiting queue。
7. 判断 ready units/scopes 是否可并行启动。
8. 创建/替换/退休 scheduler、更新 heartbeat，或记录 valid_wait/global_blocker。
9. 如果 next_owner=watcher 或 next_action_by=watcher，先执行对应 side effect，再输出本轮结果；不能只写下一步由 watcher 执行。

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

## Replacement Scheduler Prompt / 替换 Scheduler 提示

```text
你是 replacement scheduler thread。

replacement_reason:
abandoned_scheduler_thread_id:
unit_id:
unit_title:
scheduler_thread_id: <created thread id if known; otherwise fill in scheduler_ack>
watcher_thread_id:
report_to_watcher_thread_id:
watcher_instruction_id:
supersedes_watcher_instruction_id: <id or N/A>
expected_scheduler_report_type:
ack_deadline_or_next_wakeup_decision:

live_facts:
- issues:
- PRs:
- branch/base/head:
- repo_carrier:
- scheduler_reports:
- dependency_edges:
- unblocked_scope:
- blocked_scope:
- lane_lock_table:
- waiting_queue:
- required_lanes:
- forbidden_shared_paths_before_grant:

allowed_scope:
- 恢复并完成本 unit 的 scheduler duties。
- 读取 current facts，重建 dispatch table。
- 必要时恢复 worker/gate/merge/readback。
- 只处理 watcher 授权的 unblocked_scope。
- 只在 watcher grant 的 shared lane scope 内处理 shared carrier/status/review/gate/merge。

forbidden_scope:
- 不处理其他 units。
- 不处理 blocked_scope 或未满足 hard dependency 消费范围。
- 不处理未获 lane_grant 的 shared lane scope。
- 不消费 watcher 误收的 worker report，除非通过 scheduler report protocol。
- 不扩展 completion predicate。

必须先输出 `scheduler_ack`，再读取 $codex-thread-orchestration，并创建自己的 scheduler heartbeat。lane-scoped blocker 必须回报 scheduler-level `lane_request` 或 `scheduler_blocked_update`。

human_summary:
- 当前恢复目标：
- 可执行的非共享工作：
- lane 限制：
- 下一步 owner 和动作：
```

## Watcher Readback Report / Watcher 读回报告

```text
Watcher Report:
- report_id:
- watcher_thread_id:
- unit_graph_version:
- scheduler_pool_version:
- watcher_instruction_id:
- scheduler_ack_status:
- scheduler_reports_consumed:
- lane_requests_consumed:
- lane_grants_issued:
- lane_waits_issued:
- lane_releases_consumed:
- active_schedulers:
- completed_units:
- blocked_units:
- stale_or_missing_schedulers:
- parallel_decision:
- lane_lock_table:
- waiting_queue:
- action_taken:
- next_owner:
- next_action:
- human_summary:
  - 当前目标状态：
  - 当前 active schedulers：
  - lane lock / waiting queue 状态：
  - 本轮 watcher 做了什么：
  - 对用户/项目的影响：
  - 下一步 owner 和动作：
```
