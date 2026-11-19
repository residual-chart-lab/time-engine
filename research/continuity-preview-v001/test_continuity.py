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
