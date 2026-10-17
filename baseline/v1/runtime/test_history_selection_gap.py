import unittest
from unittest.mock import patch

from history_selection_gap import *


class HistorySelectionGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.problem=make_problem()
        cls.cat=catalog(cls.problem)

    def test_cycle_is_proved_by_strict_interval_gaps_at_both_exact_roots(self):
        for branch in BRACKETS:
            cert=exact_greedy_cycle_certificate(branch)
            self.assertEqual(cert['cycle_indices'],(4,3))
            for row in cert['comparisons']:
                self.assertLess(row['best_error_upper'],row['other_errors_lower'])

    def test_bracket_contains_a_sign_change_and_is_not_a_numeric_point_estimate(self):
        for branch in BRACKETS:
            lo,hi=root_bracket(branch)
            self.assertLess(geometry(lo)['mismatch']*geometry(hi)['mismatch'],0)
            self.assertLess(hi-lo,Q(1,10**18))

    def test_greedy_can_ignore_an_exact_two_action_closure(self):
        control=finite_greedy_control(self.problem)
        self.assertFalse(control['closed_within_cap'])
        self.assertEqual(control['feasible_exact_word']['closure_error'],0)
        self.assertNotEqual(control['indices'][0],self.cat.head)

    def test_diagnostic_port_does_not_rewrite_the_original_entry_or_tape(self):
        before=(self.problem.start,self.problem.prepared,self.problem.entry)
        state=diagnostic_port(self.problem)
        self.assertNotEqual(state,self.problem.start)
        self.assertEqual(state.executed_word,())
        self.assertEqual(before,(self.problem.start,self.problem.prepared,self.problem.entry))

    def test_retained_search_does_not_call_local_ranker_distance_or_future_solver(self):
        state=diagnostic_port(self.problem)
        with patch('history_selection_gap.choose_one_step',side_effect=AssertionError('local ranking forbidden')), \
             patch('intrinsic_connection_progress.distance',side_effect=AssertionError('distance forbidden')), \
             patch('robust_flower_geometry.isolate',side_effect=AssertionError('future root forbidden')):
            found=retained_candidates(state,self.cat,2)
        self.assertIn((self.cat.head,self.cat.head),[p['indices'] for p in found['candidates']])
        self.assertFalse(found['winner_selected'])

    def test_no_witness_within_small_cap_is_not_called_unreachable(self):
        state=diagnostic_port(self.problem)
        found=retained_candidates(state,self.cat,1)
        self.assertEqual(found['status'],'NO_WITNESS_WITHIN_CAP')
        self.assertFalse(found['global_exhaustiveness_proved'])
        self.assertTrue(retained_candidates(state,self.cat,2)['candidates'])

    def test_longer_compatible_words_are_not_discarded_at_the_first_short_solution(self):
        found=retained_candidates(self.problem.start,self.cat,4,head_pending=True)
        h=self.cat.head;s=self.cat.actions.index(self.problem.source)
        words={p['indices'] for p in found['candidates']}
        self.assertIn((h,s),words)
        self.assertIn((h,h,s,s),words)
        self.assertNotIn((h,s,h,s),words)  # Its earlier boundary already ended the flower.

    def test_possible_continuations_do_not_become_published_actual_occurrences(self):
        stock=self.problem.prepared.stock;events=self.problem.prepared.events
        found=retained_candidates(diagnostic_port(self.problem),self.cat,2)
        self.assertTrue(all(not p['published_actual_occurrence'] for p in found['candidates']))
        self.assertEqual(found['new_stock_items_published'],0)
        self.assertEqual(stock,self.problem.prepared.stock)
        self.assertEqual(events,self.problem.prepared.events)

    def test_full_response_profiles_preserve_the_ordered_history_difference(self):
        info=response_profiles(self.problem)
        short,long=info['profiles']
        self.assertNotEqual(short['full_ordered_record'],long['full_ordered_record'])
        self.assertEqual(short['kernel_by_port']['present_correction'],long['kernel_by_port']['present_correction'])
        self.assertNotEqual(short['kernel_by_port']['head_origin'],long['kernel_by_port']['head_origin'])
        self.assertFalse(info['neighbor_coupling_inferred'])

    def test_missing_neighbor_data_is_undefined_instead_of_a_vacuous_pass(self):
        for args in ({},{'peers':()},{'coupling':'declared-isolated-product'},
                     {'coupling':'declared-isolated-product','peers':()}):
            value=assess_isolation(**args)
            self.assertEqual(value.status,'UNDEFINED_EXTERNAL_COUPLING')
            self.assertIsNone(value.external_state_unchanged)

    def test_isolated_completion_is_explicit_and_does_not_select_one_history(self):
        h=self.cat.actions[self.cat.head];s=self.problem.source
        peer=PeerPort(h.cell.start.live.context)
        for word in ((h,s),(h,h,s,s)):
            value=assess_isolation(word,'declared-isolated-product',(peer,))
            self.assertTrue(value.external_state_unchanged)
            self.assertTrue(value.sealed)
            shared=assess_isolation(word,'declared-shared-response-product',(peer,))
            self.assertFalse(shared.sealed)
            self.assertGreater(shared.changes[0]['external_delta'],0)

    def test_an_unknown_coupling_is_not_silently_treated_as_isolation(self):
        value=assess_isolation(coupling='unknown',peers=(PeerPort(self.cat.context),))
        self.assertEqual(value.status,'UNSUPPORTED_COUPLING')
        self.assertIsNone(value.external_state_unchanged)

    def test_exact_endpoint_is_retained_for_the_diagnostic_closing_witness(self):
        proof=proof_for_word(diagnostic_port(self.problem),self.cat,(self.cat.head,self.cat.head))
        self.assertEqual(proof['endpoint'],(-1,0,0,0))
        self.assertEqual(proof['output_level'],3)

    def test_empty_words_and_wrong_contexts_are_not_accepted(self):
        with self.assertRaises(ValueError): proof_for_word(self.problem.start,self.cat,())
        wrong=ExecutionState(UpperState(((Q(1),0,0),(0,0,0),(0,0,0)),(-2,0,0,0)))
        with self.assertRaises(ValueError): retained_candidates(wrong,self.cat,2)


if __name__=='__main__': unittest.main()
