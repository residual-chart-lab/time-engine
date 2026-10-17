import unittest
from dataclasses import replace

from robust_flower_geometry import *


class RobustFlowerGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cert=uniform_certificate()
        cls.first=execute_model()
        cls.second=execute_model(branch='second')

    def test_uniform_box_covers_both_branches_without_grid_extrapolation(self):
        self.assertEqual(self.cert['independent_parameters'],4)
        self.assertEqual(self.cert['parameter_box_radius'],Q(1,10**8))
        for branch in self.cert['branches']:
            self.assertGreater(branch['derivative_abs_lower'],0)
            self.assertTrue(Interval(*branch['root_fixed_boundary_gain']).excludes_zero())
            self.assertGreater(branch['first_prefix_error_lower'],TOLERANCE)

    def test_interval_certificate_encloses_interior_values_and_derivatives(self):
        radius=self.cert['parameter_box_radius']
        p=Parameters(radius/2,-radius/3,radius/5,-radius/7)
        for cert in self.cert['branches']:
            lo,hi=cert['bracket'];t=(lo+hi)/2;g=geometry(t,p)
            self.assertTrue(Interval(*cert['derivative']).contains(g['derivative']))
            self.assertTrue(Interval(*cert['source_null']).contains(g['source_null']))
            # A degree-four polynomial's derivative is independently recovered
            # from exact interpolation at five distinct points.
            points=[t+Q(k,10**6) for k in (-2,-1,0,1,2)]
            coefficients=solve([[x**j for j in range(5)] for x in points],
                               [geometry(x,p)['mismatch'] for x in points])
            independent=sum(j*coefficients[j]*t**(j-1) for j in range(1,5))
            self.assertEqual(independent,g['derivative'])
            second=sum(j*(j-1)*coefficients[j]*t**(j-2) for j in range(2,5))
            self.assertEqual(second,g['second_derivative'])

    def test_base_instances_preserve_the_original_exact_occurrences(self):
        for new in (self.first,self.second):
            old=record_occurrence(endogenous_flower(new.branch),'old')
            self.assertEqual(new.source,old.source)
            self.assertEqual(new.decoded.state,old.consumer_after)
            self.assertEqual(new.emitted,old.consumer_before.live.context)

    def test_simultaneous_interior_changes_keep_actual_certificates_and_inheritance(self):
        r=self.cert['parameter_box_radius'];p=Parameters(r/2,r/3,-r/4,r/5)
        changed=execute_model(p)
        self.assertNotEqual(changed.source,self.first.source)
        self.assertNotEqual(changed.entry.designated_head,self.first.entry.designated_head)
        self.assertNotEqual(changed.emitted,self.first.emitted)
        self.assertEqual(changed.entry.upper,changed.entry.designated_head.cell.endpoint)
        self.assertEqual(changed.entry.events[0].upper,changed.entry.upper)
        self.assertEqual(changed.entry.events[0].lower,changed.entry.lower)
        self.assertEqual(changed.entry.events[0].stock,changed.entry.stock)
        self.assertEqual(changed.consumer_start.live.accumulated,changed.entry.upper.live.accumulated)
        self.assertEqual(changed.consumer_start.executed_word,changed.entry.upper.executed_word)
        self.assertEqual(changed.prepared.pending.result,(-1,0,0,0))
        self.assertLess(changed.closure_error,TOLERANCE/2)
        self.assertEqual(promote_word(changed.decoded.outputs[0].cell),changed.decoded.outputs[0])

    def test_null_line_and_actual_terminal_source_reconstruction_remain_exact(self):
        for o in (self.first,self.second):
            g=geometry(o.representative,o.parameters)
            current=diagonal(g['current'])
            delta=(*g['delta'],0,0,0)
            self.assertTrue(all(sum(a*b for a,b in zip(row,delta))==0
                                for row in action_matrix(current,o.entry.library)))
            self.assertEqual(o.current_rank,5)
            self.assertEqual(o.joint_rank,6)
            self.assertEqual(o.reconstructed,o.source.cell.beta[0].weights)

    def test_fixed_boundary_gain_is_not_the_total_branch_derivative(self):
        for o in (self.first,self.second):
            g=geometry(o.representative,o.parameters)
            self.assertNotEqual(o.fixed_gain[0],g['derivative'])
            eta=Q(1,10**9)
            delta=(*g['delta'],0,0,0)
            leaf=o.source.cell.beta[0]
            varied=AffineLetter(tuple(w+eta*d for w,d in zip(leaf.weights,delta)),leaf.library)
            before=step(o.entry.designated_head,o.consumer_start).live.accumulated
            response=tuple(qmul(varied.kernel(o.emitted),before))
            self.assertEqual(response[0]-o.decoded.state.live.accumulated[0],eta*o.fixed_gain[0])

    def test_terminal_tube_scaling_is_exact_without_changing_execution_tolerance(self):
        for o in (self.first,self.second):
            width=terminal_tube_width(o,Q(1,10**6))
            self.assertEqual(terminal_tube_width(o,Q(1,10**9)),width/1000)
            self.assertEqual(terminal_tube_width(o,0),0)
            self.assertEqual(o.entry.result,(-1,0,0,0))
        with self.assertRaises(ValueError): terminal_tube_width(self.first,-1)

    def test_exact_chronological_requirement_can_weaken_before_the_terminal_result(self):
        for o in (self.first,self.second):
            cuts=ordered_cut_requirements(o)
            self.assertLess(cuts[1]['exact_half_width'],cuts[0]['exact_half_width'])
            self.assertLess(cuts[1]['exact_half_width'],cuts[2]['exact_half_width'])
            self.assertEqual(cuts[2]['exact_half_width'],TOLERANCE)

    def test_remaining_budget_bound_is_nested_and_necessary_not_sufficient(self):
        for o in (self.first,self.second):
            cuts=ordered_cut_requirements(o)
            for a,b in zip(cuts,cuts[1:]):
                self.assertGreaterEqual(a['necessary_terminal_radius'],b['necessary_terminal_radius'])
            self.assertEqual(cuts[-1]['remaining_actual_path_budget'],0)
            # The initial necessary ball is much wider than the true preimage.
            self.assertGreater(cuts[0]['necessary_terminal_radius'],cuts[0]['exact_half_width'])

    def test_transverse_readout_has_a_verified_nonreal_obstruction(self):
        proof=transverse_readout_obstruction()
        for o in (self.first,self.second):
            e=proof['epsilon'];y=[list(row) for row in o.emitted];y[0][1]=y[1][0]=e;y=context(y)
            actual=tuple(qmul(kernel(o.decoded.outputs[0].cell.beta,y),o.entry.upper.live.accumulated))
            g=geometry(o.representative)
            predicted=2*g['z']*e*(g['weights'][0]-g['weights'][1])*(g['head']+4*e*e-2*g['source'])
            self.assertEqual(actual[3],predicted)
            self.assertGreater(abs(actual[3]),TOLERANCE)
            coefficient=next(b for b in proof['branches'] if b['branch']==o.branch)
            self.assertTrue(Interval(*coefficient['imaginary_coefficient']).contains(actual[3]/e))
        with self.assertRaises(ValueError): transverse_readout_obstruction(0)

    def test_future_approach_strengthens_at_fixed_target_and_tolerance(self):
        cert=approach_certificate()
        for branch in cert['branches']:
            self.assertGreater(branch['fixed_gain_derivative'][0],0)
        for o in (self.first,self.second):
            path=approach_probes(o)
            probes=path['probes']
            self.assertTrue(all(a['distance_to_fixed_result']>b['distance_to_fixed_result']
                                for a,b in zip(probes,probes[1:])))
            self.assertTrue(all(a['allowable_source_half_width']>b['allowable_source_half_width']
                                for a,b in zip(probes,probes[1:])))
            self.assertFalse(probes[0]['completed_flower'])
            self.assertTrue(probes[-1]['completed_flower'])
            self.assertEqual(probes[-1]['endpoint'],o.decoded.state.live.accumulated)

    def test_approach_gain_derivative_matches_a_separate_polynomial_interpolation(self):
        p=Parameters(Q(1,2*10**8),Q(-1,3*10**8),Q(1,5*10**8),Q(-1,7*10**8))
        for branch,(lo,hi) in APPROACH_WINDOWS.items():
            t=(lo+hi)/2
            points=[t+Q(k,10**6) for k in (-1,0,1,2)]
            coefficients=solve([[x**j for j in range(4)] for x in points],
                               [geometry(x,p)['fixed_boundary_gain'] for x in points])
            independent=sum(j*coefficients[j]*t**(j-1) for j in range(1,4))
            self.assertEqual(independent,geometry(t,p)['fixed_gain_derivative'])

    def test_full_coordinate_rotation_preserves_genuine_nested_certificates(self):
        for o in (self.first,self.second):
            control=rotated_model_control(o)
            self.assertTrue(control['genuinely_nondiagonal'])
            self.assertTrue(control['source_and_consumer_certified'])
            self.assertEqual(control['endpoint'],o.decoded.state.live.accumulated)
            r=control['rotation']
            for i in range(3):
                for j in range(3):
                    self.assertEqual(sum(r[i][k]*r[j][k] for k in range(3)),int(i==j))

    def test_whole_law_sensitivity_and_fixed_boundary_strength_have_opposite_changes(self):
        cert=approach_certificate()
        for b in cert['branches']:
            self.assertGreater(b['whole_law_second_derivative'][0],0)
        for o in (self.first,self.second):
            trials=approach_probes(o)['probes']
            for a,b in zip(trials,trials[1:]):
                self.assertGreater(abs(a['whole_law_derivative']),abs(b['whole_law_derivative']))
                self.assertLess(abs(a['fixed_boundary_gain']),abs(b['fixed_boundary_gain']))


if __name__=='__main__': unittest.main()
