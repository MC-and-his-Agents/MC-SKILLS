# Templates

语言规则：模板里的自然语言默认写中文；字段名、状态枚举、工具名、命令和日志保持英文机器可读。复制模板时不要把整段回报改成英文。

所有模板默认遵守 `references/orchestration-carrier.md`：完整 report 写 `report_output_path`，跨线程只发 locator notice；没有可写 report path 时输出 blocker，不把完整 report 粘进线程正文。

## Common Carrier Fields / 通用载体字段

```text
orchestration_state_root: /Users/<username>/orchestration/<project>/<round-or-unit>
report_output_path: <orchestration_state_root>/reports/<report_id>.json
report_size_budget: <=4KB for report notice
cross_thread_message_budget: <=2KB
do_not_read_retired_thread_turns: true
```

## Worker Initial Prompt / Worker 初始 Prompt

```text
Worker 身份:
- worker id: <Tn>
- worker_thread_id: <worker-thread-id if known>
- scheduler_thread_id: <concrete scheduler thread id>
- report_to_thread_id: <scheduler_thread_id>
- instruction_id: <Tn-initial-YYYYMMDDHHMM>
- supersedes_instruction_id: N/A
- expected_report_type: instruction_ack_then_startup_report
- orchestration_state_root: /Users/<username>/orchestration/<project>/<round-or-unit>
- report_output_path: <state_root>/reports/<worker-id-ack-YYYYMMDDHHMM>.json
- report_size_budget: <=4KB notice; full report in artifact
- cross_thread_message_budget: <=2KB
- do_not_read_retired_thread_turns: true
- report_deadline_or_next_heartbeat_decision: <if no ack locator/report by next heartbeat, treat as instruction unacknowledged>
- title: [<Project/Round>][<Tn>][<units>][<PR/Task>] <short task>
- model/reasoning: <default gpt-5.5 + high for complex/high-risk/shared-contract/gate work; lower only for low-risk read-only or mechanical work>

目标:
"<exact objective>"

分配现场:
- project/root: <project-root for repository identity only>
- worker worksite: <actual worker cwd, or ask worker to read back cwd first>
- assigned branch: <branch>
- base: <base branch/ref>
- related units: <PRs/issues/tasks>
- allowed write paths:
- forbidden paths/actions:
- gate_owner: scheduler | worker-authorized

第一步:
只读确认 worksite、branch、HEAD、base、status、PR/task metadata 和 issue/task state。如果 Codex-managed worker worksite 处于 detached at base/main，这可能是正常初始化状态；只有本 prompt 明确授权时，才在 worker worksite 内切换到 assigned branch。

如果 worksite 一致，用上面的 exact objective 创建 goal，立即运行 get_goal，把完整 instruction_ack/startup report 写入 report_output_path，并只向 scheduler_thread_id 发送 locator notice。

禁止:
- 不写入 project/root main worktree。
- 不扩大 scope。
- 不读取 retired/systemError/abandoned thread turns。
- 不把完整 validation、gate output、shell output 或 report 粘进线程正文。
- 除非 scheduler 针对当前 head 明确授权，不运行 guardian/formal review/controlled merge/closeout。
```

## Scheduler Correction Prompt / Scheduler 纠偏 Prompt

```text
<Worker id>, scheduler decision:
instruction_id: <worker-id-correction-YYYYMMDDHHMM>
supersedes_instruction_id: <prior instruction id or N/A>
scheduler_thread_id: <scheduler thread id>
report_to_thread_id: <scheduler_thread_id>
expected_report_type: instruction_ack_then_correction_result
orchestration_state_root: <state_root>
report_output_path: <state_root>/reports/<worker-id-correction-result-YYYYMMDDHHMM>.json
report_size_budget: <=4KB notice; full report in artifact
cross_thread_message_budget: <=2KB
do_not_read_retired_thread_turns: true
report_deadline_or_next_heartbeat_decision: <if no ack locator/report by next heartbeat, mark instruction unacknowledged and recover>
Current state locator:
- report_id:
- report_path:
- head:
- base:

纠偏目标/边界:
- <specific correction>

执行:
- <allowed actions>

禁止:
- <forbidden actions>
- 不读取 retired/systemError/abandoned thread turns。
- 不把完整 report/log/output 放进跨线程正文。

回报:
- 写完整 report 到 report_output_path。
- 只发送 Scheduler Report Notice，包括 report_id/report_path/state_root/unit_id/state/head/base/next_owner/next_action。
```

