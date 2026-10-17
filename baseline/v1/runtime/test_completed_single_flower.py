import copy
import unittest
from dataclasses import replace
from unittest.mock import patch

from completed_single_flower import *


class CompletedSingleFlowerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ready=arrive_internal_context(produce_source(begin()))
        cls.committed=commit(propose(cls.ready))
        cls.receipt=cls.committed.commitment
        machine=cls.committed
        while machine.cursor<len(cls.receipt.word): machine=advance(machine,cls.receipt)
        cls.ended=close(machine,cls.receipt)

    def test_end_to_end_closes_one_cell_and_retains_the_actual_endpoint(self):
        record=self.ended.record
        self.assertTrue(verify_record(record,self.receipt))
        self.assertEqual(self.ended.phase,'ONE_FLOWER_COMPLETE')
        self.assertNotEqual(record.actual_endpoint,record.fixed_result)
        self.assertLess(record.closure_error,TOLERANCE/2)
        self.assertEqual(len(record.closed_engine.outputs),1)
        self.assertEqual(len(record.closed_engine.rounds),1)

    def test_different_free_choices_preserve_two_distinct_completed_histories(self):
        other=run_flower(Configuration(petal_choice=1))
        self.assertTrue(verify_record(other.record,other.commitment))
        self.assertEqual(len(self.receipt.word),2)
        self.assertEqual(len(other.commitment.word),4)
        self.assertNotEqual(self.ended.record.residue,other.record.residue)
        self.assertEqual(self.ended.problem.source,other.problem.source)
        self.assertEqual(self.ended.problem.context,other.problem.context)

    def test_execution_and_value_resume_never_call_a_solver_search_or_local_ranker(self):
        paused=copy.deepcopy(advance(self.committed,self.receipt))
        with patch('completed_single_flower.isolate',side_effect=AssertionError('solver forbidden')), \
             patch('completed_single_flower.candidates',side_effect=AssertionError('replanning forbidden')), \
             patch('history_selection_gap.retained_candidates',side_effect=AssertionError('search forbidden')), \
             patch('local_closure_selection.choose_one_step',side_effect=AssertionError('greed forbidden')):
            machine=restore(paused,self.receipt)
            while machine.cursor<len(self.receipt.word): machine=advance(machine,self.receipt)
            machine=close(machine,self.receipt)
        self.assertEqual(machine.record,self.ended.record)

    def test_target_substitution_cannot_turn_the_approximate_endpoint_into_zero_error(self):
        r=self.ended.record
        forged=replace(r,fixed_result=r.actual_endpoint,closure_error=Q(0))
        with self.assertRaisesRegex(ValueError,'original request'): verify_record(forged,self.receipt)

    def test_tolerance_substitution_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'tolerance'):
            verify_record(replace(self.ended.record,tolerance=TOLERANCE*10),self.receipt)

    def test_consumer_inheritance_and_committed_prefix_cannot_be_replaced_on_resume(self):
        paused=advance(self.committed,self.receipt)
        fake=ExecutionState(UpperState(paused.engine.upper.live.context,(-2,0,0,0)),paused.engine.upper.executed_word)
        with self.assertRaisesRegex(ValueError,'inheritance'):
            restore(replace(paused,engine=replace(paused.engine,upper=fake)),self.receipt)

    def test_changed_word_and_cursor_are_rejected_against_the_trusted_receipt(self):
        forged=replace(self.receipt,word=tuple(reversed(self.receipt.word)))
        with self.assertRaisesRegex(ValueError,'bound'):
            advance(replace(self.committed,commitment=forged),self.receipt)
        with self.assertRaises(ValueError): restore(replace(self.committed,cursor=1),self.receipt)

    def test_a_coherently_replaced_petal_does_not_pass_the_anchored_choice_rule(self):
        long=run_flower(Configuration(petal_choice=1))
        # Keep the original choice=0 anchor, but replace both record and receipt
        # consistently with the other legal path. Canonical choice validation
        # must reject this, not merely verify internal result consistency.
        forged_receipt=replace(long.commitment,anchor=self.receipt.anchor)
        forged_record=replace(long.record,commitment=forged_receipt)
        with self.assertRaisesRegex(ValueError,'anchored free entry choice'):
            verify_record(forged_record,forged_receipt)

    def test_source_producer_and_stock_cannot_be_modified_between_planning_and_commit(self):
        planned=propose(self.ready)
        fake=replace(planned.engine,lower=planned.engine.upper)
        with self.assertRaises(ValueError): commit(replace(planned,engine=fake))
        fake=replace(planned.engine,stock=planned.engine.stock[:-1])
        with self.assertRaises(ValueError): commit(replace(planned,engine=fake))

    def test_discarding_or_inserting_a_candidate_is_rejected_before_choice(self):
        planned=propose(self.ready)
        self.assertEqual(len(planned.frontier),2)
        with self.assertRaises(ValueError): commit(replace(planned,frontier=planned.frontier[:1]))
        with self.assertRaises(ValueError): commit(replace(planned,frontier=planned.frontier+planned.frontier[:1]))

    def test_no_candidate_is_not_a_completed_flower_or_a_global_impossibility(self):
        machine=run_flower(Configuration(search_cap=1))
        self.assertEqual(machine.phase,'OPEN_WITHIN_SEARCH_CAP')
        self.assertIsNone(machine.record)
        self.assertEqual(machine.engine.upper,machine.problem.start)
        with self.assertRaises(ValueError): commit(machine)

    def test_early_closure_and_postclosure_extension_are_rejected(self):
        with self.assertRaises(ValueError): close(self.committed,self.receipt)
        with self.assertRaises(ValueError): advance(self.ended,self.receipt)
        with self.assertRaises(ValueError): propose(self.ended)
        with self.assertRaises(ValueError): produce_source(self.ended)

    def test_full_terminal_residue_cannot_be_replaced_by_the_other_valid_petal(self):
        long=run_flower(Configuration(petal_choice=1))
        forged=replace(self.ended.record,residue=long.record.residue)
        with self.assertRaisesRegex(ValueError,'retained residue'): verify_record(forged,self.receipt)

    def test_retention_is_faithful_and_preserves_the_complete_nested_word(self):
        residue=retain(self.ended.record.residue)
        self.assertEqual(residue,self.ended.record.residue)
        self.assertEqual(residue.terminal_operation.cell.beta,self.receipt.word)
        self.assertEqual(residue.consumer_after.executed_word,
                         self.ended.problem.start.executed_word+self.receipt.word)
        self.assertEqual(promote_word(residue.source.cell),residue.source)
        self.assertEqual(promote_word(residue.terminal_operation.cell),residue.terminal_operation)

    def test_only_the_actual_source_is_published_and_no_next_flower_is_requested(self):
        engine=self.ended.engine;before=self.ended.anchor.original
        self.assertEqual(engine.stock,before.stock+(self.ended.problem.source,))
        self.assertIsNone(engine.pending)
        self.assertEqual(sum(e.kind=='boundary-requested' for e in engine.events),1)
        self.assertEqual(sum(e.kind=='rr52-internal-context-arrived' for e in engine.events),1)
        self.assertFalse(self.ended.frontier)

    def test_actual_event_order_is_publication_arrival_commit_execution_then_closure(self):
        kinds=[e.kind for e in self.ended.engine.events]
        ordered=['same-level-operation-published','rr52-internal-context-emitted',
                 'rr52-internal-context-arrived','rr52-petal-committed',
                 'rr52-consumer-action-executed','upper-cell-closed:'+ROUTE]
        indices=[kinds.index(k) for k in ordered]
        self.assertEqual(indices,sorted(indices))
        self.assertEqual(kinds[-1],'upper-cell-closed:'+ROUTE)

    def test_source_incompatible_with_its_bound_entry_is_refused(self):
        p=self.ready.problem
        forged=replace(p,start=ExecutionState(UpperState(p.context,(-2,0,0,0)),p.start.executed_word))
        with self.assertRaises(ValueError): validate_problem(forged,self.ready.anchor)
        forged=replace(p,entry=replace(p.entry,result=(-2,0,0,0)))
        with self.assertRaises(ValueError): validate_problem(forged,self.ready.anchor)

    def test_free_choice_is_bound_before_future_arrival_and_reproducible_modulo_candidates(self):
        same=run_flower(Configuration(petal_choice=2))
        self.assertEqual(same.commitment.selected_ordinal,0)
        self.assertEqual(same.commitment.word,self.receipt.word)
        self.assertEqual(same.record.actual_endpoint,self.ended.record.actual_endpoint)
        for invalid in (-1,True,'0'):
            with self.assertRaises(ValueError): Configuration(petal_choice=invalid)

    def test_exact_json_roundtrip_preserves_the_whole_actual_occurrence(self):
        payload=json.loads(json.dumps(export_record(self.ended.record)))
        restored=import_record(payload,Configuration())
        self.assertEqual(restored,self.ended.record)
        self.assertEqual(restored.residue.terminal_operation.cell.beta,self.receipt.word)

    def test_loading_a_record_under_a_different_entry_choice_is_rejected(self):
        payload=export_record(self.ended.record)
        with self.assertRaisesRegex(ValueError,'trusted entry configuration'):
            import_record(payload,Configuration(petal_choice=1))

    def test_unknown_serialized_type_cannot_request_an_arbitrary_constructor(self):
        payload=export_record(self.ended.record)
        payload['nodes'][payload['root']['ref']]['type']='untrusted.module.Command'
        with self.assertRaisesRegex(ValueError,'unknown graph node'):
            import_record(payload,Configuration())


if __name__=='__main__': unittest.main()
