"""Inspect omission of retained differences and run a chosen RR65 bundle."""
from pathlib import Path
import sys,argparse,json
from fractions import Fraction as Q
sys.path.insert(0,str(Path(__file__).resolve().parent/'integrations/inquiry'))
import mixed_action_sets as m
import mixed_execution as plant


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=('inspect','run','verify'))
    p.add_argument('--context',choices=('main','mixed','zero_head','outside_chart'),default='mixed')
    p.add_argument('--strength',type=Q,default=Q(1,1024))
    p.add_argument('--s-mode',choices=('keep','erase','restore'),default='keep')
    p.add_argument('--t-mode',choices=('keep','erase','restore'),default='keep')
    p.add_argument('--omit',choices=('s','t','s,t'));p.add_argument('--joint',action='store_true')
    p.add_argument('--v',type=Q,default=Q(1));p.add_argument('--word',choices=m.WORDS,default='HHHSUT')
    p.add_argument('--out',type=Path);p.add_argument('--record',type=Path);p.add_argument('--sha256')
    args=p.parse_args()
    if args.joint and args.omit:p.error('choose a joint observation or an individual omission proof')
    e=m.register(modes=(args.s_mode,args.t_mode));scope=m.Scope(e.digest,m.context(e,args.context),args.strength)
    if args.command=='inspect':
        if args.joint:
            rows=[dict(v=str(v),word=w,joint_observation_sufficient=m.joint_polynomials(m.build(e,scope,v,w)) is not None)
                for v in scope.controls for w in scope.words]
            print(json.dumps(dict(rows=rows,requested_bundle_flowers_executed=0),indent=2));return
        if args.omit is None:p.error('inspect needs --omit or --joint')
        c=m.compare(e,scope,tuple(args.omit.split(',')))
        print(json.dumps(dict(verdict=c.verdict,omission_permitted=c.verdict=='SAME',exact_retained_reads=c.reads[2],
            finite_bound_refinements=c.reads[1],candidate_verdicts=[dict(v=x[0],word=x[1],verdict=x[2]) for x in c.rows],
            requested_bundle_flowers_executed=0),indent=2));return
    certificate=None
    if args.omit:
        certificate=m.compare(e,scope,tuple(args.omit.split(',')))
        if certificate.verdict!='SAME':
            print(json.dumps(dict(status=certificate.verdict,omission_permitted=False,requested_bundle_flowers_executed=0)));return
    a=(m.joint_action(e,scope,args.v,args.word) if args.joint else m.action(e,scope,args.v,args.word,certificate))
    if args.command=='verify':
        if args.record is None or args.sha256 is None:p.error('verify needs --record and the externally retained --sha256')
        actual=plant.loads(args.record.read_bytes(),args.sha256,e,scope,args.v,args.word)
        print(json.dumps(dict(verified=True,bundle_certified=actual.certified)));return
    if a.status!='ADMISSIBLE':print(json.dumps(dict(status=a.status,requested_bundle_flowers_executed=0)));return
    if args.out is not None and args.out.exists():raise ValueError('choose a new output path')
    actual=plant.run(e,scope,a)
    result=dict(phase='STOPPED',requested_bundle_flowers=2,bundle_certified=actual.certified,exact_read_keys=a.read_keys,
        local_endpoints=[str(actual.first.engine.upper.live.accumulated[0]),str(actual.second.engine.upper.live.accumulated[0])],
        bundle_endpoint=str(actual.upper_trial.live.accumulated[0]))
    if args.out is not None:
        raw,h=plant.dumps(e,scope,actual);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(raw)
        result.update(record=str(args.out),sha256=h)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
