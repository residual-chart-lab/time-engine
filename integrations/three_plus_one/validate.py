"""Run the outbound experiment, relevant old tests, and exact actual records."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import time
import unittest

import outbound as port

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def transport_published():
    """Use pinned source snapshots and exact receiver checks; no local SGD."""
    manifest = json.loads((HERE/'records/manifest.json').read_bytes())
    if (manifest['schema'] != 'time-engine-3plus1-published-records-v1'
            or manifest['source_commit'] != 'd7a8387ec26fc2b06b454337063f2336e418a686'):
        raise ValueError('the declared published record source is required')
    examples = []
    for item in manifest['records']:
        config = port.CourseConfig(item['config']['start_epoch'], item['config']['carry_epochs'], tuple(item['config']['order']))
        spec = port.PortSpec(port.Q(item['spec']['gain']), item['spec']['reference_contact'])
        data = item['requirement']
        future = port.FutureRequirement(tuple(tuple(port.Q(v) for v in row) for row in data['context']),
                                        tuple(port.Q(v) for v in data['result']), port.Q(data['tolerance']))
        path = (HERE/item['path']).resolve()
        if not path.is_relative_to((HERE/'records').resolve()):
            raise ValueError('the published record path escaped its directory')
        raw = path.read_bytes()
        actual = port.import_occurrence(raw, future, config, item['mode'], spec, item['free_choice'],
                                       verification='transport', trusted_sha256=item['sha256'])
        examples.append(dict(path=item['path'], sha256=hashlib.sha256(raw).hexdigest(),
                             exact_receiver_verified=True, contact_index=actual.neural_contact.contact_index))
    report = dict(passed=True, verification='trusted-hash transport', published_records=len(examples),
                  source_snapshots_preserved=True, exact_port_and_receiver_verified=True,
                  upstream_floating_point_regenerated=False,
                  independent_upstream_dynamics_verified=False, examples=examples)
    return report


def run():
    started = time.monotonic()
    result = port.run()
    raw = (json.dumps(result, default=port.encode, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    port.LOCAL_OUTPUT.mkdir(parents=True, exist_ok=True)
    (port.LOCAL_OUTPUT / 'outbound_result.json').write_bytes(raw)
    print(json.dumps(dict(stage='main-finished', groups=result['groups'])), flush=True)
    tests = unittest.defaultTestLoader.discover(str(HERE), pattern='test_*.py')
    outbound_tests = tests.countTestCases()
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
    output = port.LOCAL_OUTPUT / 'records'
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
                  tests=tested.testsRun, outbound_tests=outbound_tests, upstream_three_plus_one_tests=10,
                  exact_joint_records=3, main_result_sha256=hashlib.sha256(raw).hexdigest(),
                  examples=examples, seconds=round(time.monotonic()-started, 3),
                  full_baseline_252_rerun=False, published_transport=transport_published())
    (port.LOCAL_OUTPUT / 'RR56-driver-validation.json').write_bytes(
        (json.dumps(report, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    print(json.dumps(report), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--transport-only', action='store_true', help='read pinned records without regenerating upstream floats')
    args = parser.parse_args()
    if args.transport_only:
        print(json.dumps(transport_published(), indent=2))
    else:
        run()
