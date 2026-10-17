from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import math
from typing import Iterable, Sequence, Tuple

from .core import Sample, ThreePlusOneMLP


Matrix = Tuple[Tuple[float, ...], ...]
ComplexVector = Tuple[complex, ...]


_BRANCH_REAL = (
    2.0 / math.sqrt(6.0),
    -1.0 / math.sqrt(6.0),
    -1.0 / math.sqrt(6.0),
)

_BRANCH_IMAG = (
    0.0,
    1.0 / math.sqrt(2.0),
    -1.0 / math.sqrt(2.0),
)


@dataclass(frozen=True)
class TransverseEpochRecord:
    epoch: int
    mse: float
    singular_values: Tuple[float, float, float, float]
    unstable_dimension: int
    cumulative_singular_values: Tuple[float, float, float, float]

    @property
    def top_growth_rate(self) -> float:
        """One-epoch log singular growth rate."""
        return math.log(self.singular_values[0])

    @property
    def cumulative_top_gain(self) -> float:
        return self.cumulative_singular_values[0]


def _local_state(net: ThreePlusOneMLP, unit: int) -> tuple[float, ...]:
    return (
        float(net.output_w[unit + 1]),
        *tuple(float(v) for v in net.hidden_w[unit]),
    )


def transverse_residual(
    net: ThreePlusOneMLP,
    group: Sequence[int] = (0, 1, 2),
) -> ComplexVector:
    """
    Extract the actual hidden residual among a three-unit symmetric group.

    For local unit states

        q_i = (output weight, hidden bias, hidden x1 weight, hidden x2 weight),

    use the branch-aligned orthonormal basis

        c_R = (2,-1,-1)/sqrt(6)
        c_I = (0,1,-1)/sqrt(2).

    The complex four-channel residual is

        Z = sum_i (c_R[i] + i c_I[i]) q_i.

    Z=0 exactly when the three local states coincide (within their affine
    three-copy subspace).

    In this convention, the three singleton rays are at phases
    0, +2*pi/3 and -2*pi/3.
    """
    if len(group) != 3:
        raise ValueError("transverse_residual requires exactly three units")

    states = [_local_state(net, int(i)) for i in group]
    width = len(states[0])

    out = []
    for channel in range(width):
        re = sum(_BRANCH_REAL[i] * states[i][channel] for i in range(3))
        im = sum(_BRANCH_IMAG[i] * states[i][channel] for i in range(3))
        out.append(complex(re, im))
    return tuple(out)


def transverse_residual_norm(
    net: ThreePlusOneMLP,
    group: Sequence[int] = (0, 1, 2),
) -> float:
    return math.sqrt(sum(abs(z) ** 2 for z in transverse_residual(net, group)))


def add_transverse_seed(
    net: ThreePlusOneMLP,
    *,
    amplitude: float,
    phase: float,
    channel: int = 0,
    group: Sequence[int] = (0, 1, 2),
) -> None:
    """
    Add a mean-zero transverse perturbation to one local parameter channel.

    channel=0 is the hidden-to-output weight.
    channels 1..3 are hidden bias, x1 and x2 incoming weights.

    The three exact singleton rays are phase 0, +2*pi/3 and -2*pi/3.
    """
    if len(group) != 3:
        raise ValueError("add_transverse_seed requires exactly three units")
    if channel not in (0, 1, 2, 3):
        raise ValueError("channel must be 0, 1, 2, or 3")

    c = math.cos(float(phase))
    s = math.sin(float(phase))
    pattern = tuple(
        float(amplitude) * (_BRANCH_REAL[i] * c + _BRANCH_IMAG[i] * s)
        for i in range(3)
    )

    for pos, unit in enumerate(group):
        unit = int(unit)
        if channel == 0:
            net.output_w[unit + 1] += pattern[pos]
        else:
            net.hidden_w[unit][channel - 1] += pattern[pos]


def _identity(n: int) -> list[list[float]]:
    return [
        [1.0 if i == j else 0.0 for j in range(n)]
        for i in range(n)
    ]


