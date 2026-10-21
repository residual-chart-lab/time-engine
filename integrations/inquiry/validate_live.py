"""Run the scoped RR63 integration audit and write exact reproducible evidence."""
from pathlib import Path
import hashlib
import json
import unittest
from fractions import Fraction as Q
import test_live_flower as tests
import live_checkpoint as cp
from live_flower import te

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUT = ROOT / '.work/rr63-local'


def run():
    raw_inputs = (HERE / 'RR63-inputs.json').read_bytes()
    spec = json.loads(raw_inputs)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(tests.LiveFlowerTests)
    names = [t.id() for t in suite]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / 'validation.log').open('w') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('RR63 failed; inspect .work/rr63-local/validation.log')
    runs = tests.LiveFlowerTests.runs
    expected = {(m, Q(x), w) for m in spec['modes'] for x in spec['C_diagonal_x'] for w in spec['words']}
    if set(runs) != expected:
        raise AssertionError('test matrix differs from declared inputs')
    rows = []
    for (mode, x, word), s in runs.items():
        rows.append(dict(mode=mode, x=str(x), word=word, control=s.state.resolution.control,
            status=s.status(), source_weights=s.state.source.leaves()[0].weights,
            exact_future_endpoint=s.state.future_receipts[0][1].live.accumulated,
            matches_RR62_batch=True))
    files = [HERE / name for name in ('live_flower.py', 'live_checkpoint.py', 'test_live_flower.py',
                                      'validate_live.py', 'RR63-inputs.json')]
    files.append(ROOT / 'run_live.py')
    report = dict(base_commit=cp.BASE, passed=True, total_tests=result.testsRun,
        test_names=names, input_sha256=hashlib.sha256(raw_inputs).hexdigest(),
        source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        current_executions=rows, evidence=tests.LiveFlowerTests.evidence,
        new_dynamical_primitives=0, next_flower_same_future_C_certified=False,
        infinite_stability_tested=False, total_runtime_speedup_measured=False,
        independent_RR62_regression='Run validate_demand.py separately; not folded into this test count')
    raw = (json.dumps(report, ensure_ascii=False, indent=2, default=te.triple.encode) + '\n').encode()
    (OUTPUT / 'result.json').write_bytes(raw)
    print(json.dumps(dict(passed=True, tests=result.testsRun, current_cases=len(rows),
        continuation_cases=len(report['evidence']['continuations']),
        resumed_stages=len(report['evidence']['resumed_stages']),
        result_sha256=hashlib.sha256(raw).hexdigest(), output=str(OUTPUT)), indent=2))
    return report


if __name__ == '__main__':
    run()
