# Scheduler Protocol

## Scheduler Self-Check / 主调度自检

创建 worker 前，先写清 scheduler facts：

```text
Role: scheduler.
Top Goal: <global user objective>
Completion: <merge/readback/closeout conditions, not only implementation done>
Constraints: <scope, forbidden paths/actions, gate owner, external-action limits>
Scheduler duties: split streams, create/resume workers, maintain dispatch table, send cross-thread instructions, classify blockers, run or authorize gates, consume closeout.
```

scheduler 默认不要创建长期 active goal。除非用户明确要求 scheduler goal，或调度动作短且能闭环，否则使用 heartbeat 和 dispatch table 保持活性。

## Dispatch Table / 调度表

维护 scheduler-owned table：

```text
Top Goal:
- completion criteria:
- global constraints:

T1:
- title:
- thread_id:
- pending_worktree_id:
- last_instruction_id:
- awaiting_ack_for:
- last_report_id:
- last_report_consumed_at:
- objective:
- goal_status_reported_by_worker: unknown | active | blocked | complete
- actual_worksite:
- branch:
- units:
- issue:
- pr:
- head_sha:
- base_sha:
- merge_base:
- current_head_sha:
- PR number/state/head/base:
- issue state:
- worker_state:
- goal_status:
- gate_state:
- next_owner: scheduler | worker | replacement | external
- next_action:
- blocker_classification:
- last_readback_at:
- gate_owner: scheduler | worker-authorized
- state: planned | confirming | instruction-sent-awaiting-ack | routing-missing | pending-materialization-stalled | active | waiting-hosted | stopped_at_waiting_scheduler_gate | waiting-scheduler | waiting-on-worker | worker-stalled | worker-stalled/abandoned | replacement-planned | replacement-active | scheduler-takeover-active | takeover-escalated | recovered-waiting-scheduler-gate | blocked | complete
- blocker:
- next_worker_action:
- next_scheduler_action:
```

每次 worker report、hosted check readback、gate result、merge、blocker triage 和 closeout event 后都要更新。消费 worker report 时必须登记 `report_consumed`，包括 `report_id`、`report_state`、`consumed_at`、`table_updated` 和 `next_owner`。

事实冲突优先级：live host/local git readback > repo carrier current files > newest scheduler-authored state > newest worker report > older heartbeat summary。旧 heartbeat 不得覆盖 newer readback。

## Stream Planning / 任务流规划

创建 worker/worktree/branch 前，先登记：

```text
Streams:
- worker id:
- units:
- exact objective:
- scope:
- dependencies:
- branch name:
- branch type/prefix:
- allowed write paths:
- title:
- expected artifacts:
- expected conflict surface:
- completion condition:
- gate owner:
- initial state: planned | ready-to-start | dependency-blocked
```

首批只创建 dependency-ready stream。dependency-blocked、closeout-only、repair-only、高冲突 carrier/status/evidence stream 保持 planned，直到触发条件成立。

推荐阶段：

```text
Phase 0: Planning
- Top Goal
- stream list
- dependency graph
- branch naming
- worker titles
- exact objectives
- first batch selection

Phase 1: First Batch
- create dependency-ready branches/worktrees/workers only
- inject scheduler thread id, worker id/thread id, title, exact objective
- require worksite confirmation plus create_goal/get_goal self-check

Phase 2: Active Scheduling
- update table through heartbeat and worker reports
- create/resume the next worker only when dependencies are satisfied
- create repair streams only after blocker classification
- escalate stalled recovery to replacement worker or scheduler controlled takeover

Phase 3: Merge And Closeout
- implementation merge/readback first
- create closeout-only branch after merge readback if versioned closeout is needed
- merge closeout-only through the controlled protocol
```

## Branch And Worktree Rules / 分支与现场规则

branch prefix 建议：

- 只改 docs、spec、governance 或 skill text：优先 `docs/...`。
- 改 runtime code、generated artifacts 或 shared implementation：使用 `feat/...` 或 `fix/...`。
- 改 test fixtures、regression cases 或 baselines：使用 `test/...`，除非仓库有更强约定。
- 如果 scope 可能从 docs 扩展到 code，先冻结 scope。无法冻结时，不要使用 `docs/...`。

