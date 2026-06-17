# Orchestration Carrier / 本地编排载体

## Purpose / 用途

本地 orchestration carrier 用于保存 scheduler/worker 编排运行时状态，避免把线程历史、thread preview、长 report、gate output 或 shell output 作为状态数据库反复带入上下文。

默认路径：

```text
/Users/<username>/orchestration/<project>/<round-or-unit>/
```

该目录不属于目标项目事实源。不要默认写入目标项目 repo，除非用户明确要求。

## Fact Layers / 事实层级

事实冲突时按以下顺序处理：

1. GitHub / git / PR / issue / repo carrier / live host readback：项目事实源。
2. `/Users/<username>/orchestration/<project>/<round-or-unit>/`：本地调度运行时状态，只保存 runtime state、report locator、消费记录、lane/dispatch 状态和恢复索引。
3. 当前 live thread 的 short locator / ACK notice：消息传递信号，不是事实数据库。
4. 当前线程内的 summary：只作为提示上下文，不能覆盖以上事实。

本地 carrier 可以帮助恢复 scheduler/worker 编排，但不能替代项目 truth。声明 complete、merge-ready、lane release、closeout consumed 或 issue terminal 时，必须用项目事实源验证。

## Required Prompt Fields / 必需提示字段

所有 scheduler/worker initial、correction、recovery、replacement、heartbeat prompt 必须包含：

```text
orchestration_state_root: /Users/<username>/orchestration/<project>/<round-or-unit>
report_output_path: /Users/<username>/orchestration/<project>/<round-or-unit>/reports/<report_id>.json
report_size_budget: <=4KB for cross-thread notice; full artifact may be larger but should stay focused
do_not_read_retired_thread_turns: true
```

heartbeat prompt 还必须包含 `heartbeat_prompt_budget: <=8KB`。跨线程消息正文必须控制在 `cross_thread_message_budget: <=2KB`。

## Directory Shape / 目录形状

推荐结构：

```text
state/
  scheduler-state.json
  dispatch-table.json
  recovery-index.json
reports/
  <report_id>.json
consumption/
  <report_id>-consumed.json
artifacts/
  <run_or_gate_id>/
```

`reports/*.json` 保存完整 report。跨线程消息只传 locator。

## Report Locator / 回报定位协议

worker、scheduler 和 heartbeat 之间默认只传：

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

完整 report 写入 `report_path`。如果 report 超过正文预算，必须写 artifact 并只传 `artifact_path`、`run_id`、结论和下一步 owner/action。

## Report Artifact / 回报工件

完整 report artifact 至少包含：

```text
report:
- report_id:
- report_type:
- report_for_instruction_id:
- writer_role: scheduler | worker
- writer_thread_id:
- scheduler_thread_id:
- unit_id:
- state:
- head:
- base:
- worksite:
- branch:
- pr_or_task:
- validation_summary:
- hosted_checks_summary:
- artifact_paths:
- blocker:
- next_owner:
- next_action:
- created_at:
```

消费 report 后，scheduler 必须写 consumption record：

```text
report_consumed:
- report_id:
- report_path:
- consumed_at:
- consumed_by_thread_id:
- table_updated: yes | no
- state_file_updated:
- next_owner:
```

没有 `report_consumed` 记录时，不得把 report 当作已经驱动 dispatch/state transition。

## Thread Tool Limits / 线程工具限制

- `read_thread` 不能作为 heartbeat 常规状态读取方式，不能读取 retired、systemError、abandoned thread 的 turns。
- `read_thread` 只允许用于当前 live thread 的短 locator/ACK 可达性确认；如果需要完整状态，读取 `report_path` 或项目事实源。
- `list_threads` 只能用于定位 thread metadata，例如 thread id、title、created/updated 时间；不能用来重建状态。
- `write_stdin`、CI log、gate output、shell output 的长输出必须写 artifact，只传 path/run_id/conclusion。

## Fallback Rules / 兜底规则

没有跨线程发送工具时，fallback 只能输出 short notice：

```text
Scheduler Report Notice:
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

禁止在 `<codex_delegation>`、`Scheduler Report:` 或普通正文中粘贴完整 report。没有可写 `report_output_path` 时，必须降级为 `report-path-missing` blocker，而不是把完整 report 塞进线程。

## Recovery Rules / 恢复规则

worker-stalled 后 replacement worker 只接收 exact recovery objective、`orchestration_state_root`、必要 report locator、branch/worksite/head/base 和禁止范围。replacement worker 不接收旧线程历史，不读取 abandoned/retired/systemError thread turns。

scheduler 恢复时从本地 carrier、GitHub/git/live readback 和当前 live locator 重建 dispatch state；旧 heartbeat summary 和旧 thread preview 不能作为恢复事实。
