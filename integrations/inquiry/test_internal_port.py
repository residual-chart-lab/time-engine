import unittest
from dataclasses import replace
from fractions import Fraction as Q
from unittest.mock import patch

import internal_port as m
from internal_port import d,te


class InternalPortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.short=m.begin('keep',1,0)
        cls.detour=m.begin('keep',1,1)
        cls.spec=te.pair.ConnectionSpec()
        cls.request=m.request_connection(cls.short)
        cls.delivery=m.emit(cls.request)

    def test_current_choice_requests_a_connection_after_a_completed_flower(self):
        f=self.short.first;r=self.request
        self.assertEqual(f.actual_endpoint,f.fixed_result)
        self.assertEqual(f.closed_engine.phase,'IDLE')
        self.assertIsNone(f.closed_engine.pending)
        self.assertEqual(r.waiting.phase,'WAIT_CONTEXT')
        self.assertEqual(r.waiting.events[-1].kind,'boundary-requested')
        self.assertIsNone(r.waiting.pending.arrived_context)
        self.assertTrue(r.notice.requested)
        self.assertEqual(r.waiting.events[:-1],f.closed_engine.events)

    def test_the_request_constructs_no_next_context_or_second_source_or_future_fixture(self):
        with patch.object(te.pair,'connection_context',side_effect=AssertionError('no next port yet')), \
             patch.object(te.triple,'source_witness',side_effect=AssertionError('no next source yet')), \
             patch.object(te,'construct_requirement',side_effect=AssertionError('no common future fixture')), \
             patch.object(te,'finite_family',side_effect=AssertionError('no 128-family lookahead')):
            r=m.request_connection(self.short)
        self.assertTrue(r.notice.requested)

    def test_notice_does_not_expand_the_original_response_or_boundary(self):
        with patch.object(d.AffineLetter,'kernel',side_effect=AssertionError('no retained kernel')), \
             patch.object(d,'tensor',side_effect=AssertionError('no original tensor')), \
             patch.object(d.RetainedPair,'residual_tensor',side_effect=AssertionError('no residual expansion')), \
             patch.object(te.pair,'ordered_terminal_readout',side_effect=AssertionError('no full port yet')):
            self.assertTrue(m.notice(self.short,self.spec).requested)

    def test_the_executed_word_gives_the_two_distinct_source_masses(self):
        self.assertEqual(m.leaf_view(self.short)[1:],((3,),Q(1,2)))
        self.assertEqual(m.leaf_view(self.detour)[1:],((5,6),Q(11,21)))

    def test_the_transport_defect_matches_the_original_ordered_RR53_readout(self):
        for f in (self.short,self.detour):
            for strength in (Q(0),Q(1,2048),Q(1,1024),Q(1,512)):
                spec=te.pair.ConnectionSpec(strength=strength)
                signal=m.notice(f,spec);raw,y=te.pair.connection_context(f.first,spec)
                _,reference=m.reference_context(f,spec)
                self.assertEqual(signal.requested,y!=reference)
                for i in range(3):
                    for j in range(3):self.assertEqual(y[i][j]-reference[i][j],
                        strength*signal.source_mass*f.pair.shift*signal.direction[i][j])

    def test_cutting_the_connection_prevents_both_notice_and_response_exposure(self):
        spec=te.pair.ConnectionSpec(strength=0)
        request=m.request_connection(self.short,spec);delivery=m.emit(request)
        self.assertFalse(request.notice.requested)
        self.assertFalse(delivery.exposure.requested)
        self.assertEqual(delivery.context,te.pair.boundary_readout(self.short.first.closed_engine.designated_head))

    def test_erasure_and_restore_affect_the_port_without_changing_current_closure(self):
        erased=m.begin('erase',1,0);restored=m.begin('restore',1,0)
        self.assertFalse(m.request_connection(erased).notice.requested)
        self.assertTrue(m.request_connection(restored).notice.requested)
        self.assertEqual(erased.first.actual_endpoint,self.short.first.actual_endpoint)
        self.assertEqual(restored.first.residue.source,self.short.first.residue.source)
        self.assertEqual(m.emit(m.request_connection(restored)).context,self.delivery.context)

    def test_arrival_keeps_actual_cumulatives_stock_tapes_and_completed_events(self):
        before=self.short.first.closed_engine;after=self.delivery.arrived
        self.assertEqual(after.lower.live.accumulated,before.lower.live.accumulated)
        self.assertEqual(after.upper.live.accumulated,before.upper.live.accumulated)
        self.assertEqual(after.lower.executed_word,before.lower.executed_word)
        self.assertEqual(after.upper.executed_word,before.upper.executed_word)
        self.assertEqual(after.stock,before.stock)
        self.assertEqual(after.outputs,before.outputs)
        self.assertEqual(after.events[:len(before.events)],before.events)
        self.assertEqual([e.kind for e in after.events[len(before.events):]],
            ['boundary-requested','rr53-terminal-residue-port-emitted','context-arrived'])
        self.assertEqual(after.phase,'OPEN')

    def test_notice_is_bound_to_strength_actual_word_and_evidence(self):
        signal=self.request.notice
        self.assertTrue(m.verify_notice(self.short,self.spec,signal))
        for flight,spec,notice in ((self.short,replace(self.spec,strength=Q(1,512)),signal),
            (self.detour,self.spec,signal),(self.short,self.spec,replace(signal,requested=False)),
            (self.short,self.spec,replace(signal,source_mass=Q(0))),
            (self.short,self.spec,replace(signal,observation='kernel'))):
            with self.assertRaises(ValueError):m.verify_notice(flight,spec,notice)

    def test_a_changed_first_requirement_is_rejected_before_emission(self):
        fake=replace(self.short,first=replace(self.short.first,fixed_result=(Q(2),0,0,0)))
        with self.assertRaises(ValueError):m.request_connection(fake)

    def test_request_inheritance_and_generated_context_cannot_be_substituted(self):
        waiting=self.request.waiting
        upper=te.port.ExecutionState(te.port.UpperState(waiting.upper.live.context,(Q(2),0,0,0)),
                                    waiting.upper.executed_word)
        fake=replace(self.request,waiting=replace(waiting,upper=upper))
        with self.assertRaises(ValueError):m.emit(fake)
        with self.assertRaises(ValueError):m.verify_delivery(replace(self.delivery,context=
            self.short.first.residue.internal_context))

    def test_a_notice_is_neither_a_replacement_certificate_nor_a_cell(self):
        with self.assertRaises(ValueError):d.read(self.short.pair,self.delivery.exposure.scope,d.Meter(),self.request.notice)
        from recursive_upper_decoder import promote_word
        with self.assertRaises(ValueError):promote_word(self.request.notice)

    def test_internal_kernel_read_uses_the_retained_original_and_preserves_old_proof(self):
        pair=self.short.pair;before=pair.original.weights
        meter=d.Meter();response=d.read(pair,self.delivery.exposure.scope,meter)
        self.assertEqual(response,pair.original.kernel(self.delivery.context))
        self.assertNotEqual(response,pair.representative.kernel(self.delivery.context))
        self.assertEqual(meter.exact_retained_responses,1)
        self.assertEqual(pair.original.weights,before)
        self.assertEqual(self.short.local_certificate.status,d.SAFE)
        with self.assertRaises(ValueError):d.verify_certificate(pair,self.delivery.exposure.scope,
                                                               self.short.local_certificate)

    def test_direction_tensor_is_a_nonzero_STF_residue_with_positive_self_response(self):
        direction=m.direction_tensor(self.short.pair)
        self.assertEqual(sum(direction[i][i] for i in range(3)),0)
        self.assertTrue(all(direction[i][j]==direction[j][i] for i in range(3) for j in range(3)))
        norm=sum(v*v for row in direction for v in row)
        self.assertGreater(norm,0)
        self.assertEqual(tuple(d.join(direction,direction)),(2*norm,0,0,0))

    def test_a_nonzero_source_line_control_changes_context_but_not_arrived_kernel(self):
        for f in (self.short,self.detour):
            pair,y,reference=m.cancellation_control(f,self.spec)
            self.assertNotEqual(pair.shift,0)
            self.assertNotEqual(y,reference)
            self.assertTrue(d.regular(y,pair.original.library))
            self.assertEqual(pair.original.kernel(y),pair.representative.kernel(y))
            self.assertFalse(m.probe.initiate(pair,d.Scope((y,),entry='RR60-cancellation')).requested)
            # This algebraic control cannot masquerade as the fixed 3+1 input.
            with self.assertRaises(ValueError):m.request_connection(replace(f,pair=pair))

    def test_one_post_notice_continuation_produces_and_certifies_its_source_before_use(self):
        second,certificate=m.continue_one(self.delivery)
        before=self.short.first.closed_engine;after=second.closed_engine
        self.assertTrue(self.request.notice.requested)
        self.assertEqual(len(after.stock),len(before.stock)+1)
        self.assertEqual(after.stock[:len(before.stock)],before.stock)
        self.assertEqual(after.events[:len(before.events)],before.events)
        self.assertEqual(te.triple.replay_frozen(second,self.short.first),second)
        self.assertLess(second.closure_error,second.tolerance/2)
        self.assertEqual(after.phase,'IDLE')
        self.assertIsNone(after.pending)
        self.assertEqual(certificate.selected_branch,0)
        kinds=[e.kind for e in after.events[len(before.events):]]
        self.assertLess(kinds.index('lower-cell-closed'),kinds.index('same-level-operation-published'))
        self.assertLess(kinds.index('same-level-operation-published'),len(kinds)-1)

    def test_only_the_declared_anchored_port_and_replay_policy_are_accepted(self):
        with self.assertRaises(ValueError):m.request_connection(self.short,te.pair.ConnectionSpec(mode='direct'))
        delivery=m.emit(m.request_connection(self.short,te.pair.ConnectionSpec(strength=0)))
        with self.assertRaises(ValueError):m.continue_one(delivery)

    def test_first_closure_requires_no_new_training_or_future_frame_search(self):
        te.prepare.cache_clear()
        with (patch('outbound.source_course',side_effect=AssertionError('no new training')),
              patch.object(te,'construct_requirement',side_effect=AssertionError('no future fixture')),
              patch.object(te,'finite_family',side_effect=AssertionError('no 128-family enumeration'))):
            f=m.begin('keep',2,1)
        self.assertEqual(f.first.actual_endpoint,f.first.fixed_result)


if __name__=='__main__':unittest.main()
