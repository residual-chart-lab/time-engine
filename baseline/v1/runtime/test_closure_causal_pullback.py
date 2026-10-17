import unittest
from dataclasses import replace
from unittest.mock import patch
from closure_causal_pullback import *
from endogenous_flower_boundary import isolate_boundary
from recursive_upper_decoder import inverse


class ClosureCausalPullbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first,cls.second,cls.p1,cls.p2=fixtures()

    def test_requirement_and_root_preview_are_not_actual_occurrences(self):
        with self.assertRaises(ValueError):
            record_occurrence(self.first.requirement,'unexecuted')
        with self.assertRaises(ValueError):
            record_occurrence(isolate_boundary(),'preview')
        with self.assertRaises(TypeError):
            extract_pullback(self.first.requirement)

    def test_incomplete_status_cannot_create_a_causal_receipt(self):
        completed=endogenous_flower()
        with self.assertRaises(ValueError):
            record_occurrence(replace(completed,status='WAIT_FUTURE'),'unclosed')

    def test_actual_outcome_and_fixed_target_are_rechecked(self):
        completed=endogenous_flower()
        with self.assertRaises(ValueError):
            record_occurrence(replace(completed,closure_error=Q(0)),'false-exact-closure')
        self.assertNotEqual(self.first.consumer_after.live.accumulated,self.first.requirement.result)

    def test_fixed_requirement_cannot_be_replaced_by_the_actual_endpoint(self):
        for branch in ('first','second'):
            with self.subTest(branch=branch):
                completed=endogenous_flower(branch)
                actual=completed.decoded.state.live.accumulated
                first=step(completed.decoded.outputs[0].cell.beta[0],completed.consumer_start)
                forged=replace(completed,fixed_result=actual,closure_error=Q(0),
                    prefix_error=sum(abs(a-b) for a,b in zip(first.live.accumulated,actual)))
                self.assertNotEqual(actual,completed.entry.result)
                with self.assertRaisesRegex(ValueError,'entry and bound request'):
                    record_occurrence(forged,'relabelled-exact-closure')
                # Rewriting the intermediate request as well must still fail
                # against the original entry; each anchor matters.
                pending=replace(completed.prepared_engine.pending,result=actual)
                prepared=replace(completed.prepared_engine,pending=pending,result=actual)
                with self.assertRaisesRegex(ValueError,'entry and bound request'):
                    record_occurrence(replace(forged,prepared_engine=prepared),'relabelled-request')
                changed_entry=replace(completed.entry,result=actual)
                with self.assertRaisesRegex(ValueError,'entry and bound request'):
                    record_occurrence(replace(forged,entry=changed_entry),'unchanged-bound-request')

    def test_consumer_inherited_value_cannot_be_changed_to_create_exact_closure(self):
        for branch in ('first','second'):
            with self.subTest(branch=branch):
                completed=endogenous_flower(branch)
                word=completed.decoded.outputs[0].cell.beta
                inherited=tuple(qmul(inverse(kernel(word,completed.emitted_context)),completed.fixed_result))
                start=ExecutionState(UpperState(completed.emitted_context,inherited),
                                     completed.consumer_start.executed_word)
                first=step(word[0],start)
                decoded=decode(start,word,(completed.fixed_result,))
                self.assertEqual(decoded.state.live.accumulated,completed.fixed_result)
                self.assertEqual(len(decoded.outputs),1)
                self.assertEqual(promote_word(decoded.outputs[0].cell),decoded.outputs[0])
                self.assertNotEqual(inherited,completed.entry.upper.live.accumulated)
                forged=replace(completed,consumer_start=start,decoded=decoded,closure_error=Q(0),
                    prefix_error=sum(abs(a-b) for a,b in zip(first.live.accumulated,completed.fixed_result)))
                with self.assertRaisesRegex(ValueError,'consumer inheritance'):
                    record_occurrence(forged,'changed-inherited-value')
                # A coherent rewrite of later checkpoints still cannot
                # replace the original entry-bound consumer state.
                staged=ExecutionState(UpperState(completed.prepared_engine.upper.live.context,inherited),
                                      completed.prepared_engine.upper.executed_word)
                pending=replace(completed.prepared_engine.pending,consumer_start=staged)
                prepared=replace(completed.prepared_engine,upper=staged,pending=pending)
                with self.assertRaisesRegex(ValueError,'consumer inheritance'):
                    record_occurrence(replace(forged,prepared_engine=prepared),'changed-later-checkpoints')
                changed_before=ExecutionState(UpperState(pending.upper_before.live.context,inherited),
                                              pending.upper_before.executed_word)
                pending=replace(pending,upper_before=changed_before)
                with self.assertRaisesRegex(ValueError,'consumer inheritance'):
                    record_occurrence(replace(forged,prepared_engine=replace(prepared,pending=pending)),
                                      'changed-bound-inheritance')

    def test_publication_and_future_arrival_must_precede_closure(self):
        completed=endogenous_flower()
        events=list(completed.events)
        a=events.index('same-level-operation-published')
        b=events.index('internal-future-context-arrived')
        events[a],events[b]=events[b],events[a]
        with self.assertRaises(ValueError):
            record_occurrence(replace(completed,events=tuple(events)),'wrong-order')

    def test_current_null_direction_becomes_terminal_observable(self):
        for p in (self.p1,self.p2):
            self.assertEqual(p.current_rank,5)
            self.assertEqual(p.joint_rank,6)
            self.assertEqual(p.current_gain,(0,0,0,0))
            self.assertNotEqual(p.terminal_gain,(0,0,0,0))

    def test_terminal_readout_recovers_source_not_available_from_current_response_alone(self):
        for p in (self.p1,self.p2):
            canonical=tuple(solve([list(row) for row in p.current_matrix],list(p.current_rhs)))
            self.assertNotEqual(canonical,p.reconstructed_weights)
            self.assertEqual(p.reconstructed_weights,source_leaf(p.occurrence).weights)

    def test_extraction_does_not_use_rr46_quartic_or_root_solver(self):
        with patch('endogenous_flower_boundary.boundary_mismatch',side_effect=AssertionError('preview forbidden')):
            with patch('endogenous_flower_boundary.isolate_boundary',side_effect=AssertionError('root formula forbidden')):
                self.assertEqual(extract_pullback(self.first),self.p1)
                self.assertEqual(causal_path_gains(self.first)['direct_residue'],self.p1.terminal_gain)

    def test_zeroing_retained_coordinate_keeps_current_response_but_breaks_same_future(self):
        for o in (self.first,self.second):
            alternate=counterfactual_replay(o,-source_leaf(o).weights[2])
            self.assertEqual(alternate.source.kernel(o.lower_before.live.context),(-9,0,0,0))
            self.assertFalse(alternate.requirement_met)
            self.assertFalse(alternate.generation_rule_preserved)
            self.assertEqual(alternate.boundary,o.consumer_before.live.context)

    def test_swapping_completed_branches_fails_when_achieved_boundary_is_held(self):
        for original,other in ((self.first,self.second),(self.second,self.first)):
            shift=source_leaf(other).weights[2]-source_leaf(original).weights[2]
            alternate=counterfactual_replay(original,shift)
            self.assertEqual(alternate.source,other.source)
            self.assertFalse(alternate.requirement_met)

    def test_regenerating_future_closes_other_branch_as_a_distinct_event(self):
        shift=source_leaf(self.second).weights[2]-source_leaf(self.first).weights[2]
        alternate=counterfactual_replay(self.first,shift,'regenerated-boundary')
        self.assertTrue(alternate.requirement_met)
        self.assertTrue(alternate.generation_rule_preserved)
        self.assertEqual(alternate.boundary,self.second.consumer_before.live.context)
        self.assertNotEqual(alternate.boundary,self.first.consumer_before.live.context)

    def test_actual_record_equality_is_stricter_than_nominal_tolerance(self):
        p=self.p1
        self.assertTrue(preserves_actual_record(p,0))
        self.assertFalse(preserves_actual_record(p,Q(1,10**15)))
        self.assertTrue(meets_fixed_requirement(p,Q(1,10**15)))

    def test_pulled_back_interval_matches_exact_counterfactual_endpoint(self):
        for p in (self.p1,self.p2):
            lo,hi=p.allowed_requirement_shift
            for h in (lo,hi):
                self.assertEqual(counterfactual_replay(p.occurrence,h).error,p.occurrence.requirement.tolerance)
            self.assertFalse(counterfactual_replay(p.occurrence,hi+hi-lo).requirement_met)

    def test_causal_paths_add_as_exact_polynomial_derivatives(self):
        for p in (self.p1,self.p2):
            gains=causal_path_gains(p.occurrence)
            self.assertEqual(gains['direct_residue'],p.terminal_gain)
            self.assertEqual(gains['total'],tuple(a+b for a,b in zip(gains['direct_residue'],gains['through_generated_context'])))

    def test_blind_future_readout_does_not_turn_memory_into_an_influence(self):
        blind=blind_readout_control(self.first)
        self.assertTrue(blind['regular'])
        self.assertEqual(blind['null_response'],(0,0,0,0))
        self.assertEqual(len(set(blind['responses'])),1)
        self.assertEqual(blind['responses'][0],(-1,0,0,0))
        self.assertEqual(blind['joint_rank'],5)
        self.assertTrue(blind['diagnostic_closure_certified'])
        self.assertFalse(blind['actual_rr46_occurrence'])
        self.assertFalse(blind['generation_rule_preserved'])

    def test_counterfactual_replays_preserve_original_actual_sources_and_certificates(self):
        snapshot=(self.first,self.second,self.first.source,self.second.terminal_operation)
        for mode in ('fixed-boundary','regenerated-boundary'):
            counterfactual_replay(self.first,Q(1,100),mode)
        self.assertEqual(snapshot,(self.first,self.second,self.first.source,self.second.terminal_operation))
        with self.assertRaises(ValueError):
            counterfactual_replay(self.first,0,'unrecorded-port-change')

    def test_sole_blind_generated_boundary_cannot_meet_the_fixed_result(self):
        for o in (self.first,self.second):
            proof=necessary_visibility_lemma(o)
            self.assertEqual(proof['generated_leaf_gain_slope'],(12,0,0,0))
            self.assertEqual(proof['unique_blind_source'],(Q(1,3),Q(-37,6),Q(41,6),0,0,0))
            self.assertEqual(proof['blind_response'],(Q(-20240,27),0,0,0))
            self.assertGreater(proof['blind_fixed_result_error'],Q(1,1000))


if __name__=='__main__':
    unittest.main()
