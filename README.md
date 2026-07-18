# Coding Context Framework

Coding Context Framework v0.1.0 是一个通用、Git-backed、repository-native 的编码上下文框架。它为跨任务、跨仓库协作提供可审计的规则、任务索引、执行计划和证据入口。

它不承载业务代码，也不把上下文文档当成实现事实。代码、测试、API 合同、PR、CI、部署和运行日志仍归具体目标仓库与外部系统所有。

## 提供的抽象

- JSON Schema 约束的 YAML task board。
- 支持任务、状态、计划、证据、备注和父子关系的原子 CLI。
- 复杂或包含多个步骤的任务使用 plan contract 与确定性检查器。
- 可按风险选择的 feedback loop 词汇：Unit / Module tests、evals、structural checks、Mock E2E、Real CLI / Workflow 与 Real API E2E。
- Reproducible evidence 与 recorded demos 用于审阅实际运行结果；Evidence / Demo 不是测试层。
- 初始化、上下文检查、发布安全检查、secret scan 和 CI。
- Codex 与 Claude Code 共享同一份 `AGENTS.md` 和 `.agents/skills` canonical source。
- Domain、plan 和 evidence 模板；不附带任何真实或教程任务内容。

## 快速开始

```bash
python3 -m pip install -r requirements-dev.txt
scripts/task validate
scripts/task list --tree
```

根 board 只包含通用的 `general` domain 和 `context-repository` 占位 repo，task 列表为空。

登记任务：

```bash
scripts/task add-task \
  --id example.first-task \
  --title "Describe the task" \
  --domain general \
  --repo context-repository \
  --status backlog \
  --requirement-ref REQ-001
```

复杂或包含多个步骤的任务先从 `docs/exec-plans/_template.md` 创建 plan，按 [task-plan](.agents/skills/task-plan/SKILL.md) 校验并登记：

```bash
.agents/skills/task-plan/scripts/check-task-plan.sh \
  docs/exec-plans/active/example.first-task.md

scripts/task register-plan \
  docs/exec-plans/active/example.first-task.md \
  --id example.first-task \
  --domain general \
  --repo context-repository
```

完整 task CLI 合同见 [task-board](.agents/skills/task-board/SKILL.md)。

## 目录

```text
AGENTS.md                          通用协作规则
CLAUDE.md                         Claude Code 入口，import AGENTS.md
ARCHITECTURE.md                    边界与组件地图
tasks/board.yaml                   空白 task 状态索引
tasks/task.schema.json             task board 合同
scripts/task                       稳定 CLI 入口
.agents/skills/task-board/         task board 实现与测试
.agents/skills/task-plan/          plan 结构与检查器
.agents/skills/plan-go/            plan 执行与 executor/evaluator 闭环
.claude/skills/                    Claude project skill 相对软链接
docs/domains/                      domain 模板
docs/exec-plans/                   active/completed 计划目录
docs/generated/evidence/           evidence 模板
```

## 验证

```bash
scripts/check-all.sh --skip-secrets
```

如果本机已安装 Gitleaks v8.24.2，去掉 `--skip-secrets`。CI 会安装固定版本并运行完整检查。

## 初始化另一个工作区

```bash
./init.sh --target /workspace/project
```

初始化支持空目录和包含空格的路径；重复执行保持幂等。若目标文件已有不同内容，它会停止而不是覆盖。旧版 `CLAUDE.md` 和 `.claude/skills` 整体软链接会自动迁移为官方支持的 import 与逐 skill 软链接布局。

## License

MIT。
