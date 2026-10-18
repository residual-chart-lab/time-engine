"""RR59 finite study, trigger boundary checks, and unchanged RR58 tests."""
from pathlib import Path
import hashlib,json,unittest
import rr59_study as e


def run():
    result=e.run()
    names=('test_inquiry_probe','test_deferred')
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    tested=unittest.TextTestRunner(verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('inspection or retained-readout checks failed')
    report=dict(date='2026-10-18',passed=True,new_groups=len(result['groups']),
        new_tests=unittest.defaultTestLoader.loadTestsFromName(names[0]).countTestCases(),
        unchanged_RR58_tests=unittest.defaultTestLoader.loadTestsFromName(names[1]).countTestCases(),
        total_tests=tested.testsRun,
        result_sha256=hashlib.sha256((e.OUTPUT/'result.json').read_bytes()).hexdigest(),
        starts_sha256=hashlib.sha256((e.OUTPUT/'starts.json').read_bytes()).hexdigest(),
        source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')},
        full_baseline_252_rerun=False,actual_second_os_test_performed=False,
        LLM_telemetry_or_biological_mechanism_validated=False)
    e.write(e.OUTPUT/'validation.json',report)
    print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':run()
