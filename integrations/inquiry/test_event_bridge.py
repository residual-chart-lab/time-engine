import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from copy import deepcopy
from unittest.mock import patch

import event_bridge as bridge
import step_session as e2
from test_step_session import RAW, SHA, DIGEST, ROOT

REQUEST = dict(context='mixed', strengths=['0', '0'], frame='identity')
CHOICE = dict(op='choose', v='1', u='0', word='HHHSUT')


def fresh():
    return bridge.Episode.receive(RAW, SHA, DIGEST)


def seed(p):
    p.apply(dict(op='record', id='received', origin='received', source='user-provided prior history',
                 text='An earlier question and its correction; its origin is not inferred.'))
    p.apply(dict(op='record', id='now', origin='reported_in_session', source='current caller',
                 text='May the E1 retained coordinate s be omitted for this continuation?'))
    p.apply(dict(op='goal', id='C1', text='Preserve the declared continuation construction', events=['now']))
    p.apply(dict(op='goal', id='Monday', text='Carry the chosen commitment into future conversation',
                 events=['received', 'now']))
    return p


def bind(p, **changes):
    cmd = dict(op='bind', goal='C1', requirement=deepcopy(REQUEST), coordinates={'s': ['now']},
               correspondence='s is the E1 coordinate referenced by this question. This does not measure personality.')
    cmd.update(changes)
    return p.apply(cmd)


def inspect(p, choice=None, **changes):
    bind(p, **changes)
    p.apply(choice or CHOICE)
    return p.apply(dict(op='inspect', omitted=['s']))


def prepare(p):
    r = inspect(p)
    return p.apply(dict(op='resolve', inspection=r['outcome']['id'], retention='preserve'))


