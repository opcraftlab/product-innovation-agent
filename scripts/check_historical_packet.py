"""Audit a source ledger before exporting a historical prompt (standard library).

This checks declared dates and roles, not truth, prompt semantics, or model memory.
Retrospective reconstruction requires an explicit flag and can never be strict.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import sys

def parse_day(value):
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError('Expected YYYY-MM-DD')
    result = date.fromisoformat(value)
    if result.isoformat() != value:
        raise ValueError('Expected YYYY-MM-DD')
    return result

def audit(packet, allow_reconstruction=False):
    cutoff = parse_day(packet['cutoff'])
    items = packet['items']
    if not isinstance(items, list) or not items:
        raise ValueError('items must be a nonempty list')
    errors, warnings, seen = [], [], set()
    count = 0
    for item in items:
        cid = item['id']
        if not isinstance(cid, str) or not cid.strip() or cid in seen:
            raise ValueError('Invalid or duplicate source item ID')
        seen.add(cid)
        role = item['role']
        if role not in ('input', 'heldout', 'excluded'):
            raise ValueError('Invalid role')
        basis = item['basis']
        if basis not in ('contemporaneous', 'retrospective_reconstruction'):
            raise ValueError('Invalid basis')
        for field in ('statement', 'source'):
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError('Missing '+field)
        available = parse_day(item['source_available_at']) if item['source_available_at'] is not None else None
        event = parse_day(item['event_date']) if item['event_date'] is not None else None
        if role != 'input':
            continue
        count += 1
        if event and event > cutoff:
            errors.append(cid+': future event cannot be input')
        if basis == 'retrospective_reconstruction':
            warnings.append(cid+': reconstructed background, not proven available at cutoff')
            if not allow_reconstruction:
                errors.append(cid+': reconstruction requires --allow-reconstruction')
        elif available is None or available > cutoff:
            errors.append(cid+': source was not demonstrably available at cutoff')
    if not count:
        errors.append('No input items')
    return {'passed': not errors, 'strict_asof_input': not errors and not warnings,
            'input_items': count, 'errors': errors, 'warnings': warnings,
            'scope': 'Declared ledger dates only; no verification of facts, prompt isolation, or model training contamination.'}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=Path)
    p.add_argument('--allow-reconstruction', action='store_true')
    args=p.parse_args(argv)
    try:
        result=audit(json.loads(args.manifest.read_text(encoding='utf-8')),args.allow_reconstruction)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({'passed':False,'error':str(exc)},ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1

if __name__=='__main__': sys.exit(main())
