"""Focused E2 session tests; E1's independently audited runtime is unchanged."""
from pathlib import Path
import hashlib
import json
import platform
import sys
import unittest
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_step_session as tests


def run():
    baseline = json.loads((HERE/'E1-BASELINE.json').read_bytes())
    for item in baseline['files']:
        if hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest() != item['sha256']:
            raise AssertionError(item['path'])
    if hashlib.sha256((HERE/'entry_transport.py').read_bytes()).hexdigest() != '2862ad46cd44aace1eade9e78fe783b4eec1e0c7289c9fabb4163735ee263741':
        raise AssertionError('audited E1 entry implementation changed')
    out = ROOT/'.work/e2-validation'; out.mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.loadTestsFromName('test_step_session')
    with (out/'tests.log').open('w', encoding='utf-8', newline='\n') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('see .work/e2-validation/tests.log')
    (out/'closed-first.record.json').write_bytes(tests.StepSessionTests.checkpoint_bytes)
    paths = (HERE/'step_session.py', HERE/'test_step_session.py', HERE/'validate_step_session.py', ROOT/'run_time_engine.py')
    report = dict(schema='time-engine-e2-validation-v1', passed=True, date='2026-10-24',
                  base_commit='35e402979fcaab419d2756dddc6ee7e4b4241a28',
                  runtime=dict(python=platform.python_version(), system=platform.system(), platform=platform.platform()),
                  tests=result.testsRun, unchanged_original_files=len(baseline['files']), E1_runtime_unchanged=True,
                  cli=tests.StepSessionTests.cli_metrics,
                  checkpoint_sha256=tests.StepSessionTests.checkpoint_sha256,
                  full_existing_suite_rerun=False,
                  source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':
    run()
