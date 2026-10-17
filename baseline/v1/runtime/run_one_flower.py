"""Run one declared flower and optionally save its complete exact record."""
import argparse
import json
from pathlib import Path

from completed_single_flower import Configuration,run_flower,summary,export_record,encode

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branch',choices=('first','second'),default='first')
    parser.add_argument('--choice',type=int,default=0)
    parser.add_argument('--cap',type=int,default=4)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    machine=run_flower(Configuration(source_branch=args.branch,petal_choice=args.choice,search_cap=args.cap))
    if args.output and machine.record is not None:
        with args.output.open('x',encoding='utf-8') as stream:
            json.dump(export_record(machine.record),stream,ensure_ascii=False,indent=2)
            stream.write('\n')
    print(json.dumps(summary(machine),default=encode,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
