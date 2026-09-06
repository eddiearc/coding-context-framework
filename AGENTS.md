# AGENTS.md - Coding Context Framework

本仓库是通用编码上下文框架，用于沉淀跨任务、跨仓库的索引、计划、证据入口和协作规则。它只定义抽象机制，不附带任何用户、组织、业务域或真实任务内容。

## 仓库定位

- 本仓库保存协调上下文，不承载生产业务代码。
- `tasks/board.yaml` 是 task 状态索引权威，但不是实现事实源。
- 业务代码、测试、API 合同、PR、CI、部署、日志和外部需求系统仍是对应事实源。
- 聊天历史、agent memory、prompt cache 和本机临时状态只能提供线索，继续工作前必须回到可审计事实源核验。
- 不复制目标仓库中容易漂移的实现事实；使用仓库相对路径、PR/issue、命令或证据入口引用它们。

## 必读顺序

1. 本文件和 `ARCHITECTURE.md`。
2. `scripts/task list --tree` 与相关 `scripts/task show <task-id>`。
3. 对应 `docs/domains/<domain>.md`。
4. 已登记的 active plan。
5. 目标仓库自己的规则、合同、代码和测试。
6. 目标仓库提供的同域 skill；仓库策略优先于通用能力。

更靠近代码的规则优先。

## Task Board

- 普通 task 变更必须通过 `scripts/task`，不要手改 `tasks/board.yaml`。
- 未规划工作可登记为 `backlog`；只有存在具体阻塞时才使用 `blocked` 并记录 blocker。
- `active` 和 `review` task 必须关联 plan；`review` 和 `done` 必须关联 evidence。
- 子任务只能有一个父任务，禁止悬空、自引用和循环。
- 修改后运行 `scripts/task validate`。
- CLI 不支持普通状态操作时，先扩展 skill-local 实现与测试，再通过根入口执行。

## Plan 与执行门禁

- 复杂任务或包含多个步骤的任务使用 `.agents/skills/task-plan/SKILL.md`，plan 放在 `docs/exec-plans/active/`。
- Aligned plan 必须登记到 task board 后才能执行。
- Draft plan 只能对应 `blocked` task。
- Plan 描述范围、合同、验证和证据边界，不替代实现事实。
- 复用 `Goal / Scope` 中的 `In scope`、`Out of scope` 和既有完成条件控制交付边界，不为此增加新的必填字段。边界外发现默认记录为 follow-up；只有直接阻止本次交付，或存在安全、数据损坏风险时才扩大范围，并明确记录原因。
- 具体实现必须在目标业务仓库的独立 git worktree 中完成（每 session / 每任务一个），不共享主 checkout 的工作区与 HEAD；主 checkout 只用于同步 main 与只读查阅。

## Optional Herdr workflow

- Herdr 是可选集成。未安装或不在 Herdr pane 内时，task/plan 核心流程保持可用。
- 使用 Herdr 前先读 `.agents/skills/herdr-workflow/SKILL.md` 与 `docs/agent-routing.md`。固定六场景 rubric 见 `.agents/skills/herdr-workflow/references/evaluation.md`。
- 命令语法以已安装的 `herdr --skill` 与 CLI help 为准；不要为了探路运行无参数的 `herdr`。
- 任何 live inspect 或 control 之前先确认 `HERDR_ENV=1`。否则只报告前置条件，不检查或控制任何 Herdr session。
- Agent kind 与 model 必须在启动前由用户在 routing 或当前 session 中明确选择；model 也可以是用户明确指定的 CLI default。未填写的 `TODO` 不能当成静默默认模型。框架不指定必选模型，也不默认 yolo。
- 实现交接前必须已有已登记且 aligned 的 plan。等待必须带 timeout；只清理本 handoff 创建的 pane，且放在证据落盘之后。
- 规划按任务复杂度比例进行，不强制规划模型或规划步骤。
- 同一 task 留在调用方 tab，用 pane split；每个 writer 使用独立目标仓 worktree。
- `idle` / `done` 只表示传输生命周期，不是 task 验收；`unknown` / timeout 不能证明完成，也不能作为重复启动的理由。
- 独立 evaluator 必须是另一个 agent；可以使用与 executor 相同的 model。

## 验证与证据

- 改代码前先读相关测试，改后运行最小但有效的目标仓库验证。
- 从用户或外部消费者可观察的验收行为开始，优先选择能覆盖该行为及其关键依赖的最深可行 feedback loop：按需使用 evals、Real API E2E、Real CLI / Workflow、跨组件 integration 或 Mock E2E，而不是默认从函数级 unit test 开始。
- 仅在 cohesive module、非平凡分支或状态转换、边界与错误路径、安全不变量或高回归成本逻辑需要快速诊断时增加 Unit / Module tests。纯改名、少量文案、展示元数据、简单配置展示、薄委托、一两行直白逻辑，以及没有独立行为合同的低复杂度 helper，默认不新增专用 unit test；使用直接检查、structural check 或已有上层 workflow 覆盖。
- 圈复杂度只是测试投入信号之一，不是机械阈值；同时考虑用户影响、行为密度、依赖边界、失败成本，以及测试是否主要锁定私有实现。Agent 行为变化优先使用固定场景、rubric、grader、threshold 和版本可复现的 eval；若声明涉及认证、外部工具、文件系统、网络服务或用户可见交付，再配套相应 Real CLI / Workflow 或 Real API E2E。
- 为实际运行的 feedback loop 保留 reproducible evidence 或 recorded demos；Evidence / Demo 是证据载体，不是测试层，也不会提升底层验证深度。
- mock、synthetic、local CLI 和真实后端结果必须准确标注。
- 真实 HTTP/CLI/workflow 或外部服务集成测试入口应提交到目标仓库并默认 skip，避免 CI 默认请求真实依赖。
- 交付说明记录命令、环境、关键输入、实际结果、跳过原因和剩余风险。

## 安全

- 不提交 token、cookie、私钥、凭证、真实用户敏感数据、大段原始日志或本机临时缓存。
- 不回滚用户已有未提交改动。
- 部署、外部发送、权限修改和不可逆操作遵守目标仓库与用户授权边界。

## 交付前

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m unittest discover -s .agents/skills/task-board/tests -p 'test_*.py' -v
python3 -m unittest discover -s .agents/skills/task-plan/tests -p 'test_*.py' -v
python3 -m unittest discover -s .agents/skills/plan-go/tests -p 'test_*.py' -v
scripts/check-context.sh
scripts/check-publication.sh
git diff --check
```

若 Gitleaks v8.24.2 可用，再运行 `scripts/check-secrets.sh`。
