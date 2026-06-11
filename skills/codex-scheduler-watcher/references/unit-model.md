# Unit Model / 调度单元模型

## Coordination Unit / 调度单元

coordination unit 是 meta-scheduler watcher 管理的最小调度单元。它可以是 milestone、parent issue、issue set、pull request、PR set、release、phase、repo carrier 或用户手工目标。

推荐字段：

```text
unit:
- unit_id:
- unit_type: milestone | parent_issue | issue_set | pull_request | pull_request_set | project_view | release | phase | repo_carrier | manual_goal
- title:
- source_locator:
- upstream_source_locator:
- completion_predicate:
- scheduler_thread_id:
- scheduler_heartbeat_id:
- dependencies:
- dependency_edges:
- downstream_units:
- owned_paths:
- owned_carriers:
- shared_contracts:
- unblocked_scope:
- blocked_scope:
- required_lanes:
- merge_lane:
- closeout_required: yes|no|unknown
- state: planned | ready | scheduler-active | scheduler-blocked | scheduler-stalled | scheduler-complete | closeout-needed | complete | deferred
- next_owner:
- next_action:
- last_readback_at:
```

## Candidate Graph / 候选调度图

candidate graph 是 watcher 在创建 scheduler 前维护的候选执行面。它比 unit graph 更细，可表达同一 unit 内的 implementation-only scope、blocked lane scope 和 later convergence scope。

```text
candidate_graph:
- candidate_id:
- unit_id:
- candidate_scope:
- candidate_type: implementation_only | lane_bound | convergence | replacement | closeout
- dependency_edges:
- required_lanes:
- forbidden_shared_paths_before_grant:
- readiness_predicate:
- lane_readiness:
- scheduler_thread_id:
- state: planned | ready | scheduler-active | waiting-lane-grant | lane-granted | complete | deferred
- next_owner:
- next_action:
```

candidate pool 用于当前或下一批可启动候选：

```text
candidate_pool:
- candidate_id:
- unit_id:
- unblocked_scope:
- blocked_scope:
- implementation_only_parallel: yes|no
- expected_lane_requests:
- waiting_lane:
- scheduler_owner:
- next_readback_at:
```

## Dependency Edge Model / 依赖边模型

不要把 milestone、Round、phase 或列表顺序直接当成硬依赖。watcher 必须把依赖拆成可审计 dependency edge，按最小阻塞范围判断 readiness。

```text
dependency_edge:
- edge_id:
- from_unit:
- to_unit:
- source_locator: <issue | PR | path | contract | carrier | manual evidence>
- dependency_type: hard | soft | convergence
- dependency_scope: unit | issue | pr | path | contract | carrier
- blocks: whole_unit | scoped_subset
- blocked_scope:
- unblocked_scope:
- readiness_predicate:
- owner_unit:
- evidence_locator:
```

分类规则：

- `hard`：候选 scope 会消费尚未完成的 issue、PR、path、contract、schema、parser、carrier 或 merge/readback 事实；只阻塞消费它的 scope。
- `soft`：背景信息、inventory、调查、文档准备、低风险 fixture 分类或可后续刷新事实；默认不阻塞 scheduler 创建，但必须记录 readback/refresh 要求。
- `convergence`：release closeout、fan-in evidence、repo carrier sync、统一 review record 等后段收敛；不应前置阻塞所有 implementation scheduler，除非 completion predicate 明确要求先完成。

如果 hard dependency 只覆盖 unit 的一部分，watcher 应写明 `blocked_scope` 和 `unblocked_scope`，并只为 unblocked scope 创建或恢复 scheduler。只有无法证明 dependency type、owner、readiness predicate 或 blocked scope 时，才把整个 unit 保持串行。

默认值：

- 没有未满足 hard dependency 时，`unblocked_scope` 必须视为完整 assigned unit，`blocked_scope` 必须视为 `none`。
- 只有存在未满足 hard dependency 且它只覆盖 scoped subset 时，才需要把 `unblocked_scope` 缩小到可启动范围。
- `unblocked_scope` 缺失但 `blocked_scope` 为 `none` 或空时，不得把候选 scope 解释为空；应先按完整 assigned unit 处理，或向 watcher 回报 template gap。

## Scheduler Pool / 调度器池

watcher 维护 scheduler pool，而不是只维护单个 current scheduler。

```text
scheduler_pool:
- unit_id:
- scheduler_thread_id:
- scheduler_heartbeat_id:
- scheduler_title:
- scheduler_state:
- heartbeat_target_readback:
- current_prs:
- current_issues:
- current_base:
- owned_paths:
- owned_carriers:
- shared_contracts:
- required_lanes:
- dependencies:
- dependency_edges:
- unblocked_scope:
- blocked_scope:
- lane_state:
- merge_lane:
- last_scheduler_report:
- last_readback_at:
- next_owner:
- next_action:
```

## Shared Lane Top-Level State / 共享通道顶层状态

watcher 必须把 shared lane ownership 作为独立事实载体维护，而不是只写在 scheduler blocker 里。详细协议见 `lane-locks.md`。

```text
lane_lock_table:
<see references/lane-locks.md>

waiting_queue:
<see references/lane-locks.md>
```

## Ownership Locks / 所有权锁

创建新 scheduler 前，watcher 必须检查 ownership locks：

- branch/worktree lock：是否已有 scheduler 使用同一 branch 或 worksite。
- PR/issue lock：是否已有 scheduler 管理同一 PR/issue。
- path lock：是否会写同一批文件或目录。
- carrier lock：是否会写同一 repo truth，如 status、progress、shadow、review record。
- contract lock：是否会改同一 schema、API、fixture naming、metadata parser 或 release contract。
- merge lane lock：是否需要串行 merge/readback。

lock 不一定阻止并行，但必须有明确 owner 和冲突处理规则。无法说明 owner 时，不并行。

ownership lock 是启动前的冲突检查；lane lock 是 scheduler 运行期间进入 shared carrier/status/review/gate/merge/contract 阶段前的 grant/wait/release 协议。不要用一次性的 ownership lock 代替持久 lane lock table。

## Fact Priority / 事实优先级

watcher 决策时按以下事实优先级处理冲突：

1. live host/local readback。
2. repo carrier current files。
3. lane lock table 和 waiting queue 的 live readback。
4. newest scheduler final/blocked/active/lane report。
5. watcher-authored state。
6. older watcher heartbeat summary。

watcher 不消费 worker report 作为 unit truth。worker report 只能转发给 scheduler。
