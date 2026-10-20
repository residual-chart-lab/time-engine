import unittest
from dataclasses import replace
from fractions import Fraction as Q
from unittest.mock import patch
import future_pullback as m
from future_pullback import geom,te,d
from word_fibre import first_return,accepts_future_parity
import rr61_study as study

class FuturePullbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.keep=m.previous.begin('keep');cls.erase=m.previous.begin('erase')
        cls.c=m.Requirement(m.diagonal(-1));cls.decision=m.derive(cls.keep,cls.c)
        cls.record=m.execute_current(cls.keep,cls.decision,'HS')

    def test_input_hash_and_full_grid_are_bound(self):
        inputs=study.load_inputs()
        self.assertEqual([Q(x['x']) for x in inputs['future_frames'][:-1]],[Q(k,4) for k in range(-4,9)])
        self.assertFalse(inputs['success_paths_used_to_construct_C'])

    def test_same_current_response_different_retained_history(self):
        self.assertEqual(study.projection(self.keep),study.projection(self.erase))
        self.assertNotEqual(self.keep.first.closed_engine.stock,self.erase.first.closed_engine.stock)

    def test_decision_uses_neither_completed_future_execution_nor_old_solvable_fixture(self):
        with patch.object(m,'execute_current',side_effect=AssertionError('no future execution')), \
             patch.object(m,'read_future',side_effect=AssertionError('no future execution')), \
             patch.object(te,'construct_requirement',side_effect=AssertionError('no success fixture')), \
             patch.object(te,'finite_family',side_effect=AssertionError('no 128 future paths')):
            decision=m.derive(self.keep,self.c)
            forward=m.forward_reachability(self.keep,self.c)
        self.assertEqual(decision.control,forward.control)

    def test_forward_solver_is_independent_of_pullback_solver(self):
        with patch.object(m,'derive',side_effect=AssertionError('independent control')):
            forward=m.forward_reachability(self.keep,self.c)
        self.assertEqual(forward.control,self.decision.control)

    def test_exact_retained_shift_changes_allowed_control(self):
        erased=m.derive(self.erase,self.c)
        self.assertEqual(erased.control-self.decision.control,self.keep.pair.shift)
        self.assertNotEqual(erased.control,self.decision.control)

    def test_independent_C_changes_current_control(self):
        other=m.derive(self.keep,m.Requirement(m.diagonal(Q(1,4))))
        self.assertNotEqual(self.decision.control,other.control)

    def test_actuator_bound_is_real_but_not_a_global_impossibility_claim(self):
        v=m.derive(self.keep,self.c,(-1,1))
        self.assertEqual(v.status,'EMPTY_DOMAIN')
        self.assertFalse(v.algebraically_feasible)
        with self.assertRaises(ValueError):m.execute_current(self.keep,v,'HS')

    def test_zero_head_and_blind_channel_are_distinct(self):
        head=m.derive(self.keep,m.Requirement(m.diagonal(Q(1,2))))
        blind=m.derive(self.keep,m.Requirement(m.diagonal(Q(1,3))))
        self.assertEqual(head.status,'EMPTY_ZERO_HEAD')
        self.assertEqual(blind.status,'EMPTY_BLIND')
        self.assertTrue(head.g);self.assertFalse(head.h)
        self.assertTrue(blind.h);self.assertFalse(blind.g)

    def test_algebraic_solution_outside_chart_does_not_authorize_execution(self):
        v=m.derive(self.keep,m.Requirement(m.diagonal(0)))
        self.assertTrue(v.algebraically_feasible)
        self.assertEqual(v.status,'ALGEBRAIC_ONLY')
        self.assertFalse(v.chart_regular)
        with self.assertRaises(ValueError):m.execute_current(self.keep,v,'HS')

    def test_current_choice_freedom_has_two_distinct_three_pair_words(self):
        for word in ('HS','HHHSSS','HHSHSS'):
            r=m.execute_current(self.keep,self.decision,word)
            trial,decoded,ok=m.read_future(self.keep,self.decision,r)
            self.assertEqual(trial.live.accumulated,m.ONE);self.assertTrue(ok)
            self.assertEqual(decoded.outputs[0].level,4)

    def test_even_word_is_not_silently_included(self):
        self.assertTrue(first_return('HHSS'));self.assertFalse(accepts_future_parity('HHSS'))
        with self.assertRaises(ValueError):m.execute_current(self.keep,self.decision,'HHSS')
        r=m.execute_current(self.keep,self.decision,'HHSS',allow_control_test=True)
        trial,_,ok=m.read_future(self.keep,self.decision,r,allow_control_test=True)
        self.assertEqual(trial.live.accumulated,m.NEG);self.assertFalse(ok)

    def test_words_that_close_early_are_not_a_single_current_flower(self):
        for word in ('','S','HSS','HSHS','HHS','SH'):
            self.assertFalse(first_return(word))
            with self.assertRaises(ValueError):m.execute_current(self.keep,self.decision,word)

    def test_wrong_history_control_still_closes_current_but_not_future(self):
        u=m.derive(self.erase,self.c).control
        with self.assertRaises(ValueError):m.execute_current(self.keep,self.decision,'HS',u)
        r=m.execute_current(self.keep,self.decision,'HS',u,allow_control_test=True)
        trial,_,ok=m.read_future(self.keep,self.decision,r,allow_control_test=True)
        self.assertEqual(r.closed_engine.upper.live.accumulated,m.NEG);self.assertFalse(ok)
        self.assertEqual(trial.live.accumulated[0]-1,-self.decision.h*self.decision.g*self.decision.retained_shift)

    def test_actual_history_publication_and_level_are_preserved(self):
        before=self.keep.first.closed_engine;r=self.record;e=r.closed_engine
        self.assertEqual(e.events[:len(before.events)],before.events)
        self.assertEqual(e.stock,before.stock+(r.source,))
        self.assertEqual(e.rounds[:-1],before.rounds)
        self.assertEqual((r.source.level,r.terminal.level),(2,3))
        self.assertEqual(r.source.cell.start,before.lower)
        kinds=[x.kind for x in e.events[len(before.events):]]
        self.assertLess(kinds.index('lower-cell-closed'),kinds.index('same-level-operation-published'))
        self.assertLess(kinds.index('same-level-operation-published'),kinds.index('rr61-current-word-executed'))

    def test_decision_evidence_tampering_rejected(self):
        for bad in (replace(self.decision,history_digest='bad'),replace(self.decision,control=self.decision.control+1),
                    replace(self.decision,retained_shift=0),replace(self.decision,domain=(-1,1))):
            with self.assertRaises(ValueError):m.verify_decision(self.keep,bad)
        with self.assertRaises(ValueError):m.verify_decision(self.erase,self.decision)

    def test_current_occurrence_tampering_and_requirement_substitution_rejected(self):
        for bad in (replace(self.record,decision_digest='bad'),replace(self.record,word='HHHSSS'),
                    replace(self.record,closed_engine=replace(self.record.closed_engine,result=m.ONE))):
            with self.assertRaises(ValueError):m.verify_current(self.keep,self.decision,bad)
        other=m.derive(self.keep,m.Requirement(m.diagonal(Q(1,4))))
        with self.assertRaises(ValueError):m.read_future(self.keep,other,self.record)

    def test_future_target_or_inheritance_cannot_be_relabelled(self):
        with self.assertRaises(ValueError):m.Requirement(self.c.context,target=m.NEG)
        with self.assertRaises(ValueError):m.Requirement(self.c.context,inherited=m.ONE)

    def test_complete_fibre_axis_is_intrinsic_and_matches_current_null_line(self):
        y=self.keep.first.residue.internal_context;lib=self.keep.pair.original.library
        g=geom.geometry(y,lib)
        self.assertEqual((g.boundary_basis_rank,g.response_rank,g.invisible_dimension),(6,4,1))
        self.assertEqual(g.coefficient_axis,(-2,1,1,0,0,0))
        self.assertEqual(geom.norm2(g.intrinsic_axis),g.discriminant/(3*g.variance))
        self.assertEqual(geom.tr(g.intrinsic_axis),0)
        self.assertEqual(tuple(d.join(g.intrinsic_axis,y)),(0,0,0,0))

    def test_repeated_and_isotropic_frames_cannot_claim_complete_one_axis(self):
        lib=self.keep.pair.original.library
        repeated=geom.geometry(m.diagonal(0),lib)
        isotropic=geom.geometry(tuple(tuple(Q(i==j,3) for j in range(3)) for i in range(3)),lib)
        self.assertEqual((repeated.invisible_dimension,isotropic.invisible_dimension),(2,5))
        for g in (repeated,isotropic):
            self.assertIsNone(g.coefficient_axis)
            with self.assertRaises(ValueError):geom.certify_pair(g.context,self.keep.pair.original,self.keep.pair.representative)

    def test_fibre_certificate_binds_pair_and_current_context(self):
        y=self.keep.first.residue.internal_context;p=self.keep.pair
        cert=geom.certify_pair(y,p.original,p.representative)
        self.assertTrue(geom.verify_pair(y,p.original,p.representative,cert))
        with self.assertRaises(ValueError):geom.verify_pair(y,p.original,p.representative,replace(cert,shift=0))

if __name__=='__main__':unittest.main()
