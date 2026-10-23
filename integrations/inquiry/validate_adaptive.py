"""RR66 adaptive observations, command replay, motion and RR65 regressions."""
from pathlib import Path
import json,hashlib,unittest
import rr66_study as study

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def integrity():
    base=json.loads((HERE/'RR66-BASELINE.json').read_bytes());checked=0
    for name,wanted in base['files'].items():
        if name in base['navigation_updates']:continue
        raw=(ROOT/name).read_bytes()
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=wanted:raise AssertionError('RR65 baseline changed: '+name)
        checked+=1
    if hashlib.sha256((HERE/'RR66-inputs.json').read_bytes()).hexdigest()!=study.INPUT_SHA:raise AssertionError('fixed input changed')
    return dict(base_commit=base['base_commit'],unchanged_baseline_files=checked,navigation_updates=base['navigation_updates'],input_commit=study.INPUT_COMMIT,input_sha256=study.INPUT_SHA)


def run():
    verified=integrity();result=study.run();names=('test_adaptive_session','test_mixed_action_sets')
    counts={n:unittest.defaultTestLoader.loadTestsFromName(n).countTestCases() for n in names}
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in names)
    with (study.OUTPUT/'validation.log').open('w',encoding='utf-8',newline='\n') as log:
        tested=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('see .work/rr66-local/validation.log')
    files=[HERE/name for name in ('resolution_algebra.py','adaptive_resolution.py','adaptive_session.py','rr66_study.py',
        'test_adaptive_session.py','validate_adaptive.py','RR66-inputs.json','RR66-BASELINE.json')]+[ROOT/'run_adaptive.py']
    report=dict(schema='time-engine-rr66-validation-v1',passed=True,integrity=verified,total_tests=tested.testsRun,
        test_counts=counts,groups=len(result['groups']),plans=result['plans'],plan_modes=result['plan_modes'],
        actual_bundles=result['requested_actual_bundles'],checkpoint_stages=len(result['checkpoint_stages']),
        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        evidence_sha256={name:hashlib.sha256((study.OUTPUT/name).read_bytes()).hexdigest()
            for name in ('starts.json','result.json','product-to-port.record.json')})
    study.write(study.OUTPUT/'validation.json',report);print(json.dumps(report,indent=2),flush=True);return report


if __name__=='__main__':run()
