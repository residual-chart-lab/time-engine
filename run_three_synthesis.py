"""Construct observations for three flowers, then inspect or execute in stages."""
from pathlib import Path
from fractions import Fraction as Q
import argparse,json,sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'integrations/inquiry'))
import rr69_study as study
import three_flower_session as live
from three_flower_synthesis import a,te


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('inspect','demo','verify'))
    parser.add_argument('--context',choices=('mixed','main','zero_head','outside_chart'),default='mixed')
    parser.add_argument('--strength',default='1/1024');parser.add_argument('--last-strength',default='1/1024')
    parser.add_argument('--frame',choices=tuple(study.FRAMES),default='identity')
    parser.add_argument('--v',default='1');parser.add_argument('--u',default='0');parser.add_argument('--word',choices=('HHHSUT','HHHUST'),default='HHHSUT')
    parser.add_argument('--out-dir',type=Path);parser.add_argument('--record',type=Path);parser.add_argument('--trusted-sha256')
    args=parser.parse_args();entry=a.register();request=study.scope(entry,args.context,(args.strength,args.last_strength),args.frame)
    if args.command=='inspect':
        plan=study.before_values(entry,request,Q(args.v),Q(args.u),args.word)
        print(json.dumps(dict(status=plan.status,proof=plan.proof.digest if plan.proof else None,nodes=len(plan.recipe.nodes),
            islands=len(plan.recipe.islands),frame_generators=plan.proof.definitions if plan.proof else (),original_values_read_for_construction=0,
            requested_future_paths_executed=0),indent=2,default=te.triple.encode));return
    if args.command=='verify':
        if args.record is None or args.trusted_sha256 is None:parser.error('verify needs --record and an externally retained --trusted-sha256')
        state=live.loads(args.record.read_bytes(),args.trusted_sha256,entry,request,(Q(args.v),Q(args.u),args.word))
        print(json.dumps(dict(phase=state.phase,certified=state.certified,stock=len(state.engine.stock))));return
    if args.out_dir is None:parser.error('demo needs a new --out-dir')
    args.out_dir.mkdir(parents=True,exist_ok=False)
    state=live.start(entry,request);index=0;reports=[]
    def save(current):
        nonlocal index
        raw,h=live.dumps(current);path=args.out_dir/(str(index).zfill(2)+'-'+current.phase.lower()+'.record.json');path.write_bytes(raw)
        reports.append(dict(path=path.name,phase=current.phase,sha256=h,stock=len(current.engine.stock)));index+=1
    save(state);state=live.choose(state,Q(args.v),Q(args.u),args.word);save(state)
    state,work=live.resolve(state);save(state)
    while state.phase in ('READY','CLOSED1','CLOSED2','CLOSED3'):state=live.advance(state);save(state)
    study.write(args.out_dir/'manifest.json',dict(snapshots=reports,work=work,certified=state.certified))
    print(json.dumps(dict(phase=state.phase,certified=state.certified,snapshots=reports,work=work),indent=2))

if __name__=='__main__':main()
