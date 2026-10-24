import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fractions import Fraction as Q
import step_session as api

ROOT = Path(__file__).resolve().parents[2]
RAW = (ROOT / 'integrations/inquiry/E1-entry.record.json').read_bytes()
SHA = 'd71a430cf049b645dd44d6ebfd9870acfe00ed2b3ac54d1b5766641fa1f805a3'
DIGEST = '24ccd25412e46f5051ee5e48325358f8f62a66ce1244b69ce65fa57abce6f5de'
REQUEST = dict(context='mixed', strengths=['1/1024', '1/1024'], frame='split')


def receive():
    return api.Session.receive(RAW, SHA, DIGEST)


def ready(s):
    s.apply(dict(op='bind', requirement=REQUEST))
    s.apply(dict(op='choose', v='1', u='0', word='HHHSUT'))
    return s.apply(dict(op='resolve'))


def encoded(doc):
    raw = (json.dumps(doc, separators=(',', ':')) + '\n').encode()
    return raw, hashlib.sha256(raw).hexdigest()


class StepSessionTests(unittest.TestCase):
    def test_receive_once_reuses_cache_and_advances_exactly_one_flower(self):
        s = receive()
        with patch.object(api.wire, 'loads', side_effect=AssertionError('no entry reload')):
            first = ready(s)
            self.assertGreater(first['last_resolution_work']['total_exact_queries'], 0)
            with patch.object(s.entry.base.vault, 'exact', side_effect=AssertionError('no new source read')), \
                 patch.object(s.entry.derived, 'exact', side_effect=AssertionError('no new observation read')):
                repeat = ready(s)
            self.assertEqual(repeat['last_resolution_work']['total_exact_queries'], 0)
            self.assertEqual(repeat['last_resolution_work']['new_feature_queries'], 0)
            self.assertEqual(repeat['numerical_reads'], first['numerical_reads'])
            phases = [s.apply(dict(op='advance'))['phase'] for _ in range(4)]
            self.assertEqual(phases, ['CLOSED1', 'CLOSED2', 'CLOSED3', 'STOPPED'])
            actual = api.live.payload(s.state)
            expected = json.loads((ROOT / 'integrations/inquiry/RR69-mixed-connected.record.json').read_bytes())
            self.assertEqual(api.wire.checkpoint.unpack(actual.pop('graph')), api.wire.checkpoint.unpack(expected.pop('graph')))
            self.assertEqual(actual, expected)
            self.assertEqual(s.status()['stock'], 9)
            self.assertTrue(s.status()['certified'])

    def test_new_request_discards_old_permission_and_can_reject(self):
        s = receive(); ready(s)
        request = dict(REQUEST, context='outside_chart')
        status = s.apply(dict(op='bind', requirement=request))
        self.assertEqual(status['phase'], 'BOUND')
        self.assertIsNone(s.state.plan); self.assertIsNone(s.state.action)
        s.apply(dict(op='choose', v=1, u=0, word='HHHSUT'))
        self.assertEqual(s.apply(dict(op='resolve'))['phase'], 'REJECTED')
        self.assertEqual(s.state.action.status, 'UNKNOWN_CHART')
        engine = s.state.engine
        with self.assertRaises(ValueError): s.apply(dict(op='advance'))
        self.assertEqual(s.state.engine, engine)
        self.assertEqual(s.status()['closed_flowers'], 0)

    def test_closed_past_cannot_be_rebound_or_reselected(self):
        s = receive(); ready(s); s.apply(dict(op='advance'))
        before = s.snapshot()
        for cmd in (dict(op='bind', requirement=REQUEST), dict(op='choose', v=0, u=0, word='HHHSUT')):
            with self.assertRaises(ValueError): s.apply(cmd)
            self.assertEqual(s.snapshot(), before)

    def test_invalid_commands_do_not_move_current_state(self):
        s = receive(); before = s.status()
        for cmd in (dict(op='advance'), dict(op='choose', v=1, u=0, word='HHHSUT'),
                    dict(op='resolve'), dict(op='unknown'), dict(op='bind', requirement=REQUEST, extra=1)):
            with self.assertRaises(ValueError): s.apply(cmd)
            self.assertEqual(s.status(), before)
        with self.assertRaises(ValueError): api.rational(1.0)
        with self.assertRaises(ValueError): api.rational(True)

    def test_checkpoint_replays_rebinding_cache_and_closed_prefix(self):
        s = receive(); ready(s); ready(s); s.apply(dict(op='advance'))
        raw, sha = s.snapshot()
        entry = api.wire.loads(RAW, SHA, DIGEST)
        restored = api.Session.restore(entry, raw, sha)
        self.assertEqual(restored.status(), s.status())
        self.assertEqual(restored.snapshot(), (raw, sha))
        type(self).checkpoint_bytes = raw
        type(self).checkpoint_sha256 = sha
        for _ in range(3): restored.apply(dict(op='advance'))
        self.assertTrue(restored.status()['certified'])
        self.assertEqual(restored.status()['stock'], 9)

    def test_checkpoint_requires_external_hash_and_exact_actual_history(self):
        s = receive(); ready(s); s.apply(dict(op='advance'))
        raw, sha = s.snapshot()
        entry = api.wire.loads(RAW, SHA, DIGEST)
        with self.assertRaises(ValueError): api.Session.restore(entry, raw, '0'*64)
        value = json.loads(raw); value['current']['phase'] = 'STOPPED'
        forged, forged_sha = encoded(value)
        with self.assertRaises(ValueError): api.Session.restore(entry, forged, forged_sha)

    def test_finite_limits_apply_to_normal_execution_and_resume(self):
        s = receive(); ready(s)
        with patch.object(api, 'MAX_COMMANDS', 3):
            with self.assertRaises(ValueError): s.apply(dict(op='advance'))
            raw, sha = s.snapshot()
            value = json.loads(raw); value['journal'].append(dict(op='advance'))
            forged, forged_sha = encoded(value)
            with self.assertRaises(ValueError): api.Session.restore(s.entry, forged, forged_sha)
        with patch.object(api, 'MAX_SNAPSHOT_BYTES', 1):
            with self.assertRaises(ValueError): s.snapshot()
            with self.assertRaises(ValueError): api.Session.restore(s.entry, raw, sha)

    def test_real_json_lines_cli_saves_and_resumes_without_reimport_per_command(self):
        script = r'''
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import sys,json
root=Path(sys.argv[1]);sys.path.insert(0,str(root));sys.path.insert(0,str(root/'integrations/inquiry'))
import run_time_engine as cli
import entry_transport as w
with ExitStack() as stack:
 for module,name in ((w.a,'register'),(w.incremental,'register'),(w.adaptive,'register'),(w.m,'register'),(w.b,'register'),(w.prior.previous,'begin'),(w.prior.te,'prepare')):
  stack.enter_context(patch.object(module,name,side_effect=AssertionError('past generator forbidden')))
 loader=stack.enter_context(patch.object(w,'loads',wraps=w.loads))
 result=cli.main(sys.argv[2:])
 print(json.dumps(dict(metrics=dict(entry_imports=loader.call_count))))
 raise SystemExit(result)
'''
        temp_root = ROOT / '.work/e2-tests'; temp_root.mkdir(parents=True, exist_ok=True)
        args = ['--entry', str(ROOT/'integrations/inquiry/E1-entry.record.json'), '--trusted-sha256', SHA, '--expected-entry-digest', DIGEST]
        def run(commands, extra=()):
            result = subprocess.run([sys.executable, '-I', '-c', script, str(ROOT), *args, *extra],
                                    input='\n'.join(json.dumps(x) for x in commands)+'\n', text=True,
                                    capture_output=True, check=True)
            return [json.loads(x) for x in result.stdout.splitlines()]
        with tempfile.TemporaryDirectory(dir=temp_root) as temp:
            self.assertTrue(Path(temp).resolve().is_relative_to(temp_root.resolve()))
            path = str(Path(temp) / 'closed-first.json')
            block = [dict(op='bind', requirement=REQUEST), dict(op='choose', v='1', u='0', word='HHHSUT'), dict(op='resolve')]
            out = run(block+block+[dict(op='advance'), dict(op='save', path=path), dict(op='save',path=path), dict(op='quit')])
            self.assertTrue(out[0]['ok']); self.assertEqual(out[0]['status']['phase'], 'UNBOUND')
            self.assertEqual(out[6]['status']['last_resolution_work']['total_exact_queries'], 0)
            saved = next(row for row in out if 'saved' in row)
            self.assertTrue(any(not row.get('ok', True) for row in out))
            self.assertEqual(out[-1]['metrics']['entry_imports'], 1)
            resumed = run([dict(op='advance')]*3+[dict(op='quit')], ['--resume', path, '--trusted-resume-sha256', saved['sha256']])
            self.assertEqual(resumed[0]['status']['phase'], 'CLOSED1')
            self.assertTrue(resumed[-2]['status']['certified'])
            self.assertEqual(resumed[-2]['status']['stock'], 9)
            self.assertEqual(resumed[-1]['metrics']['entry_imports'], 1)
            type(self).cli_metrics = dict(entry_imports_per_process=1, repeated_resolution_exact_reads=0,
                                          phase='STOPPED', certified=True, stock=9,
                                          saved_after='CLOSED1', past_generators_forbidden=True)


if __name__ == '__main__':
    unittest.main()
