"""Meaningful persistence/host tests; all notes and sessions here are synthetic.

The receiver processes are Python/TE processes, NOT separate reasoning models.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import unittest
import uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE
BACKEND=ROOT/'open_use/te_use.py'
SPEC=importlib.util.spec_from_file_location('continuity_under_test',HERE/'continuity.py')
H=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(H)


def frame(role,text,phase=None):
    p=dict(type='message',role=role,content=[dict(type='output_text' if role=='assistant' else 'input_text',text=text)])
    if phase: p['phase']=phase
    return H.encoded(dict(type='response_item',timestamp='2026-11-19T00:00:00Z',payload=p)).replace(b'\n',b'')+b'\n'


class ContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=ROOT/'work'/('te-continuity-check-'+uuid.uuid4().hex[:10])
        cls.evidence.mkdir(parents=True)
        cls.ws=cls.evidence/'room'
        result=cls.call('init','--backend',str(BACKEND),'--work','synthetic continuity checks')
        assert result.returncode==0,result.stdout+result.stderr
        cls.session=cls.evidence/'source.jsonl'
        cls.session.write_bytes(frame('user','START\n original 🌿\n  spacing\t')+
                                frame('assistant','private scratch, must not be captured','analysis')+
                                frame('assistant','Visible reply','final_answer'))
        assert cls.call('capture','--session',str(cls.session),'--start-marker','START').returncode==0

    @classmethod
    def call(cls,*args,env=None):
        return subprocess.run([sys.executable,'-I','-B','-X','utf8',str(HERE/'continuity.py'),
                               '--workspace',str(cls.ws),*args],capture_output=True,text=True,
                              encoding='utf-8',env=env,timeout=90)

    def note(self,name,**overrides):
        request=dict(id=name,kind='candidate',actor='synthetic-main',actor_role='main',
                     sources=['s000001'],links=[],reading_time='current',
                     payload=dict(status='unresolved',reading='not yet classified',unknown_reason=None))
        request.update(overrides)
        path=self.evidence/(name+'.json'); path.write_bytes(H.encoded(request))
        return path

    def result(self,process):
        self.assertEqual(process.returncode,0,process.stdout+process.stderr)
        return json.loads(process.stdout)['result']

    def test_01_raw_bytes_and_visible_boundary(self):
        status=self.result(self.call('status'))
        self.assertEqual(status['sources'],2)
        actual=self.result(self.call('source','--id','s000001'))
        self.assertEqual(actual['text'],'START\n original 🌿\n  spacing\t')
        again=self.result(self.call('capture','--session',str(self.session)))
        self.assertEqual(again['captured'],0)

    def test_02_unfinished_source_frame_is_retried(self):
        raw=frame('user','Later observed source')
        with self.session.open('ab') as f: f.write(raw[:-1])
        self.assertEqual(self.result(self.call('capture','--session',str(self.session)))['captured'],0)
        with self.session.open('ab') as f: f.write(b'\n')
        self.assertEqual(self.result(self.call('capture','--session',str(self.session)))['captured'],1)

    def test_03_capture_scope_cannot_be_silently_widened(self):
        p=self.call('capture','--session',str(self.session),'--start-marker','different scope')
        self.assertEqual(p.returncode,2)

    def test_04_unknown_source_and_future_link_rejected(self):
        before=self.result(self.call('status'))['notes']
        self.assertEqual(self.call('note','--file',str(self.note('invalid-source',sources=['s999999']))).returncode,2)
        self.assertEqual(self.call('note','--file',str(self.note('invalid-link',links=['future-note']))).returncode,2)
        self.assertEqual(self.result(self.call('status'))['notes'],before)

    def test_05_te_read_survives_new_receiver_process(self):
        self.result(self.call('note','--file',str(self.note('first-reading',kind='reading',slot='current-reading',adoption='adopt'))))
        packet=self.result(self.call('resume'))
        first=[r for r in packet['records'] if r['slot']=='current-reading'][0]
        self.assertEqual(first['record']['payload']['request']['payload']['unknown_reason'],None)
        self.assertEqual(first['record']['payload']['source_refs'][0]['id'],'s000001')
        self.assertEqual(self.result(self.call('read','--id','first-reading'))['id'],'first-reading')

    def test_06_duplicate_cannot_overwrite_the_past(self):
        old=self.result(self.call('read','--id','first-reading'))
        p=self.call('note','--file',str(self.note('first-reading',payload={'reading':'rewrite past'})))
        self.assertEqual(p.returncode,2)
        self.assertEqual(self.result(self.call('read','--id','first-reading')),old)
        con=sqlite3.connect(self.ws/'archive.sqlite3')
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("UPDATE sources SET body=x'00' WHERE seq=1")
        finally: con.close()

    def test_07_death_after_intake_needs_no_final_handoff(self):
        path=self.note('queued-before-death',slot='open-candidate',adoption='adopt')
        env=dict(os.environ,TE_CONTINUITY_TEST_EXIT='after_intake')
        p=self.call('note','--file',str(path),env=env)
        self.assertEqual(p.returncode,83)
        self.assertIn('queued-before-death',self.result(self.call('status'))['pending'])
        packet=self.result(self.call('resume'))
        self.assertIn('queued-before-death',packet['recovered_pending'])
        self.assertIn('queued-before-death',[r['record']['id'] for r in packet['records']])

    def test_08_death_after_checkpoint_before_commit_is_recoverable(self):
        path=self.note('saved-before-death',slot='checkpoint-window',adoption='adopt')
        env=dict(os.environ,TE_CONTINUITY_TEST_EXIT='after_te_save')
        self.assertEqual(self.call('note','--file',str(path),env=env).returncode,83)
        before=self.result(self.call('status'))
        self.assertIn('saved-before-death',before['pending'])
        self.assertTrue(before['uncommitted_checkpoints'])
        packet=self.result(self.call('resume'))
        self.assertIn('saved-before-death',packet['recovered_pending'])
        self.assertEqual(self.result(self.call('read','--id','saved-before-death'))['id'],'saved-before-death')

    def test_09_commit_survives_missing_restart_pointer(self):
        env=dict(os.environ,TE_CONTINUITY_TEST_EXIT='after_commit')
        p=self.call('note','--file',str(self.note('committed-before-pointer',slot='pointer-window',adoption='adopt')),env=env)
        self.assertEqual(p.returncode,83)
        packet=self.result(self.call('resume'))
        self.assertIn('committed-before-pointer',[r['record']['id'] for r in packet['records']])
        bootstrap=json.loads((self.ws/'BOOTSTRAP.json').read_bytes())
        self.assertEqual(bootstrap['resume_sha256'],hashlib.sha256((self.ws/'RESUME.json').read_bytes()).hexdigest())

    def test_10_shelf_proposal_cannot_pin_the_main_state(self):
        request=self.note('shelf-imposition',actor='helper',actor_role='shelf',slot='self-image',adoption='adopt')
        self.assertEqual(self.call('note','--file',str(request)).returncode,2)
        self.result(self.call('note','--file',str(self.note('shelf-suggestion',actor='helper',actor_role='shelf'))))

    def test_11_revision_and_release_preserve_earlier_reads(self):
        self.result(self.call('note','--file',str(self.note('revised-reading',kind='reading',links=['first-reading'],
                    slot='current-reading',adoption='adopt',reading_time='retrospective',payload={'reading':'a new reading'}))))
        packet=self.result(self.call('resume'))
        ids=[r['record']['id'] for r in packet['records']]
        self.assertIn('revised-reading',ids); self.assertNotIn('first-reading',ids)
        self.result(self.call('read','--id','first-reading'))
        self.result(self.call('note','--file',str(self.note('released-reading',links=['revised-reading'],slot='current-reading',adoption='release'))))
        self.assertNotIn('current-reading',[r['slot'] for r in self.result(self.call('resume'))['records']])
        self.result(self.call('read','--id','revised-reading'))

    def test_12_packet_budget_is_explicit_not_silent(self):
        packet=self.result(self.call('resume','--max-records','1'))
        self.assertEqual(len(packet['records']),1)
        self.assertTrue(packet['omitted'])
        self.assertTrue(all('id' in r and 'reason' in r for r in packet['omitted']))

    def test_13_automatic_rollover_preserves_old_episode(self):
        # Enough real writes to exercise the unmodified runtime's finite limit.
        for i in range(12):
            self.result(self.call('note','--file',str(self.note(f'rollover-{i}',payload={'reading':'finite capacity','pad':'x'*350}))))
        self.assertGreater(self.result(self.call('status'))['episodes'],1)
        self.result(self.call('read','--id','first-reading'))
        self.result(self.call('read','--id','rollover-11'))

    def test_14_two_writers_are_serialized_without_lost_intake(self):
        args=[]
        for name in ('parallel-a','parallel-b'):
            path=self.note(name)
            args.append([sys.executable,'-I','-B','-X','utf8',str(HERE/'continuity.py'),
                         '--workspace',str(self.ws),'note','--queue-only','--file',str(path)])
        processes=[subprocess.Popen(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for a in args]
        for p in processes:
            stdout,stderr=p.communicate(timeout=30)
            self.assertEqual(p.returncode,0,stdout+stderr)
        status=self.result(self.call('status'))
        self.assertIn('parallel-a',status['pending']); self.assertIn('parallel-b',status['pending'])
        self.result(self.call('resume'))

    def test_15_corrupt_checkpoint_is_not_silently_accepted(self):
        con=H.database(self.ws)
        try:
            state=H.meta(con,'backend_state')
            cp=self.ws/'te'/state['episodes'][0]['checkpoint']['file']
            raw=cp.read_bytes()
            cp.write_bytes(raw+b' ')
            try:
                p=self.call('read','--id','first-reading')
                self.assertEqual(p.returncode,2)
            finally: cp.write_bytes(raw)
        finally: con.close()

    def capture_texts(self, *lines):
        with self.session.open('ab') as stream:
            for text in lines:
                stream.write(frame('user', text))
        result = self.result(self.call('capture', '--session', str(self.session)))
        self.assertEqual(result['captured'], len(lines))
        return result['ids']

    def test_16_selected_proposal_and_decision_reopen_together(self):
        draft = '舞台係「札には『合図をお待ちください』と書きましょう」'
        other = '受付係「札には『ここでお待ちください』と書きましょう」'
        decision = '進行係「受付係の文に決めます」'
        draft_id, other_id, decision_id = self.capture_texts(draft, other, decision)
        specs = {'state': 'adopted', 'proposal': other_id, 'decision': decision_id}
        request = self.note('sign-final', sources=[decision_id, draft_id, other_id],
                            slot='entrance-sign', adoption='adopt', decision_bookmark=specs)
        self.result(self.call('note', '--queue-only', '--file', str(request)))
        resumed = self.result(self.call('resume'))
        entry = next(row['record'] for row in resumed['records'] if row['slot'] == 'entrance-sign')
        self.assertEqual(entry['payload']['request']['decision_bookmark'], specs)
        self.assertEqual(self.result(self.call('read', '--id', 'sign-final')), entry)
        self.assertNotIn(other, json.dumps(entry, ensure_ascii=False))

        opened = self.result(self.call('read', '--id', 'sign-final', '--bookmark'))
        self.assertEqual((opened['id'], opened['state']), ('sign-final', 'adopted'))
        self.assertTrue(opened['assurance'])
        self.assertEqual(set(opened['sources']), {'proposal', 'decision'})
        for role, source_id, text in [('proposal', other_id, other), ('decision', decision_id, decision)]:
            original = opened['sources'][role]
            self.assertEqual((original['id'], original['text']), (source_id, text))
            self.assertEqual(original['sha256'], hashlib.sha256(text.encode('utf-8')).hexdigest())
            self.assertEqual(original, self.result(self.call('source', '--id', source_id)))

        # A bookmark must go through the committed TE record before it can return originals.
        con = H.database(self.ws)
        try:
            name, = con.execute("SELECT checkpoint FROM receipts WHERE id=?", ('sign-final',)).fetchone()
        finally:
            con.close()
        checkpoint = self.ws / 'te' / name
        saved = checkpoint.read_bytes()
        try:
            checkpoint.write_bytes(saved + b' ')
            self.assertEqual(self.call('read', '--id', 'sign-final', '--bookmark').returncode, 2)
        finally:
            checkpoint.write_bytes(saved)

    def test_17_proposal_only_and_explicit_deferral_have_different_evidence(self):
        proposal, decision = self.capture_texts('受付係「入口で待つ案です」', '進行係「文面は次回決めます」')
        cases = [('sign-offer', 'proposal_only', {'proposal': proposal}),
                 ('sign-deferred', 'deferred', {'decision': decision}),
                 ('sign-deferred-offer', 'deferred', {'decision': decision, 'proposal': proposal})]
        for name, state, roles in cases:
            with self.subTest(state=state, roles=tuple(roles)):
                request = self.note(name, sources=list(roles.values()), decision_bookmark={'state': state, **roles})
                self.result(self.call('note', '--file', str(request)))
                opened = self.result(self.call('read', '--id', name, '--bookmark'))
                self.assertEqual(opened['state'], state)
                self.assertEqual({role: row['id'] for role, row in opened['sources'].items()}, roles)

    def test_18_one_message_can_supply_both_sources(self):
        text = '進行係「『ここでお待ちください』と提案します。今、その文に決めました」'
        source_id, = self.capture_texts(text)
        specs = {'state': 'adopted', 'proposal': source_id, 'decision': source_id}
        request = self.note('sign-same', sources=[source_id], decision_bookmark=specs)
        self.result(self.call('note', '--file', str(request)))
        sources = self.result(self.call('read', '--id', 'sign-same', '--bookmark'))['sources']
        self.assertEqual(sources['proposal'], sources['decision'])
        self.assertEqual(sources['decision']['text'], text)

    def test_19_invalid_bookmarks_never_enter_the_queue(self):
        a, b = 's000001', 's000002'
        invalid = [None, [], {}, {'state': 'unknown', 'proposal': a},
                   {'state': 'adopted', 'proposal': a}, {'state': 'adopted', 'decision': a},
                   {'state': 'proposal_only'}, {'state': 'proposal_only', 'proposal': a, 'decision': a},
                   {'state': 'deferred', 'proposal': a}, {'state': 'deferred', 'decision': None},
                   {'state': 'deferred', 'decision': a, 'extra': a},
                   {'state': 'adopted', 'proposal': a, 'decision': b},
                   {'state': 'proposal_only', 'proposal': 's999999'}]
        before = self.result(self.call('status'))
        for index, specs in enumerate(invalid):
            with self.subTest(specs=specs):
                path = self.note(f'bad-bookmark-{index}', sources=[a], decision_bookmark=specs)
                rejected = self.call('note', '--queue-only', '--file', str(path))
                self.assertEqual(rejected.returncode, 2, rejected.stdout + rejected.stderr)
        after = self.result(self.call('status'))
        for key in ('notes', 'te_saved', 'pending'):
            self.assertEqual(after[key], before[key])

    def test_20_legacy_records_keep_their_original_read_shape(self):
        path = self.note('ordinary-reading', slot='ordinary-slot', adoption='adopt')
        self.result(self.call('note', '--file', str(path)))
        ordinary = self.result(self.call('read', '--id', 'ordinary-reading'))
        self.assertNotIn('decision_bookmark', ordinary['payload']['request'])
        self.assertEqual(self.call('read', '--id', 'ordinary-reading', '--bookmark').returncode, 2)
        packet = self.result(self.call('resume'))
        active = next(e['record'] for e in packet['records'] if e['slot'] == 'ordinary-slot')
        self.assertEqual(active, ordinary)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ContinuityTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report=dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                evidence=str(ContinuityTests.evidence),passed=result.wasSuccessful(),
                receiver_type='fresh Python/TE process; no new LLM, no model substitution',
                scope='synthetic durability, provenance, restart and host-interface tests')
    (HERE/'VALIDATION.json').write_bytes(H.encoded(report))
    print(json.dumps(report,ensure_ascii=False))
    raise SystemExit(0 if result.wasSuccessful() else 1)
