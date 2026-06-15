# Templates / 模板

语言规则：模板里的自然语言默认写中文；字段名、状态枚举、工具名、命令和日志保持英文机器可读。

所有模板默认遵守 `references/orchestration-carrier.md`：完整 state/report 写入 `orchestration_state_root`，跨线程只传 locator；没有可写 path 时报告 blocker，不把完整表或 report 放进线程正文。

## Common Carrier Fields / 通用载体字段

```text
orchestration_state_root: /Users/<username>/orchestration/<project>/<round-or-unit>
report_output_path: <orchestration_state_root>/reports/<report_id>.json
report_size_budget: <=4KB for report notice
heartbeat_prompt_budget: <=8KB
cross_thread_message_budget: <=2KB
do_not_read_retired_thread_turns: true
```

## Runtime State Files / 运行时状态文件

```text
state_files:
- unit_graph_path: <state_root>/state/unit-graph.json
- candidate_graph_path: <state_root>/state/candidate-graph.json
- scheduler_pool_path: <state_root>/state/scheduler-pool.json
- lane_lock_table_path: <state_root>/state/lane-lock-table.json
- waiting_queue_path: <state_root>/state/waiting-queue.json
- recovery_index_path: <state_root>/state/recovery-index.json
- report_inbox_glob: <state_root>/reports/*.json
- consumption_path: <state_root>/consumption/
- artifact_root: <state_root>/artifacts/
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
- orchestration_carrier_observability:
- recovery_capacity:
- decision: start_parallel | start_parallel_implementation_only | keep_serial | defer
- reason:
- decision_artifact_path: <state_root>/artifacts/parallel/<decision-id>.json

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

carrier:
- orchestration_state_root: /Users/<username>/orchestration/<project>/<round-or-unit>
- report_output_path: <state_root>/reports/<scheduler-id-ack-YYYYMMDDHHMM>.json
- report_size_budget: <=4KB notice; full report in artifact
- heartbeat_prompt_budget: <=8KB
- cross_thread_message_budget: <=2KB
- do_not_read_retired_thread_turns: true
- scheduler_state_path: <state_root>/state/scheduler-pool.json
- lane_lock_table_path: <state_root>/state/lane-lock-table.json
- waiting_queue_path: <state_root>/state/waiting-queue.json
- recovery_index_path: <state_root>/state/recovery-index.json

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
lane_lock_table_locator:
waiting_queue_locator:
merge_lane:
forbidden_scope:
forbidden_until_dependency_ready:
forbidden_shared_paths_before_grant:
allowed_non_lane_work:

shared_lane_policy:
- 可以在 assigned scope 内做 implementation-only / non-shared branch refresh / metadata / readback / local validation。
- 写 shared lane paths、更新 shared carrier/status/shadow/current-item-bound review、运行 shared gate 或 merge 前，必须写 lane_request report artifact，并向 watcher 发送 locator notice，等待 lane_grant。
- worker objective 必须继承 grant 前 forbidden shared paths。
- 如果被 shared lane 阻塞，回报 scheduler-level `scheduler_blocked_update` 或 `lane_request` locator，不要把 worker detail 发给 watcher。
- 没有 `lane_grant` 时禁止运行 shared gate、禁止 controlled merge、禁止写 shared carrier/status/shadow/review record。

first required response:
0. 写 `scheduler_ack` artifact 到 report_output_path，并发送 locator notice，确认 watcher/scheduler 双向 thread id 和 watcher_instruction_id。
1. 读取 repo/host live facts。
2. 在 state_root 写 dispatch table，不把完整 dispatch table 输出到线程正文。
3. 创建 scheduler heartbeat，并 read back target。
4. 只在 unblocked_scope 内创建 dependency-ready worker；如果 blocked_scope 为 none 或空，unblocked_scope 默认为完整 assigned unit。
5. 所有 worker objective 必须包含 scheduler_thread_id、report_to_thread_id、instruction_id、expected_report_type、orchestration_state_root、report_output_path、report_size_budget、do_not_read_retired_thread_turns。
6. 不得处理 blocked_scope 或 `forbidden_until_dependency_ready`，除非 watcher 发送带新 `watcher_instruction_id` 的 correction/replacement 指令。
7. 不得处理 shared lane scope，除非 watcher 已发新的 `lane_grant`。

hard_forbidden:
- 不读取 retired/systemError/abandoned thread turns。
- 不用 list_threads/read_thread 重建状态。
- 不把完整 dispatch table、lane table、thread preview、gate output 或 shell output 写进 prompt 或跨线程正文。

human_summary:
- 当前目标状态：
- 可立即执行的非共享工作：
- grant 前禁止事项：
- 下一步 owner 和动作：
```

