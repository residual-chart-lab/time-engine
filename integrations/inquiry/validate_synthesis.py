"""Validate synthesized observations, fixed-source integrity and regressions."""
from pathlib import Path
import hashlib,json,unittest
import rr68_study as study
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def run():
    base=json.loads((HERE/'RR68-BASELINE.json').read_bytes());checked=0
    for name,wanted in base['files'].items():
        if name in base['navigation_updates']:continue
        raw=(ROOT/name).read_bytes()
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=wanted:raise AssertionError('baseline changed: '+name)
        checked+=1
    result=study.run();names=('test_synthesized_session','test_incremental_session','test_adaptive_session','test_mixed_action_sets')
    counts={name:unittest.defaultTestLoader.loadTestsFromName(name).countTestCases() for name in names}
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    with (study.OUTPUT/'validation.log').open('w',encoding='utf-8',newline='\n') as log:
        tested=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('see .work/rr68-local/validation.log')
    sources=[HERE/name for name in ('observation_synthesis.py','synthesized_resolution.py','synthesized_session.py',
        'rr68_study.py','test_synthesized_session.py','validate_synthesis.py','RR68-inputs.json','RR68-BASELINE.json')]+[ROOT/'run_synthesis.py']
    report=dict(schema='time-engine-rr68-validation-v1',passed=True,tests=tested.testsRun,test_counts=counts,
        base_commit=base['base_commit'],unchanged_baseline_files=checked,input_commit=study.INPUT_COMMIT,input_sha256=study.INPUT_SHA,
        groups=len(result['groups']),plans=result['plans'],actual_sequence_bundles=5,retention_control_motions=5,checkpoint_stages=result['checkpoint_stages'],
        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        evidence_sha256={name:hashlib.sha256((study.OUTPUT/name).read_bytes()).hexdigest() for name in
            ('starts.json','result.json','unregistered-split.record.json','word-and-frame.record.json')})
    study.write(study.OUTPUT/'validation.json',report);print(json.dumps(report,indent=2),flush=True);return report


if __name__=='__main__':run()
