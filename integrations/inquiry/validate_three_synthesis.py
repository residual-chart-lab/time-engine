"""Reproduce RR69 and check the unchanged RR68 consumer/component regressions."""
from pathlib import Path
import hashlib,json,unittest
import rr69_study as study
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def run():
    base=json.loads((HERE/'RR69-BASELINE.json').read_bytes());checked=0
    for name,wanted in base['files'].items():
        if name in base['navigation_updates']:continue
        raw=(ROOT/name).read_bytes()
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=wanted:raise AssertionError('baseline changed: '+name)
        checked+=1
    result=study.run()
    names=('test_three_flower_synthesis','test_synthesized_session','test_incremental_session','test_adaptive_session','test_mixed_action_sets')
    counts={name:unittest.defaultTestLoader.loadTestsFromName(name).countTestCases() for name in names}
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    with (study.OUTPUT/'validation.log').open('w',encoding='utf-8',newline='\n') as log:
        tested=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('see .work/rr69-local/validation.log')
    sources=[HERE/name for name in ('three_flower_synthesis.py','three_flower_session.py','rr69_study.py',
        'test_three_flower_synthesis.py','validate_three_synthesis.py','RR69-inputs.json','RR69-BASELINE.json','observation_synthesis.py')]+[ROOT/'run_three_synthesis.py']
    report=dict(schema='time-engine-rr69-validation-v1',passed=True,tests=tested.testsRun,test_counts=counts,base_commit=base['base_commit'],
        unchanged_baseline_files=checked,input_commit=study.INPUT_COMMIT,input_sha256=study.INPUT_SHA,groups=len(result['groups']),plans=result['plans'],
        actual_three_flower_bundles=len(result['motions']),retention_controls=len(result['retention_controls']),checkpoint_stages=len(result['checkpoints']),
        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        evidence_sha256={name:hashlib.sha256((study.OUTPUT/name).read_bytes()).hexdigest() for name in ('starts.json','result.json','mixed-connected.record.json','mixed-last-port.record.json')})
    study.write(study.OUTPUT/'validation.json',report)
    print(json.dumps(report,indent=2),flush=True);return report

if __name__=='__main__':run()
