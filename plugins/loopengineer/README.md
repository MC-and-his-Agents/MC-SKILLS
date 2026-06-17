[中文](README.zh-CN.md)

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

**The control plane for reliable AI agent loops.**

AI agents are no longer just answering prompts. They plan work, edit code, call tools, spawn subtasks, wait on checks, review evidence, hand off state, and resume across sessions.

That creates a new engineering problem:

> The loop around the agent is now as important as the model inside it.

LoopEngineer helps teams build agent loops that stay within context, preserve evidence, coordinate ownership, control orchestration cost, and recover when long-running work drifts or breaks.

It is not a prompt library.
It is not a workflow checklist.
It is not another "agent tips" repository.

LoopEngineer is an **agent loop control plane**.

## Why Agent Loops Need Engineering

A single prompt can make an agent do something useful once.

A reliable agent loop must keep working across:

- long-running tasks;
- large context surfaces;
- tool calls and hosted checks;
- multiple agents or threads;
- partial failures;
- review and merge readiness;
- handoff and recovery;
- evidence that must remain inspectable after the conversation moves on.

Without a control plane, agent loops tend to fail in predictable ways:

- the thread grows until it exceeds the context window;
- logs, diffs, reports, and reviews get pasted into chat history;
- workers say "done" before their reports are consumed;
- schedulers lose track of ownership;
- multiple agents touch shared state without coordination;
- old evidence is reused after the head changed;
- completion becomes a claim instead of a verifiable state;
- safety protocols add so much overhead that simple tasks become expensive.

LoopEngineer exists for this layer.

It treats the agent loop itself as an engineering object.

---

## What LoopEngineer Provides

LoopEngineer focuses on six control-plane capabilities:

```text
Context
Routing
Orchestration
Evidence
Audit
Cost
```

### Context Control

Long-running agents fail when context becomes an invisible dependency.

LoopEngineer moves context safety before message sending, thread creation, heartbeat updates, and handoff.

Target capabilities include:

* context budget profiles;
* outgoing prompt checks;
* no-inline-large-artifact rules;
* locator-only messaging;
* artifact-backed reports;
* handoff manifests;
* thread rotation before overflow.

Core rule:

```text
No context guard pass, no large message.
```

The v1 context budget structure is defined in
`schemas/v1/context-budget.schema.json`, with default profiles in
`schemas/v1/context-budget.default.json`.

### Loop Routing

Not every task needs a scheduler.
Not every scheduler needs a watcher.
Not every change needs full orchestration.

LoopEngineer routes work into the lightest sufficient profile:

```text
direct
worker_lite
scheduler_lite
scheduler_full
watcher_full
incident_recovery
```

`worker_lite` can choose the lightest sufficient provider:

```text
direct
subagent
thread
```

Subagent provider is for short, low-risk, isolated bounded execution. It returns
through an assignment, a report locator, validation evidence, and report
consumption. It does not own state transitions, gates, merge, release, shared
channels, or closeout.

Simple work should stay simple.
Risky work gets structure.
Broken loops get recovery.

### Agent Orchestration

LoopEngineer defines explicit roles for complex agent work:

* **Router** chooses the execution profile.
* **Worker** executes a bounded scope and writes a report.
* **Scheduler** coordinates workers, consumes reports, and owns gates.
* **Watcher** manages scheduler pools, shared lanes, and lifecycle.
* **Audit** checks whether the loop is still safe to continue.

Ownership is explicit.
State transitions require evidence.
Shared resources require coordination.

### Evidence Consumption

LoopEngineer does not treat "the agent said it is done" as completion.

Evidence must be written, located, consumed, and reflected in state.

Large evidence belongs in artifacts:

```text
reports/<report_id>.json
artifacts/<run_id>/
```

Threads carry compact locators:

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

Core rule:

```text
No consumed report, no state transition.
```

### Audit and Recovery

LoopEngineer aims to detect loop drift before agents continue from invalid state.

Audit checks may include:

* unconsumed reports;
* missing acknowledgements;
* stale heartbeat targets;
* stale lane owners;
* self-owned next actions;
* completion without consumed evidence;
* old head-bound artifacts;
* context rotation violations.

Recovery should rebuild from explicit facts, not from bloated conversation history.

### Coordination Cost

Safety has a cost. Over-orchestration is also a failure mode.

LoopEngineer introduces coordination cost as a first-class design concern:

* control-plane text;
* cross-thread messages;
* report read/write overhead;
* heartbeat cost;
* recovery cost;
* marginal cost of adding schedulers or workers.

The goal is not maximum governance.
The goal is the minimum reliable loop.

---

## How It Works

A LoopEngineer-managed loop follows a simple shape:

```text
User Goal
  ↓
Loop Router
  ↓
Protocol Profile
  ↓
Context Guard
  ↓
Worker / Scheduler / Watcher
  ↓
Artifact-backed Reports
  ↓
Report Consumption
  ↓
Gate / Audit / Handoff
  ↓
Next Owner / Next Action
```

