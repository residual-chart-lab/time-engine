import unittest
from dataclasses import replace

from certified_cell_bridge import certify,promotion,seed_cells,CellWitness,construct_upper_boundary,UpperState,tuples
from future_existence_residual import boundary,zero,one_existence_witness,NEG_ONE


class CertifiedCellBridgeTests(unittest.TestCase):
    def test_only_verified_cells_are_promoted(self):
        cell=seed_cells()[0]
        with self.assertRaises(ValueError):
            promotion(cell.witness)
        forged=replace(cell,endpoint=tuple(tuple(x for x in row) for row in boundary(zero())))
        with self.assertRaises(ValueError):
            promotion(forged)

    def test_active_residue_and_ordered_record_both_survive(self):
        cell=seed_cells()[0]
        op=promotion(cell)
        self.assertEqual(op.full_residue.ordered_cell_record[2],cell.witness.beta)
        self.assertEqual(op.apply(one_existence_witness([list(row) for row in cell.endpoint])),NEG_ONE)
        state=UpperState(tuples(one_existence_witness([list(row) for row in cell.endpoint])))
        self.assertEqual(op.execute(state).accumulated,tuple(NEG_ONE))
        self.assertEqual(op.execute(op.execute(state)).accumulated,(1,0,0,0))

    def test_declared_upper_rule_reconstructs_a_single_boundary(self):
        ops=[promotion(c) for c in seed_cells()]
        built=construct_upper_boundary(boundary(zero()),ops)
        self.assertEqual(sum(built['coefficients']),1)
        self.assertEqual(built['boundary'],tuple(tuple(r) for r in boundary(zero())))


if __name__=='__main__':
    unittest.main()