## Root-Cause Correction Prompt / 根因纠偏 Prompt

```text
<Worker id>, scheduler root-cause correction:
instruction_id: <worker-id-root-cause-YYYYMMDDHHMM>
supersedes_instruction_id: <prior instruction id or N/A>
scheduler_thread_id: <scheduler thread id>
report_to_thread_id: <scheduler_thread_id>
expected_report_type: instruction_ack_then_root_cause_correction_result
orchestration_state_root: <state_root>
report_output_path: <state_root>/reports/<worker-id-root-cause-result-YYYYMMDDHHMM>.json
report_size_budget: <=4KB notice; full report in artifact
cross_thread_message_budget: <=2KB
do_not_read_retired_thread_turns: true
report_deadline_or_next_heartbeat_decision: <if no ack locator/report by next heartbeat, mark instruction unacknowledged and recover>

trigger: <same_class_semantic_boundary_repetition | metadata_repetition | hosted_check_repetition | tool_flake_repetition>
repeated_subject: <PR/helper/admission path>
repeated_findings_artifact_path: <state_root>/artifacts/<gate-id>/findings.json
admission_path:
- <valid=true / admission-style / closeout boundary path or N/A>

required_invariant_checklist:
- evidence contract proven before valid=true/admission
- fail-closed behavior before positive admission
- route/provider binding proves source and freshness
- redaction/freshness/provenance/ref locator requirements covered
- provider evidence shape / evidence_class / closeout_plan gaps audited

required_fail_closed_matrix:
- positive paths:
- negative cases:
- gaps:

same_class_audit_surfaces:
- admission helpers:
- route/provider binding:
- evidence shape:
- readiness/freshness:
- redaction/provenance/ref locators:
- closeout carrier/status/review surfaces:

rules:
- no narrow latest-finding patching only.
- unverifiable_invariants_must_report_blocker: yes
- no_guardian_until_scheduler_consumes_root_cause_report: yes
- full evidence goes to artifact paths; cross-thread notice stays locator-only.

回报:
- 写完整 root-cause report 到 report_output_path。
- 只发送 locator notice。
```

## Recovery Prompt For Blocked/Complete Goal / 恢复 Prompt

```text
instruction_id: <worker-id-recovery-YYYYMMDDHHMM>
supersedes_instruction_id: <prior instruction id or N/A>
scheduler_thread_id: <scheduler thread id>
report_to_thread_id: <scheduler_thread_id>
expected_report_type: instruction_ack_then_new_goal_report
orchestration_state_root: <state_root>
report_output_path: <state_root>/reports/<worker-id-recovery-report-YYYYMMDDHHMM>.json
report_size_budget: <=4KB notice; full report in artifact
cross_thread_message_budget: <=2KB
do_not_read_retired_thread_turns: true
report_deadline_or_next_heartbeat_decision: <if no ack locator/report by next heartbeat, mark worker-stalled or create replacement>

你的 previous goal 已经 blocked/complete。goal API 不能恢复或编辑它。
请用下面的 exact objective 创建新 goal：
"<new exact objective>"

创建后运行 get_goal，把 objective/status 写入 report_output_path，并只向 report_to_thread_id 发送 locator notice。不要把旧 goal 当作 active。
```

## Recovery Checkpoint Record / 恢复检查点记录

```text
recovery_prompt:
- worker_id:
- thread_id:
- instruction_id:
- supersedes_instruction_id:
- sent_at:
- expected_report_type:
- report_output_path:
- recovery_index_path: <state_root>/state/recovery-index.json
- target_head:
- target_base:
- target_pr_or_task:
- next_heartbeat_decision: if no report locator or no fact change, mark worker-stalled
```

## Replacement Worker Prompt / 替换 Worker Prompt

