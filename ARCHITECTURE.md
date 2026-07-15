# Coding Context Framework Architecture

Coding Context Framework 是一个 repository-native、file-based 的通用协调框架。它管理跨仓库上下文，不拥有业务实现。

## 组件

```text
AGENTS.md                          通用工作协议
tasks/board.yaml                   task 状态索引
tasks/task.schema.json             board 数据合同
scripts/task                       稳定 CLI 入口
.agents/skills/task-board/         board 行为、实现和测试
.agents/skills/task-plan/          plan 格式、检查器和测试
docs/domains/                      domain 抽象与模板
docs/exec-plans/                   active/completed 决策记录
docs/design-docs/                  验证词汇
docs/generated/evidence/templates/ evidence 模板
```

根 `scripts/task` 只委托给 skill-local 实现。CLI 通过 `AGENTS.md` 和 `tasks/board.yaml` 定位仓库根目录，变更前后校验数据，并以原子替换写回 board。

## 事实边界

框架拥有跨仓库规则、domain 路由、task 状态、plan 元数据、evidence 索引、验证词汇和模板。

目标仓库拥有业务代码、最终设计、API/schema 合同、测试、分支、worktree、commit、PR、CI、部署行为与运行证据。

## 不变量

- task board 满足 JSON Schema。
- task 和 domain 标识唯一，所有引用存在。
- 一个子任务最多一个父任务，层级无环。
- artifact 路径为仓库相对路径，不能通过 `..` 或 symlink 逃逸。
- `requirement_refs` 是唯一需求引用字段。
- active/review task 关联 plan，review/done task 关联 evidence。
- 根 board 的 task 列表为空，不包含实例或教程数据。

## 非目标

当前版本不提供 Web UI、数据库、托管同步、多写入者协调服务、telemetry、业务仓库迁移或 runtime 专用 adapter。原子写入避免半写文件，但调用方仍需自行串行化并发 mutation。
