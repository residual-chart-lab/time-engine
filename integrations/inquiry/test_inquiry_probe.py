import unittest
from dataclasses import replace
from fractions import Fraction as Q
from unittest.mock import patch

import inquiry_probe as p
from inquiry_probe import d
import rr59_study as e


class InquiryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared,cls.firsts,cls.pairs,cls.current,cls.future,_=e.retained.fixtures()
        cls.local=d.Scope((cls.current,),entry='RR59-test-current')
        cls.later=d.Scope((cls.future,),entry='RR59-test-arrived')

    def test_identical_present_projection_has_distinct_later_labels(self):
        features=[(pair.value,pair.original.kernel(self.current)) for pair in self.pairs]
        labels=[pair.original.kernel(self.future)!=pair.representative.kernel(self.future)
                for pair in self.pairs]
        self.assertEqual(len(set(features)),1)
        self.assertEqual(labels,[False,True,True,True])

    def test_trigger_reads_no_exact_original_leaf_or_closure_oracle(self):
        d.base_responses.cache_clear()
        with patch.object(d.AffineLetter,'kernel',side_effect=AssertionError('no original leaf response')), \
             patch.object(d.RetainedPair,'residual_tensor',side_effect=AssertionError('no tensor expansion')), \
             patch.object(d,'exact_preview',side_effect=AssertionError('no closure oracle')), \
             patch.object(d,'adaptive_preview',side_effect=AssertionError('no closure preview')):
            self.assertFalse(p.initiate(self.pairs[1],self.local).requested)
            self.assertTrue(p.initiate(self.pairs[1],self.later).requested)

    def test_silence_now_is_not_permission_for_later_replacement(self):
        pair=self.pairs[1];signal=p.initiate(pair,self.local)
        self.assertFalse(signal.requested)
        self.assertEqual(d.assess(pair,self.local).status,d.SAFE)
        self.assertEqual(d.assess(pair,self.later).status,d.DIFFERENT)
        self.assertTrue(p.initiate(pair,self.later).requested)

    def test_signal_binds_arrived_frame_entry_pair_and_evidence(self):
        pair=self.pairs[1];signal=p.initiate(pair,self.later)
        self.assertTrue(p.verify_signal(pair,self.later,signal))
        for changed_pair,scope,changed_signal in (
            (pair,self.local,signal),
            (pair,replace(self.later,entry='other entry'),signal),
            (replace(pair,origin='other source'),self.later,signal),
            (pair,self.later,replace(signal,requested=False)),
            (pair,self.later,replace(signal,factor=(Q(0),)*4))):
            with self.assertRaises(ValueError):p.verify_signal(changed_pair,scope,changed_signal)

    def test_an_inspection_signal_is_not_a_replacement_or_cell_certificate(self):
        pair=self.pairs[1];signal=p.initiate(pair,self.later)
        with self.assertRaises(ValueError):d.read(pair,self.later,d.Meter(),signal)
        from recursive_upper_decoder import promote_word
        with self.assertRaises(ValueError):promote_word(signal)

    def test_large_and_tiny_residues_use_the_same_directional_rule(self):
        for shift in (Q(1,10**20),Q(10**50)):
            pair=e.pair_with_shift(self.pairs[0],shift,'RR59-size-'+str(shift))
            saved=(pair.original,pair.original.weights,pair.digest)
            self.assertFalse(p.initiate(pair,self.local).requested)
            self.assertTrue(p.initiate(pair,self.later).requested)
            self.assertEqual(saved,(pair.original,pair.original.weights,pair.digest))

    def test_zero_shift_does_not_raise_for_a_nonzero_direction(self):
        signal=p.initiate(self.pairs[0],self.later)
        self.assertTrue(any(signal.factor))
        self.assertFalse(signal.requested)

    def test_known_scope_is_not_silently_widened_or_changed(self):
        for scope in (d.Scope((self.current,self.future)),
                      d.Scope((self.current,),observation='compression'),
                      d.Scope((self.current,),observation='boundary_tensor')):
            with self.assertRaises(ValueError):p.initiate(self.pairs[1],scope)
        singular=d.Scope((((Q(1,3),0,0),(0,Q(1,3),0),(0,0,Q(1,3))),))
        with self.assertRaises(ValueError):p.initiate(self.pairs[1],singular)

    def test_primitive_intervention_keeps_prefix_groups_and_order(self):
        first=self.firsts[3]
        original=d.query_from_first(first,self.future,'RR59-original-order')
        reference=e.representative_query(first,self.future,self.pairs[1].representative,'RR59-reference-order')
        self.assertEqual(tuple(map(len,original.groups)),tuple(map(len,reference.groups)))
        self.assertEqual(original.groups[:2],reference.groups[:2])
        self.assertNotEqual(original.groups[2:],reference.groups[2:])
        self.assertEqual(original.inherited,reference.inherited)
        self.assertEqual(original.target,reference.target)
        self.assertEqual(original.tolerance,reference.tolerance)

    def test_a_signal_can_leave_both_fixed_result_verdicts_unchanged(self):
        y=e.perturbed_frame(self.future);scope=d.Scope((y,),entry='RR59-control')
        first=self.firsts[2];pair=self.pairs[1]
        self.assertTrue(p.initiate(pair,scope).requested)
        original=d.query_from_first(first,y,'RR59-control-original')
        reference=e.representative_query(first,y,pair.representative,'RR59-control-reference')
        self.assertFalse(d.exact_preview(original,d.Meter())[0])
        self.assertFalse(d.exact_preview(reference,d.Meter())[0])

    def test_trigger_digest_remains_the_same_after_later_validation(self):
        pair=self.pairs[1];signal=p.initiate(pair,self.later);digest=signal.digest
        first=self.firsts[2];original=first.residue.terminal_operation
        query=d.query_from_first(first,self.future,'RR59-later-audit')
        self.assertIsNotNone(d.adaptive_preview(query,d.Meter()).verdict)
        self.assertEqual(signal.digest,digest)
        self.assertIs(first.residue.terminal_operation,original)
        self.assertTrue(p.verify_signal(pair,self.later,signal))

    def test_archived_input_authentication_and_payloads_are_preserved(self):
        self.assertEqual(len(e.retained.actuals()),3)
        for pair in self.pairs:
            self.assertEqual(pair.original.weights,tuple(w+pair.shift*v for w,v in
                zip(pair.representative.weights,pair.direction)))


if __name__=='__main__':unittest.main()
