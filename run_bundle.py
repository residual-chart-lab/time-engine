"""RR64 entry: inspect current choices, execute a selected pair, verify a record."""
from pathlib import Path
import sys,argparse,json
from fractions import Fraction as Q
sys.path.insert(0,str(Path(__file__).resolve().parent/'integrations/inquiry'))
import bundle_demand as b
import bundle_execution as plant


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=('choices','run','verify'))
    p.add_argument('--mode',default='keep',choices=('keep','erase','restore'))
    p.add_argument('--x',type=Q,required=True)
    p.add_argument('--v',type=Q,default=Q(64))
    p.add_argument('--word',default='HHST',choices=b.old.WORDS)
    p.add_argument('--later-min',type=Q,default=Q(0));p.add_argument('--later-max',type=Q,default=Q(16))
    p.add_argument('--strength',type=Q,default=Q(1,1024))
    p.add_argument('--out',type=Path);p.add_argument('--record',type=Path);p.add_argument('--sha256')
    args=p.parse_args();entry=b.register(args.mode)
    def scope(v,word,obs):return b.Scope(entry.digest,args.x,v,word,args.strength,(args.later_min,args.later_max),obs)
    if args.command=='choices':
        choices=[];meter=b.fn.Meter()
        for v in (Q(-64),Q(0),Q(64)):
            for word in b.old.WORDS:
                s=scope(v,word,b.EXISTS);r=b.build(entry,s);a=b.assess(entry,s,r);z=b.resolve(entry,s,r,a,meter)
                choices.append(dict(v=str(v),word=word,allowed=z.feasible,status=z.status))
        print(json.dumps(dict(choices=choices,exact_residual_reads=meter.exact_reads,executed_flowers=0),ensure_ascii=False,indent=2));return
    s=scope(args.v,args.word,b.ACTIONS);r=b.build(entry,s);a=b.assess(entry,s,r);z=b.resolve(entry,s,r,a)
    if args.command=='verify':
        if args.record is None or args.sha256 is None:p.error('verify needs --record and the externally retained --sha256')
        actual=plant.loads(args.record.read_bytes(),args.sha256,entry,s)
        print(json.dumps(dict(verified=True,bundle_certified=actual.certified)));return
    if not z.feasible:
        print(json.dumps(dict(status=z.status,allowed=z.feasible,executed_flowers=0)));return
    if args.out is not None and args.out.exists():raise ValueError('choose a new output path')
    actual=plant.execute(entry,s,r,a,z)
    result=dict(phase='STOPPED',flowers=2,bundle_certified=actual.certified,
        local_endpoints=[str(actual.first.engine.upper.live.accumulated[0]),str(actual.second.engine.upper.live.accumulated[0])],
        bundle_endpoint=str(actual.upper_trial.live.accumulated[0]))
    if args.out is not None:
        raw,h=plant.dumps(entry,s,r,a,actual);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(raw)
        result.update(record=str(args.out),sha256=h)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
