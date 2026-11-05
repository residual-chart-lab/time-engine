"""Focused phase-feedback and existing E2 operation checks."""
from pathlib import Path
import hashlib,json,platform,sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import test_phase_feedback as tests


def run():
    out=ROOT/'.work/e3-validation';out.mkdir(parents=True,exist_ok=True)
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in ('test_phase_feedback','test_step_session'))
    with (out/'tests.log').open('w',encoding='utf-8',newline='\n') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if not result.wasSuccessful():raise AssertionError('see .work/e3-validation/tests.log')
    paths=(HERE/'step_session.py',HERE/'test_phase_feedback.py',HERE/'validate_phase_feedback.py',HERE/'fixtures/P0-first-use-CLOSED1.record.json')
    report=dict(schema='time-engine-e3-feedback-validation-v1',date='2026-10-24',passed=True,tests=result.testsRun,new_tests=3,existing_E2_tests=8,
        runtime=dict(python=platform.python_version(),system=platform.system()),cli=tests.FeedbackTests.cli_summary,
        legacy_checkpoint=tests.FeedbackTests.legacy_summary,checkpoint_schema_changed=False,
        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        full_historical_suite_rerun=False,independent_audit=False)
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report,indent=2));return report

if __name__=='__main__':run()