def _matmul(a: Sequence[Sequence[float]], b: Sequence[Sequence[float]]) -> list[list[float]]:
    rows = len(a)
    inner = len(b)
    cols = len(b[0])
    return [
        [
            sum(float(a[i][k]) * float(b[k][j]) for k in range(inner))
            for j in range(cols)
        ]
        for i in range(rows)
    ]


def _transpose(a: Sequence[Sequence[float]]) -> list[list[float]]:
    return [list(row) for row in zip(*a)]


def _jacobi_eigenvalues_symmetric(
    matrix: Sequence[Sequence[float]],
    *,
    tolerance: float = 1e-14,
    max_iterations: int = 1000,
) -> list[float]:
    """
    Small dependency-free Jacobi eigensolver.

    Used only on the 4x4 positive-semidefinite matrix M^T M.
    """
    a = [list(map(float, row)) for row in matrix]
    n = len(a)

    for _ in range(max_iterations):
        p = 0
        q = 0
        largest = 0.0

        for i in range(n):
            for j in range(i + 1, n):
                value = abs(a[i][j])
                if value > largest:
                    largest = value
                    p, q = i, j

        if largest < tolerance:
            break

        app = a[p][p]
        aqq = a[q][q]
        apq = a[p][q]

        angle = 0.5 * math.atan2(2.0 * apq, aqq - app)
        c = math.cos(angle)
        s = math.sin(angle)

        for k in range(n):
            if k == p or k == q:
                continue
            akp = a[k][p]
            akq = a[k][q]
            a[k][p] = a[p][k] = c * akp - s * akq
            a[k][q] = a[q][k] = s * akp + c * akq

        a[p][p] = c * c * app - 2.0 * s * c * apq + s * s * aqq
        a[q][q] = s * s * app + 2.0 * s * c * apq + c * c * aqq
        a[p][q] = a[q][p] = 0.0

    return sorted((a[i][i] for i in range(n)), reverse=True)


def singular_values(matrix: Sequence[Sequence[float]]) -> tuple[float, ...]:
    ata = _matmul(_transpose(matrix), matrix)
    eigenvalues = _jacobi_eigenvalues_symmetric(ata)
    return tuple(math.sqrt(max(0.0, value)) for value in eigenvalues)


def sample_transverse_matrix(
    net: ThreePlusOneMLP,
    x: Sequence[float],
    target: float,
    *,
    representative_unit: int = 0,
) -> Matrix:
    """
    Exact first-order transverse map for one SGD sample on the S3 manifold.

    Let one member of the three-copy group have local state

        q = (a, w0, w1, w2),

    and let xhat=(1,x1,x2).

    For any mean-zero difference among the three copies, the first-order
    perturbation of the network output vanishes.  Therefore the output delta
    is shared by all three copies and the local perturbation evolves by the
    same 4x4 matrix K:

        [ 1                 eta*d*g*xhat^T                  ]
        [ eta*d*g*xhat      I + eta*d*a*g'*xhat*xhat^T     ]

    where g=h(1-h) and g'=g(1-2h).

    This is the exact linearization of the existing ThreePlusOneMLP update,
    not a separate reduced model.
    """
    if len(x) != net.inputs:
        raise ValueError(f"expected {net.inputs} inputs, got {len(x)}")
    if net.inputs != 2:
        raise ValueError("current transverse matrix implementation expects 2 inputs")

    h, y = net._forward(x)
    unit = int(representative_unit)
    hv = float(h[unit])
    output_delta = (float(target) - y) * y * (1.0 - y)
    a = float(net.output_w[unit + 1])

    xhat = (1.0, float(x[0]), float(x[1]))
    g = hv * (1.0 - hv)
    g_prime = g * (1.0 - 2.0 * hv)
    eta = float(net.learning_rate)

    out = _identity(4)

    for j in range(3):
        value = eta * output_delta * g * xhat[j]
        out[0][j + 1] = value
        out[j + 1][0] = value

    coeff = eta * output_delta * a * g_prime
    for i in range(3):
        for j in range(3):
            out[i + 1][j + 1] += coeff * xhat[i] * xhat[j]

    return tuple(tuple(row) for row in out)