## Scheduler ACK / Scheduler 确认回报

完整 ACK 写入 `report_output_path`，跨线程只发：

```text
Scheduler Report Notice:
- report_id:
- report_path:
- state_root:
- unit_id:
- state: scheduler_ack
- head: N/A
- base: N/A
- next_owner: watcher
- next_action: consume_ack
```

ACK artifact 必须包含：

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

完整 scheduler report 写入 `report_output_path`，跨线程只发 locator notice：

```text
Scheduler Report Notice:
- report_id:
- report_path:
- state_root:
- unit_id:
- state: <scheduler-active | scheduler-blocked | scheduler-blocked-on-lane | scheduler-waiting-lane-grant | scheduler-lane-granted | scheduler-lane-release-pending | scheduler-stalled | scheduler-complete | closeout-needed>
- head:
- base:
- next_owner:
- next_action:
```

artifact 必须包含 current_head_or_carrier、completion_predicate_status、scheduler_heartbeat_target_readback、lane_request/lane_release/scheduler_blocked_update locator、action_taken 和 human_summary。

## Lane-Level Messages / Lane 级消息

lane request/release/blocker 的完整内容写入 `report_output_path`。跨线程只发 `Scheduler Report Notice`。artifact 使用以下结构：

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

lane_release:
- release_id:
- lane_id:
- owner_scheduler_id:
- owner_pr:
- release_evidence_artifact_paths:
- release_predicate_status:
- next_waiting_scheduler:
- human_summary:
```

旧 scheduler retired/systemError/abandoned 后，其 `lane_grant` 不自动继承。replacement scheduler 必须重新发 lane_request locator，watcher 必须重新验证项目事实源、release predicate、current PR/head/base 和 waiting_queue 后 grant。

## Watcher Heartbeat Prompt / Watcher 唤醒提示

```text
你是 meta-scheduler watcher。不要调度 worker，不要运行 gate，不要 merge。默认用中文输出自然语言说明和 human_summary；协议字段、状态枚举、命令、日志、ID 和 sha 保持原文。

