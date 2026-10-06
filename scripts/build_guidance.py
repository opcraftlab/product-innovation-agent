"""Generate all copyable entry points from the same packaged method sources."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from innovation_agent import __version__, guidance


def generated_files():
    title = "AI 产品创意评估与验证助手 / AI Product Idea Validator"
    intro = (f"{title}\n项目资料版本：{__version__}（公开试用版）\n"
             "本文件是固定版本，不会自动更新项目设置或其他副本。\n"
             "项目中保留一个生效版本；方法示例均为虚构练习。\n")
    full = intro + "\n可复制的项目指令\n\n" + guidance.read("project_instructions.txt")
    full += "\n\n一、项目指令\n\n" + guidance.read("project.md") + "\n\n二、完整工作模块\n"
    for agent, (letter, name, _) in guidance.TASK_NAMES.items():
        full += (f"\n===== 模块{letter}：{name}：开始 =====\n\n{guidance.module(agent)}"
                 f"\n\n===== 模块{letter}：{name}：结束 =====\n")
    full += "\n三、输出验收与纠偏\n\n" + guidance.read("quality.md") + "\n"
    products = {
        "AGENT.md": "# " + full,
        "chatgpt/PROJECT_KNOWLEDGE.txt": full,
        "chatgpt/PROJECT_INSTRUCTIONS.txt": guidance.read("project_instructions.txt") + "\n",
        "docs/INNOVATION_MECHANISMS.md": "# 六种创新机制\n\n" + guidance.mechanism_reference() +
            "\n\n## 通用机制练习\n\n" + guidance.read("exercises.md") + "\n",
    }
    for agent, (_, name, english) in guidance.TASK_NAMES.items():
        sections = ["opportunity", "concept"] if agent == "opportunity" else [agent]
        content = f"# {name} / {english}\n\n版本：{__version__} · 公开试用版。\n\n"
        content += "复制本文件到新对话，提供目标和背景；默认中文表格，无需JSON。\n\n"
        content += guidance.read("project.md") + "\n\n"
        content += "\n\n".join(guidance.module(key) for key in sections)
        if agent != "validation":
            content += ("\n\n用户问下一步时，每个未停止方向给一个对应关键机制的小测试，"
                        "包含现方案对照、观察指标与何时调整或停止。"
                        "用户明确要求执行计划时再补样本、费用、期限和负责人；未知写待确认。")
        content += "\n\n" + guidance.read("quality.md")
        content += ("\n\n对话模式依赖模型遵循指令，不会运行Python结构、引用或预算检查。"
                    "显式调用CLI时按随附Schema输出；机会入口在一次调用内覆盖A+B的机制草案。\n")
        products[f"agents/{agent}/AGENT.md"] = content
        products[f"innovation_agent/data/agents/{agent}.md"] = guidance.structured_task_rules(agent)
    return products


def check():
    return [name for name, text in generated_files().items()
            if not (ROOT / name).is_file() or (ROOT / name).read_text(encoding="utf-8") != text]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        stale = check()
        if stale:
            print("Stale generated guidance: " + ", ".join(stale), file=sys.stderr)
            return 1
        print("PASS: project, standalone and API guidance use the same method sources")
        return 0
    for name, text in generated_files().items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print("Generated project, standalone and API guidance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
