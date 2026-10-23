"""RR66: step an adaptive request, keep every snapshot, normally stop."""
from pathlib import Path
from fractions import Fraction as Q
import sys,argparse,json
sys.path.insert(0,str(Path(__file__).resolve().parent/'integrations/inquiry'))
import adaptive_resolution as a
import adaptive_session as live
import rr66_study as study


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=('demo','start','choose','resolve','revise','execute','verify'))
    p.add_argument('--context',choices=('mixed','main','zero_head','outside_chart'))
    p.add_argument('--strength',type=Q)
    p.add_argument('--initial-context',default='mixed',choices=('mixed','main','zero_head','outside_chart'))
    p.add_argument('--initial-strength',type=Q,default=Q(0))
    p.add_argument('--s-mode',choices=('keep','erase','restore'),default='keep')
    p.add_argument('--t-mode',choices=('keep','erase','restore'),default='keep')
    p.add_argument('--max-features',type=int,choices=(0,1,2))
    p.add_argument('--v',type=Q,default=Q(1));p.add_argument('--word',choices=a.m.WORDS,default='HHHSUT')
    p.add_argument('--record',type=Path);p.add_argument('--sha256');p.add_argument('--out',type=Path)
    p.add_argument('--out-dir',type=Path,default=Path('.work/adaptive-demo'))
    args=p.parse_args()
    if args.command=='demo':
        if args.out_dir.exists():raise ValueError('choose a new demo directory')
        entry=a.register((args.s_mode,args.t_mode));spec=json.loads((study.HERE/'RR66-inputs.json').read_bytes())
        case=next(x for x in spec['scenarios'] if x['name']=='product-to-port')
        session,trace,stages=study.scenario(entry,case)
        args.out_dir.mkdir(parents=True);items=[]
        for index,stage in enumerate(stages):
            raw,h=live.dumps(stage);path=args.out_dir/('stage-'+str(index).zfill(2)+'.json');path.write_bytes(raw)
            items.append(dict(path=str(path),phase=stage.phase,sha256=h))
        (args.out_dir/'manifest.json').write_bytes((json.dumps(dict(trace=trace,snapshots=items),indent=2)+'\n').encode())
        print(json.dumps(dict(phase=session.phase,certified=session.result.certified,trace=trace,final=items[-1]),indent=2));return
    if args.command!='verify':
        if args.out is None:p.error('a new --out snapshot path is required')
        if args.out.exists():raise ValueError('snapshots are not overwritten')
    entry=a.register((args.s_mode,args.t_mode))
    if args.command=='start':
        scope=study.scope(entry,args.context or 'mixed',args.strength if args.strength is not None else 0)
        session=live.start(entry,scope,a.Policy(args.max_features if args.max_features is not None else 2))
    else:
        if args.record is None or args.sha256 is None:p.error('--record and its externally retained --sha256 are required')
        initial=study.scope(entry,args.initial_context,args.initial_strength)
        session=live.loads(args.record.read_bytes(),args.sha256,entry,initial)
        if args.command=='choose':session=live.choose(session,args.v,args.word)
        elif args.command=='resolve':session=live.resolve(session)
        elif args.command=='revise':
            if args.context is None or args.strength is None:p.error('revise needs an explicit --context and --strength')
            policy=session.policy if args.max_features is None else a.Policy(args.max_features)
            session=live.revise(session,study.scope(entry,args.context,args.strength),policy)
        elif args.command=='execute':session=live.execute(session)
        elif args.command=='verify':print(json.dumps(dict(verified=True,state=live.view(session)),indent=2));return
    raw,h=live.dumps(session);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(raw)
    print(json.dumps(dict(state=live.view(session),path=str(args.out),sha256=h),indent=2))


if __name__=='__main__':main()
