import copy
import json
import unittest
from dataclasses import replace
from unittest.mock import patch

from completed_single_flower import export_record, import_record, Configuration
from retrospective_residue_readout import *


class RetrospectiveResidueReadoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records={b:tuple(load_published(b,c) for c in (0,1)) for b in ('first','second')}
        cls.short,cls.long=cls.records['first']
        cls.origin=cls.short.commitment.anchor.original.designated_head.cell.start.live.context
        cls.reference=ReferenceInput(UpperState(cls.origin))

    def test_actual_saved_operation_changes_the_current_reference_state(self):
        r=self.short
        response=read_retained(r,r.commitment,self.reference)
        self.assertEqual(response.after,r.residue.terminal_operation.execute(self.reference.live))
        self.assertNotEqual(response.after,self.reference.live)

    def test_two_saved_histories_act_differently_in_the_changed_reference(self):
        a,b=(read_retained(r,r.commitment,self.reference) for r in (self.short,self.long))
        self.assertNotEqual(a.after,b.after)
        self.assertNotEqual(a.visible_normalized_after,b.visible_normalized_after)

    def test_reference_reads_need_no_original_solver_search_or_reconstructed_experiment(self):
        with patch('completed_single_flower.run_flower',side_effect=AssertionError('no rerun')), \
             patch('completed_single_flower.prepare_model',side_effect=AssertionError('no reconstruction')), \
             patch('completed_single_flower.isolate',side_effect=AssertionError('no root solving')), \
             patch('completed_single_flower.candidates',side_effect=AssertionError('no candidate search')), \
             patch('history_selection_gap.retained_candidates',side_effect=AssertionError('no future search')):
            a=read_retained(self.short,self.short.commitment,self.reference)
            b=read_retained(self.long,self.long.commitment,self.reference)
        self.assertNotEqual(a.after,b.after)

    def test_reference_does_not_mutate_or_extend_the_completed_history(self):
        before=copy.deepcopy(self.short)
        read_retained(self.short,self.short.commitment,self.reference)
        self.assertEqual(self.short,before)
        self.assertEqual(len(self.short.closed_engine.rounds),1)
        self.assertIsNone(self.short.closed_engine.pending)

    def test_a_further_exact_file_style_round_trip_keeps_active_response(self):
        r=import_record(json.loads(json.dumps(export_record(self.long))),Configuration(petal_choice=1))
        self.assertEqual(read_retained(r,r.commitment,self.reference),
                         read_retained(self.long,self.long.commitment,self.reference))

    def test_the_current_correction_context_can_be_exactly_blind(self):
        for pair in self.records.values():
            y=pair[0].commitment.anchor.current_context
            responses=[read_retained(r,r.commitment,ReferenceInput(UpperState(y))) for r in pair]
            self.assertEqual(responses[0].after,responses[1].after)
            self.assertEqual(responses[0].after.accumulated,(1,0,0,0))

    def test_actual_endpoint_gain_is_removed_by_a_declared_reading_convention(self):
        for pair in self.records.values():
            self.assertNotEqual(pair[0].actual_endpoint,pair[1].actual_endpoint)
            y=pair[0].residue.internal_context
            reference=ReferenceInput(UpperState(y,(1,2,-1,3)))
            responses=[read_retained(r,r.commitment,reference) for r in pair]
            for r,response in zip(pair,responses):
                self.assertEqual(response.visible_normalized_after,reference.live)
                baseline=tuple(qmul(inverse(r.residue.terminal_operation.visible),
                                    response.visible_only_after.accumulated))
                self.assertEqual(baseline,reference.live.accumulated)
            self.assertNotEqual(pair[0].actual_endpoint,pair[1].actual_endpoint)

    def test_nontrivial_current_quaternion_keeps_the_distinction(self):
        reference=ReferenceInput(UpperState(self.origin,(1,2,-1,3)))
        a,b=[read_retained(r,r.commitment,reference) for r in (self.short,self.long)]
        self.assertNotEqual(a.after,b.after)
        self.assertNotEqual(a.visible_normalized_after,b.visible_normalized_after)
        self.assertEqual(a.after.context,reference.live.context)

    def test_zero_reference_is_blind_not_a_universal_history_discriminator(self):
        reference=ReferenceInput(UpperState(self.origin,(0,0,0,0)))
        for r in (self.short,self.long):
            response=read_retained(r,r.commitment,reference)
            self.assertEqual(response.after,reference.live)
            self.assertEqual(response.residue_effect,(0,0,0,0))

    def test_reference_cannot_mix_a_lower_primitive_level_with_the_saved_operation(self):
        with self.assertRaisesRegex(ValueError,'same level'):
            read_retained(self.short,self.short.commitment,ReferenceInput(self.reference.live,level=1))

    def test_nonregular_reference_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'regular chart'):
            read_retained(self.short,self.short.commitment,ReferenceInput(UpperState(diagonal((Q(1,3),)*3))))

    def test_replaced_requirement_and_consumer_inheritance_are_rejected(self):
        fake=replace(self.short,fixed_result=self.short.actual_endpoint,closure_error=Q(0))
        with self.assertRaises(ValueError): read_retained(fake,self.short.commitment,self.reference)
        state=self.short.residue.consumer_after
        residue=replace(self.short.residue,consumer_after=replace(state,live=UpperState(state.live.context,(-2,0,0,0))))
        with self.assertRaises(ValueError):
            read_retained(replace(self.short,residue=residue),self.short.commitment,self.reference)

    def test_replaced_history_and_the_other_legal_receipt_are_rejected(self):
        with self.assertRaises(ValueError):
            read_retained(replace(self.short,residue=self.long.residue),self.short.commitment,self.reference)
        with self.assertRaises(ValueError): read_retained(self.short,self.long.commitment,self.reference)

    def test_a_candidate_is_not_an_actual_occurrence(self):
        from completed_single_flower import Candidate
        candidate=Candidate(self.short.commitment.indices,self.short.actual_endpoint)
        with self.assertRaisesRegex(ValueError,'actual completed record'):
            read_retained(candidate,self.short.commitment,self.reference)

    def test_uniform_interval_proof_and_independent_scalar_formula_cover_both_branches(self):
        for short,long in self.records.values():
            proof=reference_neighborhood(short,long)
            self.assertGreater(proof['normalized_abs_lower'],0)
            self.assertGreater(proof['raw_abs_lower'],0)
            y=diagonal(proof['center'])
            for record in (short,long):
                operation=record.residue.terminal_operation
                value=diagonal_kernel_interval(operation,tuple(Interval(v,v) for v in proof['center']))
                self.assertEqual(value.lo,value.hi)
                self.assertEqual(operation.kernel(y),(value.lo,0,0,0))

    def test_interval_statement_rejects_a_nonregular_or_zero_radius_domain(self):
        with self.assertRaises(ValueError): reference_neighborhood(self.short,self.long,0)
        with self.assertRaises(AssertionError): reference_neighborhood(self.short,self.long,1)


if __name__=='__main__': unittest.main()