worker objective 必须包含 branch prefix、allowed write paths 和 forbidden paths。worker 发现 branch type 与 actual diff 不一致时，必须回报并等待 correction。

如果 thread creation tool 要求既有 branch ref，先创建或验证 ref：

```bash
git fetch origin --prune
git show-ref --verify --quiet "refs/heads/<branch-name>" || git branch "<branch-name>" <base-ref>
git rev-parse "<branch-name>"
```

不要假设 thread creation tool 会同时创建 branch 并 checkout。创建后读回 worker 真实 `cwd`；Codex-managed worktree path 才是 worker worksite，`project/root` 只是仓库身份。

detached HEAD at base/main 可以是 worktree 初始化的正常中间态。若 worker 位于自己的 Codex-managed worktree，scheduler 可明确授权它在该 worksite 内执行 `git switch <assigned-branch>` 后再创建 goal。不要要求 worker 切换 project/root main worktree。

## Worker Creation / 创建 Worker

新 worker 应收到：

- worker id，以及创建后可得的具体 `worker_thread_id`。
- 具体 `scheduler_thread_id`；不要写 "current scheduler thread"。
- 具体 `report_to_thread_id`，通常等于 `scheduler_thread_id`。
- 唯一 `instruction_id`，格式建议 `<worker-id>-<kind>-<YYYYMMDDHHMM>`；替代旧指令时填写 `supersedes_instruction_id`。
- `expected_report_type` 和 `report_deadline_or_next_heartbeat_decision`。
- 标准标题：`[<Project/Round>][T3][<unit-range>][PR#123] short task name`。
- exact objective。
- project/root 和 actual worker worksite。
- assigned branch、base、related units、allowed write paths、forbidden paths。
- gate owner 和 high-cost gate authorization status。
- 第一动作：只读 worksite check，然后 `create_goal` 和 `get_goal` self-check。

model/reasoning 默认规则：

- 复杂调度、shared contracts、跨模块 work、release/merge risk、高成本 gate、security/data/policy risk 或 repeated blockers：使用高能力模型，例如 `gpt-5.5` + `high` reasoning。
- 常规单模块 implementation、test analysis 或 local review：使用标准能力模型 + `medium` reasoning；不确定性或 blast radius 增大时升到 `high`。
- 机械 lookup、formatting、inventory 或低风险 read-only checks：使用快速低成本模型 + `low` reasoning。
- 如果环境不能显式选择 model 或 reasoning，在 dispatch table 中记录限制，并提高 review/validation 强度。

创建后立即登记 thread id 和 `instruction_id`。若有 title 工具，立即 set/rename；否则在 prompt 和 dispatch table 中保留标准标题。worker 回 `instruction_ack` 或 startup report 前，状态只能是 `instruction-sent-awaiting-ack` 或 `confirming`，不能标记为 `active`。

`pendingWorktreeId` 只表示创建请求已排队，不表示 worker 已经存在。scheduler 必须在创建后短轮询确认：

- `worker_thread_id` 可读。
- worker 真实 `cwd` / worksite 可读。
- branch/head/base 与 objective 对齐，或 worker 收到明确的 branch switch authorization。
- startup report 能回到 scheduler thread。

如果短轮询后没有 thread/worksite，或搜索 title/branch/unit 仍无法定位 worker，标记 `pending-materialization-stalled`。此时 Top Goal 未完成且没有其他有效 worker 推进时，scheduler 必须立即重建/恢复 worker，或记录真实 tool/global blocker；不得把 `pendingWorktreeId` 当作 `active`、`waiting-hosted` 或合法跨 heartbeat 等待对象。

## Tool Availability And Fallbacks / 工具可用性与兜底

优先使用专门的 thread 和 automation 工具：

- `create_thread`：创建 dependency-ready worker，并在工具支持时绑定目标 branch/worktree。
- `send_message_to_thread`：发送任何需要 worker 行动的指令。
- `read_thread`：读取 worker report 或 status summary；不要当作 goal API。
- `handoff_thread`：恢复或迁移已有 worker；不要替代新 worker 创建。
- heartbeat automation：在 hosted checks、gate waits 和 closeout 跨越时间时保持 scheduler liveness；默认间隔为 15 分钟，等价 `FREQ=MINUTELY;INTERVAL=15`。