def sample_transverse_quadratic_direction(
    net: ThreePlusOneMLP,
    x: Sequence[float],
    target: float,
    direction: Sequence[float],
    *,
    representative_unit: int = 0,
) -> tuple[float, float, float, float]:
    """
    Exact second-order C3-equivariant coefficient for one real transverse
    channel direction on the S3-symmetric manifold.

    Write the complex transverse local state as

        z = (z_a, z_w0, z_w1, z_w2)

    and s = xhat . z_w.  For the copy-space basis used by
    transverse_residual, pointwise products project according to

        P_E(u_i v_i) = (1/sqrt(6)) * conj(z_u) * conj(z_v).

    Therefore the one-sample local map

        z+ = K z + Q(conj(z), conj(z)) + O(|z|^3)

    has, along a real direction v, the exact quadratic vector

        Q_a = eta*d*g' * s^2 / (2 sqrt(6))

        Q_w = eta*d/sqrt(6)
              * [g' * v_a * s + (a*g''/2) * s^2] * xhat.

    Here g'=d g / d preactivation and g''=d^2 g / d preactivation^2.
    The output-delta perturbation starts at second order but contributes only
    at third order to the transverse projection, so the shared coarse d is
    exact at quadratic order.
    """
    if len(direction) != 4:
        raise ValueError("direction must have length 4")
    if len(x) != net.inputs or net.inputs != 2:
        raise ValueError("current quadratic direction implementation expects 2 inputs")

    h, y = net._forward(x)
    unit = int(representative_unit)
    hv = float(h[unit])
    d = (float(target) - y) * y * (1.0 - y)
    a = float(net.output_w[unit + 1])
    eta = float(net.learning_rate)

    g = hv * (1.0 - hv)
    g_prime = g * (1.0 - 2.0 * hv)
    g_second = g * (1.0 - 6.0 * hv + 6.0 * hv * hv)

    xhat = (1.0, float(x[0]), float(x[1]))
    va = float(direction[0])
    vw = tuple(float(direction[j + 1]) for j in range(3))
    s = sum(xhat[j] * vw[j] for j in range(3))
    copy_product = 1.0 / math.sqrt(6.0)

    qa = eta * d * copy_product * 0.5 * g_prime * s * s
    qw_coeff = eta * d * copy_product * (
        g_prime * va * s
        + 0.5 * a * g_second * s * s
    )

    return (
        float(qa),
        float(qw_coeff * xhat[0]),
        float(qw_coeff * xhat[1]),
        float(qw_coeff * xhat[2]),
    )


def epoch_transverse_quadratic_direction(
    net: ThreePlusOneMLP,
    samples: Iterable[Sample],
    direction: Sequence[float],
    *,
    representative_unit: int = 0,
) -> tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]:
    """
    Compose the exact linear and second-order transverse maps over one epoch
    along one real input direction.

    Returns (linear_response, quadratic_response), where

        z_out = linear_response * r
              + quadratic_response * r^2
              + O(r^3)

    for a phase-0 real seed z_in = r * direction.

    For composition F2(F1(z)), the quadratic term obeys

        q <- K q + Q(l, l)
        l <- K l,

    because every K is real in the chosen channel coordinates.
    """
    data = list(samples)
    if not data:
        raise ValueError("samples must not be empty")
    if len(direction) != 4:
        raise ValueError("direction must have length 4")

    work = deepcopy(net)
    linear = [float(v) for v in direction]
    quadratic = [0.0, 0.0, 0.0, 0.0]

    for x, target in data:
        step = sample_transverse_matrix(
            work,
            x,
            target,
            representative_unit=representative_unit,
        )
        local_q = sample_transverse_quadratic_direction(
            work,
            x,
            target,
            linear,
            representative_unit=representative_unit,
        )
        quadratic = [
            sum(step[i][j] * quadratic[j] for j in range(4))
            + local_q[i]
            for i in range(4)
        ]
        linear = [
            sum(step[i][j] * linear[j] for j in range(4))
            for i in range(4)
        ]
        work.train_one(x, target)

    return (
        tuple(float(v) for v in linear),
        tuple(float(v) for v in quadratic),
    )


