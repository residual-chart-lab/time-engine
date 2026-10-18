"""Validate RR57 plus RR56 and the reused decoder/connection machinery."""
from pathlib import Path
import argparse
import hashlib
import json
import time
import unittest

import three_flower as model


def transport_published():
    directory=Path(__file__).with_name('rr57-records')
    manifest=json.loads((directory/'manifest.json').read_bytes())
    if manifest['schema']!='time-engine-rr57-published-records-v1':
        raise ValueError('the pinned RR57 manifest is required')
    verified=[]
    for item in manifest['records']:
        target=(directory/item['path']).resolve()
        if not target.is_relative_to(directory.resolve()):
            raise ValueError('the published path escaped its record directory')
        raw=target.read_bytes()
        result=model.import_record(raw,model.triple.TerminalRequirement(model.Q(item['upper_x'])),
            mode=item['mode'],gain=model.Q(item['gain']),free_choice=item['free_choice'],
            trusted_sha256=item['sha256'])
        again=(json.dumps(model.export_record(result),ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
        if again!=raw: raise AssertionError('the original record graph bytes changed')
        verified.append(dict(path=item['path'],sha256=item['sha256'],exact_te_verified=True))
    return dict(passed=True,records=verified,upstream_snapshots_and_selection_evidence_authenticated=True,
        upstream_floating_point_regenerated=False,full_128_family_independently_recomputed=False)


def run():
    started=time.monotonic()
    result=model.run()
    old=model.port.run()
    if old['groups']!=9:
        raise AssertionError('the original outbound groups changed')
    names=('test_three_flower','test_outbound','test_portability',
           'test_recursive_upper_decoder','test_certified_correction_release','test_completed_single_flower',
           'test_two_flower_connection','test_three_flower_constraint')
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names)
    suite.addTests(unittest.defaultTestLoader.discover(str(model.port.ROOT/'vendor/three-plus-one/tests'),pattern='test_*.py'))
    tested=unittest.TextTestRunner(verbosity=2).run(suite)
    if not tested.wasSuccessful():
        raise AssertionError('embedded experiment or related checks failed')
    report=dict(date='2026-10-18',passed=True,new_groups=len(result['groups']),outbound_groups=old['groups'],
        new_tests=16,total_tests=tested.testsRun,full_baseline_252_rerun=False,
        seconds=round(time.monotonic()-started,3),
        result_sha256=hashlib.sha256((model.OUTPUT/'result.json').read_bytes()).hexdigest(),
        python_source_sha256={str(Path(name).relative_to(model.port.ROOT)).replace('\\','/'):
            hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in
            (model.__file__,__file__,str(Path(__file__).with_name('test_three_flower.py')))})
    (model.OUTPUT/'validation.json').write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--transport-only',action='store_true')
    args=parser.parse_args()
    if args.transport_only:
        print(json.dumps(transport_published(),indent=2))
    else:
        run()
