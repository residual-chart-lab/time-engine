import unittest
from persistent_correction_cycle import *


class PersistentCorrectionCycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial,cls.contexts,cls.zero_context=fixtures_sequence()

    def test_persistent_stock_and_two_clocks(self):
        engine=run_schedule(self.initial,self.contexts).engine
        self.assertEqual([t.route for t in engine.rounds],['produced','reused','produced','reused','head','reused'])
        self.assertEqual(len(engine.stock),6)
        self.assertEqual(len(engine.lower.executed_word),7)
        self.assertEqual(len(engine.upper.executed_word),16)
        self.assertEqual(engine.rounds[2].pending.plan.lower_start.live.accumulated,(Q(1,6),0,0,0))
        self.assertTrue(replay_trace(self.initial,engine))

    def test_old_correction_is_reused_without_new_production(self):
        once=run_round(self.initial,self.contexts[0])
        twice=run_round(once,self.contexts[1])
        self.assertEqual(twice.lower,once.lower)
        self.assertEqual(twice.stock,once.stock)
        self.assertEqual(twice.rounds[-1].decoded.outputs[0].cell.beta[1],once.stock[-1])

    def test_request_is_fixed_before_context_arrival(self):
        waiting=request_boundary(self.initial)
        self.assertIsNone(waiting.pending.arrived_context)
        self.assertEqual(waiting.pending.upper_before,self.initial.upper)
        self.assertEqual(waiting.lower,self.initial.lower)
        with self.assertRaises(ValueError):
            request_boundary(waiting)

    def test_published_only_after_actual_persistent_lower_closure(self):
        planned=resolve_open(accept_context(request_boundary(self.initial),self.contexts[0]))
        issued=execute_producer(planned)
        self.assertEqual(issued.upper,planned.upper)
        self.assertEqual(len(issued.lower.executed_word),len(planned.lower.executed_word)+1)
        with self.assertRaises(ValueError):
            available(issued,issued.pending.issue.operation)
        published=publish_producer(issued)
        available(published,published.pending.issue.operation)
        with self.assertRaises(ValueError):
            publish_producer(published)

    def test_pause_and_continue_agree(self):
        first=run_schedule(self.initial,self.contexts[:3])
        later=run_schedule(first.engine,self.contexts[3:])
        self.assertEqual(later,run_schedule(self.initial,self.contexts))
        self.assertEqual(later.engine.rounds[:3],first.engine.rounds)

    def test_resume_inside_a_round_preserves_boundary_and_producer_history(self):
        waiting=request_boundary(self.initial)
        self.assertEqual(run_schedule(waiting,()).stop,'ContextExhausted')
        planned=resolve_open(accept_context(waiting,self.contexts[0]))
        full=run_schedule(self.initial,self.contexts)
        self.assertEqual(run_schedule(waiting,self.contexts),full)
        self.assertEqual(run_schedule(planned,self.contexts[1:]),full)

    def test_zero_stops_without_consuming_pending_head(self):
        prefix=run_schedule(self.initial,self.contexts[:2]).engine
        result=run_schedule(prefix,(self.zero_context,self.contexts[2]))
        self.assertEqual(result.stop,'ZERO_STOP')
        self.assertEqual(result.engine.upper.executed_word,prefix.upper.executed_word)
        self.assertEqual(result.engine.stock,prefix.stock)
        self.assertEqual(result.unoffered_contexts,(self.contexts[2],))
        self.assertEqual(run_schedule(result.engine,result.unoffered_contexts),result)
        with self.assertRaises(ValueError):
            request_boundary(result.engine)

    def test_chart_exit_keeps_real_past(self):
        prefix=run_round(self.initial,self.contexts[0])
        singular=context([[0,0,0],[0,0,0],[0,0,1]])
        result=run_schedule(prefix,(singular,self.contexts[1]))
        self.assertEqual(result.stop,'CHART_STOP')
        self.assertEqual(result.engine.upper.live.context,singular)
        self.assertEqual(result.engine.upper.executed_word,prefix.upper.executed_word)
        self.assertEqual(result.engine.stock,prefix.stock)

    def test_bounded_existing_word_can_avoid_new_producer_cell(self):
        engine=run_round(self.initial,self.initial.upper.live.context,head=self.initial.stock[0])
        self.assertEqual(engine.rounds[-1].route,'reused')
        self.assertEqual(len(engine.outputs[-1].cell.beta),3)
        self.assertEqual(engine.lower.executed_word,self.initial.lower.executed_word)

    def test_higher_output_needs_a_separate_receiver(self):
        engine=run_schedule(self.initial,self.contexts).engine
        with self.assertRaises(ValueError):
            request_boundary(engine,engine.outputs[0])
        receipt=receive_higher(engine)
        self.assertEqual(receipt.anchor,engine.upper)
        self.assertEqual(receipt.decoded.outputs[0].level,4)
        self.assertEqual(len(receipt.decoded.state.executed_word),len(engine.upper.executed_word)+1)


if __name__=='__main__':
    unittest.main()
