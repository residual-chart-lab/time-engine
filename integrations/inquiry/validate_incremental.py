"""Validate frozen baselines, the declared study and runtime regressions."""
from pathlib import Path
import hashlib,json,unittest
import rr67_study as study
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def run():
    base=json.loads((HERE/'RR67-BASELINE.json').read_bytes());count=0
    for name,wanted in base['files'].items():
        if name in base['navigation_updates']:continue
        raw=(ROOT/name).read_bytes();actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if actual!=wanted:raise AssertionError('RR66 baseline changed: '+name)
        count+=1
    result=study.run()
    names=('test_incremental_session','test_adaptive_session','test_mixed_action_sets')
    counts={name:unittest.defaultTestLoader.loadTestsFromName(name).countTestCases() for name in names}
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    with (study.OUTPUT/'validation.log').open('w',encoding='utf-8',newline='\n') as log:
        tested=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('see .work/rr67-local/validation.log')
    sources=[HERE/n for n in ('incremental_resolution.py','incremental_session.py','rr67_study.py',
        'test_incremental_session.py','validate_incremental.py','RR67-inputs.json','RR67-BASELINE.json')]+[ROOT/'run_incremental.py']
    report=dict(schema='time-engine-rr67-validation-v1',passed=True,tests=tested.testsRun,test_counts=counts,
        unchanged_baseline_files=count,base_commit=base['base_commit'],input_commit=study.INPUT_COMMIT,input_sha256=study.INPUT_SHA,
        groups=len(result['groups']),plans=result['plans'],actual_bundles=result['actual_bundles'],
        full_control_actual_bundles=result['full_control_actual_bundles'],checkpoint_stages=result['checkpoint_stages'],
        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        evidence_sha256={name:hashlib.sha256((study.OUTPUT/name).read_bytes()).hexdigest() for name in
            ('starts.json','result.json','changes-and-return.record.json','current-word.record.json')})
    study.write(study.OUTPUT/'validation.json',report);print(json.dumps(report,indent=2),flush=True);return report


if __name__=='__main__':run()
