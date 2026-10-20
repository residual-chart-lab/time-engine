"""RR62 plus RR61, Free Numbers and transport regressions."""
from pathlib import Path
import hashlib,json,unittest
import rr62_study as e

def run(reuse_study=False):
    result=json.loads((e.OUTPUT/'result.json').read_bytes()) if reuse_study else e.run()
    names=('test_demand_filter','test_future_pullback','test_deferred','test_portability')
    counts={n:unittest.defaultTestLoader.loadTestsFromName(n).countTestCases() for n in names}
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in names)
    tested=unittest.TextTestRunner(verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('demand, execution or reused protocol tests failed')
    report=dict(date='2026-10-20',passed=True,new_groups=len(result['groups']),new_tests=counts[names[0]],
        reused_tests={n:counts[n] for n in names[1:]},total_tests=tested.testsRun,
        queries=168,exact_shift_reads=result['exact_shift_reads'],actual_executions=result['actual_executions'],
        certified_future_closures=result['certified_future_closures'],
        result_sha256=hashlib.sha256((e.OUTPUT/'result.json').read_bytes()).hexdigest(),
        starts_sha256=hashlib.sha256((e.OUTPUT/'starts.json').read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('demand_filter.py','retained_execution.py','rr62_study.py','test_demand_filter.py','validate_demand.py')},
        full_RR57_128_family_rerun=False,actual_second_OS_test=False,
        full_TE_speedup_or_storage_reduction_measured=False)
    e.write(e.OUTPUT/'validation.json',report);print(json.dumps(report),flush=True);return report

if __name__=='__main__':run()
