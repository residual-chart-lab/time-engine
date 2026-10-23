"""Focused E1 falsification; run from this pinned repository with python -I."""
from pathlib import Path
from dataclasses import replace
from fractions import Fraction as Q
from unittest.mock import patch
import sys, json, hashlib, time, platform, copy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'integrations/inquiry'))
import entry_transport as w
import three_flower_session as live
import rr69_study as study

raw = (ROOT / 'integrations/inquiry/E1-entry.record.json').read_bytes()
doc = json.loads(raw)
digest = doc['entry_digest']
roots = w.checkpoint.unpack(doc['graph'])
first, second, engine, u = roots
registries = (w.m._ISSUED, w.adaptive._ISSUED, w.incremental._ISSUED, w.a._ISSUED)
results = []

def reject(name, changed):
    data = (json.dumps(changed, separators=(',', ':')) + '\n').encode()
    before = tuple(map(len, registries))
    try:
        # Recompute the external hash deliberately: test structural verification,
        # not merely the outer checksum. Original expected identity stays fixed.
        w.loads(data, hashlib.sha256(data).hexdigest(), digest)
    except ValueError as exc:
        assert before == tuple(map(len, registries)), name
        results.append(dict(name=name, rejected=True, error=str(exc), authority_issued=False))
    else:
        raise AssertionError(name + ' was accepted')

def physical(name, changed):
    new = dict(doc, graph=w.checkpoint.pack(changed))
    reject(name, new)

def corrupt(obj, **changes):
    # Test-only creation of invalid immutable data; receiver constructors must
    # recheck these invariants. Serialization still uses the real graph packer.
    out=copy.copy(obj)
    for key,value in changes.items():object.__setattr__(out,key,value)
    return out

physical('history_event_kind', (first, second, replace(engine, events=(replace(engine.events[0], kind='altered'),) + engine.events[1:]), u))
physical('inherited_upper_value', (first, second, replace(engine, upper=replace(engine.upper, live=replace(engine.upper.live, accumulated=(Q(1),Q(0),Q(0),Q(0))))), u))
physical('inherited_lower_value', (first, second, replace(engine, lower=replace(engine.lower, live=replace(engine.lower.live, accumulated=(Q(1),Q(0),Q(0),Q(0))))), u))
physical('retained_stock_deleted', (first, second, replace(engine, stock=engine.stock[:-1]), u))
physical('first_retained_shift', (replace(first, pair=corrupt(first.pair, shift=first.pair.shift+Q(1,1024))), second, engine, u))
physical('second_retained_shift', (first, replace(second, pair=corrupt(second.pair, shift=second.pair.shift+Q(1,1024))), engine, u))
weights=first.pair.original.weights
physical('original_coefficients', (replace(first, pair=corrupt(first.pair, original=corrupt(first.pair.original, weights=(weights[0]+1,)+weights[1:]))), second, engine, u))
physical('published_U_value', (first, second, engine, corrupt(u, visible=(Q(1),Q(0),Q(0),Q(0)))))
physical('source_roles_swapped', (second, first, engine, u))
physical('history_truncated', (first, second, replace(engine, events=engine.events[:-1]), u))
changed=json.loads(raw);changed['numbers']['base']='00'
reject('number_archive_changed',changed)

t=time.perf_counter();entry=w.loads(raw,hashlib.sha256(raw).hexdigest(),digest)
receive_seconds=time.perf_counter()-t
assert not entry.derived._records()
original=entry.base.engine
cases=[]
for name, request in [('outside_chart',study.scope(entry,'outside_chart')),('empty_domain',study.scope(entry,domain=('0','0')))]:
    state=live.choose(live.start(entry,request),1,0,'HHHSUT')
    with patch.object(w.m.plant,'produce',side_effect=AssertionError('rejected request executed')):
        state, work=live.resolve(state)
        assert state.phase=='REJECTED'
        try:live.advance(state)
        except ValueError:pass
        else:raise AssertionError('old authentication became new permission')
    assert entry.base.engine==original
    cases.append(dict(name=name,status=state.action.status,execution_blocked=True))

scope=study.scope(entry,'mixed',('1/1024','1/1024'),'split')
t=time.perf_counter();chosen=live.choose(live.start(entry,scope),1,0,'HHHSUT');compile_seconds=time.perf_counter()-t
ready,first_work=live.resolve(chosen)
assert ready.phase=='READY'
with patch.object(entry.base.vault,'exact',side_effect=AssertionError('unnecessary original reread')), patch.object(entry.derived,'exact',side_effect=AssertionError('unnecessary derived reread')):
    repeated,cache,repeat_work=live.n.resolve(entry,scope,chosen.plan,ready.cache)
assert repeated==ready.action and repeat_work['total_exact_queries']==0
try:live.n.resolve(entry,replace(scope,last_strength=Q(0)),chosen.plan,ready.cache)
except ValueError:cases.append(dict(name='plan_under_changed_requirement',execution_blocked=True))
else:raise AssertionError('plan reused for a different requirement')
assert entry.base.engine==original

report=dict(pinned_commit='0f708c1d35eda52415a24347839d122046cf595b',runtime=platform.platform(),python=platform.python_version(),passed=True,
    canonical_tampering_cases=results,requirement_separation=cases,
    reuse=dict(first_resolution=first_work,repeated_resolution=repeat_work,action_equal=True),
    single_run_seconds=dict(receive=receive_seconds,compile=compile_seconds),
    timing_note='One warmed-process timing sample after negative cases; not a benchmark. Prior rejected requests may populate observations.')
out=Path(__file__).with_name('observed.json');out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,tampering_cases=len(results),requirement_cases=len(cases),reuse=repeat_work,timings=report['single_run_seconds'])))
