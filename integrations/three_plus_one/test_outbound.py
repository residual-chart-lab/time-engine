import json
import unittest
from dataclasses import replace
from unittest.mock import patch

import outbound as port
from outbound import Q


class OutboundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared = {mode: port.prepare(mode=mode) for mode in port.MODES}
        cls.requirement = port.primary_requirement()
        cls.keep_receipt = port.select(cls.prepared['keep'], cls.requirement, 1)
        cls.keep = port.execute(cls.keep_receipt)
        cls.erase = port.execute(port.select(cls.prepared['erase'], cls.requirement, 1))
        cls.alternate = port.alternative_requirement(cls.prepared['keep'])
        cls.other_receipt = port.select(cls.prepared['keep'], cls.alternate.requirement, 1)
        cls.other = port.execute(cls.other_receipt)

    def test_actual_base_and_carried_motion_are_present_including_all_seventeen_parameters(self):
        course = self.keep_receipt.state.course
        self.assertEqual(len(course.checkpoints), 9)
        self.assertTrue(all(len(s.network) == 17 and len(s.tangent) == 4 for s in course.checkpoints))
        self.assertNotEqual(course.checkpoints[0].network, course.checkpoints[-1].network)
        self.assertNotEqual(course.checkpoints[0].tangent, course.checkpoints[-1].tangent)

    def test_exact_present_phase_and_current_receiver_action_survive_every_intervention(self):
        self.assertEqual(len({p.state.phase for p in self.prepared.values()}), 1)
        for p in self.prepared.values():
            self.assertEqual(port.dot(p.state.radial, p.state.hidden), 0)
            self.assertEqual(port.dot(p.state.radial, p.state.vector)/port.dot(p.state.radial, p.state.radial), p.state.phase)
            for c in p.candidates:
                self.assertEqual(c.leaf.kernel(p.receiver.anchor.current_context), (-9, 0, 0, 0))
                self.assertEqual(sum(c.leaf.weights), 1)

    def test_shape_channel_excludes_common_offset_and_parallel_gain(self):
        state = self.prepared['keep'].state
        b = port.centered(port.mv(state.response_matrix, state.visible))
        self.assertEqual(sum(state.shape), 0)
        self.assertEqual(port.dot(b, state.shape), 0)
        self.assertGreater(sum(float(v)**2 for v in state.shape), 1e-12)

    def test_same_four_real_contacts_same_future_and_tolerance_give_different_permissions(self):
        for p in self.prepared.values():
            self.assertEqual(tuple(c.contact_index for c in p.candidates), (0, 1, 2, 3))
        self.assertEqual(port.allowed_indices(self.prepared['keep'], self.requirement), (0,))
        self.assertEqual(port.allowed_indices(self.prepared['erase'], self.requirement), (0, 1, 2, 3))
        self.assertEqual(self.keep.commitment.requirement, self.erase.commitment.requirement)
        self.assertEqual(self.requirement.tolerance, Q(1, 10**12))
        self.assertTrue(all(port.preview(c, self.keep_receipt.receiver, self.requirement)[-1] > Q(1, 10**10)
                            for c in self.prepared['keep'].candidates[1:]))

    def test_exact_affine_response_identity_explains_the_port_effect(self):
        p = self.prepared['keep']
        baseline = p.candidates[0]
        e0 = port.preview(baseline, p.receiver, self.requirement)[0][0]
        shifted_leaf = replace(baseline.leaf, weights=tuple(w+d for w, d in zip(baseline.leaf.weights, p.receiver.delta)))
        slope_candidate = replace(baseline, leaf=shifted_leaf)
        slope = port.preview(slope_candidate, p.receiver, self.requirement)[0][0]-e0
        self.assertNotEqual(slope, 0)
        for candidate in p.candidates:
            self.assertEqual(port.preview(candidate, p.receiver, self.requirement)[0][0]-e0, candidate.shift*slope)

    def test_restore_and_same_norm_blind_control_separate_shape_from_memory_size(self):
        self.assertEqual(self.prepared['restore'].state.vector, self.prepared['keep'].state.vector)
        self.assertEqual(port.allowed_indices(self.prepared['restore'], self.requirement), (0,))
        self.assertEqual(port.allowed_indices(self.prepared['blind'], self.requirement), (0, 1, 2, 3))
        keep_norm = float(port.dot(self.prepared['keep'].state.hidden, self.prepared['keep'].state.hidden))
        blind_norm = float(port.dot(self.prepared['blind'].state.hidden, self.prepared['blind'].state.hidden))
        self.assertLess(abs(keep_norm/blind_norm-1), 1e-12)

    def test_opposite_hidden_direction_keeps_exact_phase_and_norm_but_changes_source_coefficients(self):
        a, b = self.prepared['keep'], self.prepared['flip']
        self.assertEqual(a.state.phase, b.state.phase)
        self.assertEqual(port.dot(a.state.hidden, a.state.hidden), port.dot(b.state.hidden, b.state.hidden))
        for x, y in zip(a.candidates, b.candidates):
            self.assertEqual(x.shift, -y.shift)
        self.assertNotEqual(a.candidates[1].leaf, b.candidates[1].leaf)

    def test_zero_coupling_and_zero_retention_remove_the_effect(self):
        zero = port.prepare(spec=port.PortSpec(gain=0))
        fresh = port.prepare(port.CourseConfig(carry_epochs=0))
        self.assertEqual(port.allowed_indices(zero, self.requirement), (0, 1, 2, 3))
        self.assertEqual(port.allowed_indices(fresh, self.requirement), (0, 1, 2, 3))

    def test_fixed_half_and_double_gains_preserve_the_representative_effect(self):
        for gain in (Q(1, 2), Q(2)):
            p = port.prepare(spec=port.PortSpec(gain=gain))
            self.assertEqual(port.allowed_indices(p, self.requirement), (0,))

    def test_admissibility_reads_actions_rather_than_contact_labels(self):
        p = self.prepared['keep']
        self.assertTrue(port.admissible(replace(p.candidates[0], contact_index=99), p.receiver, self.requirement))
        self.assertFalse(port.admissible(replace(p.candidates[1], contact_index=0), p.receiver, self.requirement))

    def test_changed_entry_shape_or_candidate_pool_is_rejected_before_commitment(self):
        p = self.prepared['keep']
        variants = [replace(p, candidates=p.candidates[:1]),
                    replace(p, candidates=tuple(reversed(p.candidates))),
                    replace(p, state=replace(p.state, shape=(Q(0),)*4)),
                    replace(p, candidates=(p.candidates[1],)*4)]
        for fake in variants:
            with self.assertRaises(ValueError):
                port.select(fake, self.requirement, 1)

    def test_actual_contact_candidates_have_distinct_network_updates_even_when_receiver_coefficients_coincide(self):
        state = self.prepared['erase'].state
        after = {port.execute_contact(state, i).after.network for i in range(4)}
        self.assertEqual(len(after), 4)
        self.assertEqual(len({c.leaf.weights for c in self.prepared['erase'].candidates}), 1)

    def test_current_free_choice_chooses_within_permissions_and_future_does_not_rank(self):
        p = self.prepared['erase']
        self.assertEqual([port.select(p, self.requirement, i).chosen.contact_index for i in range(4)], [0, 1, 2, 3])
        self.assertEqual([port.select(self.prepared['keep'], self.requirement, i).chosen.contact_index for i in range(4)], [0]*4)

    def test_committed_execution_calls_no_root_search_shape_projection_or_candidate_selection(self):
        with patch('outbound.source_course', side_effect=AssertionError('no past regeneration')), \
             patch('outbound.carrier', side_effect=AssertionError('no receiver reconstruction')), \
             patch('outbound.prepare', side_effect=AssertionError('no new comparison')), \
             patch('outbound.port_state', side_effect=AssertionError('no new shape projection')), \
             patch('outbound.select', side_effect=AssertionError('no new selection')), \
             patch('outbound.admissible', side_effect=AssertionError('no candidate comparison')), \
             patch('outbound.single.isolate', side_effect=AssertionError('no root solver')), \
             patch('outbound.single.candidates', side_effect=AssertionError('no word search')):
            actual = port.execute(self.keep_receipt)
        self.assertEqual(actual, self.keep)

    def test_actual_producer_publication_and_exact_consumer_cell_are_ordered_and_level_correct(self):
        for occurrence in (self.keep, self.erase, self.other):
            e = occurrence.closed_engine
            kinds = [event.kind for event in e.events]
            self.assertLess(kinds.index('rr56-3plus1-contact-executed'), kinds.index('lower-cell-closed'))
            self.assertLess(kinds.index('lower-cell-closed'), kinds.index('same-level-operation-published'))
            self.assertLess(kinds.index('same-level-operation-published'), kinds.index('rr56-shared-future-context-arrived'))
            self.assertEqual(len(e.stock), 5)
            self.assertTrue(all(x.level == 2 for x in e.stock))
            self.assertEqual(len(e.outputs), 1)
            self.assertEqual(occurrence.terminal_operation.level, 3)
            self.assertEqual(len(occurrence.terminal_operation.cell.beta), 2)
            self.assertEqual(port.promote_word(occurrence.terminal_operation.cell), occurrence.terminal_operation)

    def test_fixed_request_actual_endpoint_and_inherited_accumulators_stay_distinct(self):
        o = self.keep
        original = o.commitment.receiver.anchor.original
        self.assertEqual(o.consumer_start.live.accumulated, original.upper.live.accumulated)
        self.assertEqual(o.consumer_start.executed_word, original.upper.executed_word)
        self.assertNotEqual(o.actual_endpoint, o.commitment.requirement.result)
        self.assertLess(o.closure_error, port.EPSILON/2)
        self.assertIsNone(o.closed_engine.pending)
        self.assertEqual(o.closed_engine.phase, 'IDLE')
        self.assertEqual(o.status, 'ONE_FLOWER_COMPLETE')

    def test_alternate_common_future_changes_the_allowed_actual_retained_contact(self):
        p = self.prepared['keep']
        self.assertEqual(port.allowed_indices(p, self.alternate.requirement), (1,))
        self.assertEqual(port.allowed_indices(self.prepared['erase'], self.alternate.requirement), ())
        self.assertNotEqual(self.other.actual_source, self.keep.actual_source)
        self.assertNotEqual(self.other.neural_contact.after.network, self.keep.neural_contact.after.network)
        self.assertTrue(port.verify_occurrence(self.other, self.other_receipt))
        with self.assertRaises(ValueError):
            port.select(self.prepared['erase'], self.alternate.requirement)

    def test_neural_contact_derivative_matches_an_independent_nonlinear_update(self):
        from xnor_retained_difference import inject, read
        from threeplusone import transverse_residual
        o = self.other
        state = o.commitment.state
        base = port.network_from_snapshot(o.neural_contact.before.network)
        r = [float(v) for v in state.radial]
        amount = 1e-3
        plus = inject(base, [float(v) for v in state.vector], amount)
        minus = inject(base, [float(v) for v in state.vector], -amount)
        before = [read(r, [z.imag for z in transverse_residual(n)]) for n in (plus, minus)]
        for n in (plus, minus):
            n.train_one(o.neural_contact.sample, o.neural_contact.target)
        after = [read(r, [z.imag for z in transverse_residual(n)]) for n in (plus, minus)]
        independent = (after[0]-after[1]-before[0]+before[1])/(2*amount)
        self.assertLess(abs(independent-float(o.neural_contact.fixed_readout_response)), 1e-8)

    def test_coherent_endpoint_or_source_or_neural_history_substitution_is_rejected(self):
        o = self.keep
        wrong_network = replace(o.neural_contact.after, network=(Q(0),)*17)
        variants = [replace(o, actual_endpoint=o.commitment.requirement.result, closure_error=Q(0)),
                    replace(o, actual_source=self.other.actual_source),
                    replace(o, neural_contact=replace(o.neural_contact, after=wrong_network))]
        for fake in variants:
            with self.assertRaises(ValueError):
                port.verify_occurrence(fake, self.keep_receipt)

    def test_fixed_future_result_tolerance_and_external_commitment_cannot_be_swapped(self):
        with self.assertRaises(ValueError):
            port.FutureRequirement(self.requirement.context, tolerance=port.EPSILON*2)
        with self.assertRaises(ValueError):
            port.FutureRequirement(self.requirement.context, result=self.keep.actual_endpoint)
        with self.assertRaises(ValueError):
            port.verify_occurrence(self.keep, replace(self.keep_receipt, requirement=self.alternate.requirement))

    def test_exact_json_round_trip_keeps_joint_history_and_external_input_binding(self):
        for o, mode, requirement in ((self.keep, 'keep', self.requirement),
                                      (self.erase, 'erase', self.requirement),
                                      (self.other, 'keep', self.alternate.requirement)):
            payload = json.loads(json.dumps(port.export_occurrence(o)))
            self.assertEqual(port.import_occurrence(payload, requirement, mode=mode, free_choice=1), o)
        payload = port.export_occurrence(self.keep)
        with self.assertRaises(ValueError):
            port.import_occurrence(payload, self.requirement, mode='erase', free_choice=1)

    def test_unknown_types_and_cyclic_graphs_are_rejected(self):
        payload = port.export_occurrence(self.keep)
        payload['nodes'][0]['type'] = 'untrusted.Type'
        with self.assertRaises(ValueError):
            port.import_occurrence(payload, self.requirement, free_choice=1)
        payload = {'schema': 'time-engine-3plus1-outbound-occurrence-v1', 'root': {'ref': 0},
                   'nodes': [{'tuple': [{'ref': 0}]}]}
        with self.assertRaises(ValueError):
            port.import_occurrence(payload, self.requirement, free_choice=1)

    def test_invalid_interventions_specs_and_input_shapes_are_rejected(self):
        for action in (lambda: port.prepare(mode='invented'), lambda: port.PortSpec(gain=-1),
                       lambda: port.PortSpec(reference_contact=2), lambda: port.network_from_snapshot((Q(1),)*4),
                       lambda: port.CourseConfig(start_epoch=1)):
            with self.assertRaises(ValueError):
                action()


if __name__ == '__main__':
    unittest.main()
