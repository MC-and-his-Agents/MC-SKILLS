# Orchestration Carrier / 本地编排载体

## Purpose / 用途

本地 orchestration carrier 用于保存 watcher 管理的 scheduler pool、candidate graph、lane lock、waiting queue、report locator、消费记录和恢复索引，避免 watcher heartbeat 依赖线程回读或在 prompt 中携带完整状态表。

默认路径：

```text
/Users/<username>/orchestration/<project>/<round-or-unit>/
```

该目录只保存调度运行时状态，不是 Loom 或其他目标项目的事实源。项目 truth 仍是 GitHub / git / PR / issue / repo carrier / live host readback。

## Required Prompt Fields / 必需提示字段

所有 watcher heartbeat、scheduler initial、scheduler correction、replacement scheduler prompt 必须包含：

```text
orchestration_state_root: /Users/<username>/orchestration/<project>/<round-or-unit>
report_output_path: /Users/<username>/orchestration/<project>/<round-or-unit>/reports/<report_id>.json
report_size_budget: <=4KB for report notice
heartbeat_prompt_budget: <=8KB
cross_thread_message_budget: <=2KB
do_not_read_retired_thread_turns: true
```

不要默认把这些 runtime state 写入目标项目 repo，除非用户明确要求。

## Directory Shape / 目录形状

推荐结构：

```text
state/
  unit-graph.json
  candidate-graph.json
  scheduler-pool.json
  lane-lock-table.json
  waiting-queue.json
  recovery-index.json
reports/
  <scheduler_or_lane_report_id>.json
consumption/
  <report_id>-consumed.json
artifacts/
  <gate_or_readback_id>/
```

大型证据、gate output、shell output、thread readback、dispatch table 和 lane table snapshot 必须写入 `artifacts/` 或 `state/`，跨线程只传 path/locator。

## Fact Layers / 事实层级

watcher 处理冲突时按以下顺序：

1. GitHub / git / PR / issue / repo carrier / live host readback。
2. `orchestration_state_root` 下的 watcher-authored runtime state 与 consumption records。
3. scheduler 写入 `reports/*.json` 的 scheduler-level report 或 lane-level report。
4. 当前 live scheduler 的 short locator / ACK notice。
5. watcher heartbeat summary。

本地 carrier 不能替代项目 truth。unit complete、lane release、merge/readback/closeout consumed 必须由项目事实源和 scheduler report locator 对齐证明。

## Report Locator / 回报定位协议

watcher、scheduler 跨线程消息默认只传：

```text
report_locator:
- report_id:
- report_path:
- state_root:
- unit_id:
- state:
- head:
- base:
- next_owner:
- next_action:
```

完整 scheduler report、lane request、lane release、blocked update 和 watcher readback report 必须写入 `reports/*.json`。消费后写 `consumption/*.json`。

## Thread Tool Limits / 线程工具限制

- `read_thread` 不能作为 watcher heartbeat 常规状态读取方式。
- 旧 `systemError`、`retired`、`abandoned` scheduler thread 不得读取 turns；只能保留 thread id、retired reason、last known locator 和 recovery index。
- replacement watcher/scheduler 不能从 abandoned thread 内容恢复，只能从 `orchestration_state_root`、GitHub/git/live readback 和当前 live short locator 恢复。
- `list_threads` 只允许定位 thread metadata，不能重建 scheduler pool、lane table 或 unit graph。
- 禁止把完整 dispatch table、完整 lane table、完整 thread preview 或完整 shell output 粘进 prompt 或跨线程正文。

## Heartbeat Rules / Heartbeat 规则

watcher heartbeat prompt 只包含：

- `orchestration_state_root`
- 本轮必须读取的 state/report locator
- next decision checklist
- hard forbidden actions
- size budget

完整 unit graph、scheduler pool、candidate graph、lane lock table、waiting queue 和 release predicates 留在 `state/*.json`。如果 heartbeat prompt 超过 `<=8KB`，必须先压缩为 locator 或写 artifact；无法写入时报告 `state-root-unavailable` blocker。

## Recovery And Lane Regrant / 恢复与 lane 重新授权

scheduler 失败后，watcher 将旧 scheduler 标记为 `retired` 或 `systemError-retired`，并写入 recovery index。旧 lane grant 不自动继承；replacement scheduler 请求 shared lane 时，watcher 必须重新读取 release predicate、current PR/head/base、repo carrier 和 waiting queue 后再发新 grant。

worker report 误发到 watcher 时，watcher 不能原样转发完整正文。只能发 short locator notice 给对应 scheduler；没有 report path 时记录 routing incident 和 blocker。