class EventBridgeTests(unittest.TestCase):
    def test_real_diagnostic_changes_available_step_and_actual_execution_matches_e2(self):
        p = seed(fresh())
        r = inspect(p)
        report = r['outcome']['report']
        self.assertTrue(report['current']['equal'])
        self.assertEqual(report['requested']['relation'], 'DIFFERENT_EXISTENCE')
        self.assertEqual(report['requested']['original_status'], 'ADMISSIBLE')
        self.assertEqual(report['requested']['projected_status'], 'EMPTY')
        self.assertEqual(r['status']['next_step'], 'retain_the_difference_or_revise_the_choice')
        self.assertIsNone(r['status']['permit'])
        before = p.snapshot()
        with self.assertRaises(ValueError):
            p.apply(dict(op='resolve', inspection=r['outcome']['id'], retention='erase'))
        self.assertEqual(p.snapshot(), before)
        p.apply(dict(op='resolve', inspection=r['outcome']['id'], retention='preserve'))
        phases = []
        for _ in range(4):
            result = p.apply(dict(op='advance', permit=p.status()['permit']))
            phases.append(result['status']['engine']['phase'])
        self.assertEqual(phases, ['CLOSED1', 'CLOSED2', 'CLOSED3', 'STOPPED'])
        self.assertTrue(p.status()['engine']['certified'])
        self.assertEqual(p.status()['episode'], 'OPEN')
        goals = {g['id']: g for g in p.status()['goals']}
        self.assertEqual(goals['C1']['model_status'], 'SCOPED_MODEL_CERTIFIED')
        self.assertEqual(goals['Monday']['model_status'], 'UNMAPPED')
        self.assertTrue(all(g['status'] == 'OPEN' and not g['semantic_certification'] for g in goals.values()))
        direct = e2.Session.receive(RAW, SHA, DIGEST)
        for cmd in [dict(op='bind', requirement=REQUEST), CHOICE, dict(op='resolve')] + [dict(op='advance')]*4:
            direct.apply(cmd)
        self.assertEqual(p._session.snapshot(), direct.snapshot())
        self.assertEqual(p.status()['reads'], dict(diagnostic_exact_source_reads=2,
                                                 execution_exact_queries=3, combined_exact_queries=5))

    def test_then_known_history_and_later_interpretation_do_not_rewrite_one_another(self):
        p = seed(fresh())
        horizon = p.status()['accepted_commands']
        original = p.recall('Monday', horizon)
        snapshot, _ = p.snapshot()
        prefix = json.loads(snapshot)['journal']
        p.apply(dict(op='record', id='later', origin='reported_in_session', source='later caller',
                     text='The correction now matters to a new question.'))
        p.apply(dict(op='relate', goal='Monday', events=['received', 'later'],
                     note='Later interpretation, not knowledge attributed to the earlier event.'))
        p.apply(dict(op='goal', id='Christmas', text='Distribute on 2026-12-25', events=['now', 'later']))
        self.assertEqual(p.recall('Monday', horizon), original)
        self.assertEqual(json.loads(p.snapshot()[0])['journal'][:len(prefix)], prefix)
        recent = p.recall('Monday')
        self.assertEqual({e['origin'] for e in recent['events']}, {'received', 'reported_in_session'})
        self.assertEqual(recent['relations_and_model_evidence'][-1]['outcome']['evidence_kind'], 'later_interpretation')
        self.assertFalse(recent['relations_and_model_evidence'][-1]['outcome']['necessity_proved'])
        self.assertIn('now', [e['id'] for e in p.recall('Christmas')['events']])

    def test_unmapped_natural_goal_cannot_certify_itself_or_execute(self):
        p = seed(fresh())
        before = p.snapshot()
        for cmd in [dict(op='choose', v=1, u=0, word='HHHSUT'),
                    dict(op='advance', permit='Monday'),
                    dict(op='resolve', inspection='Monday', retention='preserve'),
                    dict(op='close', goal='Monday')]:
            with self.assertRaises(ValueError):
                p.apply(cmd)
            self.assertEqual(p.snapshot(), before)

    def test_requirement_and_choice_changes_invalidate_old_evidence_and_permission(self):
        p = seed(fresh()); prepare(p)
        old_permit = p.status()['permit']; old_inspection = p.status()['inspection']['id']
        bind(p, requirement=dict(REQUEST, frame='split'))
        self.assertIsNone(p.status()['permit']); self.assertIsNone(p.status()['inspection'])
        with self.assertRaises(ValueError):
            p.apply(dict(op='advance', permit=old_permit))
        p.apply(CHOICE)
        with self.assertRaises(ValueError):
            p.apply(dict(op='resolve', inspection=old_inspection, retention='preserve'))
        result = p.apply(dict(op='inspect', omitted=['s']))
        self.assertNotEqual(result['outcome']['id'], old_inspection)
        p.apply(dict(op='resolve', inspection=result['outcome']['id'], retention='preserve'))
        p.apply(dict(op='choose', v=0, u=0, word='HHHSUT'))
        self.assertIsNone(p.status()['permit']); self.assertIsNone(p.status()['inspection'])

    def test_unknown_and_empty_results_request_revision_instead_of_permission(self):
        for request, choice, relation in [
            (dict(REQUEST, context='outside_chart'), CHOICE, 'UNDETERMINED'),
            (REQUEST, dict(CHOICE, v='0'), 'SAME_EMPTY'),
        ]:
            p = seed(fresh()); result = inspect(p, choice, requirement=request)
            self.assertEqual(result['outcome']['report']['requested']['relation'], relation)
            self.assertIsNone(result['status']['permit'])
            before = p.snapshot()
            with self.assertRaises(ValueError):
                p.apply(dict(op='resolve', inspection=result['outcome']['id'], retention='preserve'))
            self.assertEqual(p.snapshot(), before)

    def test_same_action_is_a_scoped_deferral_not_erasure(self):
        entry = e2.n.a.register(('erase', 'keep'))
        p = seed(bridge.Episode(e2.Session(entry)))
        result = inspect(p, requirement=dict(REQUEST, context='main'))
        self.assertEqual(result['outcome']['report']['requested']['relation'], 'SAME_NEW_ACTION')
        self.assertEqual(result['status']['next_step'], 'difference_may_stay_unexpanded_in_this_scope_not_erased')
        self.assertFalse(result['status']['erasure_authorized'])
        self.assertFalse(result['outcome']['report']['execution_authorized'])

    def test_closed_past_stays_closed_while_later_goals_remain_recordable(self):
        p = seed(fresh()); prepare(p)
        old_permit = p.status()['permit']
        p.apply(dict(op='advance', permit=old_permit))
        before = p.snapshot()
        for cmd in [dict(op='advance', permit=old_permit), CHOICE]:
            with self.assertRaises(ValueError): p.apply(cmd)
            self.assertEqual(p.snapshot(), before)
        with self.assertRaises(ValueError): bind(p)
        self.assertEqual(p.snapshot(), before)
        p.apply(dict(op='goal', id='Later', text='A later open question', events=['now']))
        self.assertEqual(p.status()['engine']['phase'], 'CLOSED1')
        self.assertEqual(p.status()['goals'][-1]['model_status'], 'UNMAPPED')

    def test_checkpoint_preserves_open_goals_reports_evidence_and_next_motion(self):
        p = seed(fresh()); prepare(p)
        for stage in range(3):
            if stage: p.apply(dict(op='advance', permit=p.status()['permit']))
            raw, sha = p.snapshot()
            restored = bridge.Episode.restore(e2.Session.receive(RAW, SHA, DIGEST), raw, sha)
            self.assertEqual(restored.snapshot(), (raw, sha))
            self.assertEqual(restored.status(), p.status())
            restored.apply(dict(op='advance', permit=restored.status()['permit']))
            self.assertEqual(restored.status()['engine']['closed_flowers'], min(stage+1, 3))

    def test_checkpoint_rejects_forged_report_permission_provenance_and_chronology(self):
        p = seed(fresh()); prepare(p)
        doc = json.loads(p.snapshot()[0])
        variants = []
        def altered(mutator):
            item = deepcopy(doc); mutator(item); variants.append(item)
        altered(lambda d: d['journal'][0]['command'].update(origin='reported_in_session'))
        altered(lambda d: d['journal'][0]['outcome'].update(evidence_kind='engine_execution'))
        altered(lambda d: d['journal'][-2]['outcome']['report']['requested'].update(projected_status='ADMISSIBLE'))
        altered(lambda d: d['journal'][-1]['outcome'].update(permit='0'*64))
        altered(lambda d: d['journal'].reverse())
        altered(lambda d: d['current'].update(numerical_reads=0))
        # A hash chain replay comparison must also reject Python's True == 1 ambiguity.
        altered(lambda d: d['journal'][0].update(seq=True))
        for item in variants:
            raw = bridge.encode(item)
            with self.assertRaises(ValueError):
                bridge.Episode.restore(e2.Session.receive(RAW, SHA, DIGEST), raw, hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError):
            bridge.Episode.restore(e2.Session.receive(RAW, SHA, DIGEST), *[p.snapshot()[0], '0'*64])

    def test_status_and_input_edits_do_not_change_retained_state(self):
        p = seed(fresh()); result = inspect(p)
        before = p.snapshot()
        result['status']['events'][0]['origin'] = 'engine_execution'
        result['status']['inspection']['report']['requested']['relation'] = 'SAME_NEW_ACTION'
        result['outcome']['report']['erasure_authorized'] = True
        p.recall('Monday')['events'].clear()
        self.assertEqual(p.snapshot(), before)

    def test_invalid_mapping_and_future_references_fail_without_mutation(self):
        p = seed(fresh()); before = p.snapshot()
        for coordinates in [{}, {'s': ['future']}, {'future': ['now']}, {'s': ['now', 'now']}]:
            with self.assertRaises(ValueError): bind(p, coordinates=coordinates)
            self.assertEqual(p.snapshot(), before)
        bind(p); p.apply(CHOICE); before = p.snapshot()
        for omitted in [['t'], ['s', 's'], []]:
            with self.assertRaises(ValueError): p.apply(dict(op='inspect', omitted=omitted))
            self.assertEqual(p.snapshot(), before)

    def test_journal_budget_keeps_last_snapshot_restorable(self):
        p = fresh()
        for i in range(bridge.MAX_COMMANDS):
            p.apply(dict(op='record', id='e'+str(i), origin='received', source='fixture',
                         text='Unresolved reported event'))
        raw, sha = p.snapshot()
        with self.assertRaises(ValueError):
            p.apply(dict(op='record', id='overflow', origin='received', source='fixture', text='No room'))
        restored = bridge.Episode.restore(e2.Session.receive(RAW, SHA, DIGEST), raw, sha)
        self.assertEqual(restored.snapshot(), (raw, sha))
        self.assertEqual(restored.status()['commands_remaining'], 0)

    def test_cli_can_inspect_decide_execute_save_and_resume_without_internal_access(self):
        work = ROOT/'.work'; work.mkdir(exist_ok=True)
        import tempfile
        args = [sys.executable, '-I', '-B', str(ROOT/'run_event_session.py'),
                '--entry', str(ROOT/'integrations/inquiry/E1-entry.record.json'),
                '--trusted-sha256', SHA, '--expected-entry-digest', DIGEST]
        with tempfile.TemporaryDirectory(dir=work) as tmp:
            path = Path(tmp)/'episode.json'
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, encoding='utf-8')
            def send(cmd):
                process.stdin.write(json.dumps(cmd)+'\n'); process.stdin.flush()
                result = json.loads(process.stdout.readline())
                self.assertTrue(result['ok'], result)
                return result
            try:
                self.assertTrue(json.loads(process.stdout.readline())['ok'])
                send(dict(op='record', id='e', origin='received', source='fixture', text='E1 s coordinate'))
                send(dict(op='goal', id='C', text='Construct continuation', events=['e']))
                send(dict(op='bind', goal='C', requirement=REQUEST, coordinates={'s': ['e']},
                          correspondence='An explicit E1 coordinate reference, not text encoding'))
                send(CHOICE)
                r = send(dict(op='inspect', omitted=['s']))
                self.assertEqual(r['outcome']['report']['requested']['relation'], 'DIFFERENT_EXISTENCE')
                r = send(dict(op='resolve', inspection=r['outcome']['id'], retention='preserve'))
                r = send(dict(op='advance', permit=r['status']['permit']))
                self.assertEqual(r['status']['engine']['phase'], 'CLOSED1')
                save = send(dict(op='save', path=str(path)))
                send(dict(op='quit'))
                process.communicate(timeout=20)
                self.assertEqual(process.returncode, 0)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), save['sha256'])
                done = subprocess.run(args+['--resume', str(path), '--trusted-resume-sha256', save['sha256']],
                                      input='{"op":"recall","goal":"C"}\n{"op":"quit"}\n',
                                      capture_output=True, text=True, timeout=60, check=True)
                replies = [json.loads(line) for line in done.stdout.splitlines()]
                self.assertEqual(replies[0]['status']['engine']['phase'], 'CLOSED1')
                self.assertEqual(replies[1]['recall']['relations_and_model_evidence'][-1]['outcome']['evidence_kind'],
                                 'engine_execution')
            finally:
                if process.poll() is None:
                    process.kill(); process.communicate()


if __name__ == '__main__':
    unittest.main()

