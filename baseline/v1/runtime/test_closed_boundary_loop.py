import unittest
from closed_boundary_loop import *


class ClosedBoundaryLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial,cls.a,cls.b,cls.policy=fixture()

    def test_source_preserves_residue_dependent_effect(self):
        ab=promote_word(certify_word(self.initial,(self.a,self.b),NEG_ONE))
        ba=promote_word(certify_word(self.initial,(self.b,self.a),NEG_ONE))
        self.assertEqual(ab.visible,ba.visible)
        self.assertEqual(ab.cell.endpoint.live,ba.cell.endpoint.live)
        self.assertNotEqual(self.policy.emit(ab).target,self.policy.emit(ba).target)

    def test_generated_boundary_precedes_access_to_new_tail(self):
        first=start_loop(self.initial,(self.a,self.b),NEG_ONE,self.policy)
        self.assertEqual(len(first.events),1)
        self.assertEqual(first.pending,((1,0,0,0),))
        for tail in [(self.a,),(self.b,self.a),(self.a,self.b)*3]:
            later=extend_loop(first,tail)
            self.assertEqual(later.events[0],first.events[0])
            self.assertEqual(later.issued[:2],first.issued)

    def test_failure_keeps_actual_state_at_last_certificate(self):
        raw=SourcePolicy(self.policy.probe,mode='raw')
        result=start_loop(self.initial,(self.a,self.b)*4,NEG_ONE,raw)
        self.assertEqual(result.stop,'NoTerminalPrefix')
        self.assertEqual(len(result.state.executed_word),2)
        self.assertEqual(len(result.tail),6)

    def test_no_event_without_closure(self):
        result=start_loop(self.initial,(self.a,),NEG_ONE,self.policy)
        self.assertEqual(result.events,())
        self.assertEqual(result.state,self.initial)
        self.assertEqual(extend_loop(result,(self.b,)),start_loop(self.initial,(self.a,self.b),NEG_ONE,self.policy))

    def test_every_split_has_identical_record_and_no_duplicate_events(self):
        word=(self.a,self.b)*4
        full=start_loop(self.initial,word,NEG_ONE,self.policy)
        for cut in range(len(word)+1):
            self.assertEqual(extend_loop(start_loop(self.initial,word[:cut],NEG_ONE,self.policy),word[cut:]),full)

    def test_source_zero_requires_an_actual_law_decision(self):
        policy=SourcePolicy(self.initial.live.context)
        result=start_loop(self.initial,(self.a,self.b)*4,NEG_ONE,policy)
        self.assertEqual(result.stop,'SourceUndecided')
        self.assertIsNone(result.events[0].target)
        self.assertEqual(extend_loop(result,(self.a,self.b)).events,result.events)

    def test_source_rejects_forged_certificate(self):
        ab=promote_word(certify_word(self.initial,(self.a,self.b),NEG_ONE))
        with self.assertRaises(ValueError):
            self.policy.emit(replace(ab,visible=(1,0,0,0)))


if __name__=='__main__':
    unittest.main()
