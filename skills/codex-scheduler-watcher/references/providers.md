# Unit Providers / 调度单元来源

## Provider Selection / 来源选择

不要假设项目一定有 milestone。先选择最小可证明的 unit provider。

provider 优先级原则：

- 如果存在更上游的 issue、milestone、repo carrier 或 release plan，优先把上游对象作为 unit，PR 作为 readback evidence。
- 如果当前真实协调面已经是一个 PR，例如 gate recovery、merge readiness、metadata repair 或 closeout sync，PR 可以作为 unit。
- 如果一组 PR 构成当前协调面，使用 `pull_request_set`，并显式规划 scheduler ownership、merge lane 和 fan-in closeout。
- watcher 不得因为发现 open PR 就绕过 scheduler；PR provider 只用于创建/维护 scheduler，不用于 watcher 亲自修 PR、跑 gate 或 merge。
- milestone、Round、phase、project column 或列表顺序不是硬依赖。只有 `blocked-by/blocks`、task dependency、shared contract/carrier、merge lane、release gate 或明确 repo evidence 才能生成 hard dependency edge。

```text
provider_selection:
- available_sources:
- chosen_provider:
- why_this_provider:
- source_locator:
- upstream_source_locator:
- completion_predicate_source:
- known_gaps:
```

## Dependency Extraction / 依赖提取

选择 provider 后，watcher 必须把依赖拆成 dependency edges，而不是用 provider 的粗粒度顺序阻塞整个 unit graph。

```text
dependency_extraction:
- source_locator:
- discovered_edges:
- hard_edges:
- soft_edges:
- convergence_edges:
- unblocked_scopes:
- blocked_scopes:
- evidence_gaps:
```

提取规则：

- GitHub `blocked-by/blocks`、明确 task dependency、消费同一未冻结 schema/API/parser、写同一 carrier/status/shadow/progress，通常是 hard edge。
- milestone/Round 的编号、issue 排序、project column 排序、PR 列表顺序，不能单独生成 hard edge。
- inventory、调查、文档整理、低风险 fixture 分类、可重复 readback 的背景事实，默认是 soft edge。
- release closeout、repo carrier sync、fan-in evidence、统一 review record，默认是 convergence edge，通常后置到 implementation scheduler 完成后。
- hard edge 只阻塞消费该事实的 issue/PR/path/contract/carrier scope；不消费该事实的 downstream scope 可以进入 scheduler pool。
- 无法证明 edge 类型或 blocked scope 时，记录 `evidence_gaps`，仅将相关候选 scope 保持 planned，不要扩大成整批 milestone 串行。

## Provider Types / 来源类型

### github_milestone

适用于 GitHub milestone 明确承载一批 issues/PRs 的项目。

默认 completion predicate：

- milestone open issues 为 0，或全部目标 issue 已 CLOSED/COMPLETED。
- milestone 相关 open PR 为 0，或所有相关 PR 已 merged/closed 且被解释。
- scheduler final report 显示 merge/readback/closeout consumed。
- repo carrier 或项目状态已消费完成事实。

### parent_issue

适用于 parent issue 拥有 child issues、blockedBy/blocks 或 task list 的项目。

默认 completion predicate：

- child issues 全部 terminal。
- parent issue 的 acceptance / closeout 被消费。
- 无 linked open PR 或 unresolved scheduler gate。
- scheduler final report 证明 parent closeout/readback。

### issue_set

适用于 label、query、project status 或手工列表定义的一组 issues。

默认 completion predicate：

- issue set 中所有 required issues terminal。
- optional/deferred issues 被明确标记 deferred，不算 complete。
- issue set 不再有 open merge/gate/closeout PR。
- scheduler final report 与 live readback 一致。

### pull_request

适用于已有 PR 本身就是待协调对象的场景，例如 gate repair、review recovery、metadata repair、merge readiness、stale head-bound artifact refresh、closeout sync。

默认 completion predicate：

- PR 已 merged 或 closed，并有 readback；如果 closed/unmerged，必须有 rationale。
- required checks、review/gate、mergeability 或 closeout blocker 已被 scheduler 消费。
- PR head/base/body metadata 与 live readback 对齐；无 stale head-bound artifacts。
- linked issue/task closeout 已完成，或有 not_applicable rationale。
- repo carrier/status/shadow/review record 已消费 PR 事实，或明确不适用。
- scheduler final report 证明 PR gate/merge/readback/closeout 处理完成。

使用限制：

- 如果 PR 只是某个 worker 的产物，而上游 issue/milestone 仍是主要 truth，优先使用上游 unit。
- watcher 可以为该 PR 创建 scheduler，但不得直接修 PR、运行 guardian/review、controlled merge 或 closeout。

### pull_request_set

适用于一组 open PR 构成当前协调面的场景，例如一个 release train 的多个 PR、一个 parent issue 的多个待合并 PR、或一次恢复中需要统一处理的 stale PR 集合。

默认 completion predicate：

- PR set 中所有 required PR 已 merged/closed/explained。
- 每个 PR 的 head-bound artifacts、review/gate、checks、metadata 已按当前 head 消费。
- linked issues/tasks 与 PR set 结果一致。
- merge lane 已执行或每个未 merge PR 有解释。
- fan-in closeout 或 repo carrier sync 完成。

使用限制：

- 必须为每个 PR 或 PR group 指定 scheduler owner。
- 必须写明 merge lane：哪些 PR 可并行推进，哪些必须串行合并/readback。
- 如果 PR set 共享 carrier/status/shadow 或 schema，先创建 shared-contract 或 fan-in scheduler，不要让多个 scheduler 并发写同一 truth。

### project_view

适用于 GitHub Project、Linear、Jira 或等价项目视图是主要 truth 的项目。

默认 completion predicate：

- project view 中目标 items 到 terminal/status done。
- linked PR/issue 状态与 project view 一致。
- scheduler final report 解释任何 project drift。

### release

适用于 release train、version、deployment 或 launch checklist。

默认 completion predicate：

- release checklist terminal。
- release/no-release evidence 记录完整。
- deployment/approval gate 由 scheduler 消费。
- post-release readback 或 no-release rationale 已记录。

### repo_carrier

适用于仓库内状态文件是权威事实，如 `.loom/status/current.md`、roadmap、plan、progress。

默认 completion predicate：

- carrier 中 current unit terminal。
- related PR/issue/live host 与 carrier 一致。
- shadow/status/review/evidence 等派生载体同步。
- scheduler final report 证明 carrier consumption。

### manual_goal

适用于用户只给了自然语言目标，尚无正式 issue/milestone。

默认 completion predicate 必须由 watcher 创建前写明，不得使用“用户说完成了”作为唯一证明。至少包含：

- expected scheduler output。
- expected host/repo readback。
- expected closeout 或 not_applicable rationale。

## Provider Gap / 来源不足

如果 provider 事实不足：

- 不创建 watcher automation。
- 不创建 scheduler pool。
- 不创建 scheduler thread。
- 不创建 worker。
- 不创建多 scheduler。
- 不运行 gate。
- 不修改 host/repo state。
- 明确告知用户当前条件不具备，并列出缺失 facts。
- 请求用户补充最小 locator，或另行启动不属于本 skill 范围的只读 discovery / 建图任务。

只有补充事实足以定义 unit graph 与 completion predicate 后，才可以继续本 skill 后续流程。

必须回报：

```text
provider_gap:
- attempted_provider:
- missing_facts:
- why_completion_predicate_cannot_be_proven:
- minimum_user_input_needed:
- recommended_next_step: provide_facts | run_separate_discovery
```
