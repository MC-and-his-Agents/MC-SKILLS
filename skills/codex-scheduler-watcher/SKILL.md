---
name: codex-scheduler-watcher
description: 创建或更新 Codex meta-scheduler watcher automation。用于为一个项目、milestone、parent issue、issue set、pull request、PR set、release、repo carrier 或手工目标维护 coordination unit graph、scheduler pool 和调度线程生命周期；在安全并行时创建多个 scheduler thread，在 scheduler 缺失、失联、阻塞、完成或需要切换 unit 时行动。默认中文说明和回报，可适配用户语言；协议字段、状态枚举、工具名和结构化模板字段保持机器可读。
---

# Codex Scheduler Watcher

## 概览

本 skill 用于创建 **meta-scheduler watcher**。它是 scheduler 的 scheduler，但只编排调度线程生命周期，不调度 worker。

watcher 拥有 coordination unit graph、scheduler pool、unit cursor、跨 scheduler ownership locks 和下一批 scheduler 启动判断。scheduler 仍然拥有单个 coordination unit 内的 global goal、worker、PR、gate、merge、readback 和 closeout。

默认语言：中文。用户使用其他语言，或明确要求切换语言时，面向用户和跨线程沟通可适配用户语言。协议字段、状态枚举、工具名、命令、日志、thread id、PR/issue 编号和 sha 保持原文。

## Role Detection / 角色自检

- Watcher / meta-scheduler：用户要求创建、维护、优化 watcher automation，或要求监控 scheduler lifecycle、milestone/phase/parent issue 切换、多个 scheduler 并行调度。
- Scheduler：用户要求拆分 worker、处理 PR/gate/merge/closeout，或当前线程负责单个 coordination unit 的执行调度。
- Worker：收到具体 scoped objective、worksite、branch 和 scheduler report_to 约束。

如果当前任务是创建 scheduler thread 或 watcher automation，先按 watcher 角色处理。创建出的 scheduler prompt 必须要求 scheduler 读取 `codex-thread-orchestration`，但 watcher 自己不要接管 scheduler/worker 协议。

## 快速开始

1. 定义 coordination unit：读取 `references/unit-model.md`。
2. 选择 unit provider：读取 `references/providers.md`，不要假设项目一定有 milestone。
3. 写明 completion predicate：unit 完成必须由 issue/PR/repo carrier/scheduler final report 等可读事实证明。
4. 建立 scheduler pool：记录每个 unit 的 scheduler thread、heartbeat、owned paths、dependencies、state、next action。
5. 判断是否并行创建多个 scheduler：读取 `references/parallel-scheduling.md`。不使用固定数量上限，必须用 isolation、capacity 和 observability 证明。
6. 创建或更新 watcher automation：读取 `references/watcher-automation.md` 和 `references/templates.md`。
7. 创建 scheduler 时，prompt 必须要求 scheduler 使用 `$codex-thread-orchestration`，包含 `watcher_instruction_id`，并创建自己的 scheduler heartbeat。

## 核心不变量

- Watcher owns coordination unit graph、scheduler pool、unit cursor 和 scheduler lifecycle。
- Scheduler owns one coordination unit 的 global goal、workers、gates、merge/readback 和 closeout。
- Worker owns scoped execution、local validation 和 scheduler-readable reports。
- Watcher 可以创建多个 scheduler thread，但必须先证明 unit 独立、ownership 隔离、gate/merge lane 可控、heartbeat 可观测、恢复能力足够。
- Watcher 不直接创建 worker，不给 worker 下指令，不消费 worker report，不跑 guardian/review/controlled merge，不修 PR finding，不写业务代码。
- Watcher 只消费 scheduler-level report：scheduler active、blocked、stalled、complete、final closeout/readback 或 scheduler missing。
- No scheduler ACK, no active。watcher 给 scheduler 的 initial/replacement/correction 指令必须有 `watcher_instruction_id`；scheduler 回 `scheduler_ack` 前，watcher 只能标记 `scheduler-instruction-sent-awaiting-ack`，不能标记 `scheduler-active`。
- No watcher report receipt, no unit transition。watcher 消费 scheduler report 后必须记录 `watcher_report_consumed`；未消费前不得把 scheduler report 当成已经更新了 scheduler pool 或 unit state。
- No bidirectional thread IDs, no scheduler coordination。watcher 必须登记 `watcher_thread_id` 和 `scheduler_thread_id`；scheduler 必须确认 `watcher_thread_id` 与 `report_to_watcher_thread_id`。任一方向缺失时只能标记 `scheduler-routing-missing` 或 `scheduler-instruction-sent-awaiting-ack`。
- 如果 worker report 误发到 watcher，watcher 不得据此更新 unit state；只能原样转发给对应 scheduler，并要求 scheduler 修正 `report_to_thread_id`。
- 如果 scheduler 缺失、不可读或生命周期卡住，watcher 创建 replacement scheduler 或请求用户介入；不要退化为亲自执行 scheduler scope。
- 如果多个 scheduler 完成后需要收敛，watcher 创建 closeout / fan-in scheduler，而不是自己合并 closeout。
- 如果 unit provider 事实不足，watcher 只回报 `provider_gap` 并停止；不要创建 watcher automation、scheduler pool、scheduler thread 或任何只读侦察线程。
- 默认串行；证明独立后并行。无法证明 isolation、capacity 或 observability 时保持串行。

## 引用路由

- `references/unit-model.md`：定义 coordination unit、scheduler pool、ownership lock、state machine 时读取。
- `references/providers.md`：项目没有 milestone，或需要从 parent issue、issue set、project view、release、repo carrier、manual goal 等来源生成 unit 时读取。
- `references/parallel-scheduling.md`：判断是否一次创建多个 scheduler、是否降低并发、是否创建 fan-in scheduler 时读取。
- `references/scheduler-lifecycle.md`：创建、恢复、替换、停止或切换 scheduler thread 时读取。
- `references/watcher-automation.md`：创建或更新 watcher heartbeat/automation、确认 target、处理 watcher stale prompt 时读取。
- `references/templates.md`：起草 watcher prompt、scheduler initial prompt、parallel decision、replacement scheduler prompt 或 watcher readback report 时读取。