兜底规则：

- 如果 `create_thread` 不可用，将 stream 保持为 `planned`，回报 exact worker prompt、branch、worksite requirement 和 blocker；不要假装 worker 已存在。
- 如果 branch/worktree binding 不可用，在允许时手动创建或验证 branch，然后在 prompt 中写入 worker-side worksite confirmation 和 branch switch authorization。
- 如果 `send_message_to_thread` 不可用，使用 `reporting.md` 的 fallback：要求 worker 输出 `<codex_delegation>` envelope 或 `Scheduler Report:` block，供 scheduler 通过 `read_thread` 消费。
- 如果 `read_thread` 不可用，在改变 scheduler state 前，必须要求 worker 在当前可达 channel 中显式回报。
- 如果 heartbeat automation 不可用，把 compact heartbeat prompt 当作 scheduler-local checklist，并回报 liveness limitation；不要为了轮询而创建长期 scheduler goal。
- 如果 high-cost gate tool 不可用，把失败分类为 tool/permission/environment，保持 `waiting-scheduler-gate`，再授权等价 controlled path 或回报 scheduler blocker。

## Cross-Thread Commands / 跨线程指令

worker 必须行动时，使用 `send_message_to_thread`。写在 scheduler thread 里的本地判断不是 worker 指令。

任何会改变 worker 行动的 initial/correction/recovery/replacement prompt 都必须包含：

```text
instruction_id:
supersedes_instruction_id: <id or N/A>
scheduler_thread_id:
report_to_thread_id:
expected_report_type:
report_deadline_or_next_heartbeat_decision:
```

scheduler 发送后在 table 标记 `instruction-sent-awaiting-ack`。worker 的 `instruction_ack` 或 startup/recovery report 到达前，不得把 worker 标为 `active`，不得声称该指令已被 worker 理解或执行。下一次 heartbeat 仍无 ACK 时，必须重发、纠正路由、创建 replacement，或标记为 classified tool/global blocker。

正确的 scheduler-local note：

```text
Scheduler judgment:
T2 正在等待同一个 hosted run。无需发送 worker message。
Next: 等待该 hosted run；不要 rerun。
```

正确的 worker message：

```text
T2, scheduler decision:
instruction_id: T2-correction-<timestamp>
scheduler_thread_id: <scheduler_thread_id>
report_to_thread_id: <scheduler_thread_id>
expected_report_type: correction-result
按以下边界继续 triage：
- 保持 fail-closed semantics。
- 不要弱化 stale review 或 head binding。
- 修 metadata 前先确认 payload/body/head readback。
- 如果是 transient API race，只 rerun failed lightweight gate。
```

scheduler-worker message 默认使用用户当前语言；scheduler 明确切换语言时除外。字段名、命令、日志和错误文本可保留原语言。

## Report Consumption / 回报消费

scheduler 读取 worker report 后，必须在 scheduler thread 或 fact table 记录：

```text
report_consumed:
- worker_id:
- worker_thread_id:
- report_id:
- report_for_instruction_id:
- report_state:
- consumed_at:
- table_updated: yes | no
- next_owner:
```

没有 `report_consumed` 时，不得把 worker report 视为已经驱动了 table transition。若 report 缺 `report_id` 或 `report_for_instruction_id`，scheduler 可以消费事实，但必须标记 `report_id_missing` 并在下一条 correction 中要求补齐。

## Blocker And Dependency Triage / 阻塞与依赖分类

worker block 不等于 global block。逐项分类：

- Worker scope blocker：向同一 worker 发送 precise correction 或 recovery objective。
- Another worker owns the blocker：将被阻塞 worker 标为 `waiting-on-worker`，激活或创建 owner worker，readback 后再恢复被阻塞 worker。
- Shared contract/schema/policy blocker：指定唯一 owner，禁止重复定义，下游 worker gate 在 owner artifact 上。
- Environment/tool/host transient：做有界 retry/readback；分类前不要标记 global failure。
- Gate/root-cause failure：停止高成本重试，发出 narrow root-cause correction objective。

