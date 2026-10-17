"""Run the outbound experiment, relevant old tests, and exact actual records."""
from pathlib import Path
import hashlib
import json
import sys
import time
import unittest

import outbound as port

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def run():
    started = time.monotonic()
    result = port.run()
    raw = (json.dumps(result, default=port.encode, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    (HERE / 'outbound_result.json').write_bytes(raw)
    print(json.dumps(dict(stage='main-finished', groups=result['groups'])), flush=True)
    tests = unittest.defaultTestLoader.discover(str(HERE), pattern='test_*.py')
    tests.addTests(unittest.defaultTestLoader.discover(str(ROOT/'vendor/three-plus-one/tests'), pattern='test_*.py'))
    for module in ('test_recursive_upper_decoder', 'test_certified_correction_release', 'test_completed_single_flower'):
        tests.addTests(unittest.defaultTestLoader.loadTestsFromName(module))
    tested = unittest.TextTestRunner(verbosity=1).run(tests)
    if not tested.wasSuccessful():
        raise AssertionError('the outbound or related source checks failed')
    p = port.prepare()
    requirement = port.primary_requirement()
    alternate = port.alternative_requirement(p).requirement
    records = [('keep-primary', 'keep', requirement), ('erase-primary', 'erase', requirement),
               ('keep-alternate', 'keep', alternate)]
    output = HERE / 'records'
    output.mkdir(exist_ok=True)
    examples = []
    for name, mode, future in records:
        actual = port.execute(port.select(port.prepare(mode=mode), future, 1))
        content = (json.dumps(port.export_occurrence(actual), ensure_ascii=False, indent=2)+'\n').encode('utf-8')
        target = output / (name+'.record.json')
        target.write_bytes(content)
        restored = port.import_occurrence(json.loads(content), future, mode=mode, free_choice=1)
        if restored != actual:
            raise AssertionError('exact joint occurrence did not round trip')
        examples.append(dict(path=target.relative_to(ROOT).as_posix(), bytes=len(content),
                             sha256=hashlib.sha256(content).hexdigest(),
                             contact_index=actual.neural_contact.contact_index,
                             closure_error=float(actual.closure_error)))
    report = dict(passed=True, date='2026-10-17', groups=result['groups'],
                  tests=tested.testsRun, outbound_tests=23, upstream_three_plus_one_tests=10,
                  exact_joint_records=3, main_result_sha256=hashlib.sha256(raw).hexdigest(),
                  examples=examples, seconds=round(time.monotonic()-started, 3),
                  full_baseline_252_rerun=False)
    (HERE / 'RR56-driver-validation.json').write_bytes(
        (json.dumps(report, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    print(json.dumps(report), flush=True)
    return report


if __name__ == '__main__':
    run()
