import unittest
from dataclasses import replace
from itertools import product
from unittest.mock import patch

from intrinsic_connection_progress import *


class IntrinsicConnectionProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first=make_problem()
        cls.second=make_problem(branch='second')

    def test_open_interval_boundaries_and_touching_gap_are_preserved(self):
        intervals=normalize((OpenInterval(0,1),OpenInterval(1,2)))
        self.assertEqual(len(intervals),2)
        self.assertFalse(contains(intervals,1))
        negative=preimage((OpenInterval(2,4),),-2)
        self.assertEqual(negative,(OpenInterval(-2,-1),))
        self.assertFalse(contains(negative,-2))

    def test_boundary_guard_band_is_not_silently_traversed(self):
        cat=catalog(self.first)
        for sign in (-1,1):
            z=cat.result+sign*cat.margin
            self.assertEqual(distance(cat,z).status,'OUTSIDE_BOUNDARY_SEPARATION')
            self.assertFalse(contains(requirements(cat,3),z))
        self.assertEqual(distance(cat,cat.result).value,0)

    def test_interval_search_agrees_with_independent_word_enumeration(self):
        cat=catalog(self.first)
        queries=(Q(-1),Q(-1,10),Q(1,7),Q(0),Q(-1)/max(cat.multipliers)**2)
        for pending in (False,True):
            for z in queries:
                expected=None
                for length in range(3):
                    if pending and length==0: continue
                    choices=product(range(len(cat.actions)),repeat=length)
                    for indices in choices:
                        if pending and indices[0]!=cat.head: continue
                        value=z;valid=True
                        if not pending and abs(value-cat.result)<cat.margin:
                            expected=0;break
                        if not pending and abs(value-cat.result)<=cat.epsilon: continue
                        for k,i in enumerate(indices):
                            value*=cat.multipliers[i]
                            if k<len(indices)-1 and abs(value-cat.result)<=cat.epsilon:
                                valid=False;break
                        if valid and abs(value-cat.result)<cat.margin:
                            expected=length;break
                    if expected is not None: break
                self.assertEqual(distance(cat,z,pending,2).value,expected,(pending,z))

    def test_head_pending_and_completed_states_with_same_live_value_differ(self):
        cat=catalog(self.first)
        self.assertEqual(self.first.start.live.accumulated[0],-1)
        self.assertEqual(distance(cat,-1,True).value,2)
        self.assertEqual(distance(cat,-1,False).value,0)

    def test_planner_does_not_consume_a_completed_word_endpoint_or_root_preview(self):
        cat=catalog(self.first)
        with patch('intrinsic_connection_progress.isolate',side_effect=AssertionError('future preview forbidden')):
            with patch('robust_flower_geometry.isolate',side_effect=AssertionError('future solver forbidden')):
                indices,ds,_=plan_shortest(cat,self.first.start.live.accumulated[0])
        self.assertEqual(ds,(2,1,0))
        self.assertEqual(indices,(cat.head,cat.actions.index(self.first.source)))

    def test_each_selected_action_is_published_same_level_and_distance_decreasing(self):
        for p in (self.first,self.second):
            cat=catalog(p);indices,ds,_=plan_shortest(cat,p.start.live.accumulated[0])
            self.assertTrue(all(a.level==2 for a in cat.actions))
            self.assertEqual(ds,(2,1,0))
            trace=certify_trace(p,indices)
            self.assertTrue(trace['exact_word_certified'])
            self.assertLess(trace['closure_error'],TOLERANCE/2)
            self.assertEqual(trace['new_contexts_after_closure'],0)

    def test_certified_detour_increases_distance_despite_shorter_unconsumed_word(self):
        for p in (self.first,self.second):
            cat=catalog(p);source=cat.actions.index(p.source)
            trace=certify_trace(p,(cat.head,cat.head,source,source))
            self.assertEqual(trace['connection_distances'],[2,1,2,1,0])
            self.assertEqual(trace['raw_remaining_word_lengths'],[4,3,2,1,0])

    def test_requirements_nest_in_one_fixed_augmented_state_space(self):
        for p in (self.first,self.second):
            cat=catalog(p)
            for pending in (False,True):
                for n in range(3): self.assertTrue(subset(requirements(cat,n,pending),requirements(cat,n+1,pending)))
            volumes=[augmented_measure(cat,n) for n in range(4)]
            self.assertTrue(all(a<b for a,b in zip(volumes,volumes[1:])))

    def test_residue_dominance_proves_strict_layers_beyond_displayed_horizon(self):
        cert=uniform_layer_certificate()
        for b in cert['branches']:
            self.assertGreater(b['source_range'][0],b['other_actions_abs_upper'])
        cat=catalog(self.first);m=max(cat.multipliers)
        for n in range(5):
            z=cat.result/m**(n+1)
            self.assertFalse(contains(requirements(cat,n),z))
            self.assertTrue(contains(requirements(cat,n+1),z))

    def test_zero_obstruction_and_limited_search_are_not_conflated(self):
        cat=catalog(self.first)
        self.assertEqual(distance(cat,0).status,'PROVED_UNREACHABLE_ZERO')
        limited=distance(cat,Q(1,10**9),horizon=0)
        self.assertEqual(limited.status,'NOT_FOUND_WITHIN_LIMIT')
        self.assertEqual(limited.lower_bound,1)

    def test_departure_head_zero_recovers_empty_fixed_boundary_requirement(self):
        for branch in BRACKETS:
            g=geometry(Q(0));factor='first' if branch=='first' else 'second'
            t0=-g[factor+'_head_action']/g[factor+'_head_slope']
            p=problem_at_representative(Parameters(),branch,t0);cat=catalog(p)
            self.assertEqual(requirements(cat,3,True),())
            self.assertEqual(distance(cat,p.start.live.accumulated[0],True).status,'PROVED_UNREACHABLE_ZERO')

    def test_live_displacement_and_full_tail_defect_fail_as_progress_variables(self):
        p=self.first;cat=catalog(p);indices,_,_=plan_shortest(cat,p.start.live.accumulated[0])
        trace=certify_trace(p,indices)
        self.assertEqual(trace['live_result_distances'][0],0)
        self.assertGreater(trace['live_result_distances'][1],Q(1,2))
        self.assertNotEqual(trace['propagated_terminal_defect'],0)
        self.assertEqual(trace['connection_distances'],[2,1,0])

    def test_visible_proxy_loses_an_actual_one_step_connection(self):
        for p in (self.first,self.second):
            result=visible_only_control(p)
            self.assertEqual(result['true_distance'],1)
            self.assertEqual(result['proxy_status'],'NOT_FOUND_WITHIN_LIMIT')

    def test_modified_consumer_inheritance_is_rejected_against_entry(self):
        p=self.first
        forged=ExecutionState(UpperState(p.context,(-2,0,0,0)),p.start.executed_word)
        with self.assertRaisesRegex(ValueError,'inheritance'):
            catalog(replace(p,start=forged))

    def test_modified_request_is_rejected_against_the_bound_request(self):
        p=self.first
        with self.assertRaisesRegex(ValueError,'fixed request'):
            catalog(replace(p,entry=replace(p.entry,result=(-2,0,0,0))))

    def test_mixed_level_action_is_rejected_even_if_it_has_the_desired_response(self):
        p=self.first;primitive=p.source.cell.beta[0]
        forged=replace(p,prepared=replace(p.prepared,stock=p.prepared.stock+(primitive,)))
        with self.assertRaisesRegex(ValueError,'same level'): catalog(forged)


if __name__=='__main__': unittest.main()