如果所有 worker 都 idle、blocked 或 waiting，而 Top Goal 未完成，scheduler 必须介入：unblock、创建 next dependency-ready worker、授权 gate，或回报真实 global blocker。

## Scheduler Turn Completion / 调度轮次完成契约

Top Goal 未完成时，scheduler heartbeat、wakeup 或调度恢复 turn 的 final response 必须满足三选一：

- `action_taken`：已经执行真实调度动作，例如 `create_thread`、`send_message_to_thread`、标记 `worker-stalled`、创建 replacement worker、运行/授权 scheduler gate、controlled merge/readback、更新或修正 heartbeat target。
- `valid_wait`：等待对象仍有效，并记录具体 thread/run/head、最近输出或 live readback、等待原因和 `next_decision_at`。合法等待只能是 active worker 最近有输出、同一 hosted run 正在运行、外部锁/权限/队列有界等待等。
- `global_blocker`：已分类为用户决策、工具不可用、权限、环境或外部系统 blocker，并写清解除条件和下一步 owner。

无效收尾：

- 只输出 fact table、heartbeat summary 或 “no action needed”，但没有上述字段。
- `next_owner=scheduler` 时只说“下一步由 scheduler 执行”却未执行，也没有 blocker。
- `next_action_by=scheduler`、`next_scheduler_action` 或 `next_owner=scheduler` 指向当前 scheduler 可执行动作时，只总结状态或记录下一步，但没有实际 side effect。
- 没有有效 worker 推进时等待下一次 heartbeat。
- 把旧 heartbeat summary 当作最新事实，覆盖新的 worker report、host readback 或 repo carrier。

No self-owned next action, no stop：

- 如果下一步 owner 是 scheduler，本轮必须先执行对应动作，例如创建/恢复 worker、发送 correction、运行/授权 gate、controlled merge/readback、标记 stalled、创建 replacement、更新 heartbeat 或消费 closeout。
- 如果无法执行，必须分类为 `global_blocker`、`tool_blocker`、`permission_blocker` 或 `external_wait`，并写清解除条件和 next owner。
- 合法等待对象必须是 external、active worker、hosted run、另一个 owner 或有界外部锁；不得把当前 scheduler 自己的待办写成 valid_wait。

## Waiting Scheduler Gate / Scheduler 强制接管

worker 报 `waiting-scheduler-gate` 且 `next_owner=scheduler` 后，scheduler 必须：

- 在 fact table 中把 `worker_state` 改为 `stopped_at_waiting_scheduler_gate`。
- 不再把该 worker 描述为 `active`、`waiting-hosted` 或 `pending`。
- 不得继续等待 worker。
- 下一步只能是 scheduler gate、scheduler correction、scheduler controlled takeover 或 replacement worker。
- heartbeat 必须跟踪 scheduler action，不得继续询问 worker 是否完成。
- 若 blocker 为 none，本轮 scheduler 必须运行/授权 gate 或执行 controlled merge/readback；不能只输出 fact table 后停止。

## Worker Stall / Worker 卡死判定

`worker-stalled` 表示 worker 已不能作为有效推进主体。它不是普通 waiting，也不是 worker blocker，而是 scheduler recovery action queue。

任一组合稳定出现时，scheduler 必须标记 `worker-stalled`：

- 最新 worker turn 长时间 `inProgress` 且无 output item。
- scheduler 已发送 recovery/checkpoint prompt，但下一次 heartbeat 仍没有 scheduler-readable report。
- PR/task head、base、`updated_at` 连续无变化，且仍处于 dirty/draft/blocked/merge-conflict 等阻塞状态。
- worker worktree HEAD 未变化，而 base/main 已前进。
- recovery prompt 要求的 target head/base、metadata repair 或 rebase 没有任何 readback 变化。

进入 `worker-stalled` 后禁止重复空转：

