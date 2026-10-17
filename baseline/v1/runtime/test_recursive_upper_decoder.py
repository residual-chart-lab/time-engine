import unittest
from fractions import Fraction as Q

from recursive_upper_decoder import build_library,AffineLetter,ExecutionState,UpperState,tuples,NEG_ONE,decode,resume,certify_word,promote_word,kernel


class RecursiveUpperDecoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lib=build_library()
        cls.a=AffineLetter((1,0,0,0,0,0),lib)
        cls.b=AffineLetter((0,1,0,0,0,0),lib)
        cls.initial=ExecutionState(UpperState(tuples([[Q(3,2),0,0],[0,Q(1,4),0],[0,0,Q(-3,4)]])))

    def test_open_tail_is_not_eagerly_consumed(self):
        partial=decode(self.initial,(self.a,),[NEG_ONE])
        self.assertEqual(partial.state,self.initial)
        self.assertEqual(partial.stop,'NoTerminalPrefix')
        self.assertEqual(resume(partial,(self.b,)),decode(self.initial,(self.a,self.b),[NEG_ONE]))

    def test_consumed_state_is_not_reset(self):
        result=decode(self.initial,(self.a,self.b)*3,[NEG_ONE,NEG_ONE])
        self.assertEqual([len(op.cell.beta) for op in result.outputs],[2,4])

    def test_returning_cell_still_has_exact_history(self):
        cell=certify_word(self.initial,(self.a,self.b),NEG_ONE)
        macro=promote_word(cell)
        second=certify_word(cell.endpoint,(macro,macro),NEG_ONE)
        self.assertEqual(second.start.live,second.endpoint.live)
        self.assertNotEqual(second.start.executed_word,second.endpoint.executed_word)
        self.assertEqual(promote_word(second).level,3)

    def test_boundary_exhaustion_can_be_resumed(self):
        short=decode(self.initial,(self.a,self.b)*3,[NEG_ONE])
        self.assertEqual(short.stop,'BoundaryExhausted')
        self.assertEqual(resume(short,extra_boundaries=[NEG_ONE]),decode(self.initial,(self.a,self.b)*3,[NEG_ONE,NEG_ONE]))

    def test_nested_kernel_keeps_noncommuting_order(self):
        y=tuples([[Q(3,2),1,0],[1,Q(1,4),1],[0,1,Q(-3,4)]])
        self.assertNotEqual(kernel((self.a,self.b),y),kernel((self.b,self.a),y))


if __name__=='__main__':
    unittest.main()