def epoch_transverse_matrix(
    net: ThreePlusOneMLP,
    samples: Iterable[Sample],
    *,
    representative_unit: int = 0,
) -> Matrix:
    """
    Compose exact sample transverse matrices over one ordered training epoch.

    The input network is not mutated.
    """
    data = list(samples)
    if not data:
        raise ValueError("samples must not be empty")

    work = deepcopy(net)
    total = _identity(4)

    for x, target in data:
        step = sample_transverse_matrix(
            work,
            x,
            target,
            representative_unit=representative_unit,
        )
        total = _matmul(step, total)
        work.train_one(x, target)

    return tuple(tuple(row) for row in total)


def scan_transverse_growth(
    net: ThreePlusOneMLP,
    samples: Iterable[Sample],
    *,
    epochs: int,
    instability_tolerance: float = 1e-12,
) -> Tuple[TransverseEpochRecord, ...]:
    """
    Follow the exact S3-symmetric learning trajectory and measure transverse
    amplification at every epoch.

    The one-epoch map is M_e.  The cumulative tangent map is

        C_e = M_e M_{e-1} ... M_1.

    singular_values(M_e) measure instantaneous finite-time amplification.
    singular_values(C_e) measure accumulated amplification from initialization.
    """
    if epochs < 1:
        raise ValueError("epochs must be positive")

    data = list(samples)
    if not data:
        raise ValueError("samples must not be empty")

    work = deepcopy(net)
    cumulative = _identity(4)
    records = []

    for epoch in range(1, epochs + 1):
        matrix = epoch_transverse_matrix(work, data)
        values = singular_values(matrix)
        cumulative = _matmul(matrix, cumulative)
        cumulative_values = singular_values(cumulative)

        for x, target in data:
            work.train_one(x, target)

        unstable = sum(
            value > 1.0 + float(instability_tolerance)
            for value in values
        )

        records.append(
            TransverseEpochRecord(
                epoch=epoch,
                mse=work.mse(data),
                singular_values=(
                    float(values[0]),
                    float(values[1]),
                    float(values[2]),
                    float(values[3]),
                ),
                unstable_dimension=int(unstable),
                cumulative_singular_values=(
                    float(cumulative_values[0]),
                    float(cumulative_values[1]),
                    float(cumulative_values[2]),
                    float(cumulative_values[3]),
                ),
            )
        )

    return tuple(records)


@dataclass(frozen=True)
class TransverseAnisotropyResult:
    """
    Dominant-channel nonlinear transverse reduction over a fixed training course.

    input_direction:
        dominant right singular direction of the cumulative linear map
    output_direction:
        corresponding dominant left singular direction
    linear_gain:
        projected +1 Fourier harmonic divided by amplitude
    quadratic_coefficient:
        projected -2 Fourier harmonic divided by amplitude^2

    The -2 harmonic is the C3-equivariant quadratic anisotropy:
        z -> lambda z + nu conjugate(z)^2 + O(|z|^3).
    """

    epochs: int
    amplitude: float
    input_direction: Tuple[float, float, float, float]
    output_direction: Tuple[float, float, float, float]
    linear_gain: complex
    quadratic_coefficient: complex


