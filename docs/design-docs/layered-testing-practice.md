# Feedback Loop 与验证证据实践

本文定义仓库共享的验证词汇。规划和实现时，应选择能最快发现本次改动真实风险的
smallest effective feedback loop，而不是机械执行所有类别。每个结果只按实际运行的
入口和依赖命名：mock 结果不是 real API 结果，截图也不是完整 acceptance test。

本文不替代 `.agents/skills/task-plan/SKILL.md` 的 plan contract；plan 的结构、alignment、
missing-evidence policy 与 checker 规则仍以该 skill 为准。

## Outside-in 选择方法

1. 先写出用户或外部消费者可观察的验收行为，以及失败会造成的影响。
2. 优先选择能运行该行为及其关键依赖的最深可行 feedback loop：Agent eval、Real API
   E2E、Real CLI / Workflow，或在真实依赖不安全、不可用、昂贵或不稳定时使用跨组件
   integration / Mock E2E。
3. 当 broader loop 无法经济地覆盖密集分支或状态转换，或需要更快定位 cohesive module
   的行为时，再增加 module test。
4. 只有函数自身拥有有意义的行为合同、非平凡决策、重要边界/错误路径或安全不变量时，
   才增加 function-level unit test。函数存在或改动行数少，本身都不是测试理由。
5. 对纯展示或直白实现改动，使用直接 review、structural check 或已有上层行为检查，不创建
   bespoke unit test。

判断时，用户影响和失败成本高于代码行数，integration 与依赖风险高于局部实现细节；行为
密度、分支、状态和边界条件越多，focused module/unit coverage 的价值越高。圈复杂度是提示
信号，不是统一数字门槛。测试应能承受合理重构；主要锁定文案、private helper 形状或偶然
实现细节的测试通常价值较低。

典型选择：

- 改名或少量文案：direct review 加相关 structural/publication check；不新增 unit test。
- 一两行 trivial helper：若没有独立行为合同，由 enclosing module/workflow 覆盖；不因函数
  单独存在而新增测试。
- 复杂有状态模块：对状态转换、边界、错误路径和不变量做 focused module tests，并在可行时
  保留一个上层行为 loop 验证 wiring。
- 跨组件 workflow：优先 integration、Real CLI / Workflow 或适当的 Real API E2E；unit tests
  不能替代跨边界证据。
- Agent 行为变化：固定 scenario set、rubric、grader、threshold 和 runtime/model version 做
  eval；若行为依赖认证、工具、filesystem、network 或用户可见交付，再配套真实或明确标注
  的 mock workflow。eval 不能单独证明外部集成成功。

## 1. Unit / Module tests

适用范围：拥有独立行为合同或非平凡逻辑的函数、parser、状态转换、安全不变量，以及具有
受控依赖的 cohesive module 或 CLI command。它是按风险选择的工具，不是每次代码改动的
默认要求。

Proves：代表性输入和边界输入下的局部逻辑、模块内分支与错误路径符合预期。

Does not prove：跨模块 wiring、真实 filesystem integration、外部依赖或完整用户 workflow。

纯改名、copy edit、presentation metadata、简单配置展示、thin delegation、一两行直白逻辑，
以及没有独立行为合同的低复杂度 helper，通常不写专用 unit test。通过直接检查、structural
check 或相关 enclosing module/integration workflow 覆盖即可。不要为测试数量、覆盖率或固定
圈复杂度阈值制造测试；但复杂或高失败成本逻辑仍应保留 focused coverage。

## 2. evals

适用范围：难以用单一确定性断言表达的 Agent 行为、生成质量、检索质量或 rubric-based
output；应固定 dataset、rubric、grader、threshold 和运行版本。

Proves：样本与 rubric 边界内的质量达到声明的 threshold，并可比较 regression。

Does not prove：样本外泛化、在线依赖可用性、真实用户体验或完整业务 workflow。

当 Agent 声明涉及 authentication、外部工具、filesystem state、network service 或用户可见
交付时，应把 eval 与适用的 Real CLI / Workflow 或 Real API E2E 配对；真实依赖不可行时，
使用明确标注的 Mock E2E。确定性的 parser、schema 和 safety logic 仍可使用 focused module
tests。

## 3. structural checks

适用范围：JSON Schema、YAML/Markdown artifact shape、API/CLI options、output format、exit
code、plan structure、static analysis、format 与 publication policy。

Proves：producer 与 consumer 遵守稳定结构，非法输入或不允许的发布内容能被拒绝。

Does not prove：运行时语义正确、完整 workflow 已执行，或外部系统真实可用。

## 4. Mock E2E

适用范围：完整 workflow，但 service、network 或 runtime dependency 被 mock、fixture 或
interception 替代。fixture 即使由真实格式生成，也必须标注为 Mock E2E。

Proves：受控输入下的端到端 wiring 和预期 state transition 是连贯的。

Does not prove：真实 authentication、私有数据访问、deployed service 或 production behavior。

## 5. Real CLI / Workflow

适用范围：真实 public CLI、脚本或 workflow entry point，使用其实际 parser、filesystem、
schema、mutation path 与明确命名的本地依赖。例如，在临时 workspace 中执行
`init.sh` 和 `scripts/task` 属于 Real CLI / Workflow。

Proves：发布的本地入口接受文档输入，并产生文档约定的本地效果。

Does not prove：未调用的 UI、hosted API、远端认证或 deployed backend 行为。

## 6. Real API E2E

适用范围：完整 client workflow 连接到真实 API、真实 authentication 和指定环境中的真实
dependencies。必须记录 environment、关键输入、实际响应与可复现入口。

Proves：被测试用户路径确实跨过所声明的真实 API 与依赖。

Does not prove：未测试 edge cases、其他环境 parity 或未来服务状态。

Coding Context Framework 自身没有 hosted backend。除非 consuming repository 提供并实际
运行真实 API workflow，否则不得声称 Real API E2E 已通过。

## 7. Evidence / Demo

Evidence / Demo 不是测试层。它是与上述 feedback loop 绑定的 reviewable output，包括
report、command summary、screenshot、trace、reproducible evidence 或 recorded demos。

Reproducible evidence 至少记录 command 或 entry point、environment、key input、expected
result、actual result，以及可用时的 artifact path。Recorded demos 适合展示行为，但不会
提高底层验证深度：mock demo 仍只支持 Mock E2E 声明，CLI transcript 仍只支持实际运行的
Real CLI / Workflow 声明。

## Synthetic、mock 与 real 标签

- `Synthetic` 描述 data，可用于真实 local CLI run。
- `Mock` 描述被替换的 dependency。
- `Real` 表示命名的 entry point 与 dependency 确实运行。
- `Not run` 或 `Omitted` 可以是诚实结果，但必须同时给出 reason 与 residual risk。

不得从较浅 feedback loop 推断更深验证。Expected 与 Actual 分开记录；不得把 credential、
private identifier、private path 或大段 raw log 放入 evidence。

## Delivery summary

使用 `docs/generated/evidence/templates/` 下的模板，只报告实际选择或执行的 feedback loops：

```text
Validated:
- Feedback loop, command, environment, expected, actual, evidence path

Not validated:
- Relevant omitted risk, reason, recovery path

Conclusion:
- What is supported by reproducible evidence
- What remains uncertain
```
