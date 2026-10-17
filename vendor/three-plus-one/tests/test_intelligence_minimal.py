import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"examples"))
from xnor_discrimination_loop import run as discrimination_run
from xnor_intelligence_minimal import course


class IntelligenceMinimalTests(unittest.TestCase):
    def test_kept_difference_changes_input_relations(self):
        result = discrimination_run()
        guard = result["representative_effect_guard"]
        self.assertGreater(guard["fixed_phase_relative_residual"], .03)
        self.assertGreater(guard["hidden_activation_relative_residual"], .01)
        end = result["records"][-1]
        self.assertLess(end["comparisons"]["fixed_phase_change"]["restore"]["affine_residual_relative"],1e-9)
        self.assertLess(end["gain_null_checks"]["fixed_phase_change"]["affine_residual_relative"],1e-9)

    def test_nonzero_memory_can_be_blind_to_discrimination(self):
        end = course(728,(0,1,2,3))["records"][-1]
        self.assertGreater(end["hidden_norm"],.001)
        self.assertAlmostEqual(end["hidden_norm"],end["blind_control_hidden_norm"],places=10)
        self.assertLess(end["blind_control_effect"],1e-8)
        self.assertLess(end["condition_identity_error"],1e-9)


if __name__ == "__main__":
    unittest.main()
