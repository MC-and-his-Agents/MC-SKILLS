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
- downstream_units:
- owned_paths:
- shared_contracts:
- merge_lane:
- closeout_required: yes|no|unknown
- state: planned | ready | scheduler-active | scheduler-blocked | scheduler-stalled | scheduler-complete | closeout-needed | complete | deferred
- next_owner:
- next_action:
- last_readback_at:
```

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
- dependencies:
- merge_lane:
- last_scheduler_report:
- last_readback_at:
- next_owner:
- next_action:
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

## Fact Priority / 事实优先级

watcher 决策时按以下事实优先级处理冲突：

1. live host/local readback。
2. repo carrier current files。
3. newest scheduler final/blocked/active report。
4. watcher-authored state。
5. older watcher heartbeat summary。

watcher 不消费 worker report 作为 unit truth。worker report 只能转发给 scheduler。