```text
Worker 身份:
- worker id: <replacement id>
- replaces worker id/thread_id: <stalled worker>
- scheduler_thread_id: <scheduler thread id>
- report_to_thread_id: <scheduler_thread_id>
- instruction_id: <replacement-id-recovery-YYYYMMDDHHMM>
- supersedes_instruction_id: <stalled worker instruction id or N/A>
- expected_report_type: instruction_ack_then_recovered_waiting_scheduler_gate
- orchestration_state_root: <state_root>
- report_output_path: <state_root>/reports/<replacement-id-recovery-report-YYYYMMDDHHMM>.json
- report_size_budget: <=4KB notice; full report in artifact
- cross_thread_message_budget: <=2KB
- do_not_read_retired_thread_turns: true
- report_deadline_or_next_heartbeat_decision: <if no ack locator/report by next heartbeat, classify replacement startup failure>
- title: [<Project/Round>][<replacement id>][Recovery][<PR/Task>] <short task>

目标:
"<exact recovery objective: rebase / metadata repair / validation / PR body readback / push only>"

恢复上下文:
- stalled_worker_id:
- stalled_worker_thread_id:
- recovery_reason:
- recovery_index_path: <state_root>/state/recovery-index.json
- prior_report_locator:
  - report_id:
  - report_path:
- branch:
- worksite:
- base:
- head:

边界:
- state starts as replacement-planned, then replacement-active after worksite + goal self-check
- allowed write paths:
- forbidden: expand original scope, run guardian/formal review/controlled merge, modify unrelated units, read abandoned/retired/systemError thread turns
- validation requirements:
- gate_owner: scheduler

恢复完成、head/base/body 已 read back 且 hosted checks green 后，写完整 report 到 report_output_path，并发送 `recovered-waiting-scheduler-gate` locator notice。
```

## Report Notice / Locator 回报

```text
Scheduler Report Notice:
- report_id:
- report_path:
- state_root:
- unit_id:
- state:
- head:
- base:
- next_owner:
- next_action:
```

## Report Consumed Receipt / 回报消费回执

```text
report_consumed:
- worker_id:
- worker_thread_id:
- report_id:
- report_path:
- report_for_instruction_id:
- report_state:
- consumed_at:
- consumed_by_thread_id:
- state_file_updated:
- table_updated: yes | no
- next_owner:
```

## Routing Missing Report / 路由缺失回报

```text
Scheduler Report Notice:
- report_id:
- report_path:
- state_root:
- unit_id:
- state: routing-missing
- head: N/A
- base: N/A
- next_owner: scheduler
- next_action: resend correction with scheduler_thread_id, report_to_thread_id, instruction_id, expected_report_type, orchestration_state_root, report_output_path, report_size_budget, do_not_read_retired_thread_turns
```

如果 `report_output_path` 不可写：

```text
Scheduler Report Notice:
- state: report-path-missing
- state_root:
- unit_id:
- next_owner: scheduler
- next_action: resend instruction with writable report_output_path
```

## Waiting Scheduler Gate Report / 等待调度 Gate 回报

完整等待 gate report 写入 `report_output_path`。跨线程只发送：

```text
Scheduler Report Notice:
- report_id: <worker-id-waiting-gate-YYYYMMDDHHMM>
- report_path: <state_root>/reports/<report_id>.json
- state_root:
- unit_id:
- state: waiting-scheduler-gate
- head: <current_head_sha>
- base: <base_sha>
- next_owner: scheduler
- next_action: <run guardian / formal review / controlled merge / post-merge readback>
```

report artifact 必须包含 worksite、branch、PR/task、scope diff、local validation、hosted checks、metadata readback、finding disposition、Gate Failure Ledger、invariant checklist、remaining risks 和 artifact paths。

## Heartbeat Prompt Skeleton / Heartbeat Prompt 骨架

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
<completion criteria，必须包含 merge/readback/closeout>

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
- relevant project truth locators

Hard forbidden actions:
- 不读取 retired/systemError/abandoned thread turns。
- 不用 list_threads/read_thread 重建状态。
- 不把完整 dispatch table、report、thread preview、gate output 或 shell output 写入 prompt 或跨线程正文。

Heartbeat Action:
1. 读取 state files 和待消费 report locator。
2. 对新 report_path 写 consumption record，再更新 dispatch table。
3. 处理 waiting-scheduler-gate / stopped_at_waiting_scheduler_gate 的 scheduler-owned gate queue。
4. 若 recovery/checkpoint prompt 已过期且没有 report locator 或事实变化，标记 worker-stalled 并选择 replacement/takeover。
5. 如果 next_owner=scheduler 或 next_action_by=scheduler，先执行对应 side effect；不能只写下一步由 scheduler 执行。

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
