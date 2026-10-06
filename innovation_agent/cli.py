"""CLI entry points for model-assisted and manual operation."""
import argparse
import json
import os
from pathlib import Path
import sys
from . import __version__
from . import core
from . import tasks
from .provider import generate
from .schemas import ANALYSIS_SCHEMA, BRIEF_SCHEMA, EVIDENCE_SCHEMA, ValidationError

def main(argv=None):
    parser=argparse.ArgumentParser(prog="innovation-agent",description="通用产品创新 Agent：方法 → 方向 → 证据 → 实验 → 决策")
    parser.add_argument("--version",action="version",version=__version__)
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("init",help="创建本地项目"); p.add_argument("--project",required=True); p.add_argument("--brief",required=True); p.add_argument("--evidence")
    p=sub.add_parser("prepare",help="导出完整提示词，无API调用"); p.add_argument("--project",required=True); p.add_argument("--output",required=True)
    p=sub.add_parser("run",help="调用模型并执行判断规则"); p.add_argument("--project",required=True); p.add_argument("--model",default=os.getenv("INNOVATION_MODEL")); p.add_argument("--max-output-tokens",type=int,default=10000); p.add_argument("--timeout",type=int,default=120)
    p=sub.add_parser("import-analysis",help="导入AI返回的JSON并执行规则"); p.add_argument("--project",required=True); p.add_argument("--file",required=True)
    p=sub.add_parser("add-evidence",help="追加真实反馈，原记录不覆盖"); p.add_argument("--project",required=True); p.add_argument("--file",required=True)
    p=sub.add_parser("status",help="查看阶段、证据和报告是否过期"); p.add_argument("--project",required=True)
    p=sub.add_parser("schemas",help="导出输入输出结构"); p.add_argument("--output",required=True)
    p=sub.add_parser("demo",help="运行预制合成示例，不调用模型"); p.add_argument("--project",required=True)
    sub.add_parser("agents",help="查看三个独立任务 Agent")
    sub.add_parser("doctor",help="检查本地运行条件，不发起网络请求")
    p=sub.add_parser("task",help="独立使用一个任务 Agent，不需要创建完整项目")
    p.add_argument("action",choices=["prepare","run","import","demo"])
    p.add_argument("--agent",required=True,choices=list(tasks.AGENTS))
    p.add_argument("--input"); p.add_argument("--analysis"); p.add_argument("--output"); p.add_argument("--output-dir")
    p.add_argument("--model",default=os.getenv("INNOVATION_MODEL"))
    p.add_argument("--max-output-tokens",type=int,default=6000); p.add_argument("--timeout",type=int,default=120)
    args=parser.parse_args(argv)
    try:
        if args.command=="agents":
            for key,spec in tasks.AGENTS.items(): print(key+" · "+spec["name"]+" · "+str(len(spec["methods"]))+" 张相关方法卡")
        elif args.command=="doctor":
            print(json.dumps({"version":__version__,"python":sys.version.split()[0],
                "api_key_configured":bool(os.getenv("OPENAI_API_KEY")),"model_configured":bool(os.getenv("INNOVATION_MODEL")),
                "offline_mode":True,"network_tested":False,"automatic_web_research":False},ensure_ascii=False,indent=2))
        elif args.command=="task":
            if args.action=="demo":
                if not args.output_dir: raise ValidationError("demo requires --output-dir")
                tasks.demo(args.agent,args.output_dir)
                print("合成示例已运行，未调用模型："+str(Path(args.output_dir)/"report.md"))
            else:
                if not args.input: raise ValidationError("This task requires --input")
                data=core.read_json(args.input); tasks.normalize(args.agent,data)
                if args.action=="prepare":
                    if not args.output: raise ValidationError("prepare requires --output")
                    if Path(args.output).exists(): raise ValidationError("Prompt output already exists; choose a new file")
                    tasks.export_prompt(args.agent,data,args.output); print("提示词已导出："+args.output)
                else:
                    if not args.output_dir: raise ValidationError("run/import requires --output-dir")
                    if Path(args.output_dir).exists(): raise ValidationError("Output directory already exists; choose a new run directory")
                    if args.action=="run":
                        if not os.getenv("OPENAI_API_KEY") or not args.model:
                            raise ValidationError("Set OPENAI_API_KEY and INNOVATION_MODEL, or use prepare/import")
                        system,user=tasks.build_prompt(args.agent,data)
                        a,meta=generate(system,user,args.model,os.getenv("OPENAI_API_KEY"),args.max_output_tokens,args.timeout,
                                        schema=tasks.output_schema(args.agent))
                        tasks.save_result(args.agent,data,a,args.output_dir,"api",meta)
                    else:
                        if not args.analysis: raise ValidationError("import requires --analysis")
                        tasks.save_result(args.agent,data,core.read_json(args.analysis),args.output_dir,"manual_import")
                    print("报告已生成："+str(Path(args.output_dir)/"report.md"))
        elif args.command=="init":
            core.init_project(args.project,core.read_json(args.brief),core.read_json(args.evidence) if args.evidence else [])
            print("项目已创建。下一步：prepare 或 run。")
        elif args.command=="prepare":
            core.export_prompt(args.project,args.output); print("提示词已导出："+args.output)
        elif args.command=="run":
            if not os.getenv("OPENAI_API_KEY") or not args.model: raise ValidationError("请设置 OPENAI_API_KEY 与 INNOVATION_MODEL；也可使用 prepare/import-analysis。")
            system,user=core.build_prompt(args.project)
            a,meta=generate(system,user,args.model,os.getenv("OPENAI_API_KEY"),args.max_output_tokens,args.timeout)
            r=core.commit_analysis(args.project,a,"api",meta)
            print("报告已生成："+str(Path(args.project)/"report.md")); print("Run: "+r["run_id"])
        elif args.command=="import-analysis":
            r=core.commit_analysis(args.project,core.read_json(args.file),"manual_import")
            print("导入通过，报告已生成："+str(Path(args.project)/"report.md")); print("Run: "+r["run_id"])
        elif args.command=="add-evidence":
            n=core.add_evidence(args.project,core.read_json(args.file)); print(f"已追加 {n} 条证据。请重新分析；旧报告不代表新证据下的结论。")
        elif args.command=="status": print(json.dumps(core.current_status(args.project),ensure_ascii=False,indent=2))
        elif args.command=="schemas":
            for name,s in [("brief",BRIEF_SCHEMA),("evidence",EVIDENCE_SCHEMA),("analysis",ANALYSIS_SCHEMA)]: core.write_json(Path(args.output)/(name+".schema.json"),s)
            core.write_json(Path(args.output)/"task-input.schema.json",tasks.INPUT_SCHEMA)
            for agent in tasks.AGENTS: core.write_json(Path(args.output)/(agent+"-output.schema.json"),tasks.output_schema(agent))
            print("Schemas exported")
        elif args.command=="demo":
            fixture=core.DATA/"demo"
            b=core.read_json(fixture/"brief.json"); e=core.read_json(fixture/"evidence.json"); a=core.read_json(fixture/"analysis.json")
            core.init_project(args.project,b,e); a["input_digest"]=core.digest(b,e)
            core.commit_analysis(args.project,a,"demo_fixture",{"live_api":False})
            print("合成示例已运行（未调用模型、未验证真实市场）。报告："+str(Path(args.project)/"report.md"))
        return 0
    except (ValidationError,OSError,ValueError,KeyError) as exc:
        print("错误："+str(exc),file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
