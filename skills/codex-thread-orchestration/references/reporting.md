# Reporting Protocol

scheduler-readable reporting 是硬要求。只在 worker thread 内写“完成了”不够，除非 scheduler 能通过 thread readback 消费。

## Delivery Priority / 投递优先级

使用当前可用的最强投递路径：

1. worker thread 可用 `send_message_to_thread` 时，发送给具体 `scheduler_thread_id`。
2. 没有跨线程发送工具时，在关键节点或 final response 输出 `<codex_delegation>` envelope。
3. 两者都不可用时，输出以 `Scheduler Report:` 开头的机器可读 block。

scheduler 必须提供具体 `scheduler_thread_id`。如果缺失，worker 在 worksite/goal self-check 后回报该缺口并等待 correction。

## Required Report Nodes / 必要回报节点

worker 必须在这些节点回报：

- worksite 和 goal self-check 完成。
- PR/task 创建或更新，且 head/body/payload metadata readback 完成。
- hosted checks pending 或 in progress。
- hosted checks pass。
- hosted checks fail，并完成 root-cause classification。
- 进入 `waiting-scheduler-gate`。
- blocker 需要 scheduler decision。
- 标记 goal `blocked` 前。
- 标记 goal `complete` 前。
- final scope completion。

scheduler 在改变 table state、运行 high-cost gate、恢复 blocked/complete worker、关闭 batch 或声明 Top Goal complete 前，必须读取并消费 report。

## Minimal Report Schema / 最小回报结构

在 `send_message_to_thread`、delegation envelope 或 fallback report 中使用这个形状：

```text
Worker: <worker_id>
Thread: <worker_thread_id>
Title: <standard title>
Unit: <issue / PR / task / N/A>
State: <active | waiting-hosted | waiting-scheduler-gate | stopped_at_waiting_scheduler_gate | waiting-scheduler | waiting-on-worker | worker-stalled | replacement-active | scheduler-controlled-takeover | recovered-waiting-scheduler-gate | blocked | complete>
Objective: <exact objective or short id>
Worksite: <path>
Branch: <branch>
Head: <head_sha>
Base: <base_sha>
Merge base: <merge_base>
PR/Task: <url or N/A>
Issue state: <state or N/A>
Validation: <commands and pass/fail summary>
Hosted checks: <pending/pass/fail with run ids if available>
hosted_failure_classification: <carrier drift | shadow drift | review stale | PR metadata drift | host stale run | code semantic failure | N/A>
head_bound_artifacts_refreshed: <yes | no | N/A>
Event: <replacement-worker-created | N/A>
Gate owner: <scheduler | worker-authorized>
Gate status: <not-ready | ready-for-scheduler | authorized | passed | failed | N/A>
Blocker: <none or classified root cause>
Next owner: <scheduler | worker | replacement | external>
Next scheduler action: <exact action needed>
Next worker action: <exact action or waiting>
Risks: <remaining risk or none>
```

## Delegation Fallback / 委派兜底

```xml
<codex_delegation>
  <source_thread_id><worker_thread_id or worker_id></source_thread_id>
  <input>
  Worker: <worker_id>
  Unit: <issue / PR / task>
  State: <active | waiting-hosted | waiting-scheduler-gate | stopped_at_waiting_scheduler_gate | worker-stalled | scheduler-controlled-takeover | recovered-waiting-scheduler-gate | blocked | complete>
  PR: <url or N/A>
  Head: <head_sha>
  Base: <base_sha>
  Validation: <commands and pass/fail summary>
  Hosted checks: <pending/pass/fail with run ids if available>
  hosted_failure_classification: <classification or N/A>
  head_bound_artifacts_refreshed: <yes/no/N/A>
  Gate owner: <scheduler | worker-authorized>
  Blocker: <none or root cause>
  Next scheduler action: <exact action needed>
  Next worker action: <exact action or waiting>
  </input>
</codex_delegation>
```

## Scheduler Decision Request / 请求调度决策

worker 需要 scheduler 判断时，回报：

```text
Scheduler decision needed:
- blocker:
- evidence:
- why outside my scope:
- proposed next action:
- current goal status:
```

如果没有该决策就不能继续有意义推进，发送 report 后 block current goal。

## Complete Before Report Is Invalid / 未回报不得完成

worker 在生成 scheduler-readable report 前，不得将 goal 标记为 complete。report 至少包含：

- PR/task URL 或等价 carrier。
- head/base。
- validation commands 和 result。
- hosted checks，以及可用的 run ids。
- gate owner 和 gate status。
- issue/task state。
- final worktree status。
- remaining risks，或明确 none。

scheduler 消费该 report 前，不得把 worker 视为 complete。
