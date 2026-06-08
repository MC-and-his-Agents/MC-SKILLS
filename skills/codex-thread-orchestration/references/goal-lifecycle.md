# Goal Lifecycle

## API Limits / API 限制

Goal tools 只作用于当前线程。

支持：

- 在当前线程创建 goal。
- 读取当前线程 goal。
- 将当前线程 goal 结束为 `complete` 或 `blocked`。

不支持：

- 编辑 goal objective。
- 暂停 goal。
- 恢复 active goal。
- 解除 blocked goal。
- 创建或读取其他线程的 goal。
- 将 `blocked` 或 `complete` 转回 active。

## Worker Rules / Worker 规则

worker 必须在确认 worksite 后自己创建 goal。objective 必须与 delegated objective 完全一致。随后立即运行 `get_goal`，并向 scheduler 回报 objective/status。

如果 `create_goal` 因 old goal 存在而失败，回报 old goal state。若 old goal 是 `blocked` 或 `complete`，scheduler 必须发送新的 exact objective，worker 才能创建新 goal 继续。

没有 scheduler-readable final report，不得标记 goal complete。如果 `gate_owner=scheduler`，complete 通常不是本地 merge；worker 应回报 `waiting-scheduler-gate`。

## Waiting Is Not Always Blocked / 等待不总是阻塞

以下情况不要 block goal：

- hosted checks pending on the same run。
- 对 already in-progress hosted run 的有界等待。
- transient API/transport issue 的有界只读 retry。
- worker 已回报 `waiting-scheduler-gate` 后，等待 scheduler 消费该 report。

这些情况使用 table/report state，例如 `waiting-hosted` 和 `waiting-scheduler-gate`。

## When To Block / 何时 Block

以下情况在回报后 block current goal：

- worksite、branch、head、status 或 metadata 与 assignment 不一致。
- `create_goal` 或 `get_goal` 异常。
- 继续推进需要修改另一个 worker 的 scope、另一个 unit 或 main/project worktree。
- scheduler 明确要求 worker pause、wait for decision 或 wait for another worker。
- 稳定语义失败需要修改 policy、parser、review、head binding、approval、merge、release 或 gate rules。
- 有界 retry 后仍无法证明 host enforcement、branch protection、ruleset 或 required checks。
- controlled wrapper 因非 transient 原因失败。
- 唯一路径是用 raw command 绕过 wrapper policy。
- objective 不一致或不可达。

`blocked` 后，scheduler 必须用新的 exact objective 恢复，worker 必须创建新 goal。

## Recovery Prompt / 恢复 Prompt

```text
你的 previous goal 已经 blocked/complete。goal API 不能恢复或编辑它。
请用下面的 exact objective 创建新 goal：
"<new exact objective>"

创建后运行 get_goal，并回报 objective/status。不要把旧 goal 当作 active。
```

## Scheduler Implications / 对 Scheduler 的含义

scheduler 审核 worker self-reports；不能通过 goal API 直接检查 worker goal。`read_thread` 可用于 status readback，但不是 goal API。

不要要求 blocked 或 complete worker “继续”而不提供新 objective。不要因为一个 worker goal blocked 就认为 global objective blocked；先分类 blocker，并调度可行动的 owner。