def add_transverse_vector_seed(
    net: ThreePlusOneMLP,
    *,
    direction: Sequence[float],
    amplitude: float,
    phase: float,
    group: Sequence[int] = (0, 1, 2),
) -> None:
    """
    Add an arbitrary four-channel complex transverse residual

        Z = amplitude * exp(i*phase) * direction

    where direction is real in parameter-channel space.
    """
    if len(group) != 3:
        raise ValueError("add_transverse_vector_seed requires exactly three units")
    if len(direction) != 4:
        raise ValueError("direction must contain four channel values")

    c = math.cos(float(phase))
    s = math.sin(float(phase))
    values = [float(amplitude) * float(v) for v in direction]

    for pos, unit in enumerate(group):
        unit = int(unit)
        copy_factor = _BRANCH_REAL[pos] * c + _BRANCH_IMAG[pos] * s

        for channel, value in enumerate(values):
            delta = value * copy_factor
            if channel == 0:
                net.output_w[unit + 1] += delta
            else:
                net.hidden_w[unit][channel - 1] += delta


def cumulative_transverse_matrix(
    net: ThreePlusOneMLP,
    samples: Iterable[Sample],
    *,
    epochs: int,
) -> Matrix:
    """Compose the exact linear transverse maps over a fixed training course."""
    if epochs < 1:
        raise ValueError("epochs must be positive")

    data = list(samples)
    if not data:
        raise ValueError("samples must not be empty")

    work = deepcopy(net)
    cumulative = _identity(4)

    for _ in range(epochs):
        matrix = epoch_transverse_matrix(work, data)
        cumulative = _matmul(matrix, cumulative)
        for x, target in data:
            work.train_one(x, target)

    return tuple(tuple(row) for row in cumulative)


def _matvec(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
) -> list[float]:
    return [
        sum(float(row[j]) * float(vector[j]) for j in range(len(vector)))
        for row in matrix
    ]


def _normalize_real(vector: Sequence[float]) -> list[float]:
    n2 = sum(float(v) * float(v) for v in vector)
    if n2 <= 0.0:
        raise ValueError("cannot normalize the zero vector")
    scale = 1.0 / math.sqrt(n2)
    return [float(v) * scale for v in vector]


def dominant_singular_pair(
    matrix: Sequence[Sequence[float]],
    *,
    iterations: int = 200,
) -> tuple[float, tuple[float, ...], tuple[float, ...]]:
    """
    Dependency-free dominant singular triplet (sigma, left, right).

    The sign convention is fixed by requiring the largest-magnitude component
    of the right singular vector to be positive.
    """
    ata = _matmul(_transpose(matrix), matrix)
    v = _normalize_real((1.0, 0.5, -0.25, 0.75))

    for _ in range(iterations):
        next_v = _matvec(ata, v)
        v = _normalize_real(next_v)

    pivot = max(range(len(v)), key=lambda i: abs(v[i]))
    if v[pivot] < 0.0:
        v = [-x for x in v]

    mv = _matvec(matrix, v)
    sigma = math.sqrt(sum(x * x for x in mv))
    if sigma == 0.0:
        raise ValueError("dominant singular value is zero")

    u = [x / sigma for x in mv]
    return sigma, tuple(u), tuple(v)


def training_harmonic_vector(
    net: ThreePlusOneMLP,
    samples: Iterable[Sample],
    *,
    epochs: int,
    input_direction: Sequence[float],
    amplitude: float,
    harmonic: int,
    phase_samples: int = 12,
) -> ComplexVector:
    """
    Vector-valued copy-space Fourier coefficient of the actual nonlinear
    training map.
    """
    if epochs < 1:
        raise ValueError("epochs must be positive")
    if amplitude <= 0.0:
        raise ValueError("amplitude must be positive")
    if phase_samples < 6 or phase_samples % 3 != 0:
        raise ValueError("phase_samples must be a multiple of 3 and at least 6")
    if len(input_direction) != 4:
        raise ValueError("input_direction must have length 4")

    data = list(samples)
    if not data:
        raise ValueError("samples must not be empty")

    total = [0j, 0j, 0j, 0j]

    for sample_index in range(phase_samples):
        phase = 2.0 * math.pi * sample_index / phase_samples
        work = deepcopy(net)
        add_transverse_vector_seed(
            work,
            direction=input_direction,
            amplitude=amplitude,
            phase=phase,
        )

        for _ in range(epochs):
            for x, target in data:
                work.train_one(x, target)

        factor = complex(
            math.cos(-harmonic * phase),
            math.sin(-harmonic * phase),
        )
        residual = transverse_residual(work)

        for channel in range(4):
            total[channel] += residual[channel] * factor

    return tuple(value / phase_samples for value in total)


