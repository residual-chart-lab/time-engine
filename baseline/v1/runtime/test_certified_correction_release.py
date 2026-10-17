import unittest
from certified_correction_release import *


class CertifiedCorrectionReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab,cls.changed,cls.first,cls.second,cls.zero_context=fixtures()

    def trial(self):
        return start(self.ab,self.second)

    def test_plan_cannot_be_used_as_same_level_operation(self):
        session=plan_correction(open_session(self.trial()))
        self.assertEqual(session.stock,self.ab.stock)
        self.assertEqual(session.lower,session.original_trial.arrival.staged)
        with self.assertRaises(ValueError):
            require_available(session,session.plan.leaf)

    def test_certificate_requires_publication_before_consumption(self):
        issued=execute_lower(plan_correction(open_session(self.trial())))
        self.assertEqual(issued.issue.operation.level,2)
        with self.assertRaises(ValueError):
            require_available(issued,issued.issue.operation)
        with self.assertRaises(ValueError):
            consume(issued)
        available=publish(issued)
        require_available(available,available.issue.operation)

    def test_actual_producer_executes_while_upper_tail_waits(self):
        original=open_session(self.trial())
        issued=execute_lower(plan_correction(original))
        self.assertEqual(issued.upper,original.upper)
        self.assertEqual(issued.issue.operation.cell.start,original.lower)
        self.assertEqual(len(issued.lower.executed_word),len(original.lower.executed_word)+1)

    def test_two_failures_close_only_with_extended_stock(self):
        for experiment,y in ((self.ab,self.second),(self.changed,self.first)):
            trial=start(experiment,y)
            self.assertIsNotNone(no_repair_certificate(trial))
            session=complete(trial)
            self.assertEqual(session.upper.state.live.accumulated,tuple(NEG_ONE))
            self.assertEqual(session.upper.outputs[0].cell.beta[0],experiment.request.operation)
            self.assertEqual(session.upper.outputs[0].level,3)
            self.assertEqual(len(session.stock),5)
            self.assertEqual(session.next_request.result,tuple(NEG_ONE))

    def test_exact_decoder_and_temporal_release_order(self):
        session=complete(self.trial())
        self.assertEqual(session.upper,decode(session.original_trial.arrival.staged,
            (self.ab.request.operation,session.issue.operation),(NEG_ONE,)))
        self.assertEqual([e.index for e in session.events],[0,1,2,3,4])
        self.assertNotIn(session.issue.operation,session.events[2].stock)
        self.assertIn(session.issue.operation,session.events[3].stock)

    def test_zero_cannot_get_a_finite_inverse_correction(self):
        session=open_session(start(self.ab,self.zero_context))
        with self.assertRaises(ValueError):
            plan_correction(session)
        self.assertEqual(session.lower,session.original_trial.arrival.staged)

    def test_double_publication_and_other_branch_are_rejected(self):
        available=publish(execute_lower(plan_correction(open_session(self.trial()))))
        with self.assertRaises(ValueError):
            publish(available)
        with self.assertRaises(ValueError):
            require_available(available,self.changed.request.operation)

    def test_nonreal_response_uses_the_same_release_pipeline(self):
        _,_,_,policy=primitive_fixture()
        session=complete(start(self.ab,policy.probe))
        self.assertTrue(any(session.plan.speculative_response[1:]))
        self.assertTrue(any(session.plan.wanted_action[1:]))
        self.assertEqual(session.upper.state.live.accumulated,tuple(NEG_ONE))

    def test_constant_scalar_solution_is_made_active_without_changing_response(self):
        _,_,_,policy=primitive_fixture()
        library=self.ab.request.operation.leaves()[0].library
        naive=AffineLetter(tuple(solve(action_matrix(policy.probe,library),[1,Q(-1,3),0,0,0])),library)
        self.assertFalse(active_leaf(naive))
        leaf=correction_leaf(policy.probe,library,(Q(-1,3),0,0,0))
        self.assertTrue(active_leaf(leaf))
        self.assertEqual(leaf.kernel(policy.probe),(Q(-1,3),0,0,0))


if __name__=='__main__':
    unittest.main()
