import math
import unittest

from threeplusone import (
    ThreePlusOneMLP,
    centered_singleton_seed,
    scan_selector_persistence,
    branch_ray_phase_derivative,
    add_transverse_vector_seed,
    transverse_residual,
    xnor,
)


def centered_net() -> ThreePlusOneMLP:
    return ThreePlusOneMLP(
        epsilon=1.0,
        seed_pattern=centered_singleton_seed(4),
    )



C_R = (
    2.0 / math.sqrt(6.0),
    -1.0 / math.sqrt(6.0),
    -1.0 / math.sqrt(6.0),
)
C_I = (
    0.0,
    1.0 / math.sqrt(2.0),
    -1.0 / math.sqrt(2.0),
)


def _local_state(net, unit):
    return [
        net.output_w[unit + 1],
        net.hidden_w[unit][0],
        net.hidden_w[unit][1],
        net.hidden_w[unit][2],
    ]


def _set_local_state(net, unit, q):
    net.output_w[unit + 1] = q[0]
    net.hidden_w[unit][0] = q[1]
    net.hidden_w[unit][1] = q[2]
    net.hidden_w[unit][2] = q[3]


def _rotate_copy_residual(net, angle):
    states = [_local_state(net, i) for i in range(3)]
    means = [
        sum(states[i][j] for i in range(3)) / 3.0
        for j in range(4)
    ]
    cc = math.cos(angle)
    ss = math.sin(angle)

    rotated = [[0.0] * 4 for _ in range(3)]
    for j in range(4):
        re = sum(C_R[i] * states[i][j] for i in range(3))
        im = sum(C_I[i] * states[i][j] for i in range(3))
        re2 = cc * re - ss * im
        im2 = ss * re + cc * im
        for i in range(3):
            rotated[i][j] = means[j] + C_R[i] * re2 + C_I[i] * im2

    for i in range(3):
        _set_local_state(net, i, rotated[i])


def _finite_phase_derivative(net, delta=1e-5, epochs=1):
    import copy

    center = copy.deepcopy(net)
    plus = copy.deepcopy(net)
    minus = copy.deepcopy(net)
    _rotate_copy_residual(plus, +delta)
    _rotate_copy_residual(minus, -delta)

    for _ in range(epochs):
        for x, target in xnor():
            center.train_one(x, target)
            plus.train_one(x, target)
            minus.train_one(x, target)

    z0 = transverse_residual(center)
    radial = [z.real for z in z0]
    norm = math.sqrt(sum(v * v for v in radial))
    direction = [v / norm for v in radial]

    def phase(work):
        z = transverse_residual(work)
        projected = sum(direction[j] * z[j] for j in range(4))
        return math.atan2(projected.imag, projected.real)

    return (phase(plus) - phase(minus)) / (2.0 * delta)


