"""An old two-query trace stays an old trace, even after the one-query repair."""
from pathlib import Path
from unittest.mock import patch
import hashlib,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'integrations/inquiry'))
import adaptive_resolution as a
import adaptive_session as live
import rr66_study as study
from reference_derivation import derive_cached as reference


def run():
    entry=a.register();fine=study.scope(entry,'mixed','1/1024');main=study.scope(entry,'main','1/1024')
    initial=live.resolve(live.choose(live.start(entry,fine),1,'HHHSUT'))
    chosen=live.choose(live.revise(initial,main),1,'HHHSUT')
    with patch.object(a,'derive_cached',reference):
        before=live.resolve(chosen);raw,h=live.dumps(before)
        assert live.loads(raw,h,entry,fine,main,before.choice).digest==before.digest
    try:live.loads(raw,h,entry,fine,main,before.choice)
    except ValueError as error:
        assert 'declared observation, query or current choice changed' in str(error)
        reason=str(error)
    else:raise AssertionError('an old query trace was silently rewritten')
    after=live.resolve(chosen)
    assert before.prepared.action==after.prepared.action and before.cache==after.cache
    assert live.history(before)[-1]['new_keys']==['s','t']
    assert live.history(after)[-1]['new_keys']==['s']
    assert live.history(after)[-1]['derived_keys']==['t']
    result=dict(passed=True,old_trace_replays_under_reference=True,new_runtime_rejects_old_query_trace=True,
        reason=reason,action_and_cache_equal=True,old_trace_sha256=h,
        old_code_commit='cb4d505dd1c93bd1b6194593a1225500f0e304e4',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out=ROOT/'.work/rr66-read-repair/replay-boundary.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2));return result


if __name__=='__main__':run()
