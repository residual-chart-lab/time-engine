"""RR68: inspect constructed observations, then explicitly choose and run."""
from pathlib import Path
from fractions import Fraction as Q
from dataclasses import replace
import argparse,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'integrations/inquiry'))
import synthesized_resolution as a
import synthesized_session as live
import rr68_study as study


def emit(value):print(json.dumps(value,indent=2,default=a.m.te.triple.encode))
def show(plan):return dict(status=plan.status,feature_count=len(plan.features),frame_definitions=plan.proof.definitions if plan.proof else (),
    physical_definitions=plan.definitions,proof_digest=plan.proof.digest if plan.proof else None)


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('inspect','demo','start','choose','resolve','revise','execute','verify'))
    contexts=('mixed','main','main_perturbed','zero_head','outside_chart')
    p.add_argument('--context',choices=contexts);p.add_argument('--strength',type=Q);p.add_argument('--frame',choices=study.FRAMES)
    p.add_argument('--initial-context',choices=contexts,default='mixed');p.add_argument('--initial-strength',type=Q,default=Q(0))
    p.add_argument('--initial-frame',choices=study.FRAMES,default='identity')
    p.add_argument('--max-features',type=int,choices=(0,1,2));p.add_argument('--max-feature-degree',type=int,choices=(1,2))
    p.add_argument('--s-mode',choices=('keep','erase','restore'),default='keep');p.add_argument('--t-mode',choices=('keep','erase','restore'),default='keep')
    p.add_argument('--v',type=Q,default=Q(1));p.add_argument('--word',choices=a.m.WORDS,default='HHHSUT')
    p.add_argument('--record',type=Path);p.add_argument('--sha256');p.add_argument('--out',type=Path)
    p.add_argument('--out-dir',type=Path,default=Path('.work/synthesis-demo'));args=p.parse_args()
    entry=a.register((args.s_mode,args.t_mode));policy=a.Policy(
        max_features=2 if args.max_features is None else args.max_features,
        max_feature_degree=2 if args.max_feature_degree is None else args.max_feature_degree)
    if args.command=='inspect':
        request=study.scope(entry,args.context or 'mixed',args.strength or Q(0),args.frame or 'identity')
        plan=study.before_values(entry,request,args.v,args.word,policy)
        emit(dict(observation=show(plan),exact_value_queries_during_discovery=0,requested_motion_executed=False));return
    if args.command=='demo':
        if args.out_dir.exists():raise ValueError('choose a new output directory')
        spec=json.loads((study.HERE/'RR68-inputs.json').read_bytes())['sequences'][1];first=spec['requests'][0]
        session=live.start(entry,study.scope(entry,*first[:3]),a.Policy(max_features=first[4]));stages=[session];trace=[]
        for i,(name,strength,frame,word,budget) in enumerate(spec['requests']):
            if i:session=live.revise(session,study.scope(entry,name,strength,frame),a.Policy(max_features=budget));stages.append(session)
            session=live.choose(session,1,word);stages.append(session);session=live.resolve(session);stages.append(session)
            trace.append(dict(observation=show(session.prepared.plan),status=session.prepared.action.status,read_work=entry._work[-1]))
        session=live.execute(session);stages.append(session);args.out_dir.mkdir(parents=True);records=[]
        for i,stage in enumerate(stages):
            raw,h=live.dumps(stage);path=args.out_dir/('stage-'+str(i).zfill(2)+'.json');path.write_bytes(raw)
            records.append(dict(path=str(path),phase=stage.phase,sha256=h))
        study.write(args.out_dir/'manifest.json',dict(trace=trace,snapshots=records))
        emit(dict(phase=session.phase,certified=session.result.certified,trace=trace,final=records[-1]));return
    if args.command!='verify' and (args.out is None or args.out.exists()):p.error('a new --out path is required')
    if args.command=='start':session=live.start(entry,study.scope(entry,args.context or 'mixed',args.strength or Q(0),args.frame or 'identity'),policy)
    else:
        if args.record is None or args.sha256 is None:p.error('--record and external --sha256 are required')
        session=live.loads(args.record.read_bytes(),args.sha256,entry,study.scope(entry,args.initial_context,args.initial_strength,args.initial_frame))
        if args.command=='choose':session=live.choose(session,args.v,args.word)
        elif args.command=='resolve':session=live.resolve(session)
        elif args.command=='revise':
            if args.context is None or args.strength is None:p.error('revise requires context and strength')
            options={}
            if args.max_features is not None:options['max_features']=args.max_features
            if args.max_feature_degree is not None:options['max_feature_degree']=args.max_feature_degree
            session=live.revise(session,study.scope(entry,args.context,args.strength,args.frame or session.scope.frame),replace(session.policy,**options))
        elif args.command=='execute':session=live.execute(session)
        elif args.command=='verify':emit(dict(verified=True,state=live.view(session)));return
    raw,h=live.dumps(session);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(raw)
    emit(dict(state=live.view(session),sha256=h,path=str(args.out)))


if __name__=='__main__':main()