class SelectorPersistenceTests(unittest.TestCase):
    def test_exact_branch_ray_phase_derivative_matches_finite_rotation(self):
        net = centered_net()
        add_transverse_vector_seed(
            net,
            direction=(1.0, 0.0, 0.0, 0.0),
            amplitude=0.1,
            phase=0.0,
        )
        for _ in range(1000):
            for x, target in xnor():
                net.train_one(x, target)

        exact = branch_ray_phase_derivative(net, xnor())
        finite = _finite_phase_derivative(net)

        self.assertAlmostEqual(exact, finite, places=8)

    def test_invisible_phase_component_returns_on_next_epoch(self):
        import copy
        from threeplusone.transverse import epoch_transverse_matrix

        net = centered_net()
        add_transverse_vector_seed(net, direction=(1, 0, 0, 0),
                                   amplitude=0.1, phase=0)
        for _ in range(728):
            for x, target in xnor():
                net.train_one(x, target)
        initial = copy.deepcopy(net)

        def radial(work):
            return [z.real for z in transverse_residual(work)]

        def apply(matrix, vector):
            return [sum(a*b for a, b in zip(row, vector)) for row in matrix]

        def readout(radius, vector):
            return sum(a*b for a, b in zip(radius, vector))/sum(a*a for a in radius)

        radius0 = radial(net)
        matrix0 = epoch_transverse_matrix(net, xnor(), representative_unit=1)
        tangent1 = apply(matrix0, radius0)
        for x, target in xnor():
            net.train_one(x, target)
        radius1 = radial(net)
        rho0 = readout(radius1, tangent1)
        hidden = [a-rho0*b for a, b in zip(tangent1, radius1)]
        self.assertAlmostEqual(readout(radius1, hidden), 0, places=14)

        matrix1 = epoch_transverse_matrix(net, xnor(), representative_unit=1)
        for x, target in xnor():
            net.train_one(x, target)
        radius2 = radial(net)
        rho1 = readout(radius2, apply(matrix1, radius1))
        full = readout(radius2, apply(matrix1, tangent1))
        returned = readout(radius2, apply(matrix1, hidden))
        self.assertGreater(returned, 1e-6)
        self.assertAlmostEqual(full-rho0*rho1, returned, places=14)
        self.assertAlmostEqual(full, _finite_phase_derivative(
            initial, delta=1e-4, epochs=2), places=8)

    def test_selector_action_continues_after_task_target_is_reached(self):
        records = scan_selector_persistence(
            centered_net(),
            xnor(),
            checkpoints=(728, 5000, 10000, 100000),
            amplitude=0.1,
            phase_delta=1e-4,
            probe_phase=math.pi / 6.0,
        )

        at_728, at_5000, at_10000, at_100000 = records

        # The ordinary task target is already reached at epoch 728.
        self.assertLessEqual(at_728.mse, 0.01001)
        self.assertLess(at_5000.mse, at_728.mse)
        self.assertLess(at_10000.mse, at_5000.mse)
        self.assertLess(at_100000.mse, at_10000.mse)

        # Nevertheless the branch-ray phase derivative keeps contracting.
        self.assertGreater(at_728.phase_contraction, at_5000.phase_contraction)
        self.assertGreater(at_5000.phase_contraction, at_10000.phase_contraction)
        self.assertGreater(at_10000.phase_contraction, at_100000.phase_contraction)

        # Therefore cumulative selector action is still increasing after the
        # task is already conventionally converged.
        self.assertLess(
            at_728.cumulative_selector_action,
            at_5000.cumulative_selector_action,
        )
        self.assertLess(
            at_5000.cumulative_selector_action,
            at_10000.cumulative_selector_action,
        )
        self.assertLess(
            at_10000.cumulative_selector_action,
            at_100000.cumulative_selector_action,
        )

        # A finite off-ray history keeps moving toward the singleton ray.
        initial_error = math.pi / 6.0
        self.assertLess(at_728.probe_lock_error, initial_error)
        self.assertLess(at_5000.probe_lock_error, at_728.probe_lock_error)
        self.assertLess(at_10000.probe_lock_error, at_5000.probe_lock_error)
        self.assertLess(at_100000.probe_lock_error, at_10000.probe_lock_error)

        # The retained residual has not been erased while this sorting occurs.
        self.assertGreater(
            at_5000.projected_residual_amplitude,
            at_728.projected_residual_amplitude,
        )
        self.assertGreater(
            at_10000.projected_residual_amplitude,
            at_5000.projected_residual_amplitude,
        )
        self.assertGreater(
            at_100000.projected_residual_amplitude,
            at_10000.projected_residual_amplitude,
        )

        # Deterministic reference values for the current implementation.
        self.assertAlmostEqual(
            at_728.cumulative_selector_action,
            0.0410643,
            places=5,
        )
        self.assertAlmostEqual(
            at_5000.cumulative_selector_action,
            0.0765029,
            places=5,
        )
        self.assertAlmostEqual(
            at_10000.cumulative_selector_action,
            0.0839642,
            places=5,
        )
        self.assertAlmostEqual(
            at_100000.cumulative_selector_action,
            0.1049100,
            places=5,
        )
        self.assertAlmostEqual(at_728.probe_output_phase, 0.4829183, places=5)
        self.assertAlmostEqual(at_5000.probe_output_phase, 0.4498922, places=5)
        self.assertAlmostEqual(at_10000.probe_output_phase, 0.4431109, places=5)
        self.assertAlmostEqual(at_100000.probe_output_phase, 0.4245341, places=5)


if __name__ == "__main__":
    unittest.main()
