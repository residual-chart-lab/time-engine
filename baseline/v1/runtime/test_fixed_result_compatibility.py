import unittest
from fixed_result_compatibility import *


class FixedResultCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.initial,cls.op,cls.changed,cls.reversed,cls.first,cls.second=examples()

    def test_same_endpoint_different_fixed_result_families(self):
        r,rp=map(generate_request,(self.op,self.changed))
        self.assertEqual(r.result,rp.result)
        self.assertEqual(r.inherited.live,rp.inherited.live)
        self.assertEqual([r.compatible(self.first),rp.compatible(self.first)],[True,False])
        self.assertEqual([r.compatible(self.second),rp.compatible(self.second)],[False,True])

    def test_requirement_exists_before_any_arrival(self):
        r=generate_request(self.op)
        self.assertEqual(r.required_net_action,(1,0,0,0))
        for y in (self.first,self.second):
            arrive(r,y)
            self.assertEqual(r.inherited,self.op.cell.endpoint)
            self.assertEqual(r.operation,self.op)

    def test_failed_arrival_is_not_successful_execution(self):
        r=generate_request(self.op)
        attempt=arrive(r,self.second)
        self.assertEqual(attempt.status,'NoTerminalPrefix')
        self.assertEqual(attempt.actual_state,attempt.staged)
        self.assertEqual(attempt.decoded.tail,(self.op,))
        self.assertEqual(attempt.actual_state.executed_word,r.inherited.executed_word)
        self.assertIsNone(attempt.next_request)

    def test_success_uses_original_decoder_and_retains_source(self):
        r=generate_request(self.op)
        attempt=arrive(r,self.first)
        self.assertEqual(attempt.decoded,decode(attempt.staged,(self.op,),(r.result,)))
        self.assertEqual(attempt.decoded.outputs[0].cell.beta,(self.op,))
        self.assertEqual(self.op.cell.endpoint.live.context,self.initial.live.context)
        self.assertEqual(attempt.next_request.result,tuple(NEG_ONE))

    def test_zero_or_forged_requirements_are_rejected(self):
        with self.assertRaises(ValueError):
            generate_request(self.op,(0,0,0,0))
        with self.assertRaises(ValueError):
            generate_request(replace(self.op,visible=(1,0,0,0)))

    def test_invalid_context_is_rejected(self):
        r=generate_request(self.op)
        for y in ([[1,1,0],[0,0,0],[0,0,0]],[[1,0,0],[0,1,0],[0,0,0]]):
            with self.assertRaises(ValueError):
                r.compatible(y)

    def test_outside_chart_is_not_promoted_as_a_certificate(self):
        attempt=arrive(generate_request(self.op),boundary(zero()))
        self.assertEqual(attempt.status,'OutsideCertifiedChart')
        self.assertIsNone(attempt.decoded)
        self.assertIsNone(attempt.next_request)

    def test_response_compatible_context_can_be_outside_certified_chart(self):
        r=generate_request(self.op)
        y=context([[0,0,0],[0,0,0],[0,0,1]])
        self.assertTrue(r.compatible(y))
        self.assertFalse(r.certifiable(y))
        self.assertEqual(arrive(r,y).status,'OutsideCertifiedChart')


if __name__=='__main__':
    unittest.main()
