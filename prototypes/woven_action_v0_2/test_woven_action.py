"""Checks specific to the route/action bridge and candidate-set boundary law."""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import woven_action as wa
import demo

ENV = None


class WovenActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = demo.fixture(ENV)

    def setUp(self):
        self.bridge = self.base.clone()

    def receiver(self, thread='short-route', requirement=demo.REQ):
        projection = self.bridge.project(thread, '保持根拠')
        receiver = ENV.api.Session(projection['bundle'], wa.fresh_episode(ENV))
        receiver.apply(dict(op='bind', requirement=requirement))
        return receiver

    def test_routes_supply_actual_texts_and_same_current_reply(self):
        full = self.bridge.project('full-route', '保持根拠')
        short = self.bridge.project('short-route', '保持根拠')
        self.assertEqual(set(full['bundle']['packet']['texts']), {'before', 'correction', 'after'})
        self.assertEqual(set(short['bundle']['packet']['texts']), {'correction', 'after'})
        self.assertEqual(full['bundle']['model'], short['bundle']['model'])
        bodies = []
        for projection in (full, short):
            receiver = ENV.api.Session(projection['bundle'], wa.fresh_episode(ENV))
            receiver.apply(dict(op='bind', requirement=demo.NOW))
            bodies.append(demo.execute(receiver, 'answer', [])['result']['reply']['body'])
        self.assertEqual(*bodies)

    def test_missing_source_rejects_retained_answer_plan(self):
        receiver = self.receiver()
        retained = self.receiver('full-route')
        plan = retained.status()['admissible_answers'][0]
        initial = receiver.snapshot()
        self.assertEqual(receiver.status()['admissible_answers'], [])
        with self.assertRaises(ValueError):
            receiver.apply(dict(op='choose', plan=plan['id']))
        self.assertEqual(receiver.snapshot(), initial)

    def test_arrival_changes_basis_window_but_not_current_window(self):
        receiver = self.receiver()
        before = receiver.snapshot()
        bridge, changed, witness = self.bridge.arrive(receiver, 'full-route', '保持根拠', 'before', 'arrival')
        self.assertEqual(receiver.snapshot(), before)
        self.assertEqual(witness['active']['comparison']['before_answers'], 0)
        self.assertEqual(witness['active']['comparison']['after_answers'], 2)
        self.assertTrue(witness['active']['comparison']['panel_crossed'])
        self.assertFalse(witness['current_window']['comparison']['panel_crossed'])
        self.assertEqual(changed.status()['phase'], 'BOUND')
        self.assertIsNone(changed.status()['permit'])
        marked = [e for e in bridge.memory.episode.status()['events'] if e['id'] == 'arrival']
        self.assertEqual(len(marked), 1)

    def test_phase_only_change_is_not_a_panel_crossing(self):
        receiver = self.receiver()
        before = wa.capacity(ENV, receiver.model, receiver.available, demo.REQ)
        requested = demo.execute(receiver, 'ask', [], role='before')
        after = wa.capacity(ENV, receiver.model, receiver.available, demo.REQ)
        self.assertEqual(receiver.status()['phase'], 'CLOSED')
        self.assertEqual(receiver.status()['plans'], [])
        self.assertFalse(wa.compare(before, after)['panel_crossed'])
        self.assertFalse(requested['result']['certificate']['contract_satisfied'])

    def test_changed_c_is_incomparable_instead_of_a_fake_boundary(self):
        receiver = self.receiver()
        a = wa.capacity(ENV, receiver.model, receiver.available, demo.REQ)
        b = wa.capacity(ENV, receiver.model, receiver.available, demo.NOW)
        self.assertEqual(wa.compare(a, b)['relation'], 'INCOMPARABLE_SCOPE')
        self.assertIsNone(wa.compare(a, b)['panel_crossed'])

    def test_arrival_from_short_route_cannot_invent_missing_text(self):
        receiver = self.receiver()
        owner, actor = self.bridge.memory.snapshot(), receiver.snapshot()
        with self.assertRaises(ValueError):
            self.bridge.arrive(receiver, 'short-route', '保持根拠', 'before', 'bad-arrival')
        self.assertEqual(owner, self.bridge.memory.snapshot())
        self.assertEqual(actor, receiver.snapshot())

    def test_recording_failure_does_not_partially_supply_either_borrowed_state(self):
        receiver = self.receiver()
        # A duplicate receipt id fails after the staged engine supply succeeds.
        self.bridge.memory.apply(dict(op='record', id='duplicate', origin='reported_in_session',
                                      source='test', text='occupied id'))
        owner, actor = self.bridge.memory.snapshot(), receiver.snapshot()
        with self.assertRaises(ValueError):
            self.bridge.arrive(receiver, 'full-route', '保持根拠', 'before', 'duplicate')
        self.assertEqual(owner, self.bridge.memory.snapshot())
        self.assertEqual(actor, receiver.snapshot())

    def test_arrival_invalidates_a_previously_prepared_permit(self):
        receiver = self.receiver()
        plan = next(p for p in receiver.status()['plans'] if p['kind'] == 'ask' and p['role'] == 'before')
        receiver.apply(dict(op='choose', plan=plan['id']))
        old_permit = receiver.apply(dict(op='resolve'))['status']['permit']
        _, changed, _ = self.bridge.arrive(receiver, 'full-route', '保持根拠', 'before', 'arrival')
        with self.assertRaises(ValueError):
            changed.apply(dict(op='advance', permit=old_permit))
        self.assertEqual(receiver.status()['permit'], old_permit)

    def test_restore_replays_source_transition_and_preserves_previous_view(self):
        receiver = self.receiver()
        old = ENV.weave.view(self.bridge.memory, 'short-route')
        demo.execute(receiver, 'ask', [], role='before')
        bridge, changed, _ = self.bridge.arrive(receiver, 'full-route', '保持根拠', 'before', 'arrival')
        # The ask was closed, so supply leaves the actor unbound until a new bind.
        self.assertEqual(changed.status()['phase'], 'UNBOUND')
        changed.apply(dict(op='bind', requirement=demo.REQ))
        self.assertTrue(demo.execute(changed, 'answer', [])['result']['certificate']['contract_satisfied'])
        raw, trusted = bridge.snapshot(changed)
        restored, actor = wa.Bridge.restore(ENV, raw, trusted)
        self.assertEqual(ENV.weave.view(restored.memory, 'short-route', old['as_of']), old)
        self.assertEqual(actor.closed[0], changed.closed[0])
        self.assertEqual(actor.commands, changed.commands)

    def test_tampered_checkpoint_and_self_consistent_wrong_boundary_are_rejected(self):
        receiver = self.receiver()
        bridge, actor, _ = self.bridge.arrive(receiver, 'full-route', '保持根拠', 'before', 'arrival')
        raw, trusted = bridge.snapshot(actor)
        with self.assertRaises(ValueError):
            wa.Bridge.restore(ENV, raw + b' ', trusted)
        value = json.loads(raw)
        value['boundaries'][0]['active']['comparison']['panel_crossed'] = False
        changed = wa.encode(value)
        # Even when an external caller supplies the modified hash, replay and
        # fixed-law verification reject this internal contradiction.
        with self.assertRaises(ValueError):
            wa.Bridge.restore(ENV, changed, hashlib.sha256(changed).hexdigest())

    def test_wrong_source_mapping_and_changed_original_are_rejected(self):
        wrong = dict(self.bridge.source_map)
        wrong['src-before'], wrong['src-after'] = wrong['src-after'], wrong['src-before']
        with self.assertRaises(ValueError):
            wa.Bridge(ENV, self.bridge.memory, self.bridge.model, wrong, 'C-basis', demo.REQ)
        changed = self.bridge.clone()
        changed.memory.apply(dict(op='record', id='changed-before', origin='received',
                                  source='altered source for a negative test', text='A different original.'))
        changed.memory.apply(dict(op='relate', goal='C-basis', events=['changed-before'], note='Negative fixture.'))
        mapping = {k: v for k, v in changed.source_map.items() if v != 'before'}
        mapping['changed-before'] = 'before'
        with self.assertRaises(ValueError):
            wa.Bridge(ENV, changed.memory, changed.model, mapping, 'C-basis', demo.REQ)

    def test_forged_candidate_list_fails_fixed_generator_verification(self):
        receiver = self.receiver()
        _, _, witness = self.bridge.arrive(receiver, 'full-route', '保持根拠', 'before', 'arrival')
        observation = deepcopy(witness['active'])
        observation['before']['answer_fingerprints'] = ['invented']
        with self.assertRaises(ValueError):
            wa.verify_observation(ENV, self.bridge.model, observation)

    def test_recomputed_other_c_cannot_replace_the_active_boundary(self):
        receiver = self.receiver()
        bridge, actor, _ = self.bridge.arrive(receiver, 'full-route', '保持根拠', 'before', 'arrival')
        value = json.loads(bridge.snapshot(actor)[0])
        value['boundaries'][0]['active'] = deepcopy(value['boundaries'][0]['current_window'])
        raw = wa.encode(value)
        with self.assertRaisesRegex(ValueError, 'actually bound'):
            wa.Bridge.restore(ENV, raw, hashlib.sha256(raw).hexdigest())

    def test_replayed_e4_cannot_relabel_a_computed_boundary_as_no_change(self):
        receiver = self.receiver()
        bridge, actor, _ = self.bridge.arrive(receiver, 'full-route', '保持根拠', 'before', 'arrival')
        pair = json.loads(bridge.snapshot(actor)[0])
        replacement = wa.fresh_memory(ENV)
        for row in pair['memory']['journal']:
            cmd = deepcopy(row['command'])
            if cmd.get('id') == 'arrival':
                receipt = json.loads(cmd['text'])
                receipt['comparison']['panel_crossed'] = False
                cmd['text'] = wa.encode(receipt).decode().strip()
            replacement.apply(cmd)
        pair['memory'] = json.loads(replacement.snapshot()[0])
        raw = wa.encode(pair)
        with self.assertRaisesRegex(ValueError, 'stored boundary receipt'):
            wa.Bridge.restore(ENV, raw, hashlib.sha256(raw).hexdigest())

    def test_omitting_witness_cannot_skip_verification_of_a_stored_arrival(self):
        receiver = self.receiver()
        bridge, actor, _ = self.bridge.arrive(receiver, 'full-route', '保持根拠', 'before', 'arrival')
        pair = json.loads(bridge.snapshot(actor)[0])
        pair['boundaries'] = []
        raw = wa.encode(pair)
        with self.assertRaisesRegex(ValueError, 'match both ways'):
            wa.Bridge.restore(ENV, raw, hashlib.sha256(raw).hexdigest())

    def test_later_projection_cannot_be_presented_as_a_pre_arrival_read(self):
        receiver = self.receiver()
        bridge, actor, _ = self.bridge.arrive(receiver, 'full-route', '保持根拠', 'before', 'arrival')
        pair = json.loads(bridge.snapshot(actor)[0])
        later = bridge.project('full-route', '保持根拠')['provenance']
        pair['boundaries'][0]['projection'] = later
        raw = wa.encode(pair)
        with self.assertRaisesRegex(ValueError, 'immediately before'):
            wa.Bridge.restore(ENV, raw, hashlib.sha256(raw).hexdigest())


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python test_woven_action.py <existing-runtime-root>')
    with redirect_stdout(io.StringIO()):
        ENV = wa.environment(Path(sys.argv.pop()).resolve())
    unittest.main(verbosity=2)
