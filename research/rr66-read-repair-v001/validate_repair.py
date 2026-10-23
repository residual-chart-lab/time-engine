"""Keep the published RR66 evidence fixed and record the audit repair separately."""
from pathlib import Path
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'integrations/inquiry'))
import adaptive_resolution as a
import adaptive_session as live
import rr66_study as study
import validate_adaptive as validation


def run():
    out=ROOT/'.work/rr66-read-repair';out.mkdir(parents=True,exist_ok=True)
    study.OUTPUT=out/'validation'
    report=validation.run()
    matches={}
    for generated,published in (('starts.json','RR66-starts.json'),('result.json','RR66-result.json'),
            ('product-to-port.record.json','RR66-product-to-port.record.json')):
        raw=(study.OUTPUT/generated).read_bytes();old=(ROOT/'integrations/inquiry'/published).read_bytes()
        assert raw==old,'published evidence changed: '+published
        matches[published]=hashlib.sha256(raw).hexdigest()
    entry=a.register();fine=study.scope(entry,'mixed','1/1024');main=study.scope(entry,'main','1/1024')
    cases=[]
    for word in a.m.WORDS:
        initial=live.resolve(live.choose(live.start(entry,fine),1,word))
        meter=a.fn.Meter();ready=live.resolve(live.choose(live.revise(initial,main),1,word),meter)
        command=live.history(ready)[-1]
        assert command['new_keys']==['s'] and command['derived_keys']==['t'] and meter.exact_reads==1
        raw,h=live.dumps(ready)
        resumed=live.loads(raw,h,entry,fine,main,ready.choice)
        complete=live.execute(ready);replayed=live.execute(resumed)
        assert complete.digest==replayed.digest and complete.result.certified
        raw,h=live.dumps(complete)
        assert live.loads(raw,h,entry,fine,main,complete.choice).digest==complete.digest
        name=word+'.record.json';(out/name).write_bytes(raw)
        cases.append(dict(word=word,mode=ready.prepared.plan.mode,new_keys=command['new_keys'],derived_keys=command['derived_keys'],
            exact_reads=meter.exact_reads,certified=True,same_resumed_motion=True,record=name,record_sha256=h,
            local_endpoints=[str(complete.result.first.engine.upper.live.accumulated),
                str(complete.result.second.engine.upper.live.accumulated)],upper_endpoint=str(complete.result.upper_trial.live.accumulated)))
    result=dict(schema='time-engine-rr66-audit-repair-validation-v1',passed=True,
        prior_commit='cb4d505dd1c93bd1b6194593a1225500f0e304e4',original_experiment=report,
        published_artifacts_byte_identical=matches,repaired_transitions=cases,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'repair-validation.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,tests=report['total_tests'],original_groups=report['groups'],
        unchanged_published_artifacts=len(matches),additional_actual_bundles=len(cases)),indent=2))
    return result


if __name__=='__main__':run()
