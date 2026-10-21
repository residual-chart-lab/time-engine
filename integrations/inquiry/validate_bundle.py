"""RR64: frozen inputs, source integrity, actual bundle study and regressions."""
from pathlib import Path
import hashlib,json,unittest
import rr64_study as study

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def integrity():
    manifest=json.loads((HERE/'RR64-BASELINE.json').read_bytes())
    allowed=set(manifest['navigation_updates'])
    checked=[]
    for name,wanted in manifest['files'].items():
        if name in allowed:continue
        raw=(ROOT/name).read_bytes()
        got=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if got!=wanted:raise AssertionError('frozen TE input changed: '+name)
        checked.append(name)
    vendor=ROOT/'vendor/free-number-runtime'
    source=json.loads((vendor/'SOURCE.json').read_bytes())
    for name,wanted in source['files'].items():
        if hashlib.sha256((vendor/name).read_bytes()).hexdigest()!=wanted['sha256']:
            raise AssertionError('adopted Free Numbers runtime changed: '+name)
    if hashlib.sha256((HERE/'RR64-inputs.json').read_bytes()).hexdigest()!=study.INPUT_SHA256:
        raise AssertionError('pre-calculation input bytes changed')
    return dict(TE_base=manifest['TE_base'],unchanged_TE_files=len(checked),
        navigation_updates=sorted(allowed),adopted_FN_merge=source['adopted_merge'],
        unchanged_FN_files=len(source['files']),input_commit=study.INPUT_COMMIT,
        input_sha256=study.INPUT_SHA256)


def run():
    verified=integrity()
    result=study.run()
    modules=('test_bundle_demand','test_demand_filter','test_live_flower','test_deferred','test_portability')
    counts={n:unittest.defaultTestLoader.loadTestsFromName(n).countTestCases() for n in modules}
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in modules)
    with (study.OUTPUT/'validation.log').open('w',encoding='utf-8',newline='\n') as stream:
        tested=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('see .work/rr64-local/validation.log')
    new_files=('bundle_demand.py','bundle_execution.py','bundle_resource_sweep.py','rr64_study.py',
               'test_bundle_demand.py','validate_bundle.py','RR64-inputs.json','RR64-resource-sweep-inputs.json','RR64-BASELINE.json')
    paths=[HERE/name for name in new_files]+[ROOT/'run_bundle.py',ROOT/'vendor/free-number-runtime/SOURCE.json']
    paths+=sorted((ROOT/'vendor/free-number-runtime/runtime/free_numbers').glob('*.py'))
    report=dict(schema='time-engine-rr64-validation-v1',passed=True,integrity=verified,
        total_tests=tested.testsRun,test_counts=counts,groups=len(result['groups']),queries=result['query_count'],
        successful_requested_pairs=len(result['executions']),
        exact_residual_reads=result['exact_residual_reads'],
        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        evidence_sha256={name:hashlib.sha256((study.OUTPUT/name).read_bytes()).hexdigest()
            for name in ('result.json','starts.json','resource-sweep.json','keep-primary.record.json')})
    study.write(study.OUTPUT/'validation.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
    return report


if __name__=='__main__':run()
