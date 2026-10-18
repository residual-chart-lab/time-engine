"""Run RR58 and targeted unchanged TE decoder/producer checks."""
from dataclasses import asdict
from pathlib import Path
import hashlib,json,time,unittest
import experiment as e


def run():
    started=time.monotonic();result=e.run()
    names=('test_deferred','test_recursive_upper_decoder','test_certified_correction_release')
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    tested=unittest.TextTestRunner(verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('the deferred filter or reused TE checks failed')
    report=dict(date='2026-10-18',passed=True,new_groups=len(result['groups']),
        new_tests=unittest.defaultTestLoader.loadTestsFromName('test_deferred').countTestCases(),
        total_tests=tested.testsRun,query_cases=22,authenticated_RR57_records=3,
        full_RR57_128_family_reenumerated=False,full_baseline_252_rerun=False,
        seconds=round(time.monotonic()-started,3),
        result_sha256=hashlib.sha256((e.OUTPUT/'result.json').read_bytes()).hexdigest(),
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')})
    (e.OUTPUT/'validation.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':run()
