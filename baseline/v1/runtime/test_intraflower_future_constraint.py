import unittest
from dataclasses import replace
from intraflower_future_constraint import *


class IntraFlowerFutureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial,cls.y,cls.plus,cls.minus,cls.union=fixtures()
        cls.left=prepare(cls.initial,cls.y,cls.plus)
        cls.right=prepare(cls.initial,cls.y,cls.minus)

    def test_future_family_selects_different_present_representatives(self):
        self.assertEqual(self.left.selection.null_shift,Q(41,14))
        self.assertEqual(self.right.selection.null_shift,Q(71,14))
        self.assertEqual(self.left.engine.pending.plan.wanted_action,self.right.engine.pending.plan.wanted_action)
        self.assertEqual(self.left.engine.pending.plan.lower_target,(9,0,0,0))

    def test_actual_future_value_is_not_an_input_to_selection(self):
        self.assertEqual(len(self.left.family.contexts),2)
        self.assertIsInstance(self.left.witness,FutureWitness)
        self.assertEqual(self.left.witness.responses,((-1,0,0,0),)*2)
        self.assertEqual(self.left.engine.outputs,())

    def test_future_guard_precedes_consumer_commit(self):
        self.assertEqual(self.left.status,'READY_FOR_JOINT_CLOSURE')
        self.assertEqual(self.left.engine.upper.executed_word,self.initial.upper.executed_word)
        self.assertEqual(self.left.engine.events[-1].kind,'intraflower-future-family-certified')
        result=close(self.left)
        self.assertEqual(result.status,'BOUNDARY_COMPATIBLE_COMPLETE')
        self.assertEqual(result.engine.outputs[-1].cell.beta,self.left.witness.word)

    def test_present_fit_does_not_certify_future_compatibility(self):
        opened=accept_context(request_boundary(self.initial),self.y)
        published=publish_producer(execute_producer(resolve_open(opened)))
        self.assertIsNone(certify_future_compatibility(published,self.plus))
        self.assertIsNone(certify_future_compatibility(published,self.minus))
        with self.assertRaises(ValueError):
            close(TwoBoundaryFlower(self.initial,self.plus,published,'PRESENT_FIT_ONLY'))

    def test_conflicting_union_is_exactly_inconsistent_without_execution(self):
        bad=prepare(self.initial,self.y,self.union)
        self.assertEqual(bad.status,'INCOMPATIBLE_BOUNDARIES')
        self.assertEqual(bad.engine.lower.executed_word,self.initial.lower.executed_word)
        self.assertEqual(bad.engine.stock,self.initial.stock)
        self.assertEqual(bad.engine.outputs,())
        with self.assertRaises(ValueError):
            close(bad)

    def test_unknown_family_remains_open(self):
        unknown=prepare(self.initial,self.y,None)
        self.assertEqual(unknown.status,'FUTURE_FAMILY_UNRESOLVED')
        self.assertIsNone(unknown.selection)
        self.assertEqual(unknown.engine.stock,self.initial.stock)
        with self.assertRaises(ValueError):
            close(unknown)

    def test_wrong_family_is_not_repaired_by_changing_the_closed_history(self):
        result=close(self.left)
        operation=result.engine.outputs[-1]
        response=future_responses(operation,self.initial.upper.live.accumulated,self.minus)
        self.assertEqual(response[1],(14,0,0,0))
        self.assertIs(close(result),result)
        self.assertEqual(result.engine.stock[-1],self.left.witness.actual_source)

    def test_future_verification_requires_actual_execution_and_publication(self):
        planned=resolve_open(accept_context(request_boundary(self.initial),self.y))
        with self.assertRaises(ValueError):
            certify_future_compatibility(planned,self.plus)
        issued=execute_producer(planned)
        with self.assertRaises(ValueError):
            certify_future_compatibility(issued,self.plus)

    def test_future_condition_is_checked_again_when_closing(self):
        changed=replace(self.left,family=self.minus)
        with self.assertRaises(ValueError):
            close(changed)

    def test_joint_history_replays_without_reset_or_pooling_alternatives(self):
        for prepared in (self.left,self.right):
            finished=close(prepared)
            self.assertTrue(replay_trace(self.initial,finished.engine))
            self.assertEqual(len(finished.engine.stock),5)
            self.assertEqual(len(finished.engine.lower.executed_word),6)
            self.assertEqual(len(finished.engine.upper.executed_word),7)
            self.assertEqual(finished.engine.stock[:4],self.initial.stock)

    def test_known_family_forward_controller_reproduces_jointly_selected_result(self):
        prepared=self.left
        flower=arrive(begin_flower(self.initial,solution_rule=SolutionRule(prepared.selection.null_shift)),self.y)
        while flower.status!='COMPLETE':
            flower=advance(flower)
        finished=close(prepared)
        self.assertEqual(flower.engine.outputs,finished.engine.outputs)
        self.assertEqual(flower.engine.upper,finished.engine.upper)
        self.assertEqual(flower.engine.lower,finished.engine.lower)
        self.assertEqual(flower.engine.stock,finished.engine.stock)

    def test_future_chart_exclusion_is_not_counted_as_success(self):
        singular=context([[0,0,0],[0,0,0],[0,0,1]])
        with self.assertRaises(ValueError):
            prepare(self.initial,self.y,FutureFamily('singular',(singular,)))


if __name__=='__main__':
    unittest.main()
