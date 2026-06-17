# Gates And Closeout

## Scheduler-Owned Gate Protocol / Scheduler 拥有的 Gate

默认高成本 gate 由 scheduler 拥有：

- guardian。
- formal review。
- semantic review。
- controlled merge。
- release/deployment approval。
- post-merge readback。
- closeout consumption。

worker 只有在 scheduler 明确授权 exact PR/task 和 exact head 时，才能运行这些 gate。

以下条件全部满足后，worker 进入 `waiting-scheduler-gate`：

- scope diff 匹配 objective 和 allowed write paths。
- local validation 通过。
- PR/task body metadata 已更新并 read back。
- hosted checks 在当前 head 上为 green。
- head/base 明确。
- branch type 匹配 actual diff。
- findings 已解决或 dispositioned。
- 修复 guardian/review finding 后，same-class drift search 已完成。

`waiting-scheduler-gate` 是 scheduler action queue。scheduler 必须运行或授权 next gate；不要要求 worker 重复同一个 missing-review report。

## Head-Bound Artifact Refresh / Head 绑定产物刷新

任何 commit/push 改变 PR head 后，进入 gate 前必须刷新并 read back：

- PR body machine carrier `head_sha`。
- PR `headRefOid`。
- PR metadata preflight / compare-body。
- review artifact stale 判断。
- hosted gate stale-run 判断。

禁止沿用旧 review artifact、旧 PR metadata readback 或旧 hosted gate 结论。无法证明绑定当前 head 时，gate 必须 fail-closed。

## Review Entry Checklist / Review 入口清单

运行 high-cost gate 前，确认：

- PR/task head、base 和 body metadata 已 read back。
- hosted checks 在当前 head 上 green，不是旧 head。
- scope diff 匹配 objective、branch type 和 allowed write paths。
- machine-readable metadata 位于 parser 可消费位置，且 enum values 合法。
- formal spec 或 spec-like PR 必须完成 metadata same-class audit。
- 最近 guardian/review findings 已 dispositioned。
- same-class search 覆盖相关表面：public API、formal spec、generated output、metadata parser、head binding、integration/live gate 或等价风险表面。
- 之前若出现 root-cause drift，先确认 root-cause correction 已完成，再重跑 guardian。

类似 finding、test failure、metadata gap 或 gate gap 出现两次时，停止 high-cost retries，发出 root-cause correction objective。不要把 root-cause correction 描述成 narrow correction。

## Repeated Semantic Gate Probing / 重复语义 Gate 探测

guardian/review 不是问题探测器。以下任一情况出现时，scheduler 必须分类为 `same_class_semantic_boundary_repetition`，停止继续 narrow latest-finding correction，并阻止下一次 high-cost gate：

- 同一 PR 的同一或相近 semantic area，或同一 helper / admission path，出现 2 次或以上 guardian/review `REQUEST_CHANGES`。
- 同一 `valid=true` 或 admission-style path 被 2 个或以上 correction commit 修改。
- guardian/review finding 反复指向 evidence boundary、closeout admission、readiness、fail-closed、redaction、freshness、route/provider binding、provider evidence shape、required ref locator 或 provenance。

触发后必须：

- 更新 Gate Failure Ledger。
- 设置 `escalation_action=root_cause_correction_required` 或 `root_cause_correction_sent`。
- 发送 Root-Cause Correction Prompt，而不是普通 Scheduler Correction Prompt。
- 将下一次 guardian/formal/semantic review 标记为 `gate_retry_blocked`，直到 scheduler 消费 worker 的 root-cause report。
- 要求 worker 回报 invariant checklist、fail-closed matrix、same-class audit surfaces、unverifiable invariants 和 remaining risks。

术语：

- `narrow correction`：修复单个明确 finding，适用于首次或孤立 finding。
- `root-cause correction`：暂停高成本 gate，审计同类不变量、admission path 和 fail-closed matrix，适用于重复同类语义边界失败。

## Formal Spec Metadata Same-Class Audit / 规约元数据同类审计

formal spec 或 spec-like PR 进入 scheduler gate 前，必须审计 PR body、spec suite、TODO、plan 和相关 closeout carrier 中的同类 drift：

- `Fixes` / `Refs` / closing semantics 是否符合目标状态，不得误关闭不该关闭的 issue。
- `closing_semantics`、`closeout_control`、`merge_gate` 是否一致。
- `integration_applicable`、`integration_check`、`integration local-only` 残留是否一致且可解释。
- `contract_surface` 与实际 spec/API/metadata surface 是否一致。
- `live_evidence_record`、release/no-release evidence、hosted/live gate 口径是否一致。
- TODO/plan/spec 中旧 gate、旧 closing、旧 review 或旧 integration 语义是否已同步。

metadata 改动后必须 read back PR body 和相关 spec/carrier。若 review input 变化，必须重新 review，或明确记录当前 review 为什么可复用；不得把旧 review 当作自动通过。

## Guardian Finding Root Cause / Finding 根因

worker 修复 finding 后，report 应包含：

- finding id/source。
- root cause。
- changed files，以及为什么 scope 足够。
- same-class search command/results。
- targeted validation。
- PR/task body update 和 readback status。
- new head/base。
- remaining risk。

scheduler 消费这些信息后，才能进入下一次 high-cost run。

## Controlled Merge / Release

使用仓库本地的 controlled wrapper 执行 merge、approval、release 或 deployment。

只有以下条件满足时才继续：

- local gate/check 通过。
- hosted required checks 通过。
- head/body/payload metadata 对齐。
- mergeability/readiness clean。
- host enforcement 和 required checks 可证明。
- controlled wrapper check 通过。

以下情况停下并请求 scheduler/root-cause action：

- 有界 retry 后 host enforcement/readback 仍不可用。
- 无法证明 required checks 被 enforced。
- wrapper 因非 transient 原因失败。
- proposed path 使用 raw host command 绕过 wrapper policy。

## Post-Merge Readback / 合并后读回

implementation merge 通常不是完整完成。必须 read back：

- merged state 和 merge/release commit。
- target branch/base state。
- related issue/task closure 或 completion。
- reconciliation/closeout checks。
- terminal carrier/status/shadow/evidence state。
- final validation evidence 和 remaining risk。

如果 target branch 仍记录 pre-merge state，基于最新 base/main 创建 closeout-only branch/PR/task。

## Closeout-Only Work / 仅收口工作

closeout-only work 只应修改消费完成事实所需的 carrier/status/evidence 文件。除非 scheduler 明确改变 objective，否则不得夹带 implementation changes。

closeout-only PR/task 仍需要：

- fresh base/main。
- narrow branch 和 allowed write paths。
- 只能消费已完成事实，不得夹带新实现。
- 本地验证：governance/init verify、fact-chain、suite validate 或 not_applicable rationale、adopt verify、carrier refresh --dry-run、shadow-parity、PR metadata preflight + readback compare，按仓库等价工具执行。
- metadata readback。
- hosted checks。
- controlled merge。
- final readback。

post-merge evidence 必须标注为 post-merge。不得把 post-merge review comments 或 checks 表述成 pre-merge gates。

hosted checks 或 merge gate 失败后，先分类为 `carrier drift`、`shadow drift`、`review stale`、`PR metadata drift`、`host stale run` 或 `code semantic failure`。分类前不得重复 rerun hosted checks。