def projected_training_harmonic(
    net: ThreePlusOneMLP,
    samples: Iterable[Sample],
    *,
    epochs: int,
    input_direction: Sequence[float],
    output_direction: Sequence[float],
    amplitude: float,
    harmonic: int,
    phase_samples: int = 12,
) -> complex:
    """
    Fourier coefficient of the actual nonlinear training map.

    If the projected map has

        y(theta)
          = lambda * eps * exp(i theta)
          + nu * eps^2 * exp(-2 i theta)
          + ...

    then harmonic=1 extracts the linear term and harmonic=-2 extracts the
    C3-equivariant quadratic anisotropy.
    """
    if epochs < 1:
        raise ValueError("epochs must be positive")
    if amplitude <= 0.0:
        raise ValueError("amplitude must be positive")
    if phase_samples < 6 or phase_samples % 3 != 0:
        raise ValueError("phase_samples must be a multiple of 3 and at least 6")
    if len(input_direction) != 4 or len(output_direction) != 4:
        raise ValueError("input_direction and output_direction must have length 4")

    vector = training_harmonic_vector(
        net,
        samples,
        epochs=epochs,
        input_direction=input_direction,
        amplitude=amplitude,
        harmonic=harmonic,
        phase_samples=phase_samples,
    )
    return sum(
        float(output_direction[i]) * vector[i]
        for i in range(4)
    )


def dominant_course_anisotropy(
    net: ThreePlusOneMLP,
    samples: Iterable[Sample],
    *,
    epochs: int,
    amplitude: float = 1e-4,
    phase_samples: int = 12,
) -> TransverseAnisotropyResult:
    """
    Reduce the actual fixed-course nonlinear map onto its dominant linear
    channel and extract the +1 and -2 copy-space Fourier harmonics.
    """
    cumulative = cumulative_transverse_matrix(
        net,
        samples,
        epochs=epochs,
    )
    _, output_direction, input_direction = dominant_singular_pair(cumulative)

    linear = projected_training_harmonic(
        net,
        samples,
        epochs=epochs,
        input_direction=input_direction,
        output_direction=output_direction,
        amplitude=amplitude,
        harmonic=1,
        phase_samples=phase_samples,
    ) / amplitude

    quadratic = projected_training_harmonic(
        net,
        samples,
        epochs=epochs,
        input_direction=input_direction,
        output_direction=output_direction,
        amplitude=amplitude,
        harmonic=-2,
        phase_samples=phase_samples,
    ) / (amplitude * amplitude)

    return TransverseAnisotropyResult(
        epochs=epochs,
        amplitude=float(amplitude),
        input_direction=(
            float(input_direction[0]),
            float(input_direction[1]),
            float(input_direction[2]),
            float(input_direction[3]),
        ),
        output_direction=(
            float(output_direction[0]),
            float(output_direction[1]),
            float(output_direction[2]),
            float(output_direction[3]),
        ),
        linear_gain=linear,
        quadratic_coefficient=quadratic,
    )


def projected_course_phase(
    net: ThreePlusOneMLP,
    samples: Iterable[Sample],
    *,
    epochs: int,
    input_direction: Sequence[float],
    output_direction: Sequence[float],
    amplitude: float,
    phase: float,
) -> float:
    """Projected output phase after a fixed nonlinear training course."""
    data = list(samples)
    work = deepcopy(net)
    add_transverse_vector_seed(
        work,
        direction=input_direction,
        amplitude=amplitude,
        phase=phase,
    )

    for _ in range(epochs):
        for x, target in data:
            work.train_one(x, target)

    residual = transverse_residual(work)
    projected = sum(
        float(output_direction[i]) * residual[i]
        for i in range(4)
    )
    return math.atan2(projected.imag, projected.real)


