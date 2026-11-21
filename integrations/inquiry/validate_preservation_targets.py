"""Focused preservation-target checks and the reused division guards."""
from pathlib import Path
import hashlib,json,platform,sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import test_preservation_targets as tests


def run():
    out=ROOT/'.work/preservation-targets';out.mkdir(parents=True,exist_ok=True)
    names=('test_preservation_targets',
           'test_three_flower_synthesis.RationalAdapterTests.test_zero_multiplication_does_not_erase_a_denominator_guard',
           'test_three_flower_synthesis.RationalAdapterTests.test_canceled_division_is_not_legal_at_a_zero_denominator')
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    with (out/'tests.log').open('w',encoding='utf-8',newline='\n') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if not result.wasSuccessful():raise AssertionError('see .work/preservation-targets/tests.log')
    paths=('integrations/inquiry/preservation_targets.py','integrations/inquiry/test_preservation_targets.py',
           'integrations/inquiry/validate_preservation_targets.py','run_preservation_check.py',
           'integrations/inquiry/three_flower_synthesis.py','integrations/inquiry/three_flower_session.py','integrations/inquiry/rr69_study.py')
    report=dict(schema='time-engine-preservation-target-validation-v1',date='2026-10-25',passed=True,
        tests=result.testsRun,new_tests=7,reused_division_guard_tests=2,runtime=dict(python=platform.python_version(),system=platform.system()),
        separation=tests.PreservationTests.separation,execution_control=tests.PreservationTests.execution_control,
        source_sha256={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in paths},
        existing_model_code_changed=False,original_P0_archive_modified=False,independent_audit=False,full_historical_suite_rerun=False,
        life_detection_claimed=False,automatic_crack_or_erasure_policy_added=False)
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,tests=result.testsRun,new_tests=7,reused_guard_tests=2,
        relation=report['separation'][0]['requested']['relation'],current_equal=True,execution_control=report['execution_control']),indent=2))
    return report


if __name__=='__main__':run()
