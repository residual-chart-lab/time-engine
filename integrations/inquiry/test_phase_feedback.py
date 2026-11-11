import hashlib,json,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
import step_session as api
from test_step_session import RAW,SHA,DIGEST,REQUEST
ROOT=Path(__file__).resolve().parents[2]


class FeedbackTests(unittest.TestCase):
    def test_cli_distinguishes_rejection_reasons_and_clears_stale_feedback(self):
        contexts=['mixed','outside_chart','zero_head','mixed']
        commands=[]
        for context in contexts:
            commands.extend([dict(op='bind',requirement=dict(REQUEST,context=context)),
                dict(op='choose',v='1',u='0',word='HHHSUT'),dict(op='resolve'),dict(op='status')])
        commands.append(dict(op='quit'))
        result=subprocess.run([sys.executable,'-I',str(ROOT/'run_time_engine.py'),'--entry',str(ROOT/'integrations/inquiry/E1-entry.record.json'),
            '--trusted-sha256',SHA,'--expected-entry-digest',DIGEST],input='\n'.join(json.dumps(x) for x in commands)+'\n',text=True,capture_output=True,check=True)
        rows=[json.loads(x) for x in result.stdout.splitlines()]
        self.assertEqual(len(rows),len(commands)+1)
        self.assertTrue(all(x['ok'] for x in rows))
        statuses=[]
        for i in range(4):
            bound,chosen,resolved,observed=rows[1+4*i:5+4*i]
            self.assertIsNone(bound['status']['assessment_status'])
            self.assertIsNone(bound['status']['plan_status'])
            self.assertIsNone(chosen['status']['assessment_status'])
            self.assertEqual(resolved['status'],observed['status'])
            statuses.append(resolved['status'])
        self.assertEqual([x['assessment_status'] for x in statuses],['ADMISSIBLE','UNKNOWN_CHART','EMPTY','ADMISSIBLE'])
        self.assertEqual([x['phase'] for x in statuses],['READY','REJECTED','REJECTED','READY'])
        self.assertEqual(['advance' in x['phase_operations'] for x in statuses],[True,False,False,True])
        self.assertEqual(statuses[-1]['last_resolution_work']['total_exact_queries'],0)
        self.assertEqual(statuses[-1]['numerical_reads'],statuses[0]['numerical_reads'])
        type(self).cli_summary=dict(contexts=contexts,assessment_statuses=[x['assessment_status'] for x in statuses],
            repeated_resolution_additional_reads=0,status_observation_changed_state=False)

    def test_audited_P0_checkpoint_bytes_survive_feedback_and_motion(self):
        path=ROOT/'integrations/inquiry/fixtures/P0-first-use-CLOSED1.record.json'
        raw=path.read_bytes();sha='7eeacc493777697c6dec70831b9307f20918edc1d6fd566fe08d61582199a476'
        self.assertEqual(hashlib.sha256(raw).hexdigest(),sha)
        entry=api.wire.loads(RAW,SHA,DIGEST)
        s=api.Session.restore(entry,raw,sha)
        self.assertEqual(s.snapshot(),(raw,sha))
        with patch.object(entry.base.vault,'exact',side_effect=AssertionError('feedback must not read source values')), \
             patch.object(entry.derived,'exact',side_effect=AssertionError('feedback must not read observations')):
            info=s.status()
        self.assertEqual(info['assessment_status'],'ADMISSIBLE')
        self.assertEqual(info['phase_operations'],['advance','status','save','quit'])
        self.assertEqual(info['commands_remaining'],64-info['accepted_commands'])
        self.assertEqual(s.snapshot(),(raw,sha))
        phases=[s.apply(dict(op='advance'))['phase'] for _ in range(3)]
        self.assertEqual(phases,['CLOSED2','CLOSED3','STOPPED'])
        self.assertTrue(s.status()['certified']);self.assertEqual(s.status()['stock'],9)
        # A displayed hint is not an execution capability.
        displayed=s.status();displayed['phase_operations'].append('advance')
        before=s.snapshot()
        with self.assertRaises(ValueError):s.apply(dict(op='advance'))
        self.assertEqual(s.snapshot(),before)
        self.assertNotIn('advance',s.status()['phase_operations'])
        type(self).legacy_summary=dict(snapshot_sha256=sha,original_bytes_preserved=True,feedback_additional_exact_reads=0,
            resumed_from='CLOSED1',phase='STOPPED',certified=True,stock=9,hints_do_not_override_guards=True)

    def test_budget_exhaustion_still_leaves_recovery_operations(self):
        s=api.Session.receive(RAW,SHA,DIGEST)
        before=s.snapshot()
        with patch.object(api,'MAX_COMMANDS',0):
            status=s.status()
            self.assertEqual(status['commands_remaining'],0)
            self.assertEqual(status['phase_operations'],['status','save','quit'])
            with self.assertRaises(ValueError):s.apply(dict(op='bind',requirement=REQUEST))
            self.assertEqual(s.snapshot(),before)


if __name__=='__main__':unittest.main()
