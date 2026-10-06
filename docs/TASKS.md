# 独立任务指南

## 选择与输入

opportunity：从资源与任务找机会，同时形成具体机制草案（一次调用内A+B）。concept：我有方向，需要形成或完善方案。validation：我有候选，需要比较、测试或复盘。

项目对话中的创新探索使用A+B；同时问下一步时再接C最小建议。CLI保持显式单任务选择，不自动发起额外调用。

每个任务输入JSON只强制 goal 与 context；validation另需非空 candidates。其余字段可选：

|字段|作用与默认|
|---|---|
|candidates|id/title/description；验证最多8个候选，全部保留评审|
|evidence|证据数组，默认空；结构见 schemas/evidence.schema.json|
|max_results|机会／概念最多几个结果，默认3，上限8；验证始终覆盖全部候选|
|dimensions|仅验证可选，默认 demand/difference/feasibility/economics|
|budget、currency|一起提供；缺失标“未确认”，不会自动变成零预算|
|constraints|id/description/status/candidate_ids；status为unknown/pass/fail，*表示全部候选|
|synthetic|演示时true；标记整个任务的结果仅用于演示|

证据字段包括来源、日期、样本、类型、支持的维度与候选。已有记录保持不变，修正作为新记录并说明关系；新一轮输入可包含上轮结果摘要，但不能把摘要当新增证据。一般背景用 candidate_ids=["*"]，针对某候选则用它的输入ID。

证据类型、日期和适用范围会检查；verified标记需要输入者完成核实。当前版本不自动去重同源报道，不判定自由文本是否真的支持主张，需人工复核。

## 完整离线运行

```bash
python -m innovation_agent task prepare --agent concept --input examples/tasks/concept.input.json --output work/concept-prompt.md
```

把生成文件交给一个AI，保存其返回的JSON为 `answer.json`，保留input_digest。然后：

```bash
python -m innovation_agent task import --agent concept --input examples/tasks/concept.input.json --analysis answer.json --output-dir work/concept-run
```

不需要其他两个Agent的输出。不接受仅一张截图或PDF路径作为结构化证据；先由宿主AI/用户读取材料并转换成输入。本CLI不自带OCR和PDF解析。

## 读懂结果

机会／概念每条包含innovation依据链：基线、矛盾、机制ID、机制解释、实现方式、用户变化、购买理由、能力状态、代价、反证、变化类型。程序只检查结构与标识，不判定新颖性或技术真实性。没有可交付方向时允许空列表。

机会／概念仅产生 hypothesis_only 或 demo_only。验证可能是 stop、rework、research、selected_checks_supported 或 demo_only。最后一种实证状态只针对所选维度；不会批准商业行动。

费用是实验费用估计，与API费用分开。budget_status为exceeded时必须调整组合，not_set时确认币种与预算；本工具从不执行费用支出。

分析失败会返回非零退出码，不保存有效报告。输入改变后旧input_digest不再通过。输出目录已存在时拒绝覆盖，也会在API调用前拒绝，避免无意义付费。

## 组合与批量

可把机会输出中的场景问题复制为产品定义背景，把产品概念整理为验证的 candidates。不同任务之间的输出是待复核假设，不自动升级成事实。

单次最多8个候选；超过8个由用户按共同市场／场景分批。没有自动并发或跨批次排名，跨批次比较需统一证据标准与预算。完整模式保留历史台账；轻量模式每轮独立保存结果，版本比较由用户复核。

## v0.3迁移

旧输入可以沿用，旧输出需重新生成。不要仅修改input_digest绕过版本检查。项目用户上传chatgpt/PROJECT_KNOWLEDGE.txt并保存PROJECT_INSTRUCTIONS.txt中的指令，移除旧版副本。固定上传文件不会自动同步。
