"""Standalone offline developer CLI."""
import argparse
import json
import sys
from pathlib import Path
from .engine import run_scenario
from .matrix import run_matrix
from .assurance import audit_warranty, compare_warranties, verify_recovery
from .incident import replay_incident
from .report import markdown


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def main(argv=None):
    parser=argparse.ArgumentParser(prog='intentproof',description='Test intent contracts, fault scenarios and semantic safety drift')
    subs=parser.add_subparsers(dest='command',required=True)
    for action in ('run','matrix','audit','diff','recovery','incident','report'):
        cmd=subs.add_parser(action)
        cmd.add_argument('file',help='Scenario, warranty, or report JSON')
        if action=='diff': cmd.add_argument('new',help='New warranty JSON file')
        cmd.add_argument('--output','-o',help='Optional report file path')
        cmd.add_argument('--format',choices=['json','markdown'],default='json',help='Report output format')
        if action=='run':cmd.add_argument('--strict',action='store_true')
        if action=='audit':cmd.add_argument('--inventory',help='Optional JSON state inventory or scenario with initial_state')
    args=parser.parse_args(argv)
    try:
        data=load(args.file)
        if args.command=='run':
            original=run_scenario(data)
            test_assertion=('PASS' if original['expected_matched'] is True else
                            'FAIL' if original['expected_matched'] is False else 'NOT_SPECIFIED')
            report={**original,'workflow':{'outcome':original['outcome']},
                    'test':{'assertion':test_assertion,
                            'reproduced_expected_failure':bool(original['expected_matched'] and original['outcome'] not in ('VERIFIED','RECOVERED'))}}
        elif args.command=='matrix': report=run_matrix(data)
        elif args.command=='audit':
            inv=load(args.inventory) if args.inventory else None
            if isinstance(inv,dict) and 'initial_state' in inv:inv=inv['initial_state']
            report=audit_warranty(data.get('warranty',data),inv)
        elif args.command=='diff':report=compare_warranties(data,load(args.new))
        elif args.command=='incident':report=replay_incident(data)
        elif args.command=='report':report=data
        else:
            obj=data.get('recovery_proof',data)
            report=verify_recovery(obj['before'],obj['after'],obj['allowed_changes'],obj.get('postconditions'))
        rendered=markdown(report) if args.format=='markdown' else json.dumps(report,ensure_ascii=False,indent=2)
        if args.output:Path(args.output).write_text(rendered+'\n',encoding='utf-8')
        print(rendered)
        if args.command=='incident':return 0 if report['reproducible'] else 1
        if args.command=='diff':return 1 if report['verdict']=='BREAKING' else 0
        if args.command=='audit':return 1 if report['survived'] or not report['baseline_consistent'] else 0
        if args.command=='recovery':return 1 if not report['verified'] else 0
        if args.command=='run':
            if report['expected_matched'] is False:return 1
            if args.strict and report['outcome'] not in ('VERIFIED','RECOVERED'):return 1
        return 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('intentproof error: '+str(exc),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
