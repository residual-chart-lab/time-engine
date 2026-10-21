"""RR65 model, scoped omission guarantees, actual history and RR64 regressions."""
from pathlib import Path
import hashlib,json,unittest
import rr65_study as study

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def integrity():
    spec=json.loads((HERE/'RR65-BASELINE.json').read_bytes());checked=[]
    for name,wanted in spec['files'].items():
        if name in spec['navigation_updates']:continue
        raw=(ROOT/name).read_bytes()
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=wanted:raise AssertionError('RR64 baseline changed: '+name)
        checked.append(name)
    if hashlib.sha256((HERE/'RR65-inputs.json').read_bytes()).hexdigest()!=study.INPUT_SHA:raise AssertionError('fixed input bytes changed')
    return dict(base_commit=spec['base_commit'],unchanged_RR64_files=len(checked),navigation_updates=spec['navigation_updates'],
        input_commit=study.INPUT_COMMIT,input_sha256=study.INPUT_SHA)


def run():
    verified=integrity();result=study.run()
    names=('test_mixed_action_sets','test_bundle_demand')
    counts={name:unittest.defaultTestLoader.loadTestsFromName(name).countTestCases() for name in names}
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    with (study.OUTPUT/'validation.log').open('w',encoding='utf-8',newline='\n') as log:
        tested=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('see .work/rr65-local/validation.log')
    paths=[HERE/name for name in ('mixed_action_sets.py','mixed_execution.py','rr65_study.py','test_mixed_action_sets.py',
        'validate_mixed.py','RR65-inputs.json','RR65-BASELINE.json')]+[ROOT/'run_mixed.py']
    report=dict(schema='time-engine-rr65-validation-v1',passed=True,integrity=verified,total_tests=tested.testsRun,
        test_counts=counts,groups=len(result['groups']),scope_comparisons=result['scope_comparisons'],
        candidate_comparisons=result['candidate_comparisons'],verdict_counts=result['verdict_counts'],
        actual_pairs=len(result['executions']),certified_pairs=sum(x['certified'] for x in result['executions']),
        labelled_counterfactual_pairs=sum(x['counterfactual'] for x in result['executions']),
        rejected_input_configurations=len(result['rejected_input_configurations']),
        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        evidence_sha256={name:hashlib.sha256((study.OUTPUT/name).read_bytes()).hexdigest()
            for name in ('result.json','starts.json','joint-observation.json','joint-complete.record.json')})
    study.write(study.OUTPUT/'validation.json',report)
    print(json.dumps(report,indent=2),flush=True);return report


if __name__=='__main__':run()