@dataclass(frozen=True)
class SelectorPersistenceRecord:
    """
    Finite-course branch-lock diagnostic for one transverse seed amplitude.

    phase_contraction:
        derivative d theta_out / d theta_in at the phase-0 singleton ray,
        estimated by a centered finite difference.
    cumulative_selector_action:
        -log(abs(phase_contraction))/3.  In the reduced phase law
        dtheta/dt = -A(t) sin(3 theta), this is the accumulated selector
        action.
    probe_lock_error:
        angular distance of a finite off-ray probe from the phase-0 singleton
        ray after the indicated number of epochs.
    """

    epoch: int
    mse: float
    linear_gain: float
    phase_contraction: float
    cumulative_selector_action: float
    probe_phase: float
    probe_output_phase: float
    probe_lock_error: float
    projected_residual_amplitude: float


def _wrapped_angle(value: float) -> float:
    return math.atan2(math.sin(float(value)), math.cos(float(value)))


def _projected_residual(
    net: ThreePlusOneMLP,
    output_direction: Sequence[float],
) -> complex:
    residual = transverse_residual(net)
    return sum(
        float(output_direction[i]) * residual[i]
        for i in range(4)
    )



def branch_ray_phase_derivative(
    net: ThreePlusOneMLP,
    samples: Iterable[Sample],
    *,
    singled_unit: int = 0,
    pair_unit: int = 1,
    group: Sequence[int] = (0, 1, 2),
) -> float:
    """
    Exact infinitesimal one-epoch phase derivative on a reflection-fixed
    singleton branch ray.

    On the phase-0 ray, one unit is singled out while the other two are equal.
    An infinitesimal copy-space rotation splits the equal pair antisymmetrically.
    Because that perturbation has zero first-order network-output effect, it is
    transported by the same 4x4 local tangent matrix as any zero-sum copy
    perturbation, evaluated at one member of the equal pair.

    Let R be the real transverse residual vector before the epoch and R+ after
    the ordinary nonlinear epoch. Let M_pair be the exact tangent map for the
    antisymmetric pair-splitting mode. Then

        dZ_in/dtheta = i R

    and

        dZ_out/dtheta = i M_pair R.

    Projecting onto the outgoing branch ray gives the exact phase derivative

        rho = <R+, M_pair R> / ||R+||^2.

    This removes finite-angle and finite-radius approximations from the local
    selector-action measurement.
    """
    data = list(samples)
    if not data:
        raise ValueError("samples must not be empty")
    if len(group) != 3:
        raise ValueError("group must contain exactly three units")

    singled_unit = int(singled_unit)
    pair_unit = int(pair_unit)
    if singled_unit not in group or pair_unit not in group:
        raise ValueError("singled_unit and pair_unit must belong to group")

    before = transverse_residual(net, group)
    if max(abs(z.imag) for z in before) > 1e-9:
        raise ValueError("branch_ray_phase_derivative requires a phase-0 real residual")
    radial_before = [float(z.real) for z in before]

    pair_map = epoch_transverse_matrix(
        net,
        data,
        representative_unit=pair_unit,
    )
    angular_after = _matvec(pair_map, radial_before)

    work = deepcopy(net)
    for x, target in data:
        work.train_one(x, target)
    after = transverse_residual(work, group)
    if max(abs(z.imag) for z in after) > 1e-9:
        raise ValueError("ordinary epoch left the reflection-fixed branch ray")
    radial_after = [float(z.real) for z in after]

    denom = sum(value * value for value in radial_after)
    if denom == 0.0:
        raise ValueError("outgoing branch residual vanished")

    return float(
        sum(radial_after[i] * angular_after[i] for i in range(4))
        / denom
    )


