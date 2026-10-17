import unittest
from closure_native_context_source import *


class ClosureNativeContextSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial=boot(fixtures()[0])

    def test_initial_context_is_generated_from_the_actual_closed_word(self):
        driver=start_native(self.initial)
        self.assertEqual(driver.messages[0].source,self.initial.designated_head)
        self.assertEqual(driver.messages[0].context_value,context([[Q(1,3),0,0],[0,Q(2,3),0],[0,0,0]]))
        self.assertIsNone(driver.engine.pending.arrived_context)

    def test_inverse_cube_recurrence_and_persistent_states(self):
        driver=advance_native(start_native(self.initial),3)
        values=[2*m.context_value[0][0]-1 for m in driver.messages]
        self.assertEqual(values,[Q(-1,3),Q(27),Q(-1,19683),Q(3**27)])
        self.assertEqual(len(driver.engine.lower.executed_word),8)
        self.assertEqual(len(driver.engine.stock),7)

    def test_normalization_bounds_the_port_but_keeps_exact_sources(self):
        driver=advance_native(start_native(self.initial,ContextPolicy('normalized')),2)
        for message in driver.messages:
            s=residue([list(row) for row in message.context_value])
            self.assertEqual(sum(abs(v)for row in s for v in row),Q(1,8))
            self.assertIn(message.source,driver.engine.stock)
        self.assertGreater(abs(driver.engine.lower.live.accumulated[0]),1)

    def test_resume_preserves_pending_message_and_old_certificates(self):
        started=start_native(self.initial)
        first=advance_native(started,1)
        final=advance_native(first,2)
        self.assertEqual(final,advance_native(started,3))
        self.assertEqual(final.messages[:2],first.messages)
        self.assertEqual(final.engine.rounds[:1],first.engine.rounds)

    def test_context_source_uses_only_published_actual_production(self):
        driver=advance_native(start_native(self.initial),1)
        self.assertEqual(driver.messages[-1].source,driver.engine.rounds[-1].pending.issue.operation)
        self.assertEqual(driver.messages[-1].source.cell.endpoint,driver.engine.lower)

    def test_empty_port_does_not_erase_an_active_source(self):
        initial=empty_port_fixture()
        driver=start_native(initial,ContextPolicy('normalized'))
        self.assertEqual(driver.stop,'SOURCE_PORT_EMPTY')
        self.assertEqual(driver.messages,())
        self.assertEqual(driver.engine.stock,initial.stock)
        self.assertEqual(driver.engine.upper,initial.upper)
        self.assertEqual(advance_native(driver,4),driver)

    def test_direct_isotropic_readout_stops_at_the_chart_gate(self):
        driver=step_native(start_native(empty_port_fixture()))
        self.assertEqual(driver.stop,'CHART_STOP')
        self.assertEqual(driver.engine.rounds,())
        self.assertEqual(driver.engine.pending.arrived_context,context(boundary([[Q(0)]*3 for _ in range(3)])))

    def test_bad_policy_or_execution_budget_is_rejected(self):
        with self.assertRaises(ValueError):
            ContextPolicy('normalized',0)
        with self.assertRaises(ValueError):
            advance_native(start_native(self.initial),-1)

    def test_normalized_branch_bounds_coefficients_but_producer_value_grows(self):
        driver=advance_native(start_native(self.initial,ContextPolicy('normalized')),3)
        for trace in driver.engine.rounds:
            self.assertLessEqual(max(abs(w) for w in trace.pending.plan.leaf.weights),Q(28423,225))
        self.assertGreater(abs(driver.engine.lower.live.accumulated[0]),1000)


if __name__=='__main__':
    unittest.main()
