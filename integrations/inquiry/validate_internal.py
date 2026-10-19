"""RR60 plus unchanged RR59/RR58 and RR53 connection checks."""
from pathlib import Path
import hashlib,json,unittest
import rr60_study as e


def run():
    result=e.run()
    names=('test_internal_port','test_inquiry_probe','test_deferred','test_two_flower_connection')
    counts={name:unittest.defaultTestLoader.loadTestsFromName(name).countTestCases() for name in names}
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    tested=unittest.TextTestRunner(verbosity=2).run(suite)
    if not tested.wasSuccessful():raise AssertionError('internal readout obligation or reused checks failed')
    report=dict(date='2026-10-19',passed=True,new_groups=len(result['groups']),
        new_tests=counts[names[0]],reused_tests={name:count for name,count in counts.items() if name!=names[0]},
        total_tests=tested.testsRun,local_first_flowers=24,current_connection_requests=48,
        new_legal_second_flowers=1,algebraic_cancellation_controls=2,
        result_sha256=hashlib.sha256((e.OUTPUT/'result.json').read_bytes()).hexdigest(),
        starts_sha256=hashlib.sha256((e.OUTPUT/'starts.json').read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('internal_port.py','rr60_study.py','test_internal_port.py','validate_internal.py')},
        full_RR57_128_family_rerun=False,full_baseline_252_rerun=False,
        actual_second_OS_test=False,live_LLM_telemetry_measured=False,
        general_attention_law_derived=False)
    e.write(e.OUTPUT/'validation.json',report)
    print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':run()
