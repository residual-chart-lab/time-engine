"""Failure-path checks for the trial evidence layer, over an actual TE input."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import subprocess
import unittest
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE
spec = importlib.util.spec_from_file_location('trial_evidence', HERE / 'trial_evidence.py')
te = importlib.util.module_from_spec(spec)
spec.loader.exec_module(te)
ARTIFACTS = ROOT / 'work' / ('checks-e-' + uuid.uuid4().hex[:6])
SOURCE = ARTIFACTS / 'synthetic-fixture'
ENTRY = ROOT / 'continuity.py'


class EvidenceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ARTIFACTS.mkdir(parents=True)
        subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', str(HERE / 'make_demo.py'), '--workspace', str(SOURCE)], check=True, capture_output=True)
        cls.base = ARTIFACTS / 'prepared'
        keys = ['a1', 'b1', 'a2', 'b2', 'b3']
        te.prepare(cls.base, SOURCE, ENTRY,
            {k: 'Test task ' + k for k in keys},
            {k: dict(task_name='test', message='Read task ' + k, fork_turns='none') for k in keys},
            dict(scope='Harness plumbing only; fake answer texts are not LLM outcomes.'))

    def setUp(self):
        self.root = ARTIFACTS / self.id().split('.')[-1].split('_')[1]
        shutil.copytree(self.base, self.root)

    def receive(self, role, stage=1):
        r = te.operate(self.root, 'receive', role, stage)
        self.assertTrue(r['ok'], r)
        return r['result']['receipt']['token']

    def submit(self, role, stage, token, text='test answer'):
        file = self.root / 'incoming' / role / (uuid.uuid4().hex + '.md')
        file.write_bytes(text.encode('utf-8'))
        return te.operate(self.root, 'submit', role, stage, token, source_file=file)

    def advance_to_two(self):
        for role in ('a', 'b'):
            self.assertTrue(self.submit(role, 1, self.receive(role))['ok'])
        self.assertTrue(te.operate(self.root, 'open-stage', stage=2)['ok'])

    def test_01_execution_can_change_db_bytes_without_changing_sealed_input(self):
        m = te.load(self.root / 'MANIFEST.json')
        before = te.file_map(self.root / 'sealed')
        self.assertEqual(te.file_map(self.root / 'execution'), before)
        token = self.receive('a')
        result = te.operate(self.root, 'use', 'a', 1, token, ['resume'])
        self.assertTrue(result['ok'], result)
        self.assertEqual(len(result['result']['value']['records']), 5)
        self.assertEqual(te.file_map(self.root / 'sealed'), before)
        self.assertEqual(te.rows_fingerprint(self.root / 'execution/archive.sqlite3'), m['initial_logical_rows'])
        self.assertTrue(te.verify(self.root)['passed'])

    def test_02_b_source_access_refused_and_logged(self):
        token = self.receive('b')
        r = te.operate(self.root, 'use', 'b', 1, token, ['source', '--id', 's000029'])
        self.assertFalse(r['ok'])
        self.assertIn('no backend capability', r['error'])
        self.assertEqual(te.verify(self.root)['refusals'], 1)

    def test_03_use_without_delivery_refused(self):
        r = te.operate(self.root, 'use', 'a', 1, 'invented', ['status'])
        self.assertFalse(r['ok'])
        self.assertIn('not been delivered', r['error'])

    def test_04_other_role_receipt_refused(self):
        token = self.receive('a')
        self.receive('b')
        self.assertFalse(self.submit('b', 1, token)['ok'])

    def test_05_closed_stage_delivery_refused(self):
        self.assertFalse(te.operate(self.root, 'receive', 'a', 2)['ok'])

    def test_06_advance_without_both_submissions_refused(self):
        self.assertFalse(te.operate(self.root, 'open-stage', stage=2)['ok'])

    def test_07_receipt_from_prior_stage_refused(self):
        old = self.receive('a')
        self.assertTrue(self.submit('a', 1, old)['ok'])
        self.assertTrue(self.submit('b', 1, self.receive('b'))['ok'])
        self.assertTrue(te.operate(self.root, 'open-stage', stage=2)['ok'])
        self.receive('a', 2)
        self.assertFalse(self.submit('a', 2, old)['ok'])

    def test_08_modified_fixed_task_refused(self):
        (self.root / 'fixed/tasks/a1.txt').write_text('changed', encoding='utf-8')
        self.assertFalse(te.operate(self.root, 'receive', 'a', 1)['ok'])

    def test_09_modified_sealed_db_refused(self):
        path = self.root / 'sealed/archive.sqlite3'
        raw = bytearray(path.read_bytes())
        raw[100] ^= 1
        path.write_bytes(raw)
        self.assertFalse(te.operate(self.root, 'receive', 'a', 1)['ok'])

    def test_10_modified_execution_original_refused(self):
        path = self.root / 'execution/archive.sqlite3'
        with sqlite3.connect(path) as c:
            for name, in c.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='sources'").fetchall():
                c.execute('DROP TRIGGER "' + name.replace('"', '""') + '"')
            c.execute('UPDATE sources SET body=? WHERE seq=29', (b'changed original',))
        self.assertFalse(te.operate(self.root, 'receive', 'a', 1)['ok'])

    def test_11_submission_copies_original_bytes_and_rejects_overwrite(self):
        token = self.receive('a')
        self.assertTrue(self.submit('a', 1, token, 'original\n')['ok'])
        incoming = next((self.root / 'incoming/a').glob('*.md'))
        incoming.write_text('edited draft', encoding='utf-8')
        self.assertEqual((self.root / 'submissions/a1.md').read_bytes(), b'original\n')
        self.assertFalse(self.submit('a', 1, token, 'replacement')['ok'])
        self.assertTrue(te.verify(self.root)['passed'])

    def test_12_modified_received_submission_detected(self):
        self.submit('a', 1, self.receive('a'))
        (self.root / 'submissions/a1.md').write_text('changed', encoding='utf-8')
        with self.assertRaises(ValueError):
            te.verify(self.root)

    def test_13_modified_delivery_response_detected(self):
        self.receive('a')
        (self.root / 'events/0001.response.bin').write_bytes(b'{}')
        with self.assertRaises(ValueError):
            te.verify(self.root)

    def test_14_missing_receipt_detected(self):
        self.receive('a')
        (self.root / 'receipts/a1.json').unlink()
        with self.assertRaises((ValueError, FileNotFoundError)):
            te.verify(self.root)

    def test_15_incomplete_trial_not_success(self):
        self.receive('a')
        with self.assertRaises(ValueError):
            te.verify(self.root, complete=True)

    def test_16_parallel_deliveries_form_one_chain(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda role: te.operate(self.root, 'receive', role, 1), ('a', 'b')))
        self.assertTrue(all(r['ok'] for r in outcomes))
        self.assertEqual(te.verify(self.root)['events'], 2)

    def test_17_all_predeclared_stages_and_original_forwarding(self):
        self.advance_to_two()
        for role in ('a', 'b'):
            self.assertTrue(self.submit(role, 2, self.receive(role, 2))['ok'])
        self.assertTrue(te.operate(self.root, 'open-stage', stage=3)['ok'])
        token = self.receive('b', 3)
        event = te.load(sorted((self.root / 'events').glob('*.json'))[-1])
        response = te.load(self.root / event['response_file'])
        self.assertEqual(response['result']['context']['id'], 's000029')
        self.assertTrue(self.submit('b', 3, token)['ok'])
        self.assertTrue(te.verify(self.root, complete=True)['passed'])

    def test_18_initial_copy_comparison_field_is_actually_validated(self):
        path = self.root / 'MANIFEST.json'
        manifest = te.load(path)
        manifest['measured_initial_copies']['execution']['files']['archive.sqlite3']['sha256'] = '0' * 64
        path.write_bytes(te.encoded(manifest))
        (self.root / 'ANCHOR.json').write_bytes(te.encoded(dict(manifest_sha256=te.fingerprint(path))))
        with self.assertRaises(ValueError):
            te.verify(self.root)

    def test_19_committed_wal_changes_are_not_hidden_by_immutable_reader(self):
        path = self.root / 'execution/archive.sqlite3'
        writer = sqlite3.connect(path)
        keeper = None
        try:
            writer.execute('PRAGMA journal_mode=WAL').fetchone()
            writer.execute('PRAGMA wal_autocheckpoint=0')
            writer.commit()
            keeper = sqlite3.connect(path)
            keeper.execute('BEGIN')
            keeper.execute('SELECT count(*) FROM sources').fetchone()
            initial = te.rows_fingerprint(path)
            for name, in writer.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='sources'").fetchall():
                writer.execute('DROP TRIGGER "' + name.replace('"', '""') + '"')
            changed = b'committed only to WAL'
            writer.execute('UPDATE sources SET body=?,sha256=? WHERE seq=29', (changed, te.digest(changed)))
            writer.commit()
            self.assertTrue(Path(str(path) + '-wal').stat().st_size > 0)
            # The old immutable-reader approach misses the committed change; the operational read must not.
            self.assertEqual(te.rows_fingerprint(path, sealed_standalone=True), initial)
            self.assertNotEqual(te.rows_fingerprint(path), initial)
            r = te.operate(self.root, 'receive', 'a', 1)
            self.assertFalse(r['ok'])
            self.assertIn('logical rows differ', r['error'])
        finally:
            if keeper is not None:
                keeper.rollback()
                keeper.close()
            writer.close()

    def test_20_execution_config_change_is_refused(self):
        path = self.root / 'execution/CONFIG.json'
        value = te.load(path)
        value['backend_entry'] = 'unexpected backend'
        path.write_bytes(te.encoded(value))
        response = te.operate(self.root, 'receive', 'a', 1)
        self.assertFalse(response['ok'])
        self.assertIn('immutable file differs', response['error'])

    def test_21_old_execution_checkpoint_change_is_refused(self):
        path = next((self.root / 'execution/te').glob('*.json'))
        path.write_bytes(path.read_bytes() + b' ')
        self.assertFalse(te.operate(self.root, 'receive', 'a', 1)['ok'])

    def test_22_execution_metadata_change_is_refused(self):
        with sqlite3.connect(self.root / 'execution/archive.sqlite3') as con:
            con.execute("UPDATE meta SET value='{}' WHERE key='backend_state'")
        self.assertFalse(te.operate(self.root, 'receive', 'a', 1)['ok'])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EvidenceChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    value = dict(tests=result.testsRun, failures=[str(t) + '\n' + detail for t, detail in result.failures],
                 errors=[str(t) + '\n' + detail for t, detail in result.errors], passed=result.wasSuccessful(),
                 artifacts=str(ARTIFACTS), scope='Evidence-layer checks; synthetic submissions are not receiver-AI trials.')
    if ARTIFACTS.exists():
        te.save(ARTIFACTS / 'RESULT.json', value)
    print(json.dumps(value, ensure_ascii=False), flush=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)
