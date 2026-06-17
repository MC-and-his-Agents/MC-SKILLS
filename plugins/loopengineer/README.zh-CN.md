[English](README.md)

# LoopEngineer

[![Latest Release](https://img.shields.io/github/v/release/MC-and-his-Agents/LoopEngineer?label=release)](https://github.com/MC-and-his-Agents/LoopEngineer/releases/latest)
[![License](https://img.shields.io/github/license/MC-and-his-Agents/LoopEngineer)](LICENSE)
![Codex Plugin](https://img.shields.io/badge/Codex-Plugin-2563EB)
![Loop Engine](https://img.shields.io/badge/Loop-Engine-0F766E)
![Agent Loop](https://img.shields.io/badge/Agent-Loop-7C3AED)
![Control Plane](https://img.shields.io/badge/Control-Plane-111827)
![Context Safety](https://img.shields.io/badge/Context-Safety-D97706)
![Runtime Neutral](https://img.shields.io/badge/Runtime-Neutral-475569)
![Evidence Driven](https://img.shields.io/badge/Evidence-Driven-059669)
![Worker Lite](https://img.shields.io/badge/Worker-Lite-0284C7)
![Subagent Ready](https://img.shields.io/badge/Subagent-Ready-4F46E5)

**可靠 Agent Loop 的控制面。**

AI agent 已经不只是回答提示词。它们会规划任务、修改代码、调用工具、拆分子任务、等待检查、审查证据、交接状态，并在不同会话之间恢复工作。

这带来了一个新的工程问题：

> 围绕 agent 的 loop，已经和 agent 模型本身一样重要。

LoopEngineer 帮助团队构建更可靠的 agent loop：控制上下文、保留证据、协调所有权、管理编排成本，并在长周期任务漂移或失败时恢复。

它不是提示词库。
它不是工作流清单。
它不是又一个"agent 使用技巧"仓库。

LoopEngineer 是一个 **agent loop control plane**。

## 为什么 Agent Loop 需要工程化

一个提示词可以让 agent 做对一次。

但一个可靠的 agent loop 需要跨越：

- 长周期任务；
- 大上下文表面；
- 工具调用和托管检查；
- 多 agent 或多线程；
- 部分失败；
- 评审与合并就绪；
- 交接与恢复；
- 在对话结束后仍可审计的证据。

没有控制面，agent loop 通常会以类似方式失效：

- 线程不断变长，直到超过上下文窗口；
- 日志、差异、报告和评审结果被直接贴进聊天历史；
- worker 在报告被消费前就宣称完成；
- scheduler 丢失所有权和下一步责任；
- 多个 agent 同时触碰共享状态；
- head 改变后仍复用旧证据；
- "完成"变成一句声明，而不是可验证状态；
- 为了安全加入大量协议后，简单任务也变得昂贵。

LoopEngineer 关注的正是这一层。

它把 agent loop 本身当作工程对象。

---

## LoopEngineer 提供什么

LoopEngineer 聚焦六类控制面能力：

```text
上下文
路由
编排
证据
审计
成本
```

### 上下文控制

长周期 agent 最隐蔽的故障点是上下文。

LoopEngineer 把上下文安全前移到消息发送、线程创建、心跳更新和交接之前。

目标能力包括：

* 上下文预算档位；
* 外发提示检查；
* 禁止内联大型工件；
* 只传定位信息；
* 基于工件的报告；
* 交接清单；
* 上下文溢出前主动轮换线程。

核心规则：

```text
没有通过上下文检查，就不发送大型消息。
```

### Loop 路由

不是每个任务都需要 scheduler。
不是每个 scheduler 都需要 watcher。
不是每个改动都需要完整编排。

LoopEngineer 会把任务路由到最轻足够的协议档位：

```text
direct
worker_lite
scheduler_lite
scheduler_full
watcher_full
incident_recovery
```

`worker_lite` 可以选择最轻足够的 provider：

```text
direct
subagent
thread
```

`subagent` provider 只用于短任务、低风险、隔离清楚的有界执行。它必须通过
assignment、report locator、验证证据和报告消费回到主控制面；它不拥有状态转换、
门禁、merge、release、共享通道或 closeout。

简单任务保持简单。
高风险任务获得结构。
损坏的 loop 进入恢复。

### Agent 编排

LoopEngineer 为复杂 agent 工作定义清晰角色：

* **Router**：选择执行档位。
* **Worker**：执行有界范围并写报告。
* **Scheduler**：协调 worker、消费报告并拥有门禁。
* **Watcher**：管理 scheduler pool、共享通道和生命周期。
* **Audit**：检查 loop 是否仍然安全可继续。

所有权必须明确。
状态转换必须有证据。
共享资源必须有协调。

### 证据消费

LoopEngineer 不把"agent 说完成了"当作完成。

证据必须被写入、定位、消费，并反映到状态中。

大型证据进入工件：

```text
reports/<report_id>.json
artifacts/<run_id>/
```

线程中只携带紧凑定位信息：

```text
report_id
report_path
state_root
unit_id
state
head
base
next_owner
next_action
```

核心规则：

```text
报告未消费，状态不转换。
```

### 审计与恢复

LoopEngineer 目标是在 agent 继续推进前发现 loop 漂移。

审计可以检查：

* 未消费报告；
* 缺失确认；
* 过期心跳目标；
* 过期通道所有者；
* 自我拥有的下一步动作；
* 没有消费证据却声明完成；
* 旧 head-bound 工件被复用；
* 上下文轮换后仍读取旧线程。

恢复应从明确事实重建，而不是从膨胀的聊天历史重建。

### 协作成本

安全有成本。过度编排也是一种失败。

LoopEngineer 把协作成本作为一等设计对象：

* 控制面文本；
* 跨线程消息；
* 报告读写成本；
* 心跳成本；
* 恢复成本；
* 新增 scheduler 或 worker 的边际成本。

目标不是最大治理。
目标是最小可靠 loop。

---

## 工作原理

LoopEngineer 管理的 loop 大致如下：

```text
用户目标
  ↓
Loop Router
  ↓
协议档位
  ↓
Context Guard
  ↓
Worker / Scheduler / Watcher
  ↓
基于工件的报告
  ↓
报告消费
  ↓
门禁 / 审计 / 交接
  ↓
下一责任方 / 下一动作
```

### 1. 先路由任务

LoopEngineer 首先判断任务需要多少控制面。

```text
小任务                         → direct
单一范围任务                   → worker_lite
小规模协调任务                 → scheduler_lite
多 worker 或重门禁任务          → scheduler_full
多 scheduler 或共享状态任务     → watcher_full
损坏或膨胀的 loop              → incident_recovery
```

在 `worker_lite` 内部，当前 owner 可完成时用 `direct`；短小隔离任务可用
`subagent`；高风险、长任务、独立 worktree、恢复敏感、外部写入或重门禁工作用
`thread`。

### 2. 再守住上下文

任何大型提示或消息发送前，都先检查是否符合预算。

受保护的表面包括：

* worker 提示；
* scheduler 提示；
* watcher 心跳提示；
* 修正提示；
* 恢复提示；
* 交接提示；
* 自动化提示；
* 跨线程消息。

如果内容过大：

```text
写入工件
发送定位信息
必要时轮换线程
```

### 3. 带所有权执行

Worker 执行有界任务。
Scheduler 协调 worker 并消费报告。
Watcher 协调 scheduler 与共享通道。

任何角色都不应悄悄接管其他角色的状态。

### 4. 记录证据

完整证据写入文件。
线程只携带紧凑定位和决策。

这样 loop 可以恢复，而不会把聊天历史变成状态数据库。

### 5. 继续前先审计

LoopEngineer 可以在推进前审计当前状态是否仍可信。

如果不可信，loop 进入恢复，而不是盲目继续。

---

## 核心原则

### 构建 loop，而不是只写 prompt

提示词质量很重要，但 agent 的可靠性取决于提示词外面的 loop。

### 简单任务保持简单

```text
路由足够时，不启动 watcher。
轻量 worker 足够时，不启动 scheduler。
直接执行足够时，不创建 worker。
```

### 不把聊天历史当数据库

长周期状态应该存在于工件和结构化状态面中，而不是对话记忆里。

### 让完成可验证

```text
没有证据，不声明完成。
没有消费报告，不转换状态。
没有新鲜门禁，不声明合并就绪。
```

### 传定位，不传大包

大型内容应该写入一次、多次引用，并被明确消费。

### 从事实恢复

恢复应使用 GitHub、git、仓库事实、状态根目录、交接清单和当前定位信息，而不是 retired thread turns。

---

## 产品表面

LoopEngineer 以插件化控制面形式交付。

当前骨架已经提供插件 manifest 和顶层目录：

```text
.codex-plugin/plugin.json
skills/
scripts/
schemas/
templates/
```

当前产品表面已经包含上下文安全、路由、导入的编排入口、结构校验、状态摘要、报告消费、循环审计、协作成本和观察者策略支持：

```text
skills/
  codex-loop-router
  codex-context-safety
  codex-thread-orchestration
  codex-scheduler-watcher
  codex-loop-audit

scripts/
  context_guard.py
  state_digest.py
  validate_structures.py
  consume_report.py
  loop_audit.py
  coordination_tax.py

schemas/
  context-budget.schema.json
  report.schema.json
  dispatch-table.schema.json
  scheduler-pool.schema.json
  channel-state.schema.json
  waiting-queue.schema.json
  channel-event.schema.json
  watcher-decision.schema.json
  watcher-inbox.schema.json

templates/
  handoff-replacement.md
  worker-lite-initial.md
  scheduler-lite-initial.md
```

预期职责划分：

```text
Skills 负责路由和解释。
Schemas 定义状态形状。
Scripts 执行校验和计算。
Artifacts 保存完整证据。
GitHub 和 git 保持事实权威。
```

---

## 适用场景

LoopEngineer 适合：

* 长周期 coding agent；
* 多 agent 工程任务；
* 多线程 agent 编排；
* review、gate、merge-ready、closeout 流程；
* 上下文安全交接与恢复；
* agent workflow 审计；
* 降低过度编排成本；
* 构建可持续的 AI 工程 loop。

不适合：

* 一次性提示词实验；
* 不需要编排的小改动；
* 替代 GitHub、git、CI、review engine 或 worktree；
* 把生产决策隐藏在完全自治 agent 背后；
* 强迫所有任务进入重型多 agent 框架。

---

## 与 Loom 的关系

LoopEngineer 是独立产品。

它可以单独使用，也可以作为 [Loom](https://github.com/MC-and-his-Agents/Loom) 的外部伴随插件搭配使用。

两者层级不同：

```text
Loom          = 项目操作层
LoopEngineer  = agent loop 控制面
```

Loom 负责项目级执行表面，例如 adopt、resume、story、build、review、merge-ready、handoff、closeout 和 `.loom/` facts。

LoopEngineer 负责 loop 级控制表面，例如上下文安全、路由、scheduler / worker / watcher 编排、报告消费、审计、恢复和协作成本。

重要边界：

```text
LoopEngineer 不是 Loom scenario skill。
LoopEngineer 不是 Loom repo companion。
LoopEngineer 不拥有 .loom facts。
LoopEngineer 不安装到 plugins/loom/skills。
集成必须通过显式 adapter contract。
```

---

## Philosophy

AI engineering is moving from prompts to loops.

下一阶段的瓶颈，不是 agent 能不能生成代码。
而是当任务变长、并行、证据密集、容易失败时，agent 外围的 loop 是否仍然可观察、安全、成本可控、可恢复。

LoopEngineer 就是为这一层而存在。

```text
更少提示词膨胀。
更多 loop 控制。
更少神秘状态。
更多可恢复工作。
```

---

## License

MIT
