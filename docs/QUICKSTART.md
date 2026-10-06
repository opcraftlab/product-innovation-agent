> 本页是保留的完整项目模式；轻量任务请先看 [TASKS.md](TASKS.md)。

# 操作指南

## 不写代码的用法

打开根目录的 `AGENT.md`，把整份内容交给一个AI对话，随后描述你的项目。开始可以只提供：目标用户、当前做法、想改善什么、已有资料、预算和期限。AI应先指出关键缺口，再形成方向和实验。

这种方式使用同一套方法，但没有本程序的自动结构校验、证据门槛、输入摘要和本地历史。要获得这些能力，使用下面的CLI流程。

## 本地运行

1. 解压项目并打开终端，进入有 `README.md` 的目录。确认Python版本至少为3.10。
2. 运行 `python -m innovation_agent demo --project work/demo`，打开生成的 `work/demo/report.md`。
3. 复制 `examples/brief.json` 成自己的任务。不要把演示假设直接当事实；真实项目将synthetic改为false，证据按实际填写。
4. 执行README中的init、prepare、import-analysis或run命令。

Windows如无python命令，可使用 `py -m innovation_agent ...`。macOS/Linux如无python命令，可使用 `python3 -m innovation_agent ...`。

## 输入填写

- `target_stage`：explore / prototype / pilot / scale，表示本轮希望申请进入的阶段。
- `max_directions`：1–8；建议首轮3个有实质差别的方案。
- `constraints`：一票约束。status为unknown/pass/fail，由负责人提供，模型不可替改。candidate_ids用["*"]表示适用于全部方向。
- `budget`：本轮实验计划费用上限，currency写清单位。模型调用费与实际支出由使用者控制。
- `verified`：自己确认有原始记录、可查口径后才设true；不要让AI替你确认。
- `synthetic`：所有合成、示例或模拟数据设true。真实任务混有合成证据时，仅真实且核实的适用证据可能进入判断。
- `dimensions`：fit/demand/difference/experience/feasibility/economics/communication/channel。
- `candidate_ids`：此条证据适用于哪些方向。扩大投入所需交易、持续使用和交付记录必须指向具体方向，不能只填通配符。

精确字段以 `schemas/` 为准。JSON不允许注释；缺证据时用空数组，不补造。

## API模式

在本机安全设置OPENAI_API_KEY与INNOVATION_MODEL。模型需支持Responses API和Structured Outputs；模型名由账号实际可用范围确定，项目不硬编码某个最新模型。每次run只有一次请求，默认输出上限10,000 tokens；接口拒绝、输出不完整或校验失败不会自动多次请求。

`store=false`是请求参数，不等于所有服务侧保留或处理均不存在。API模式会发送项目任务、证据摘要与前次分析；程序不上传未指定的本地PDF或扫描目录。

## 查看与迭代

- `report.md`：当前可读报告。
- `latest.json`：最近一次成功分析、输入快照与门槛结果。
- `history/`：所有成功运行的JSON与报告。
- `status`：输入是否与最近分析一致。stale代表需要重新分析。

追加证据不能重用旧ID。修订证据时使用新ID，并在statement明确纠正哪条及原因；若旧条目失实，应在本地evidence.json将其verified设false，并保留历史里的原快照。修改brief或evidence会让旧输出摘要失效。

## 常见错误

|提示|原因与动作|
|---|---|
|目录非空|避免覆盖已有项目；使用新目录|
|digest mismatch|回答对应旧输入；重新prepare或run|
|unknown evidence IDs|AI引用了台账外记录；修正或补录真实证据后重新分析|
|duplicate IDs|使用新ID，或核对是否重复导入|
|API HTTP 401/403|检查密钥与模型权限，勿粘贴密钥到反馈|
|API HTTP 429|检查限额，确认用量后决定是否重试|
|not completed|输出可能达到上限或中断；减少方向/输入或调整上限|

API未接入时仍可用prepare/import-analysis。离线示例只检验程序流程；不代表实时模型质量。
