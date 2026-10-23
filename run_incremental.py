"""RR67: revise requests, reuse certified projections, execute and resume."""
from pathlib import Path
from fractions import Fraction as Q
from dataclasses import asdict
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'integrations/inquiry'))
import incremental_resolution as a
import incremental_session as live
import rr67_study as study


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('demo','start','choose','resolve','revise','execute','verify'))
    contexts=('mixed','main','zero_head','outside_chart','main_perturbed')
    p.add_argument('--context',choices=contexts);p.add_argument('--strength',type=Q)
    p.add_argument('--domain',choices=('wide','zero'))
    p.add_argument('--initial-context',choices=contexts,default='mixed');p.add_argument('--initial-strength',type=Q,default=Q(0))
    p.add_argument('--initial-domain',choices=('wide','zero'),default='wide')
    p.add_argument('--max-features',type=int,choices=(0,1,2))
    p.add_argument('--s-mode',choices=('keep','erase','restore'),default='keep');p.add_argument('--t-mode',choices=('keep','erase','restore'),default='keep')
    p.add_argument('--v',type=Q,default=Q(1));p.add_argument('--word',choices=a.m.WORDS,default='HHHSUT')
    p.add_argument('--record',type=Path);p.add_argument('--sha256');p.add_argument('--out',type=Path)
    p.add_argument('--out-dir',type=Path,default=Path('.work/incremental-demo'))
    args=p.parse_args();entry=a.register((args.s_mode,args.t_mode))
    if args.command=='demo':
        if args.out_dir.exists():raise ValueError('choose a new demo directory')
        spec=json.loads((study.HERE/'RR67-inputs.json').read_bytes())['sequences'][0]
        first=spec['requests'][0];session=live.start(entry,study.scope(entry,*first[:3]),a.Policy(first[5]))
        stages=[session];trace=[]
        for index,(name,strength,domain,v,word,budget) in enumerate(spec['requests']):
            if index:session=live.revise(session,study.scope(entry,name,strength,domain),a.Policy(budget));stages.append(session)
            session=live.choose(session,v,word);work=asdict(entry._receipts[-1][1]);stages.append(session)
            session=live.resolve(session);stages.append(session)
            trace.append(dict(revision=session.revision,context=name,domain=domain,mode=session.prepared.plan.mode,
                status=session.prepared.action.status,work=work,reads=live.history(session)[-1]))
        session=live.execute(session);stages.append(session);args.out_dir.mkdir(parents=True)
        records=[]
        for index,stage in enumerate(stages):
            raw,h=live.dumps(stage);path=args.out_dir/('stage-'+str(index).zfill(2)+'.json');path.write_bytes(raw)
            records.append(dict(path=str(path),phase=stage.phase,sha256=h))
        (args.out_dir/'manifest.json').write_bytes((json.dumps(dict(trace=trace,snapshots=records),indent=2)+'\n').encode())
        print(json.dumps(dict(phase=session.phase,certified=session.result.certified,final=records[-1]),indent=2));return
    if args.command!='verify' and (args.out is None or args.out.exists()):p.error('a new --out path is required')
    if args.command=='start':session=live.start(entry,study.scope(entry,args.context or 'mixed',args.strength or Q(0),args.domain or 'wide'),
        a.Policy(2 if args.max_features is None else args.max_features))
    else:
        if args.record is None or args.sha256 is None:p.error('--record and external --sha256 are required')
        session=live.loads(args.record.read_bytes(),args.sha256,entry,study.scope(entry,args.initial_context,args.initial_strength,args.initial_domain))
        if args.command=='choose':session=live.choose(session,args.v,args.word)
        elif args.command=='resolve':session=live.resolve(session)
        elif args.command=='revise':
            if args.context is None or args.strength is None:p.error('revise requires explicit context and strength')
            domain=args.domain or ('zero' if session.scope.domain==(0,0) else 'wide')
            policy=session.policy if args.max_features is None else a.Policy(args.max_features)
            session=live.revise(session,study.scope(entry,args.context,args.strength,domain),policy)
        elif args.command=='execute':session=live.execute(session)
        elif args.command=='verify':print(json.dumps(dict(verified=True,state=live.view(session)),indent=2));return
    raw,h=live.dumps(session);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(raw)
    print(json.dumps(dict(state=live.view(session),sha256=h,path=str(args.out)),indent=2))


if __name__=='__main__':main()
