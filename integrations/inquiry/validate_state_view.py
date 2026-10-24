"""Focused state/readout boundary checks plus the affected E3/E2 interface."""
from pathlib import Path
import hashlib
import json
import platform
import sys
import unittest
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import test_state_view as tests


def run():
    out = ROOT/'.work/state-view-validation'
    out.mkdir(parents=True, exist_ok=True)
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name)
        for name in ('test_state_view', 'test_phase_feedback', 'test_step_session'))
    with (out/'tests.log').open('w', encoding='utf-8', newline='\n') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('see .work/state-view-validation/tests.log')
    paths = ('integrations/inquiry/step_session.py', 'integrations/inquiry/test_state_view.py',
             'integrations/inquiry/validate_state_view.py', 'integrations/inquiry/test_phase_feedback.py',
             'integrations/inquiry/test_step_session.py', 'integrations/inquiry/fixtures/P0-first-use-CLOSED1.record.json')
    report = dict(schema='time-engine-state-view-validation-v1', date='2026-10-24', passed=True,
        tests=result.testsRun, new_tests=3, existing_E3_tests=3, existing_E2_tests=8,
        runtime=dict(python=platform.python_version(), system=platform.system()),
        isolation=tests.StateViewTests.isolation, rejection=tests.StateViewTests.rejection,
        provenance=tests.StateViewTests.provenance, checkpoint_schema_changed=False,
        source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
        full_historical_suite_rerun=False, independent_audit=False)
    (out/'validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    run()
