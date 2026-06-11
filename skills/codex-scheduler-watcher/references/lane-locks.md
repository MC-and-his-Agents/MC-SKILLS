# Lane Locks / 共享通道锁

## Purpose / 用途

lane lock 用于协调多个 scheduler 对共享 carrier、status、review、gate、merge 和 contract 资源的排他访问。watcher 拥有 lane lock table 和 waiting queue；scheduler 只能请求、等待、持有和释放 lane，不能自行判定共享 lane 已可用。

partial-order scheduling 决定 scheduler 是否可以启动。lane locks 决定已启动 scheduler 是否可以进入共享资源阶段。

## Lane Model / 通道模型

必须支持这些 lane：

```text
shared_fact_chain_status_lane
shadow_carrier_lane
current_item_review_lane
high_cost_gate_lane
merge_lane
contract_lane
```

默认同一 lane 排他。只有 `granted_paths`、`grant_scope` 和 release predicate 能证明不冲突时，watcher 才能做更细粒度 grant。无法证明不冲突时，保持排他。

lane entry schema：

```text
lane_lock_table:
- lane_id:
  state: lane-free | lane-granted | lane-release-pending | lane-blocked | lane-stale-owner | lane-released
  owner_scheduler_id:
  owner_unit_id:
  owner_pr:
  owner_issue_set:
  owned_paths:
  grant_time:
  last_readback_time:
  release_predicate:
  waiting_schedulers:
  allowed_non_lane_work:
  forbidden_until_grant:
```

常见映射：

- `shared_fact_chain_status_lane`：status/current、bootstrap result、progress、fact-chain 等共享事实载体。
- `shadow_carrier_lane`：shadow tree、derived carrier、跨 item 派生状态。
- `current_item_review_lane`：绑定 current item/head 的 review record、semantic review、finding disposition。
- `high_cost_gate_lane`：guardian、formal review、semantic review、release admission 等高成本共享 gate。
- `merge_lane`：merge queue、controlled merge、post-merge readback、base/head refresh。
- `contract_lane`：schema、API contract、fixture naming、metadata parser、release contract。

## State Machine / 状态机

```text
lane-free -> lane-granted -> lane-release-pending -> lane-released -> lane-free
lane-granted -> lane-stale-owner -> lane-blocked
lane-blocked -> lane-release-pending | lane-granted
```

- `lane-free`：没有 owner，可以 grant 给下一个符合条件的 scheduler。
- `lane-granted`：有明确 owner；其他 scheduler 必须进入 waiting queue 或继续 allowed non-lane work。
- `lane-release-pending`：owner 声称完成，watcher 正在验证 release predicate。
- `lane-blocked`：release predicate 失败、owner 无法推进或外部事实不一致。
- `lane-stale-owner`：owner scheduler missing/stalled，或 owner PR/head/carrier 长时间无变化。
- `lane-released`：release predicate 已通过；watcher 可授予下一个 waiting scheduler 或标记 lane-free。

## Request / Grant / Wait / Deny / Release

lane request schema：

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
```

lane grant schema：

```text
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
```

lane wait schema：

```text
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
```

lane denied schema：

```text
lane_denied:
- denial_id:
- lane_id:
- scheduler_thread_id:
- reason:
- missing_facts:
- required_correction:
- allowed_non_lane_work:
- next_owner:
```

lane release schema：

```text
lane_release:
- release_id:
- lane_id:
- owner_scheduler_id:
- owner_pr:
- release_evidence:
- release_predicate_status:
- next_waiting_scheduler:
```

## Waiting Queue / 等待队列

waiting queue 由 watcher 拥有，按 lane 维护：

```text
waiting_queue:
- lane_id:
  queued_schedulers:
  - scheduler_thread_id:
    unit_id:
    request_id:
    requested_paths:
    intended_action:
    wait_since:
    allowed_non_lane_work:
    forbidden_until_grant:
    resume_condition:
    next_readback_at:
```

队列顺序默认按 request 时间。watcher 可以根据 dependency readiness、stale owner recovery、release urgency、merge lane plan 或用户明确优先级调整顺序，但必须在 `human_summary` 解释原因。

## Release Predicate / 释放条件

PR merged 不自动释放 lane。watcher 必须验证 release predicate：

- PR merged/read back，或明确 terminalized 且有 rationale。
- scheduler final closeout/readback 已被 watcher 消费，或 watcher 有独立 terminal carrier proof。
- status/current/bootstrap/shadow 与 lane scope 对齐，如果 lane 触碰这些 carrier。
- 同一 owner 没有仍触碰该 lane 的 open PR。
- lane scope 不存在 stale review/head drift、waiting-hosted、waiting-scheduler-gate、carrier/shadow gap。
- release evidence 包含 owner scheduler、owner PR、head/base/readback、carrier proof 和验证时间。

release predicate 未通过时，lane 保持 `lane-release-pending` 或转为 `lane-blocked`，并给 waiting scheduler 返回 `lane_wait`，不是让 waiting scheduler 自行处理 owner 的 gate/merge 细节。

## Scheduler Rules / Scheduler 规则

- scheduler 可以做 implementation-only、non-shared branch refresh、metadata、readback、local validation。
- scheduler 写 shared lane path、运行 shared gate、更新 current-item-bound review 或 merge 前，必须发送 `lane_request` 并等待 watcher `lane_grant`。
- worker objective 必须继承 grant 前的 forbidden shared paths。
- scheduler lane-scoped blocker 必须回报 scheduler-level `scheduler_blocked_update` 或 `lane_request`，不要把 worker detail 直接发给 watcher。
- scheduler 完成 granted lane action 后必须回报 `lane_release` 或 release-pending report，等待 watcher 验证。

## Watcher Rules / Watcher 规则

- watcher 消费 `lane_request` 后，必须返回 `lane_grant`、`lane_wait` 或 `lane_denied`。
- watcher 不运行 gate、不 merge、不修 PR finding、不写业务代码。
- watcher 只更新 lane table、waiting queue、scheduler pool、heartbeat prompt 和 scheduler-level instructions。
- `next_owner=watcher` 时，watcher 必须执行 grant/wait/release/recovery 等真实 side effect；不能只输出下一步由 watcher 处理。

## End-to-End Example / 端到端示例

场景：

- Round 8 scheduler 持有 PR `#1433`，因为该 PR 触碰 `.loom/status/current.md` 和 `.loom/bootstrap/init-result.json`，watcher 授予 `shared_fact_chain_status_lane`。
- `#1243` replacement scheduler 已有 implementation PR `#1437`，现在想写 WI-1243 review / fact-chain。
- 这不是 “Round 8 incomplete” 阻塞；真正 blocker 是 `shared_fact_chain_status_lane` 当前由 PR `#1433` 持有。

watcher response：

```text
lane_wait:
- wait_id: shared_fact_chain_status_lane-wait-1243
- lane_id: shared_fact_chain_status_lane
- scheduler_thread_id: <scheduler for #1243>
- blocked_by_scheduler: <Round 8 scheduler>
- blocked_by_pr: #1433
- blocked_by_issue: <Round 8 issue set if any>
- resume_condition: PR #1433 merged/read back and terminal carrier proof confirms .loom/status/current.md plus .loom/bootstrap/init-result.json aligned
- allowed_non_lane_work: non-shared branch refresh, metadata readback, local validation, PR body alignment
- forbidden_until_grant: write WI-1243 fact-chain/review carrier, update shared status/current/bootstrap, run shared gate, merge
- next_readback_at: <timestamp>

human_summary:
- 当前目标状态：#1243 可继续非共享准备工作，但不能写 fact-chain/review carrier。
- lane lock / waiting queue 状态：shared_fact_chain_status_lane 由 PR #1433 持有，#1243 已进入等待队列。
- 本轮 watcher 做了什么：消费 #1243 lane_request，记录 waiting queue，并返回 lane_wait。
- 对用户/项目的影响：Round 9/10/11 不需要整体等待 Round 8；只有消费 PR #1433 持有 lane 的 scope 暂停。
- 下一步 owner 和动作：Round 8 scheduler 继续完成 PR #1433；watcher 下一次 heartbeat 读回 release predicate。
```

当 PR `#1433` merge 且 terminal carrier readback 通过：

```text
lane_release:
- release_id: shared_fact_chain_status_lane-release-1433
- lane_id: shared_fact_chain_status_lane
- owner_scheduler_id: <Round 8 scheduler>
- owner_pr: #1433
- release_evidence: merged/readback plus terminal carrier proof
- release_predicate_status: passed
- next_waiting_scheduler: <scheduler for #1243>
```

随后 watcher 可以向 `#1243` scheduler 发 `lane_grant`。
