import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import preservation_targets as target
import step_session as api
import three_flower_synthesis as n
import three_flower_session as live
import rr69_study as study
from test_step_session import RAW, SHA, DIGEST, ROOT, REQUEST


def entry():
    return api.wire.loads(RAW, SHA, DIGEST)


def request(e, context='mixed', strengths=('0','0')):
    return api.requirement(e, dict(context=context, strengths=list(strengths), frame='identity'))[0]


class PreservationTests(unittest.TestCase):
    def test_same_current_endpoint_can_lose_the_declared_continuation_without_erasing_the_archive(self):
        e=entry();scope=request(e);before=api.wire.dumps(e);past=e.base.engine
        reports=[]
        with patch.object(n.plant,'produce',side_effect=AssertionError('diagnosis must not execute future sources')):
            for omitted in (('s',),('t',),('s','t')):
                r=target.compare(e,scope,1,0,'HHHSUT',omitted)
                self.assertTrue(r['current']['equal'])
                self.assertEqual(r['current']['original'],['-1','0','0','0'])
                self.assertEqual(r['requested']['relation'],'DIFFERENT_EXISTENCE')
                self.assertEqual(r['requested']['original_status'],'ADMISSIBLE')
                self.assertEqual(r['requested']['projected_status'],'EMPTY')
                self.assertFalse(r['execution_authorized']);self.assertFalse(r['erasure_authorized'])
                self.assertEqual(r['exact_source_reads'],2)
                reports.append(r)
        self.assertIs(e.base.engine,past)
        self.assertEqual(api.wire.dumps(e),before)
        self.assertEqual(e.derived._records(),())
        type(self).separation=reports

    def test_prediction_matches_independent_matrices_and_real_closure_controls(self):
        e=entry();scope=request(e);r=target.compare(e,scope,1,0,'HHHSUT',('s',))
        original=study.oracle(e,scope,1,0,'HHHSUT')
        self.assertEqual(r['requested']['original_status'],original[0])
        self.assertEqual(r['requested']['original_new_action_digest'],n.a.fingerprint(original[1:4]))
        done=live.finish(live.resolve(live.choose(live.start(e,scope),1,0,'HHHSUT'))[0])
        self.assertTrue(done.certified)
        self.assertEqual([f.engine.upper.live.accumulated for f in done.flowers],[n.b.NEG]*3)
        self.assertEqual(done.upper[1].live.accumulated,n.b.ONE)
        erased=n.a.register(('erase','keep'));escope=request(erased)
        direct=study.oracle(erased,escope,1,0,'HHHSUT')
        self.assertEqual(direct[0],r['requested']['projected_status'])
        counter=study.counterfactual(erased,escope)
        self.assertEqual(counter['local_endpoints'],[n.b.NEG]*3)
        self.assertEqual(counter['upper_endpoint'],(0,0,0,0))
        self.assertFalse(counter['certified']);self.assertFalse(counter['successful_record_issued'])
        type(self).execution_control=dict(original_certified=True,original_upper=list(map(str,done.upper[1].live.accumulated)),
            projected_control_locals=[list(map(str,q)) for q in counter['local_endpoints']],
            projected_control_upper=list(map(str,counter['upper_endpoint'])),projected_success_record_issued=False,
            original_action_matches_independent_matrix_solve=True)

    def test_two_empty_action_sets_are_not_reported_as_a_success(self):
        e=entry();r=target.compare(e,request(e),0,0,'HHHSUT',('s',))
        self.assertTrue(r['current']['equal'])
        self.assertEqual(r['requested']['relation'],'SAME_EMPTY')
        self.assertEqual(r['requested']['original_status'],'EMPTY')
        self.assertIsNone(r['requested']['original_new_action_digest'])
        self.assertFalse(r['execution_authorized'])

    def test_unknown_chart_is_not_converted_into_same_or_different_future(self):
        e=entry();r=target.compare(e,request(e,'outside_chart'),1,0,'HHHSUT',('s',))
        self.assertTrue(r['current']['equal'])
        self.assertEqual(r['requested']['original_status'],'UNKNOWN_CHART')
        self.assertEqual(r['requested']['projected_status'],'UNKNOWN_CHART')
        self.assertEqual(r['requested']['relation'],'UNDETERMINED')

    def test_zero_difference_control_has_the_same_requested_action(self):
        e=n.a.register(('erase','keep'));scope=request(e,'main')
        r=target.compare(e,scope,1,0,'HHHSUT',('s',))
        self.assertEqual(r['requested']['relation'],'SAME_NEW_ACTION')
        self.assertEqual(r['requested']['original_new_action_digest'],r['requested']['projected_new_action_digest'])
        direct=study.oracle(e,scope,1,0,'HHHSUT')
        self.assertEqual(direct[0],'ADMISSIBLE')
        self.assertEqual(r['requested']['original_new_action_digest'],n.a.fingerprint(direct[1:4]))

    def test_changed_scope_invalid_projection_and_report_as_permission_are_rejected(self):
        e=entry();scope=request(e);other=entry()
        for omitted in ((),('s','s'),('future',),('s',1),'s'):
            with self.assertRaises(ValueError):target.compare(e,scope,1,0,'HHHSUT',omitted)
        from dataclasses import replace
        with self.assertRaises(ValueError):
            target.compare(e,replace(scope,base_scope=replace(scope.base_scope,entry_digest='0'*64)),1,0,'HHHSUT',('s',))
        report=target.compare(e,scope,1,0,'HHHSUT',('s',))
        report['execution_authorized']=True
        session=api.Session(other);before=session.snapshot()
        with self.assertRaises(ValueError):session.apply(dict(op='advance',assessment=report))
        self.assertEqual(session.snapshot(),before)

    def test_real_external_cli_reports_the_targets_and_rejects_invalid_input(self):
        args=[sys.executable,'-I',str(ROOT/'run_preservation_check.py'),'--entry',str(ROOT/'integrations/inquiry/E1-entry.record.json'),
              '--trusted-sha256',SHA,'--expected-entry-digest',DIGEST]
        result=subprocess.run(args+['--omit','s'],capture_output=True,text=True,check=True)
        response=json.loads(result.stdout)
        self.assertTrue(response['ok']);self.assertTrue(response['assessment']['current']['equal'])
        self.assertEqual(response['assessment']['requested']['relation'],'DIFFERENT_EXISTENCE')
        bad=subprocess.run(args+['--omit','s','s'],capture_output=True,text=True)
        self.assertEqual(bad.returncode,2);self.assertFalse(json.loads(bad.stdout)['ok'])


if __name__=='__main__':unittest.main()
