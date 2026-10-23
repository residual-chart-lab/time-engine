"""Focused E1 tests and the unchanged three-flower consumer regressions."""
from pathlib import Path
import unittest,hashlib,json
import test_entry_transport as tests
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.work/e1-validation'


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((HERE/'E1-BASELINE.json').read_bytes())
    for item in baseline['files']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    names=('test_entry_transport','test_three_flower_synthesis')
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    with (OUT/'tests.log').open('w',encoding='utf-8',newline='\n') as log:result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    if not result.wasSuccessful():raise AssertionError('see .work/e1-validation/tests.log')
    raw,h=tests.EntryTransportTests.raw,tests.EntryTransportTests.sha
    (OUT/'entry.record.json').write_bytes(raw)
    report=dict(schema='time-engine-e1-entry-validation-v1',passed=True,base_commit='fbf0bb413436f26b29825addccd435aace288fa3',
        unchanged_baseline_files=len(baseline['files']),tests=result.testsRun,new_entry_tests=11,three_flower_regression_tests=31,
        entry_digest=tests.EntryTransportTests.digest,entry_sha256=h,entry_bytes=len(raw),entry_nodes=len(json.loads(raw)['graph']['nodes']),
        fresh_process=tests.EntryTransportTests.fresh_report,old_record_byte_identity_claimed=False,
        limits=dict(max_bytes=tests.wire.MAX_BYTES,max_nodes=tests.wire.MAX_NODES),supported_profile=tests.wire.MODEL,
        different_environment_tested=False,full_247_regression_rerun=False,
        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'entry_transport.py',HERE/'test_entry_transport.py',HERE/'validate_entry_transport.py',HERE/'E1-BASELINE.json',ROOT/'run_entry_transport.py')})
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(report,indent=2),flush=True);return report

if __name__=='__main__':run()
