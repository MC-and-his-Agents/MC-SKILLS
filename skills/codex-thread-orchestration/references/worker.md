# Worker Protocol

## Worksite Confirmation / 现场确认

第一步只读。确认并回报：

- worker id、title、objective、具体 `scheduler_thread_id`。
- `pwd`、repo root，以及当前目录是否为 assigned worker worksite。
- branch、HEAD、base branch 或等价 target。
- `git status` 和 dirty diff。
- assigned branch 和 allowed write paths。
- 适用时读取 PR/task head/body metadata 和 issue/task state。

如果当前 `cwd` 是 Codex-managed worktree 且 detached at base/main，这可能是正常初始化状态。只有 scheduler 授权时，才在 worker worksite 内切换 assigned branch。除非明确授权，绝不切换或写入 project/root main worktree。

任何 locator 缺失或不一致时，先生成 scheduler-readable report 并等待 correction。如果不一致导致无法有意义推进，且已有 goal，则将当前 goal 结束为 `blocked`。

## Goal Start / 创建 Goal

worksite confirmation 干净后，用 exact delegated objective 创建 worker goal。不要改写、扩写或重新解释 objective。

立即运行 `get_goal` 并回报：

- confirmed worksite 和 head。
- `get_goal.objective`。
- `get_goal.status`。
- `create_goal` 是否失败，或是否残留 old goal。
- 是否可以继续执行。

block、complete 或 recover goal 前读取 `goal-lifecycle.md`。

## Scope Boundaries / 范围边界

应当：

- 只执行 assigned units 和 allowed write paths。
- 只更新 assigned scope 的 PR/task metadata。
- 根据 diff 运行 local 和 targeted validation。
- retry 前先分类 hosted checks、tool failures 和 findings。
- 所有关键节点都按 reporting protocol 回报。

不得：

- 修改其他 worker 的 unit、branch、PR/task、carrier/state 或 blocker。
- 扩大 scope 修 unrelated failures。
- 弱化 policy、parser、review、head-binding、approval、merge、release 或 gate semantics。
- 除非 scheduler 明确授权当前 head，否则运行 high-cost guardian/formal review/semantic review/controlled merge/release。
- 使用 raw host commands 绕过 controlled wrappers。
- 没有 scheduler-readable final report 就标记 complete。

## Worker States / Worker 状态

使用这些 table/report states：

- `confirming`：正在确认 worksite 和 goal。
- `active`：正在执行 scoped work。
- `waiting-hosted`：等待同一 hosted run 或有界 transient retry；通常不是 goal-blocked。
- `waiting-scheduler-gate`：local validation、metadata readback、hosted checks 和 finding disposition 已干净；scheduler 必须运行或授权下一个 high-cost gate。这不是 worker blocker。
- `waiting-scheduler`：需要 scheduler decision；如果必须暂停有意义推进，则 block goal。
- `waiting-on-worker`：另一个 worker 拥有 unblock；block goal 并等待 scheduler resume。
- `blocked`：goal 已正式 blocked，或没有 scheduler/external change 就无法继续有意义推进。
- `complete`：scoped objective 已完成，且 final evidence 已回报。

这些是 scheduler table states，不总是 goal API states。goal API 只按 `goal-lifecycle.md` 使用。

## Required Reports / 必要回报

以下节点必须向 scheduler 回报：

- worksite plus goal self-check 完成。
- local validation 通过。
- PR/task 创建或更新，且 head/body/payload metadata readback 对齐。
- hosted checks pending、in progress、passing 或 failing after classification。
- transient API/transport issue 已分类且有界。
- guardian/review finding 已修复，包括 root cause、fix scope、same-class search、targeted validation、new head 和 PR body status。
- 进入 `waiting-scheduler-gate`。
- 需要 scheduler decision。
- 即将将 goal 标记为 `blocked` 或 `complete`。

如果 `gate_owner=scheduler`，正常本地完成态是 `waiting-scheduler-gate`，不是 merge 或 final complete。

## Read-Only Explorers / 只读 Explorer

环境支持时，worker 可使用只读 explorer subagent，用于 code entry discovery、implementation survey、tests/logs review、fixture/schema lookup 或 local risk review。

只读 explorer 边界：

- 不改文件、不提交、不推送、不编辑 PR/issue、不执行 merge/release/closeout。
- 不改变 scope、objective 或 gate strategy。
- 不承担独立交付责任。
- scheduler 只追踪 worker；worker 摘要 explorer findings。

下一次 milestone 回报 explorer 使用：

```text
Used read-only explorer:
- purpose:
- conclusion:
- effect on implementation/validation:
- scope changed: no
```

以下 nested agent 必须先请求 scheduler 授权：会写文件、改变 host state、拥有 implementation slice、改变 scope/gate strategy，或运行时间足以让 worker 状态不清晰。
