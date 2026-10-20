import hashlib
import json
import unittest
import subprocess
import sys
import tempfile
from pathlib import Path
from fractions import Fraction as Q
from unittest.mock import patch

import live_flower as live
import live_checkpoint as cp
import retained_execution as plant
from live_flower import f, prior, te, cycle


def ready(mode='keep', x=-1):
    s = live.Session(live.Seed(mode=mode))
    s.request(x); s.run()
    assert s.state.phase == 'AWAIT_CHOICE'
    return s


def finished(mode='keep', x=-1, word='HHST'):
    s = ready(mode, x)
    s.choose(word); s.run()
    assert s.state.phase == 'STOPPED'
    return s


def restore(s):
    raw = cp.dumps(s)
    restored = cp.loads(raw, trusted_sha256=hashlib.sha256(raw).hexdigest())
    return raw, restored


class LiveFlowerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = {}
        cls.runs = {(m, x, w): finished(m, x, w)
                    for m in ('keep', 'erase', 'restore')
                    for x in (Q(-1), Q(1, 4)) for w in f.WORDS}

    def test_all_twelve_staged_executions_equal_original_RR62(self):
        for key, s in self.runs.items():
            with self.subTest(key=key):
                t = s.state
                old = plant.execute(s.archive, s.entry, t.scope, t.demand, t.resolution, t.word)
                self.assertEqual(t.engine, old.closed_engine)
                self.assertEqual(t.source, old.new_source)
                self.assertEqual(t.terminal, old.terminal)
                self.assertEqual(t.errors, old.prefix_errors)
                trial, decoded, ok = plant.future(s.archive, s.entry, t.scope, t.demand, old)
                self.assertTrue(ok)
                self.assertEqual(t.future_receipts, ((t.scope.requirement, trial, decoded),))

    def test_existence_does_not_choose_execute_or_discard_retention(self):
        s = live.Session(); before = s.state.engine
        s.request(-1, f.EXISTS)
        with patch.object(s.archive, 'read_shift', side_effect=AssertionError('not needed')):
            s.run()
        self.assertEqual(s.state.phase, 'ANSWERED')
        self.assertEqual(s.state.exact_shift_reads, 0)
        self.assertEqual(s.state.engine, before)
        with self.assertRaises(ValueError): s.choose('HHST')
        s.request(-1); s.run()
        self.assertEqual(s.state.phase, 'AWAIT_CHOICE')
        self.assertEqual(s.state.exact_shift_reads, 1)
        self.assertEqual(len(s.state.answers), 2)
        self.assertEqual(s.state.engine, before)

    def test_current_must_choose_and_C_cannot_be_replaced_after_resolution(self):
        s = ready(); before = (s.state, s.commands)
        self.assertFalse(s.tick())
        for action in (lambda: s.choose('HS'), lambda: s.request(Q(1, 4)), lambda: s.connect()):
            with self.assertRaises(ValueError): action()
            self.assertEqual((s.state, s.commands), before)
        s.choose('HHST')
        with self.assertRaises(ValueError): s.request(Q(1, 4))
        s.run()
        with self.assertRaises(ValueError): s.request(Q(1, 4))

    def test_empty_or_unknown_queries_never_actuate(self):
        for x, domain, expected in ((Q(1, 2), (-64, 64), 'REJECTED'),
                (Q(1, 3), (-64, 64), 'REJECTED'), (0, (-64, 64), 'OUTSIDE_CHART'),
                (-1, (0, 1), 'REJECTED')):
            with self.subTest(x=x, domain=domain):
                s = live.Session(); before = s.state.engine
                s.request(x, domain=domain); s.run()
                self.assertEqual(s.state.phase, expected)
                self.assertEqual(s.state.engine, before)
                self.assertEqual(s.state.exact_shift_reads, 0)
                with self.assertRaises(ValueError): s.choose('HHST')

    def test_completion_stops_without_scheduling_next_flower(self):
        s = self.runs['keep', Q(-1), 'HHST']; before = (s.state, s.commands)
        s.run(100)
        self.assertEqual((s.state, s.commands), before)
        self.assertFalse(s.tick())
        self.assertEqual(len(s.state.engine.rounds), 2)  # Seed + requested flower.

    def test_old_history_and_all_three_levels_survive(self):
        for s in self.runs.values():
            e = s.state.engine; before = s.history.first.closed_engine
            self.assertEqual(e.stock, before.stock + (s.state.source,))
            self.assertEqual(e.events[:len(before.events)], before.events)
            self.assertEqual(e.rounds[:-1], before.rounds)
            self.assertEqual(e.outputs, before.outputs + (s.state.terminal,))
            self.assertEqual((s.state.source.level, s.state.terminal.level,
                s.state.future_receipts[0][2].outputs[0].level), (2, 3, 4))

    def test_no_C_fixture_or_future_path_enumeration_is_called(self):
        with patch.object(te, 'construct_requirement', side_effect=AssertionError('no future fixture')), \
             patch.object(te, 'finite_family', side_effect=AssertionError('no completed future paths')):
            s = finished(); s.connect(); s.run()
        self.assertEqual(s.state.phase, 'STOPPED')

    def test_resume_at_every_stage_preserves_bytes_and_next_transition(self):
        s = live.Session(); stages = []
        for command in ({'op': 'request', 'x': '-1', 'observation': f.ACTIONS, 'domain': ['-64', '64']},
                        {'op': 'choose', 'word': 'HHST'},
                        {'op': 'connect', 'strength': '1/1024'}):
            s.apply(command)
            while True:
                stages.append((s.state.phase, s.state.cursor))
                raw, restored = restore(s)
                self.assertEqual(cp.dumps(restored), raw)
                self.assertEqual(restored.state, s.state)
                if not s.tick():
                    self.assertFalse(restored.tick())
                    s = restored
                    break
                self.assertTrue(restored.tick())
                self.assertEqual(restored.state, s.state)
                self.assertEqual(restored.commands, s.commands)
                s = restored
        self.assertIn(('CURRENT_LOWER_CLOSED', 0), stages)
        self.assertIn(('CURRENT_AVAILABLE', 0), stages)
        self.assertIn(('EXECUTING', 3), stages)
        self.assertIn(('CONNECT_AVAILABLE', 4), stages)
        self.assertEqual((len(s.state.engine.rounds), len(s.state.engine.stock)), (3, 7))
        control = finished(); control.connect(); control.run()
        self.assertEqual(s.state, control.state)
        self.evidence['resumed_stages'] = stages

    def test_checkpoint_rejects_changed_bytes_and_changed_snapshot_even_with_new_hash(self):
        raw = cp.dumps(self.runs['keep', Q(-1), 'HHST'])
        digest = hashlib.sha256(raw).hexdigest()
        with self.assertRaises(ValueError): cp.loads(raw + b' ', trusted_sha256=digest)
        p = json.loads(raw)
        for node in p['graph']['nodes']:
            if node.get('type') == 'live_flower.State':
                node['fields']['exact_shift_reads'] = 0
        changed = json.dumps(p).encode()
        with self.assertRaisesRegex(ValueError, 'replay'):
            cp.loads(changed, trusted_sha256=hashlib.sha256(changed).hexdigest())

    def test_checkpoint_rejects_unknown_classes_cycles_and_malformed_commands(self):
        for graph in ({'root': {'ref': 0}, 'nodes': [{'type': 'os.system', 'fields': {}}]},
                      {'root': {'ref': 0}, 'nodes': [{'tuple': [{'ref': 0}]}]}):
            with self.assertRaises(ValueError): cp.unpack(graph)
        s = live.Session(); before = (s.state, s.commands)
        for cmd in (None, [], {'op': 'tick', 'extra': 1}, {'op': 'invent'}):
            with self.assertRaises(ValueError): s.apply(cmd)
        self.assertEqual((s.state, s.commands), before)

    def test_continuation_equals_existing_RR53_RR43_composition(self):
        rows = []
        for mode in ('keep', 'erase', 'restore'):
            for word in f.WORDS:
                with self.subTest(mode=mode, word=word):
                    _, s = restore(self.runs[mode, Q(-1), word]); old = s.state
                    raw, y = te.pair.connection_context(live.exit_view(old), te.pair.ConnectionSpec())
                    expected = cycle.request_boundary(old.engine)
                    expected = cycle.event(expected, 'rr53-terminal-residue-port-emitted')
                    expected = cycle.finish_current(cycle.accept_context(expected, y))
                    s.connect(); s.run()
                    self.assertEqual(s.state.engine, expected)
                    self.assertEqual(s.state.port, (raw, y))
                    self.assertEqual(s.state.future_receipts, old.future_receipts)
                    self.assertEqual(s.state.engine.stock[:len(old.engine.stock)], old.engine.stock)
                    self.assertEqual(s.state.engine.outputs[:-1], old.engine.outputs)
                    self.assertEqual(s.state.engine.rounds[:-1], old.engine.rounds)
                    self.assertEqual(s.state.engine.upper.live.accumulated, prior.NEG)
                    rows.append(dict(mode=mode, **s.status()))
        self.evidence['continuations'] = rows

    def test_order_changes_next_motion_and_zero_coupling_removes_that_difference(self):
        pairs = {}
        for strength in (Q(1, 1024), Q(0)):
            result = []
            for word in f.WORDS:
                _, s = restore(self.runs['keep', Q(-1), word]); s.connect(strength); s.run()
                self.assertEqual(s.state.phase, 'STOPPED')
                result.append(s.state)
            a, b = result; pairs[strength] = result
            self.assertNotEqual(a.port[0], b.port[0])  # The retained order is never deleted.
            if strength:
                self.assertNotEqual(a.port[1], b.port[1])
                self.assertNotEqual(a.engine.stock[-1].leaves()[0].weights,
                                    b.engine.stock[-1].leaves()[0].weights)
            else:
                self.assertEqual(a.port[1], b.port[1])
                self.assertEqual(a.engine.stock[-1].leaves()[0].weights,
                                 b.engine.stock[-1].leaves()[0].weights)

    def test_erasure_changes_source_and_restore_recovers_keep_response(self):
        keep, erase, restored = (self.runs[m, Q(-1), 'HHST'] for m in ('keep', 'erase', 'restore'))
        self.assertNotEqual(keep.state.source.leaves()[0].weights, erase.state.source.leaves()[0].weights)
        self.assertEqual(keep.state.source.leaves()[0].weights, restored.state.source.leaves()[0].weights)
        self.assertEqual(keep.state.engine.upper.live.accumulated, erase.state.engine.upper.live.accumulated)

    def test_cli_start_choice_closure_connection_and_no_overwrite(self):
        root = Path(__file__).resolve().parents[2]
        (root / '.work').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root / '.work') as folder:
            paths = [Path(folder) / (x + '.json') for x in ('choice', 'closed', 'connected')]
            def call(*args):
                result = subprocess.run([sys.executable, str(root / 'run_live.py'), *map(str, args)],
                    capture_output=True, text=True, timeout=180, cwd=root)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            a = call('start', '--x=-1', '--out', paths[0])
            self.assertEqual(a['phase'], 'AWAIT_CHOICE')
            b = call('resume', paths[0], '--sha256', a['sha256'], '--word', 'HHST', '--out', paths[1])
            self.assertEqual((b['phase'], b['rounds'], b['future_certificates']), ('STOPPED', 2, 1))
            c = call('resume', paths[1], '--sha256', b['sha256'], '--connect', '--out', paths[2])
            self.assertEqual((c['phase'], c['rounds'], c['future_certificates']), ('STOPPED', 3, 1))
            before = paths[2].read_bytes()
            rejected = subprocess.run([sys.executable, str(root / 'run_live.py'), 'start', '--x=-1',
                '--out', str(paths[2])], capture_output=True, timeout=30, cwd=root)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(paths[2].read_bytes(), before)
            self.evidence['cli'] = {name: {k: v for k, v in value.items() if k not in ('checkpoint', 'sha256')}
                                   for name, value in zip(('choice', 'closed', 'connected'), (a, b, c))}


if __name__ == '__main__':
    unittest.main()
