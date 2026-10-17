import math
import unittest
from copy import deepcopy

from threeplusone import ThreePlusOneMLP, centered_singleton_seed, xnor
from threeplusone.transverse import (
    add_transverse_seed,
    epoch_transverse_matrix,
    scan_transverse_growth,
    transverse_residual,
    transverse_residual_norm,
)


class ActualXNORTransverseTests(unittest.TestCase):
    def centered_net(self):
        return ThreePlusOneMLP(
            epsilon=1.0,
            seed_pattern=centered_singleton_seed(4),
        )

    def test_centered_three_copy_group_has_zero_transverse_residual(self):
        net = self.centered_net()
        self.assertEqual(transverse_residual(net), (0j, 0j, 0j, 0j))
        self.assertEqual(transverse_residual_norm(net), 0.0)

    def test_branch_aligned_seed_has_requested_phase_and_amplitude(self):
        phases = (0.0, 2.0 * math.pi / 3.0, -2.0 * math.pi / 3.0)

        for phase in phases:
            net = self.centered_net()
            add_transverse_seed(
                net,
                amplitude=1e-4,
                phase=phase,
                channel=0,
            )
            residual = transverse_residual(net)

            self.assertAlmostEqual(abs(residual[0]), 1e-4, places=14)
            self.assertAlmostEqual(abs(residual[1]), 0.0, places=14)
            self.assertAlmostEqual(abs(residual[2]), 0.0, places=14)
            self.assertAlmostEqual(abs(residual[3]), 0.0, places=14)

            measured = math.atan2(residual[0].imag, residual[0].real)
            error = math.atan2(
                math.sin(measured - phase),
                math.cos(measured - phase),
            )
            self.assertAlmostEqual(error, 0.0, places=12)

    def test_exact_epoch_tangent_matches_finite_difference(self):
        net = self.centered_net()
        data = xnor()
        matrix = epoch_transverse_matrix(net, data)

        epsilon = 1e-7

        for channel in range(4):
            perturbed = deepcopy(net)
            add_transverse_seed(
                perturbed,
                amplitude=epsilon,
                phase=0.0,
                channel=channel,
            )

            for x, target in data:
                perturbed.train_one(x, target)

            residual = transverse_residual(perturbed)

            for out_channel in range(4):
                measured = residual[out_channel].real / epsilon
                self.assertAlmostEqual(
                    measured,
                    matrix[out_channel][channel],
                    places=7,
                )
                self.assertAlmostEqual(
                    residual[out_channel].imag,
                    0.0,
                    places=13,
                )

    def test_centered_xnor_is_transversely_unstable_while_exact_symmetry_survives(self):
        net = self.centered_net()
        records = scan_transverse_growth(
            net,
            xnor(),
            epochs=728,
        )

        # Exact zero residual remains exactly zero on the baseline trajectory.
        work = self.centered_net()
        for x, target in xnor():
            work.train_one(x, target)
        self.assertEqual(transverse_residual_norm(work), 0.0)

        # But the tangent dynamics around that invariant manifold expands
        # nonzero residuals in at least one transverse channel at every epoch.
        self.assertTrue(
            all(record.singular_values[0] > 1.0 for record in records)
        )

        # The number of instantaneously expanding channel directions follows
        # the observed 2 -> 3 -> 2 -> 1 sequence.
        self.assertEqual(records[0].unstable_dimension, 2)      # epoch 1
        self.assertEqual(records[7].unstable_dimension, 2)      # epoch 8
        self.assertEqual(records[8].unstable_dimension, 3)      # epoch 9
        self.assertEqual(records[130].unstable_dimension, 3)    # epoch 131
        self.assertEqual(records[131].unstable_dimension, 2)    # epoch 132
        self.assertEqual(records[557].unstable_dimension, 2)    # epoch 558
        self.assertEqual(records[558].unstable_dimension, 1)    # epoch 559
        self.assertEqual(records[-1].unstable_dimension, 1)     # epoch 728

        self.assertAlmostEqual(
            records[-1].cumulative_top_gain,
            34.7030447,
            places=5,
        )

    def test_tiny_real_history_is_amplified_by_actual_xnor_training(self):
        net = self.centered_net()
        add_transverse_seed(
            net,
            amplitude=1e-6,
            phase=0.0,
            channel=0,
        )

        initial = transverse_residual_norm(net)

        for _ in range(728):
            for x, target in xnor():
                net.train_one(x, target)

        final = transverse_residual_norm(net)

        self.assertGreater(final / initial, 15.0)
        self.assertLess(final / initial, 15.3)


if __name__ == "__main__":
    unittest.main()
