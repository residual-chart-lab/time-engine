import unittest
from same_level_continuation import *


class SameLevelContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab,cls.changed,cls.first,cls.second,cls.zero_context=fixtures()

    def test_actual_common_preparation_is_required(self):
        self.assertEqual(self.ab.prepared,self.changed.prepared)
        with self.assertRaises(ValueError):
            PreparedPast(self.ab.prepared.initial,tuple(reversed(self.ab.prepared.operations)))

    def test_same_level_repair_keeps_head_context_and_result(self):
        y=self.ab.prepared.endpoint.live.context
        trial=start(self.ab,y)
        repaired=append(trial,self.ab.prepared.operations[:2])
        self.assertEqual(repaired.decoded.state.live.context,y)
        self.assertEqual(repaired.offered_word[0],self.ab.request.operation)
        self.assertEqual(repaired.decoded.state.live.accumulated,self.ab.request.result)
        self.assertEqual(repaired.decoded.outputs[0].level,3)

    def test_append_schedule_and_exact_decoder_agree(self):
        trial=start(self.ab,self.ab.prepared.endpoint.live.context)
        stock=self.ab.prepared.operations
        self.assertEqual(append(append(trial,stock[:1]),stock[1:2]),append(trial,stock[:2]))

    def test_original_failure_has_unbounded_stock_obstruction(self):
        for experiment,y,expected in ((self.ab,self.second,-1),(self.changed,self.first,-2)):
            trial=start(experiment,y)
            self.assertEqual(no_repair_certificate(trial)['required_valuation'],expected)
            expanded=append(trial,experiment.stock*3)
            self.assertEqual(expanded.decoded.state,trial.arrival.staged)
            self.assertEqual(expanded.decoded.stop,'NoTerminalPrefix')

    def test_replacement_is_a_separate_success(self):
        trial=start(self.changed,self.first)
        self.assertIsNotNone(no_repair_certificate(trial))
        replacement=replace_head(trial,self.changed.prepared.operations[:2])
        self.assertEqual(replacement.state.live.accumulated,tuple(NEG_ONE))
        self.assertNotIn(self.changed.request.operation,replacement.outputs[0].cell.beta)

    def test_level_one_algebra_is_not_available_level_two_stock(self):
        trial=start(self.ab,self.second)
        leaf=diagnostic_primitive_correction(trial)
        self.assertEqual(leaf.kernel(self.second),(Q(-1,6),0,0,0))
        with self.assertRaises(ValueError):
            append(trial,(leaf,))

    def test_other_source_branch_is_not_an_available_correction(self):
        trial=start(self.ab,self.second)
        with self.assertRaises(ValueError):
            append(trial,(self.changed.request.operation,))

    def test_zero_is_not_committed_or_compensated(self):
        trial=start(self.ab,self.zero_context)
        self.assertEqual(no_repair_certificate(trial)['kind'],'zero-absorbing')
        self.assertEqual(append(trial,self.ab.stock).decoded.state,trial.arrival.staged)


if __name__=='__main__':
    unittest.main()
