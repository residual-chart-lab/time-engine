import unittest
from unittest.mock import patch
from single_flower_model import *
from recursive_upper_decoder import certify_word


class SingleFlowerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial,cls.y,cls.left,cls.right=solution_pair()

    def test_entry_precedes_context_and_binds_rule(self):
        waiting=begin_flower(self.initial,solution_rule=SolutionRule(1))
        self.assertIsNone(waiting.engine.pending.arrived_context)
        self.assertEqual(waiting.entry.solution_rule,SolutionRule(1))
        self.assertEqual(waiting.engine.upper,self.initial.upper)
        self.assertEqual(finish(waiting),waiting)

    def test_completion_is_absorbing_and_does_not_emit_next(self):
        flower=self.left
        for _ in range(5):
            self.assertIs(advance(flower),flower)
        self.assertIsNone(flower.engine.pending)
        self.assertEqual(len(flower.engine.rounds),1)
        self.assertEqual(flower.exit.events[-1].kind,'upper-cell-closed:produced')
        with self.assertRaises(ValueError):
            arrive(flower,self.y)

    def test_helper_closure_is_not_outer_completion_and_not_yet_available(self):
        planned=advance(arrive(begin_flower(self.initial),self.y))
        issued=advance(planned)
        self.assertEqual(issued.status,'LOWER_CLOSED')
        self.assertIsNone(issued.exit)
        self.assertEqual(issued.engine.upper,ExecutionState(
            UpperState(self.y,self.initial.upper.live.accumulated),self.initial.upper.executed_word))
        self.assertEqual(issued.engine.outputs,())
        with self.assertRaises(ValueError):
            available(issued.engine,issued.engine.pending.issue.operation)
        self.assertEqual(advance(issued).status,'AVAILABLE')

    def test_first_boundary_and_unexecuted_open_prefix(self):
        opened=arrive(begin_flower(self.initial),self.y)
        self.assertEqual(opened.engine.pending.trial_response,(6,0,0,0))
        self.assertEqual(opened.engine.pending.decoded.tail,(self.initial.designated_head,))
        self.assertEqual(opened.engine.upper.executed_word,self.initial.upper.executed_word)
        c=self.left.exit.consumer_cell
        self.assertEqual(len(c.beta),2)
        with self.assertRaises(ValueError):
            certify_word(c.start,c.beta+c.beta,c.target)

    def test_full_exact_exit_replays_both_actual_histories(self):
        for flower in (self.left,self.right):
            self.assertTrue(replay_trace(self.initial,flower.engine))
            receipt=flower.exit
            self.assertEqual(receipt.consumer_after.executed_word[:5],self.initial.upper.executed_word)
            self.assertEqual(receipt.lower_after.executed_word[:5],self.initial.lower.executed_word)
            self.assertEqual(promote_word(receipt.consumer_cell),receipt.higher_operation)
            self.assertEqual(receipt.stock_after[-1],receipt.produced_operation)

    def test_explicit_solution_choice_same_response_different_retention(self):
        left,right=self.left,self.right
        lp=left.engine.rounds[-1].pending.plan
        rp=right.engine.rounds[-1].pending.plan
        self.assertEqual(lp.leaf.kernel(self.y),rp.leaf.kernel(self.y))
        self.assertEqual(left.exit.consumer_after.live,right.exit.consumer_after.live)
        self.assertEqual(left.exit.lower_after.live,right.exit.lower_after.live)
        self.assertNotEqual(left.exit.consumer_cell,right.exit.consumer_cell)
        self.assertNotEqual(left.exit.stock_after,right.exit.stock_after)
        self.assertNotEqual(boundary_readout(left.exit.produced_operation),boundary_readout(right.exit.produced_operation))

    def test_difference_changes_exported_action_at_common_context(self):
        probe=context([[Q(3,2),0,0],[0,Q(3,4),0],[0,0,Q(-5,4)]])
        self.assertNotEqual(self.left.exit.higher_operation.kernel(probe),self.right.exit.higher_operation.kernel(probe))

    def test_second_problem_cannot_revoke_completed_unit(self):
        receipt=self.left.exit
        success=probe_higher_connection(receipt,self.y)
        failure=probe_higher_connection(receipt,self.initial.upper.live.context)
        self.assertEqual(success.status,'CONNECTED')
        self.assertEqual(failure.status,'NO_TERMINAL_PREFIX')
        self.assertIs(failure.source_exit,receipt)
        self.assertEqual(self.left.status,'COMPLETE')
        self.assertEqual(len(self.left.engine.rounds),1)

    def test_separate_following_unit_preserves_completed_prefix(self):
        _,_,zero=fixtures_sequence()
        second=one_flower(self.left.engine,zero)
        self.assertEqual(second.status,'HEAD_ZERO')
        self.assertIsNone(second.exit)
        self.assertEqual(second.engine.outputs,self.left.engine.outputs)
        self.assertEqual(second.engine.rounds,self.left.engine.rounds)
        self.assertEqual(self.left.status,'COMPLETE')

    def test_zero_and_chart_outside_are_incomplete_not_computational_errors(self):
        _,_,zero=fixtures_sequence()
        blocked=one_flower(self.initial,zero)
        outside=one_flower(self.initial,context([[0,0,0],[0,0,0],[0,0,1]]))
        self.assertEqual(blocked.status,'HEAD_ZERO')
        self.assertEqual(outside.status,'OUTSIDE_CERTIFIED_CHART')
        self.assertIsNone(outside.exit)
        self.assertEqual(outside.engine.upper.executed_word,self.initial.upper.executed_word)
        self.assertEqual(finish(outside),outside)

    def test_actual_computation_errors_are_not_hidden_as_waiting(self):
        opened=arrive(begin_flower(self.initial),self.y)
        with patch('single_flower_model.resolve_open',side_effect=ArithmeticError('diagnostic computation failure')):
            with self.assertRaises(ArithmeticError):
                finish(opened)

    def test_mixed_scale_and_unpublished_heads_are_rejected(self):
        with self.assertRaises(ValueError):
            begin_flower(self.initial,head=self.initial.designated_head.leaves()[0])
        with self.assertRaises(ValueError):
            begin_flower(self.initial,head=self.left.exit.higher_operation)
        with self.assertRaises(ValueError):
            begin_flower(self.initial,head=self.left.exit.produced_operation)

    def test_direct_closure_and_existing_reuse_need_no_producer(self):
        _,ys,_=fixtures_sequence()
        for y,route in ((ys[4],'head'),(self.initial.upper.live.context,'reused')):
            flower=one_flower(self.initial,y)
            self.assertEqual(flower.status,'COMPLETE')
            self.assertEqual(flower.exit.route,route)
            self.assertIsNone(flower.exit.produced_operation)
            self.assertEqual(flower.engine.lower.executed_word,self.initial.lower.executed_word)

    def test_pausing_at_each_internal_phase_preserves_exact_exit(self):
        flower=arrive(begin_flower(self.initial),self.y)
        phases=[]
        while flower.status!='COMPLETE':
            phases.append(flower.status)
            self.assertEqual(finish(flower),self.left)
            flower=advance(flower)
        self.assertEqual(phases,['OPEN','PLANNED','LOWER_CLOSED','AVAILABLE'])


if __name__=='__main__':
    unittest.main()