orchestration:
- orchestration_state_root: /Users/<username>/orchestration/<project>/<round-or-unit>
- unit_graph_path: <state_root>/state/unit-graph.json
- candidate_graph_path: <state_root>/state/candidate-graph.json
- scheduler_pool_path: <state_root>/state/scheduler-pool.json
- lane_lock_table_path: <state_root>/state/lane-lock-table.json
- waiting_queue_path: <state_root>/state/waiting-queue.json
- recovery_index_path: <state_root>/state/recovery-index.json
- report_inbox_glob: <state_root>/reports/*.json
- consumption_path: <state_root>/consumption/
- artifact_root: <state_root>/artifacts/
- heartbeat_prompt_budget: <=8KB
- report_size_budget: <=4KB
- cross_thread_message_budget: <=2KB
- do_not_read_retired_thread_turns: true

watcher_goal:
- 维护 coordination unit graph。
- 维护 scheduler pool。
- 维护 candidate graph / candidate pool。
- 维护 shared lane lock table。
- 维护 scheduler waiting queue。
- 在安全并行时创建多个 scheduler。
- 在 shared lane 争用时发出 lane_grant / lane_wait / lane_denied，并验证 lane_release。
- 在 scheduler complete/stalled/missing 时切换、替换或通知用户。

current locators to consume:
- report_id:
  report_path:
  scheduler_thread_id:
  unit_id:
  state:
  head:
  base:
  next_owner:
  next_action:

hard_forbidden:
- 不读取 retired/systemError/abandoned thread turns。
- 不用 list_threads/read_thread 重建 scheduler pool、lane table 或 unit graph。
- 不把完整 dispatch table、lane table、thread preview、gate output 或 shell output 写进 prompt 或跨线程正文。
- 不把本地 orchestration carrier 当成项目 truth；complete/lane release/merge/readback/closeout 必须由 GitHub/git/PR/issue/repo carrier/live readback 证明。

next wakeup actions:
1. 读取 state files 和待消费 scheduler ACK/report locator。
2. 对未消费 report_path 记录 `watcher_report_consumed`。
3. 读取 lane_lock_table_path、waiting_queue_path、open PR changed files 和 release_predicates。
4. 消费 lane_request / lane_release / scheduler_blocked_update artifact，并发出 lane_grant / lane_wait / lane_denied。
5. 读取 live unit completion facts。
6. 更新 scheduler pool、candidate pool、lane table 和 waiting queue state files。
7. 判断 ready units/scopes 是否可并行启动。
8. 创建/替换/退休 scheduler、更新 heartbeat，或记录 valid_wait/global_blocker。
9. 如果 next_owner=watcher 或 next_action_by=watcher，先执行对应 side effect，再输出本轮结果。

Watcher Decision:
- watcher_decision: action_taken | valid_wait | DONT_NOTIFY | notify_user | global_blocker | complete
- action_taken:
- valid_wait_reason:
- scheduler_pool_locator:
- lane_lock_table_locator:
- lane_requests_consumed:
- lane_grants_issued:
- lane_waits_issued:
- lane_releases_consumed:
- waiting_queue_locator:
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

carrier:
- orchestration_state_root: <state_root>
- report_output_path: <state_root>/reports/<replacement-scheduler-ack-YYYYMMDDHHMM>.json
- report_size_budget: <=4KB notice; full report in artifact
- heartbeat_prompt_budget: <=8KB
- cross_thread_message_budget: <=2KB
- do_not_read_retired_thread_turns: true
- recovery_index_path: <state_root>/state/recovery-index.json
- scheduler_pool_path: <state_root>/state/scheduler-pool.json
- lane_lock_table_path: <state_root>/state/lane-lock-table.json
- waiting_queue_path: <state_root>/state/waiting-queue.json

recovery_inputs:
- prior_scheduler_locator:
  - scheduler_thread_id:
  - last_report_id:
  - last_report_path:
- live_facts:
  - issues:
  - PRs:
  - branch/base/head:
  - repo_carrier:
- dependency_edges:
- unblocked_scope:
- blocked_scope:
- required_lanes:
- forbidden_shared_paths_before_grant:

allowed_scope:
- 恢复并完成本 unit 的 scheduler duties。
- 读取 current facts，重建 dispatch table artifact。
- 必要时恢复 worker/gate/merge/readback。
- 只处理 watcher 授权的 unblocked_scope。
- 只在 watcher 重新 grant 的 shared lane scope 内处理 shared carrier/status/review/gate/merge。

forbidden_scope:
- 不处理其他 units。
- 不处理 blocked_scope 或未满足 hard dependency 消费范围。
- 不处理未获新 lane_grant 的 shared lane scope。
- 不读取 abandoned/retired/systemError thread turns。
- 不消费 watcher 误收的 worker report 正文；只能处理 locator。
- 不扩展 completion predicate。

必须先写 `scheduler_ack` artifact 并发送 locator notice，再读取 $codex-thread-orchestration，并创建自己的 scheduler heartbeat。lane-scoped blocker 必须回报 scheduler-level `lane_request` 或 `scheduler_blocked_update` locator。

human_summary:
- 当前恢复目标：
- 可执行的非共享工作：
- lane 限制：
- 下一步 owner 和动作：
```

## Watcher Readback Report / Watcher 读回报告

完整 watcher readback 写入 `report_output_path` 或 `artifacts/`，用户/跨线程摘要只传：

```text
Watcher Report Notice:
- report_id:
- report_path:
- state_root:
- unit_graph_version:
- scheduler_pool_version:
- watcher_instruction_id:
- scheduler_ack_status:
- active_schedulers:
- completed_units:
- blocked_units:
- stale_or_missing_schedulers:
- action_taken:
- next_owner:
- next_action:
- human_summary:
```