- heartbeat 不得继续只重复 stale readback。
- 不得无限发送同类 recovery prompt。
- dispatch table 的 `next_scheduler_action` 必须改为 `create replacement worker` 或 `scheduler controlled takeover`。
- heartbeat prompt 必须从“继续读该 worker 状态”改成跟踪 replacement/recovery path。

## Recovery Prompt Expiry / 恢复 Prompt 过期

scheduler 发送 recovery/checkpoint prompt 时，必须在 dispatch table 或 heartbeat prompt 记录：

```text
recovery_prompt:
- sent_at:
- expected_report_type:
- target_head:
- target_base:
- target_pr_or_task:
- next_heartbeat_decision: if no report or no fact change, mark worker-stalled
```

下一次 heartbeat 如果没有收到 expected report，或 PR/worktree/base 事实没有变化，必须升级为 `worker-stalled`。只有看到新的 scheduler-readable report 或 host/worktree 事实变化，才能继续等待。

## Replacement Worker / 替换 Worker

worker-stalled 后默认恢复路径是 replacement worker，而不是 scheduler 长期 takeover。选择 replacement worker 时：

- 原 worker 标记 `worker-stalled/abandoned`，不再作为有效执行者。
- 新 worker 使用 fresh base/main、明确 branch/worksite、exact recovery objective 和 allowed write paths。
- 状态先设为 `replacement-planned`，创建并完成 worksite/goal self-check 后改为 `replacement-active`。
- 创建成功时报告 `replacement-worker-created` 事件，并登记新 thread/worksite/head/base。
- replacement objective 只覆盖恢复目标，例如 rebase、metadata repair、validation、PR body readback、push；不得扩大原 worker scope。
- replacement 完成后进入 `recovered-waiting-scheduler-gate`，由 scheduler 运行或授权 gate。
- replacement worker objective 必须包含 stalled worker id/thread、recovery reason、exact branch/worksite/base/head、allowed write paths、forbidden scope、validation requirements、`gate_owner=scheduler`、`report_to_thread_id=scheduler_thread_id`。

## Scheduler Controlled Takeover / Scheduler 受控接管

scheduler controlled takeover 只能用于短程恢复动作，默认目标是确认现场并准备 replacement worker。允许动作：

- 判断并记录 `worker-stalled`。
- 读取 PR/head/worktree/base/main 状态。
- 确认没有并发写入。
- 确认 worktree clean 且没有未处理 rebase/merge/cherry-pick。
- 修正极小的机械状态，例如明显错误的本地状态标记或只读 readback 缺口。
- 准备或创建 replacement worker。

禁止 scheduler 长期执行 worker scope：

- 大段文档或代码修改。
- 多轮 rebase 冲突处理。
- 完整 validation matrix。
- PR body 大幅重写。
- push 后等待 hosted checks。
- review finding 修复。

只有同时满足以下条件，scheduler 才能短程接管正式 worksite：

- 确认没有 worker 或外部进程正在并发写入。
- worktree clean，且没有未处理 rebase/merge/cherry-pick 状态。
- branch/head/PR 与 scheduler readback 对齐。
- takeover objective 限于一次短步骤 recovery：readback、极小机械修正、replacement worker 准备。
- 不扩大原 worker scope，不处理其他 unit，不绕过 controlled gate。

Takeover escalation threshold：

- 如果恢复动作超过一个短步骤，必须停止 takeover。
- 如果需要语义判断、产生 commit、完整验证、push、等待 hosted checks、修 review finding，必须停止 takeover。
- takeover 不能跨多个 heartbeat 延续为“scheduler 继续干活”。
- 升级后 dispatch state 设为 `takeover-escalated`，下一步必须创建 replacement worker。

接管期间 dispatch state 使用 `scheduler-takeover-active`。接管完成后，若只是短程确认/机械修正，可进入 `recovered-waiting-scheduler-gate` 或 `waiting-scheduler-gate`；一旦触发 escalation threshold，必须 `takeover-escalated -> replacement-planned`。replacement 创建后，scheduler 立即恢复 scheduler duties：更新 dispatch table、更新 heartbeat、等待 replacement report、运行 scheduler-owned gate/merge/readback、继续后续 batch scheduling。
