import unittest
from dataclasses import replace
from unittest.mock import patch
from itertools import permutations

from local_closure_selection import *


class LocalClosureSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=make_problem()
        cls.cat=catalog(cls.p)

    def test_distance_and_future_solvers_are_forbidden_during_selection(self):
        with patch('intrinsic_connection_progress.distance',side_effect=AssertionError('distance forbidden')), \
             patch('intrinsic_connection_progress.plan_shortest',side_effect=AssertionError('planner forbidden')), \
             patch('intrinsic_connection_progress.isolate',side_effect=AssertionError('root forbidden')), \
             patch('robust_flower_geometry.isolate',side_effect=AssertionError('future solver forbidden')), \
             patch('local_closure_selection.bounded_next_actions',side_effect=AssertionError('tail search forbidden')):
            ran=run_local(self.p)
        self.assertEqual(ran.status,'CLOSED')
        self.assertEqual(ran.actions,(self.p.prepared.pending.head,self.p.source))

    def test_head_pending_cannot_close_at_initial_live_target(self):
        self.assertEqual(self.p.start.live.accumulated[0],-1)
        ran=run_local(self.p)
        self.assertEqual(len(ran.actions),2)
        self.assertGreater(abs(ran.states[1].live.accumulated[0]+1),TOLERANCE)

    def test_local_mismatch_rule_can_pick_head_without_receiving_its_label(self):
        match=choose_one_step(self.p.start,self.cat.actions)
        self.assertEqual(match.actions,(self.cat.actions[self.cat.head],))
        with patch('intrinsic_connection_progress.distance',side_effect=AssertionError('distance forbidden')), \
             patch('intrinsic_connection_progress.plan_shortest',side_effect=AssertionError('planner forbidden')), \
             patch('robust_flower_geometry.isolate',side_effect=AssertionError('root forbidden')):
            ran=run_greedy(self.p)
        self.assertEqual(ran.status,'CLOSED')
        self.assertEqual(ran.actions,(self.cat.actions[self.cat.head],self.p.source))

    def test_local_mismatch_priority_is_not_a_monotone_live_error_law(self):
        ran=run_greedy(self.p)
        errors=[abs(s.live.accumulated[0]+1) for s in ran.states]
        self.assertEqual(errors[0],0)
        self.assertGreater(errors[1],Q(1,2))
        self.assertLess(errors[2],TOLERANCE/2)

    def test_greedy_computation_limit_is_not_an_impossibility_claim(self):
        ran=run_greedy(self.p,max_steps=1)
        self.assertEqual(ran.status,'ITERATION_LIMIT')
        self.assertEqual(len(ran.actions),1)

    def test_match_is_invariant_under_stock_order_and_repeated_identical_handles(self):
        state=step(self.cat.actions[self.cat.head],self.p.start)
        for stock in permutations(self.cat.actions):
            match=match_stock(state,stock+(self.p.source,))
            self.assertEqual(match.status,'UNIQUE_IMMEDIATE_CLOSURE')
            self.assertEqual(match.actions,(self.p.source,))

    def test_interval_certificate_excludes_every_competing_stock_action(self):
        cert=uniform_match_certificate()
        for branch in cert['branches']:
            self.assertEqual(len(branch['competitor_error_lower_bounds']),4)
            self.assertGreater(min(branch['competitor_error_lower_bounds']),TOLERANCE)

    def test_no_immediate_match_does_not_mean_no_longer_legal_continuation(self):
        h=self.cat.head;s=self.cat.actions.index(self.p.source)
        after_two_heads=step(self.cat.actions[h],step(self.cat.actions[h],self.p.start))
        self.assertEqual(match_stock(after_two_heads,self.cat.actions).status,'NO_IMMEDIATE_CLOSURE')
        self.assertTrue(certify_trace(self.p,(h,h,s,s))['exact_word_certified'])

    def test_unique_one_step_match_is_not_unique_unbounded_next_action(self):
        h=self.cat.head;s=self.cat.actions.index(self.p.source)
        self.assertEqual(set(bounded_next_actions(self.p,(h,),1)),{s})
        choices=bounded_next_actions(self.p,(h,),3)
        self.assertIn(h,choices);self.assertIn(s,choices)
        for word in choices.values(): self.assertTrue(certify_trace(self.p,word)['exact_word_certified'])

    def test_distinct_certified_histories_are_not_collapsed_on_equal_live_response(self):
        state,matched,outputs=ambiguous_port(self.p)
        self.assertEqual(matched.status,'MULTIPLE_IMMEDIATE_CLOSURES')
        self.assertEqual(len(set(matched.actions)),2)
        self.assertEqual(len(outputs),2)
        for stock in (self.cat.actions,tuple(reversed(self.cat.actions))):
            self.assertEqual(set(match_stock(state,stock).actions),set(matched.actions))

    def test_actual_endpoint_is_retained_and_full_word_certified(self):
        ran=run_local(self.p)
        self.assertEqual(ran.output.cell.endpoint,ran.states[-1])
        self.assertNotEqual(ran.states[-1].live.accumulated[0],-1)
        self.assertLess(abs(ran.states[-1].live.accumulated[0]+1),TOLERANCE/2)
        self.assertEqual(promote_word(ran.output.cell),ran.output)

    def test_catalog_refuses_target_and_consumer_inheritance_tampering(self):
        with self.assertRaises(ValueError):
            run_local(replace(self.p,entry=replace(self.p.entry,result=(-2,0,0,0))))
        forged=ExecutionState(UpperState(self.p.context,(-2,0,0,0)),self.p.start.executed_word)
        with self.assertRaises(ValueError): run_local(replace(self.p,start=forged))

    def test_offered_stock_cannot_add_an_unpublished_or_omit_an_existing_action(self):
        with self.assertRaises(ValueError): run_local(self.p,self.cat.actions[:-1])

    def test_primitive_action_is_rejected_even_if_its_response_could_fit(self):
        with self.assertRaisesRegex(ValueError,'level-two'):
            match_stock(self.p.start,(self.p.source.cell.beta[0],))

    def test_zero_has_separate_algebraic_obstruction_status(self):
        state=ExecutionState(UpperState(self.p.context,(0,0,0,0)))
        self.assertEqual(match_stock(state,self.cat.actions).status,'ZERO_OBSTRUCTION')

    def test_boundary_margin_is_strict_and_not_replaced_by_epsilon(self):
        state=step(self.cat.actions[self.cat.head],self.p.start)
        response=step(self.p.source,state).live.accumulated[0]
        self.assertNotIn(self.p.source,match_stock(state,self.cat.actions,response+TOLERANCE/2).actions)
        self.assertIn(self.p.source,match_stock(state,self.cat.actions,response+TOLERANCE/4).actions)

    def test_closed_output_is_not_fed_to_a_new_context_and_entry_is_immutable(self):
        before=(self.p.prepared.events,self.p.prepared.stock,self.p.start)
        ran=run_local(self.p)
        self.assertEqual(ran.output.level,3)
        self.assertEqual(before,(self.p.prepared.events,self.p.prepared.stock,self.p.start))
        self.assertEqual(len(ran.states[-1].executed_word),len(self.p.start.executed_word)+2)


if __name__=='__main__': unittest.main()
