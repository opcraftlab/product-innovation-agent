"""Check shipped fixtures, schemas, entry files and local documentation links."""
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from innovation_agent import core,tasks

def main():
    errors=[]
    for agent in tasks.AGENTS:
        for name in [f'agents/{agent}/AGENT.md',f'innovation_agent/data/agents/{agent}.md',
                     f'examples/tasks/{agent}.input.json',f'examples/tasks/{agent}.output.json',
                     f'examples/tasks/{agent}.report.md']:
            if not (ROOT/name).is_file(): errors.append('Missing: '+name)
        inp=core.read_json(ROOT/f'examples/tasks/{agent}.input.json')
        out=core.read_json(ROOT/f'examples/tasks/{agent}.output.json')
        tasks.evaluate(agent,inp,out)
        for suffix in ['input','output']:
            public=core.read_json(ROOT/f'examples/tasks/{agent}.{suffix}.json')
            packaged=core.read_json(core.DATA/f'task_examples/{agent}.{suffix}.json')
            if public!=packaged: errors.append(agent+': example and packaged fixture differ')
        if core.read_json(ROOT/f'schemas/{agent}-output.schema.json')!=tasks.output_schema(agent):
            errors.append(agent+': output schema is stale')
    if core.read_json(ROOT/'schemas/task-input.schema.json')!=tasks.INPUT_SCHEMA:
        errors.append('Task input schema is stale')
    for folder in [ROOT/'docs',ROOT/'agents']:
        for p in folder.rglob('*.md'):
            for url in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
                if '://' in url or url.startswith('#') or '{' in url: continue
                if not (p.parent/url.split('#',1)[0]).exists(): errors.append(f'{p.relative_to(ROOT)}: missing link {url}')
    for filename in ['README.md','README.en.md']:
        p=ROOT/filename
        for url in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if '://' not in url and not url.startswith('#') and not (p.parent/url.split('#',1)[0]).exists():
                errors.append(filename+': missing link '+url)
    if errors:
        print('\n'.join(errors),file=sys.stderr);return 1
    print('PASS: task fixtures, packaged resources, schemas, entry files, documentation links')
    return 0

if __name__=='__main__': raise SystemExit(main())
