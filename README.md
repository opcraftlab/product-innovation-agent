# AI 产品创意评估与验证助手 / AI Product Idea Validator

有一个产品想法，值得尝试吗？用 AI 发现机会、比较方案，制定低成本验证计划。

三个独立任务：找产品机会、把想法变成方案、评估方向与设计验证。输出可比较的候选、判断依据、资源假设、风险和下一步动作。适用于实体产品、数字产品与服务。

**v0.2.0a1 · 公开试用版。方法、程序检查和离线工作流程已交付；API真实联调与外部使用反馈持续完善。**

团队根据自身资金、人员、时间、供应链和执行能力决定是否尝试。Agent交付决策支持；终端市场验证发生在团队实际执行之后，商业成功不是本工具开源发布的前置条件。

[English](README.en.md) · [发布自查](docs/RELEASE_READINESS.md) · [更新记录](CHANGELOG.md)

## 选一个任务开始

|入口|你提供什么|你获得什么|
|---|---|---|
|[找产品机会](agents/opportunity/AGENT.md)|任务目标、品类或用户背景，可附研究材料|机会假设、替代做法、依据与研究缺口|
|[把想法变成方案](agents/concept/AGENT.md)|一个机会或已有想法|价值主张、必须功能、不做范围、原型测试|
|[评估方向与设计验证](agents/validation/AGENT.md)|一个或多个候选方案，可附证据、预算与约束|逐项判断、风险、实验优先级、继续／调整／停止依据|

每个入口可以直接使用，无需先跑其他两个。默认每次只调用一个模型，不配置多 Agent 自动对话或后台协作。

**不写代码：** 打开上述任意 AGENT.md，复制到你使用的 AI 对话，再提供任务。此模式依赖模型遵循指令，没有程序自动核查。

**需要自动核查：** 使用下面的 Python CLI。运行核心只用标准库，Python 3.10+，不需要安装依赖。

## 先跑演示

在解压后的项目根目录执行：

```bash
python -m innovation_agent agents
python -m innovation_agent task demo --agent validation --output-dir work/validation-demo
```

打开 `work/validation-demo/report.md`。这是预制合成输入输出，不调用模型，不代表市场验证。再次运行请使用新目录。

机会发现和产品定义只需两个字段：

```json
{"goal":"寻找居家办公整理线材的产品机会","context":"先形成假设；暂无访谈或购买数据。"}
```

方向验证另需 `candidates`，每项包含 `id`、`title`、`description`。参考 [输入示例](examples/tasks/validation.input.json)。合成示例始终保留 synthetic=true；自己的真实任务可省略此字段，但不能把合成反馈改标为真实记录。

## 两种运行方式

无 API 密钥：导出提示词，交给你使用的 AI，保存返回的 JSON，再导入检查。

```bash
python -m innovation_agent task prepare --agent validation --input examples/tasks/validation.input.json --output work/prompt.md
python -m innovation_agent task import --agent validation --input examples/tasks/validation.input.json --analysis answer.json --output-dir work/run-001
```

有 API 环境：先设置 `OPENAI_API_KEY` 与 `INNOVATION_MODEL`，选择账号支持 Responses API 和 Structured Outputs 的模型。

```bash
python -m innovation_agent doctor
python -m innovation_agent task run --agent validation --input examples/tasks/validation.input.json --output-dir work/run-api-001
```

API 运行会发送本轮输入材料并产生费用。每次一次请求，不自动重试，默认输出上限 6000 tokens；token 上限不是金额上限。`doctor` 不验证网络或账号权限。API路径尚未用真实密钥联调。

输出包括可读的 `report.md` 和保留输入、分析、核查、版本与调用元数据的 `result.json`。修改输入或加入证据后重新运行到新目录，旧分析不能用于新输入。

## 判断边界

- 机会与概念始终标为待验证假设。
- 方向验证默认检查需求、差异、可行性、经济性，也可显式选择维度。
- 模拟、未核实、错方向、错维度的证据不能让相应判断通过；真实反证要求重新考虑方案。
- 硬约束失败的方向不能消失，也不能继续分配实验费用。程序检查所有实验预算合计。
- 引用存在及类型匹配不证明语义正确；verified 是输入者声明，程序不联网核实。
- 所选维度满足记录条件，不等于立项、量产、扩大投入或市场成功。

本版不自动联网检索、不自动执行访谈投放、不训练或微调模型。这里的“方向验证”是审查已有证据并设计下一步验证，不是在文字中证明需求成立。团队负责投入、执行和结果回填；Agent可据此继续复盘。

## 方法与文档

- [方法论与18张方法卡](docs/METHODOLOGY.md)、[方法组件与实现](docs/METHOD_DESIGN.md)
- [三个入口操作指南](docs/TASKS.md)、[完整项目模式](docs/QUICKSTART.md)
- [判断体系](docs/JUDGMENT.md)、[架构决定与同类参考](docs/ARCHITECTURE.md)
- [评测方案及用例](docs/EVALUATION.md)、[历史案例重演与日期审查](docs/HISTORICAL_EVALUATION.md)、[已执行测试](docs/TEST_RESULTS.md)
- [试用与商业化路径](docs/COMMERCIALIZATION.md)、[贡献](CONTRIBUTING.md)
- [GitHub发布](docs/GITHUB.md)、[交接说明](docs/HANDOFF.md)

v0.1 的完整项目模式保留用于需要历史和阶段评审的任务；新用户从上方三个独立入口开始。

## 开发与发布

```bash
python -m unittest discover -s tests -v
python scripts/check_release.py
```

可选 `python -m pip install .` 后使用 `innovation-agent` 命令。源代码与项目文档采用 [MIT](LICENSE)。发布包包含代码、通用方法、文档及自拟合成示例。实际业务记录和密钥由使用者保存在自己的环境中。

GitHub 提供源码、版本和协作；上传源码不会自动托管运行服务。公开仓库：[opcraftlab/product-innovation-agent](https://github.com/opcraftlab/product-innovation-agent)。2026-10-06 已发布源码，GitHub Actions 的 Python 3.10／3.12 检查均通过。
