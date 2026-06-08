---
name: codex-thread-orchestration
description: Codex 线程编排的 scheduler 与 worker 协作协议。用于 Codex 作为 scheduler 拆分全局目标、创建或恢复 worker、管理 branch/worktree、发送跨线程指令、运行 gate、完成 closeout；也用于 Codex 作为 worker 确认分配现场、创建并自检 scoped goal、只执行指定 scope、回报 scheduler-readable 关键节点，并等待 scheduler-owned gate。默认使用中文说明和回报，可根据用户语言适配；协议字段、状态枚举、工具名和结构化模板字段保持机器可读。
---

# Codex 线程编排

## Overview

本 skill 是 scheduler thread 与 worker thread 共享的协作协议。

scheduler 拥有全局目标：拆分 stream、创建 worker、管理依赖顺序、决定 gate owner、执行 merge/readback，并消费 closeout。worker 拥有局部执行：确认分配的 worksite，创建自己的 goal，只做指定 scope 内的工作，完成验证，并用 scheduler-readable 形式回报关键节点。

本协议与具体项目无关。PR、issue、Work Item、release、review、closeout 等词，均表示当前仓库或宿主系统中的等价事实载体。

默认语言：中文。用户使用其他语言，或 scheduler 明确要求切换语言时，面向用户和跨线程沟通应适配用户语言。协议字段、状态枚举、工具名、命令、日志、错误文本、XML/YAML/JSON 模板字段可保留英文，以保证机器可读和跨线程稳定。

## Role Detection / 角色自检

先判断当前线程角色：

- Scheduler：用户要求你协调多个 worker、branch、PR、issue、release gate、merge readiness 或 closeout。
- Worker：你收到被委派的 objective、thread/worksite/branch 标识，或被要求向 scheduler 回报。
- Mixed/unclear：只有 prompt 中同时包含具体 scoped objective 和 scheduler 身份时，才默认当 worker；否则先当 scheduler，创建 worker 前先完成调度计划。

不要让 worker 从零推断全局计划。不要让 scheduler 把只写在 scheduler thread 里的话伪装成 worker 已收到的指令。

## Worker Quick Start

1. 读取 `references/worker.md` 和 `references/reporting.md`。
2. 确认分配的 `scheduler_thread_id`、worker id/title、objective、branch 和 worksite。
3. 只读检查 `pwd`、repo root、branch、HEAD、base、status、PR/task metadata，以及适用的 issue/task state。
4. worksite 一致后，在 worker thread 中用原样 delegated objective 创建 goal，立即运行 `get_goal`，并回报 objective/status。
5. 只执行分配 scope。关键节点必须向 scheduler 回报。
6. 如果 `gate_owner=scheduler`，本地验证、metadata readback、hosted checks、finding disposition 全部干净后，停在 `waiting-scheduler-gate`。除非 scheduler 明确授权当前 head，否则不要运行 guardian、formal review、controlled merge 或 closeout。

## Scheduler Quick Start

1. 读取 `references/scheduler.md`、`references/reporting.md` 和 `references/heartbeat.md`。
2. 定义 Top Goal、completion criteria、constraints、streams、dependencies、branch names、allowed write paths、expected artifacts、gate owner 和 first batch。
3. 只创建 dependency-ready worker。使用需要既有 branch 的 thread 创建工具前，先创建或验证 branch ref。
4. 登记 Scheduler Fact Table：worker/worksite/branch/head/base/PR/issue/state/owner/action/blocker/readback。
5. worker 需要行动时，使用跨线程消息。用压缩 heartbeat 保持 scheduler liveness，并确认 heartbeat target 是 scheduler thread。
6. recovery/checkpoint prompt 后，下一次 heartbeat 若无 scheduler-readable report 且 PR/worktree/base 事实无变化，升级为 `worker-stalled`。
7. 默认由 scheduler 拥有高成本 gate：guardian、formal review、semantic review、controlled merge、post-merge readback 和 closeout consumption。

## 核心不变量

- Scheduler owns global goal、dependency graph、gate policy、merge/readback 和 closeout。
- Scheduler owns current fact table；事实冲突时按 live host/local git readback > repo carrier current files > newest scheduler-authored state > newest worker report > older heartbeat summary 处理。
- Worker owns scoped execution、local validation、PR/task metadata 和 scheduler-readable reporting。
- No scheduler-readable report, no complete。
- scheduler 不能替 worker 创建、读取、编辑、暂停、恢复或解除 goal blocked；worker 必须自己创建并自检 goal。
- goal 一旦变成 `blocked` 或 `complete`，继续推进必须创建带有新 exact objective 的新 goal。
- `waiting-hosted` 不是 blocked，前提是 worker 正在等待同一个 hosted run 或有界 transient retry。
- `waiting-scheduler-gate` 是 scheduler action queue，不是 worker blocker。
- worker 报 `waiting-scheduler-gate` 且 `next_owner=scheduler` 后，scheduler 必须记录 `stopped_at_waiting_scheduler_gate`，不得继续等待 worker。
- `worker-stalled` 不是普通 waiting，也不是 worker blocker；它是 scheduler recovery action queue，下一步必须是 replacement worker 或 scheduler controlled takeover。
- 当 `gate_owner=scheduler` 时，worker 停在 `waiting-scheduler-gate`，等待 scheduler 执行 gate 或明确授权。
- heartbeat 必须挂在 scheduler thread；创建或更新后必须 read back `target_thread_id == scheduler_thread_id`，挂错时立即修正，不继续调度。
- PR head 改变后，所有 head-bound artifacts 必须刷新并 read back；旧 review、旧 metadata readback、旧 hosted gate 结论不得沿用。
- 除非 scheduler 明确授权，worker 不得写入或 checkout main/project worktree。
- 不得用 raw host command 绕过 controlled merge、release、review 或 approval wrapper。

## Reference Routing / 引用路由

- `references/scheduler.md`：作为 scheduler、创建/恢复 worker、处理 `worker-stalled`、replacement worker、scheduler controlled takeover、选择 model/reasoning、处理编排工具不可用、维护 dispatch table、命名 branch、triage blocker 或规划 next batch 时读取。
- `references/worker.md`：作为 worker、确认 delegated worksite、创建 scoped goal、处理状态转换或检查 scope 边界时读取。
- `references/reporting.md`：两个角色在任何 milestone、blocker、gate wait、final completion 或 cross-thread message 前都应读取。
- `references/goal-lifecycle.md`：创建、complete、block、recover 或解释 goal 时读取。
- `references/heartbeat.md`：创建或更新 scheduler heartbeat automation、确认 heartbeat target、记录 recovery prompt expiry、压缩 scheduler prompt 时读取。
- `references/gates-and-closeout.md`：guardian/review/merge/release gate、formal spec metadata same-class audit、post-merge readback、closeout-only work 或重复 gate 失败前读取。
- `references/templates.md`：起草 worker initial prompt、scheduler correction、recovery/takeover/replacement prompt、delegation fallback、`waiting-scheduler-gate` report 或 heartbeat prompt 时读取。