### 1. Route the Work

LoopEngineer first decides how much control plane the task needs.

```text
Small task                       → direct
Bounded single-scope task         → worker_lite
Small coordinated task            → scheduler_lite
Multi-worker or gate-heavy task   → scheduler_full
Multi-scheduler shared state      → watcher_full
Broken or bloated loop            → incident_recovery
```

Inside `worker_lite`, use `direct` for current-owner work, `subagent` for
short isolated bounded work, and `thread` for high-risk, long-running,
worktree-backed, recovery-sensitive, external-write, or gate-heavy work.

### 2. Guard the Context

Before any large prompt or message is sent, LoopEngineer checks whether it fits the selected budget.

Protected surfaces include:

* worker prompts;
* scheduler prompts;
* watcher heartbeat prompts;
* correction prompts;
* recovery prompts;
* handoff prompts;
* automation prompts;
* cross-thread messages.

If content is too large:

```text
write artifact
send locator
rotate thread if needed
```

### 3. Execute with Ownership

Workers execute bounded tasks.
Schedulers coordinate workers and consume reports.
Watchers coordinate schedulers and shared lanes.

No role should silently take over another role's state.

### 4. Record Evidence

Complete evidence is written to files.
Threads carry only compact locators and decisions.

This keeps loops recoverable without turning chat history into a state database.

### 5. Audit Before Continuing

Before the loop advances, LoopEngineer can audit whether the current state is still trustworthy.

If not, the loop enters recovery instead of continuing blindly.

---

## Core Principles

### Build the loop, not just the prompt

Prompt quality matters, but agent reliability depends on the loop around the prompt.

### Keep simple work simple

```text
Do not start a watcher if routing is enough.
Do not start a scheduler if a lightweight worker is enough.
Do not create a worker if direct execution is enough.
```

### Do not use chat history as a database

Long-running state belongs in artifacts and structured state surfaces, not in conversation memory.

### Make completion verifiable

```text
No evidence, no completion.
No consumed report, no state transition.
No fresh gate, no merge-ready claim.
```

### Prefer locators over payloads

Large payloads should be written once, referenced many times, and consumed deliberately.

### Recover from facts

Recovery should use GitHub, git, repository facts, state roots, handoff manifests, and current locators—not retired thread turns.

---

## Product Surfaces

LoopEngineer is a plugin-oriented control-plane package.

The current skeleton provides the plugin manifest and top-level directories:

```text
.codex-plugin/plugin.json
skills/
scripts/
schemas/
templates/
```

The current product surface includes context safety, routing, imported
orchestration entrypoints, structure validation, state digest, report
consumption, loop audit, coordination cost, and watcher policy support:

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
```

The intended division of responsibility is:

```text
Skills route and explain.
Schemas define state shape.
Scripts validate and calculate.
Artifacts preserve evidence.
GitHub and git remain sources of truth.
```

---

## Use Cases

LoopEngineer is designed for:

* long-running coding agents;
* multi-agent engineering work;
* multi-thread agent orchestration;
* review, gate, merge-ready, and closeout workflows;
* context-safe handoff and recovery;
* agent workflow auditing;
* reducing over-orchestration cost;
* building durable AI engineering loops.

It is not intended for:

* one-off prompt experiments;
* tiny edits that do not need orchestration;
* replacing GitHub, git, CI, review engines, or worktrees;
* hiding production decisions behind autonomous agents;
* forcing every task into a heavy multi-agent framework.

---

## Relationship with Loom

LoopEngineer is independent.

It can be used on its own, or alongside [Loom](https://github.com/MC-and-his-Agents/Loom) as an external companion plugin.

The layers are different:

```text
Loom          = project operating layer
LoopEngineer  = agent loop control plane
```

Loom owns project-level execution surfaces such as adoption, resume, story, build, review, merge-ready, handoff, closeout, and `.loom/` facts.

LoopEngineer owns loop-level control surfaces such as context safety, routing, scheduler/worker/watcher orchestration, report consumption, audit, recovery, and coordination cost.

Important boundaries:

```text
LoopEngineer is not a Loom scenario skill.
LoopEngineer is not a Loom repo companion.
LoopEngineer does not own .loom facts.
LoopEngineer does not install itself into plugins/loom/skills.
Integration must go through an explicit adapter contract.
```

---

## Philosophy

AI engineering is moving from prompts to loops.

The next bottleneck is not whether an agent can produce code.
It is whether the loop around the agent can stay observable, safe, cost-aware, and recoverable when the work becomes long, parallel, or failure-prone.

LoopEngineer exists for that layer.

```text
Less prompt sprawl.
More loop control.
Fewer mystery states.
More recoverable work.
```

---

## License

MIT
