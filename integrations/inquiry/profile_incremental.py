"""Paired cold/warm comparison within the same RR67 arithmetic engine."""
from dataclasses import asdict
from pathlib import Path
from statistics import median
from time import perf_counter_ns
import hashlib,json,platform
import incremental_resolution as a
import rr67_study as study


def run(samples=3):
    if type(samples) is not int or not 1<=samples<=9:raise ValueError('use 1..9 paired samples')
    cases=[('future-C',('mixed','1/1024','wide',2),('main','1/1024','wide',2)),
        ('domain',('main','1/1024','wide',2),('main','1/1024','zero',2)),
        ('budget',('mixed','1/1024','wide',1),('mixed','1/1024','wide',2))]
    rows=[]
    for name,before,after in cases:
        trials=[]
        for i in range(samples):
            warm=a.register();cold=a.register()
            assert warm.digest==cold.digest
            a.compile(warm,study.scope(warm,*before[:3]),1,'HHHSUT',a.Policy(before[3]))
            result={}
            for mode in (('cold','warm') if i%2==0 else ('warm','cold')):
                entry=cold if mode=='cold' else warm;request=study.scope(entry,*after[:3])
                start=perf_counter_ns();plan=a.compile(entry,request,1,'HHHSUT',a.Policy(after[3]));ms=(perf_counter_ns()-start)/1e6
                result[mode]=dict(ms=ms,plan_digest=plan.digest,work=asdict(entry._receipts[-1][1]),mode=plan.mode,status=plan.status)
                assert not result[mode]['work']['plan_cache_hits']
            assert result['cold']['plan_digest']==result['warm']['plan_digest']
            trials.append(result)
        rows.append(dict(name=name,before=before,after=after,trials=trials,
            cold_median_ms=median(x['cold']['ms'] for x in trials),warm_median_ms=median(x['warm']['ms'] for x in trials)))
        print(json.dumps(dict(case=name,cold_median_ms=rows[-1]['cold_median_ms'],warm_median_ms=rows[-1]['warm_median_ms'])),flush=True)
    files=[Path(__file__),study.HERE/'incremental_resolution.py']
    result=dict(schema='time-engine-rr67-paired-profile-v1',date='2026-10-23',
        environment=dict(python=platform.python_version(),system=platform.system(),machine=platform.machine()),
        cases=rows,paired_samples=samples,
        comparison='same RR67 arithmetic implementation; identical entry content, new request, v=1 and HHHSUT; only prior caches differ',
        excludes='entry registration, preparing the prior request, exact feature resolution, actuation and checkpoint replay',
        all_mathematical_plan_digests_equal=True,all_final_requests_previously_uncompiled=True,
        total_system_speedup_claimed=False,
        source_sha256={p.relative_to(study.HERE.parents[1]).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    study.OUTPUT.mkdir(parents=True,exist_ok=True);study.write(study.OUTPUT/'paired-cost.json',result);return result


if __name__=='__main__':run()
