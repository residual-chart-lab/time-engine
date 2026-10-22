"""Measure the audit repair against its frozen derivation on the same entry.

Only the derive_cached implementation changes between paired trials. Timings
are diagnostic measurements on this in-memory Vault, not a performance test.
"""
from pathlib import Path
from contextlib import contextmanager
from time import perf_counter_ns,get_clock_info
from statistics import median
from unittest.mock import patch
import argparse,hashlib,json,platform,sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'integrations/inquiry'))
import adaptive_resolution as a
import adaptive_session as live
import rr66_study as study
from reference_derivation import derive_cached as reference


def timed(call):
    start=perf_counter_ns();value=call()
    return value,(perf_counter_ns()-start)/1_000_000


def statistics(samples):
    return dict(samples_ms=samples,median_ms=median(samples),min_ms=min(samples),max_ms=max(samples))


def signature(session):
    r=session.result
    return a.fingerprint((r.action.status,r.action.T,r.action.R,r.port,
        r.first.engine.upper.live.accumulated,r.second.engine.upper.live.accumulated,
        r.upper_trial.live.accumulated,r.certified))


def run(samples=3):
    if type(samples) is not int or not 1<=samples<=9:raise ValueError('use 1..9 finite paired samples')
    repaired=a.derive_cached
    # Both registration and plan compilation are unchanged by this repair.
    # Report them once, outside the extraction-only A/B comparison.
    common={'registration':[],'plan_cold':[],'plan_warm':[]}
    for _ in range(samples):
        entry,ms=timed(a.register);common['registration'].append(ms)
    fine=study.scope(entry,'mixed','1/1024');main=study.scope(entry,'main','1/1024')
    for _ in range(samples):
        entry._plans.clear()
        _,ms=timed(lambda:a.compile(entry,main,1,'HHHSUT'));common['plan_cold'].append(ms)
        _,ms=timed(lambda:a.compile(entry,main,1,'HHHSUT'));common['plan_warm'].append(ms)
    initial=live.resolve(live.choose(live.start(entry,fine),1,'HHHSUT'))
    chosen=live.choose(live.revise(initial,main),1,'HHHSUT')
    before_archive=live.archives(entry)
    rows={name:dict(phases={key:[] for key in ('resolve','execute','save_complete','load_complete')},trials=[])
        for name in ('before','after')}
    cache_fingerprint=None;motion_fingerprint=None
    for i in range(samples):
        order=('before','after') if i%2==0 else ('after','before')
        for name in order:
            with patch.object(a,'derive_cached',reference if name=='before' else repaired):
                meter=a.fn.Meter()
                ready,ms=timed(lambda:live.resolve(chosen,meter));rows[name]['phases']['resolve'].append(ms)
                command=live.history(ready)[-1]
                assert command['new_keys']==(['s','t'] if name=='before' else ['s'])
                assert command['derived_keys']==([] if name=='before' else ['t'])
                assert meter.exact_reads==(2 if name=='before' else 1)
                current=a.fingerprint(ready.cache)
                if cache_fingerprint is None:cache_fingerprint=current
                assert current==cache_fingerprint
                complete,ms=timed(lambda:live.execute(ready));rows[name]['phases']['execute'].append(ms)
                current=signature(complete)
                if motion_fingerprint is None:motion_fingerprint=current
                assert current==motion_fingerprint and complete.result.certified
                (raw,h),ms=timed(lambda:live.dumps(complete));rows[name]['phases']['save_complete'].append(ms)
                restored,ms=timed(lambda:live.loads(raw,h,entry,fine,main,complete.choice))
                rows[name]['phases']['load_complete'].append(ms)
                assert restored.digest==complete.digest and signature(restored)==motion_fingerprint
                rows[name]['trials'].append(dict(sample=i,exact_reads=meter.exact_reads,
                    new_keys=command['new_keys'],derived_keys=command['derived_keys'],checkpoint_bytes=len(raw),
                    physical_signature=current,archives_unchanged=live.archives(entry)==before_archive))
        print(json.dumps(dict(paired_sample=i+1,exact_reads_before=2,exact_reads_after=1)),flush=True)
    assert all(t['archives_unchanged'] for row in rows.values() for t in row['trials'])
    for row in rows.values():
        row['phases']={key:statistics(values) for key,values in row['phases'].items()}
        row['measured_phase_sum_ms']=[sum(row['phases'][key]['samples_ms'][i] for key in row['phases']) for i in range(samples)]
    source_files=[ROOT/'integrations/inquiry/adaptive_resolution.py',HERE/'reference_derivation.py',HERE/'profile_repair.py']
    return dict(schema='time-engine-rr66-read-repair-cost-v1',date='2026-10-22',
        environment=dict(python=platform.python_version(),implementation=platform.python_implementation(),
            system=platform.system(),machine=platform.machine(),clock_resolution_s=get_clock_info('perf_counter').resolution),
        workload=dict(word='HHHSUT',requests=['mixed/1/1024','main/1/1024'],v='1',
            initial_cached_keys=[k for k,v in initial.cache],selected_mode='INDIVIDUAL',paired_samples=samples,
            before_source_commit='cb4d505dd1c93bd1b6194593a1225500f0e304e4',
            treatment='only derive_cached is replaced; same entry, current choice, requests, plans and cache',
            plan_cold='entry._plans cleared; already registered entry',
            planning_and_registration_shared=True,save_and_load_include_strict_command_and_motion_replay=True,
            in_memory_vault=True,registration_exact_references=len(entry.base.vault._records())+len(entry.derived._records())),
        common_phases={key:statistics(values) for key,values in common.items()},comparison=rows,
        equivalent_cache_and_physical_signature=True,retained_archives_unchanged=True,
        interpretation='One fewer exact archive query; extra rational reconstruction and commitment checks remain. Timings do not establish general end-to-end acceleration.',
        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--samples',type=int,default=3)
    parser.add_argument('--out',type=Path,default=ROOT/'.work/rr66-read-repair/cost.json');args=parser.parse_args()
    result=run(args.samples);args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps(dict(output=str(args.out),shared_median_ms={k:v['median_ms'] for k,v in result['common_phases'].items()},
        median_ms={name:{k:v['median_ms'] for k,v in row['phases'].items()} for name,row in result['comparison'].items()}),indent=2))
