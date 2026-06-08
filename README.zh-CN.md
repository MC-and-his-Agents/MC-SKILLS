# MCSKILLS

本仓库收集 Codex skills 和 Codex plugins。

[English](./README.md)

## Skills

独立 skill 放在 `skills/` 下。它们作为轻量复用资产保留，不进入 plugin marketplace。

- [write-a-goal](./skills/write-a-goal/SKILL.md) - 起草、优化或设置可持续推进的 Codex goal。
- [code-smell-decision](./skills/code-smell-decision/SKILL.md) - 发现代码坏味道，收集工程证据，并判断应立即修复、延后处理、记录技术债、接受现状或交给人工判断。
- [codex-thread-orchestration](./skills/codex-thread-orchestration/SKILL.md) - 协调 scheduler/worker 线程，处理 scoped execution、关键回报、gate 和 closeout。

## 本地源码同步

维护者在本地源码 checkout 中迭代时，变更 merge 到 `main` 且本地 main
快进后，可以用软链暴露给本机 Codex runtime：

```bash
./scripts/install-local-skills.sh <skill-name>
```

这是本地源码迭代的开发便利方式，不是普通用户安装 MCSKILLS 的默认方式。
脚本会把选定的 `skills/*/SKILL.md` 目录链接到
`~/.codex/skills/<skill-name>`，并验证安装后的路径。只有确认所有本地
skill 都适合链接时，才省略 `<skill-name>` 批量安装。

## Plugins

可安装 plugin 放在 `plugins/` 下。仓库级 marketplace 元数据定义在
[`.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json)。

- [codegraph-intelligence](./plugins/codegraph-intelligence/README.md) - 基于 CodeGraph 的代码探索、影响分析、重构和 review 工作流。

## Notes

- 新增 skill 时，保持本 README 作为轻量导航页。
- 后续新增的独立 skill 应放在 `skills/` 下。
- 后续新增的可安装 plugin 应放在 `plugins/` 下，并且只在 plugin 元数据准备好后加入 marketplace。