def scan_selector_persistence(
    net: ThreePlusOneMLP,
    samples: Iterable[Sample],
    *,
    checkpoints: Sequence[int],
    amplitude: float = 0.1,
    phase_delta: float = 1e-4,
    probe_phase: float = math.pi / 6.0,
    input_direction: Sequence[float] = (1.0, 0.0, 0.0, 0.0),
) -> Tuple[SelectorPersistenceRecord, ...]:
    """
    Measure whether threefold branch sorting continues after task convergence.

    The phase-0 singleton ray is probed with two nearby histories at
    +/- phase_delta.  Their output phase separation gives the finite-course
    phase derivative rho_N.  Define

        A_N = -(1/3) log |rho_N|.

    For the ideal reduced phase equation

        d theta / dt = -a(t) sin(3 theta),

    exact asymptotic locking requires A_N -> infinity.  A finite limiting
    A_N leaves a nonzero phase offset.

    A third finite probe, by default theta=pi/6, tracks actual movement toward
    the singleton ray.  All three nonlinear histories are evolved under the
    unmodified training rule.

    The projection direction at each checkpoint is the normalized linear
    response of the cumulative transverse tangent map to input_direction.
    """
    data = list(samples)
    if not data:
        raise ValueError("samples must not be empty")
    if amplitude <= 0.0:
        raise ValueError("amplitude must be positive")
    if phase_delta <= 0.0:
        raise ValueError("phase_delta must be positive")
    if len(input_direction) != 4:
        raise ValueError("input_direction must have length 4")

    requested = sorted({int(epoch) for epoch in checkpoints})
    if not requested or requested[0] < 1:
        raise ValueError("checkpoints must contain positive epochs")

    base = deepcopy(net)
    plus = deepcopy(net)
    minus = deepcopy(net)
    probe = deepcopy(net)

    add_transverse_vector_seed(
        plus,
        direction=input_direction,
        amplitude=amplitude,
        phase=phase_delta,
    )
    add_transverse_vector_seed(
        minus,
        direction=input_direction,
        amplitude=amplitude,
        phase=-phase_delta,
    )
    add_transverse_vector_seed(
        probe,
        direction=input_direction,
        amplitude=amplitude,
        phase=probe_phase,
    )

    cumulative = _identity(4)
    records = []
    checkpoint_index = 0
    final_epoch = requested[-1]

    for epoch in range(1, final_epoch + 1):
        for x, target in data:
            step = sample_transverse_matrix(base, x, target)
            cumulative = _matmul(step, cumulative)

            base.train_one(x, target)
            plus.train_one(x, target)
            minus.train_one(x, target)
            probe.train_one(x, target)

        if epoch != requested[checkpoint_index]:
            continue

        response = _matvec(cumulative, input_direction)
        linear_gain = math.sqrt(sum(value * value for value in response))
        if linear_gain == 0.0:
            raise ValueError("linear response vanished at a requested checkpoint")
        output_direction = tuple(value / linear_gain for value in response)

        z_plus = _projected_residual(plus, output_direction)
        z_minus = _projected_residual(minus, output_direction)
        z_probe = _projected_residual(probe, output_direction)

        phase_plus = math.atan2(z_plus.imag, z_plus.real)
        phase_minus = math.atan2(z_minus.imag, z_minus.real)
        output_probe_phase = math.atan2(z_probe.imag, z_probe.real)

        phase_contraction = (
            _wrapped_angle(phase_plus - phase_minus)
            / (2.0 * phase_delta)
        )

        magnitude = abs(phase_contraction)
        if magnitude == 0.0:
            selector_action = math.inf
        else:
            selector_action = -math.log(magnitude) / 3.0

        records.append(
            SelectorPersistenceRecord(
                epoch=epoch,
                mse=base.mse(data),
                linear_gain=float(linear_gain),
                phase_contraction=float(phase_contraction),
                cumulative_selector_action=float(selector_action),
                probe_phase=float(probe_phase),
                probe_output_phase=float(output_probe_phase),
                probe_lock_error=abs(_wrapped_angle(output_probe_phase)),
                projected_residual_amplitude=float(abs(z_probe)),
            )
        )

        checkpoint_index += 1
        if checkpoint_index == len(requested):
            break

    return tuple(records)
