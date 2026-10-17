import unittest
from endogenous_flower_boundary import *


class EndogenousFlowerBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first=endogenous_flower()
        cls.second=endogenous_flower('second')

    def test_roots_are_exactly_bracketed_and_simple(self):
        for f in (self.first,self.second):
            lo,hi=f.root.initial_interval
            self.assertLess(boundary_mismatch(lo)*boundary_mismatch(hi),0)
            self.assertFalse(f.root.derivative_bounds[0]<=0<=f.root.derivative_bounds[1])

    def test_current_correction_and_actual_production_are_exact(self):
        for f in (self.first,self.second):
            self.assertEqual(f.source.kernel(f.source.cell.start.live.context),(-9,0,0,0))
            self.assertEqual(f.prepared_engine.lower.live.accumulated,(9,0,0,0))
            self.assertEqual(f.source.cell.endpoint,f.prepared_engine.lower)

    def test_future_context_comes_from_the_actual_published_source(self):
        f=self.first
        self.assertEqual(f.emitted_context,generated_context(f.source,ContextPolicy('direct')))
        self.assertIn(f.source,f.prepared_engine.stock)
        self.assertNotEqual(f.emitted_context,f.source.cell.start.live.context)

    def test_no_consumer_history_is_rewritten_when_internal_context_arrives(self):
        f=self.first
        self.assertEqual(f.prepared_engine.upper.executed_word,f.entry.upper.executed_word)
        self.assertEqual(f.consumer_start.executed_word,f.entry.upper.executed_word)
        self.assertEqual(f.decoded.state.executed_word[:5],f.entry.upper.executed_word)

    def test_declared_result_stays_fixed_and_approximation_is_explicit(self):
        f=self.first
        self.assertEqual(f.fixed_result,(-1,0,0,0))
        self.assertLess(f.closure_error,Q(1,2*10**12))
        self.assertNotEqual(f.decoded.outputs[0].cell.target,f.fixed_result)
        self.assertEqual(f.decoded.outputs[0].cell.target,f.decoded.state.live.accumulated)

    def test_first_tolerant_boundary_is_the_second_letter(self):
        f=self.first
        self.assertGreater(f.prefix_error,f.root.closure_tolerance)
        self.assertEqual(len(f.decoded.outputs[0].cell.beta),2)
        self.assertEqual(f.decoded.tail,())
        self.assertEqual(f.decoded.boundaries,())

    def test_two_explicit_branch_rules_retain_different_actual_sources(self):
        self.assertNotEqual(self.first.root.representative,self.second.root.representative)
        self.assertNotEqual(self.first.source,self.second.source)
        self.assertNotEqual(self.first.emitted_context,self.second.emitted_context)
        self.assertEqual(self.first.prepared_engine.lower.live.accumulated,self.second.prepared_engine.lower.live.accumulated)

    def test_canonical_current_success_fails_at_its_own_future_context(self):
        value=head_at_source(Q(0))*leaf_at_source(Q(0))
        self.assertEqual(value,-531441)
        self.assertGreater(abs(-value+1),1)

    def test_forward_replay_preserves_exact_outputs(self):
        for f in (self.first,self.second):
            self.assertEqual(forward_replay(f),(f.prepared_engine.lower,f.prepared_engine.stock,f.emitted_context,f.decoded))

    def test_invalid_tolerance_or_unselected_branch_is_not_silently_changed(self):
        with self.assertRaises(ValueError):
            isolate_boundary('unknown')
        with self.assertRaises(ValueError):
            isolate_boundary(tolerance=0)
        with self.assertRaises(ValueError):
            isolate_boundary(tolerance=Q(1,10))


if __name__=='__main__':
    unittest.main()
