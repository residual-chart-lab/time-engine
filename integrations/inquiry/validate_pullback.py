"""RR61 study and exact current/previous protocol regressions."""
from pathlib import Path
import hashlib,json,unittest
import rr61_study as e

def run():
    result=e.run()
    names=('test_future_pullback','test_internal_port','test_portability','test_two_flower_connection')
    counts={name:unittest.defaultTestLoader.loadTestsFromName(name).countTestCases() for name in names}
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    tested=unittest.TextTestRunner(verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('pullback or existing certification/transport checks failed')
    report=dict(date='2026-10-20',passed=True,new_groups=len(result['groups']),
        new_tests=counts[names[0]],reused_tests={n:counts[n] for n in names[1:]},total_tests=tested.testsRun,
        decisions=result['decisions'],current_and_future_executions=result['current_and_future_executions'],
        certified_future_closures=result['certified_future_closures'],
        forward_equivalence=True,TE_exclusive_property_demonstrated=False,
        result_sha256=hashlib.sha256((e.OUTPUT/'result.json').read_bytes()).hexdigest(),
        starts_sha256=hashlib.sha256((e.OUTPUT/'starts.json').read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('fibre_geometry.py','word_fibre.py','future_pullback.py','rr61_study.py',
                         'test_future_pullback.py','validate_pullback.py')},
        full_RR57_128_family_rerun=False,actual_second_OS_test=False)
    e.write(e.OUTPUT/'validation.json',report)
    print(json.dumps(report),flush=True)
    return report

if __name__=='__main__':run()
