from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional, Tuple


@dataclass(frozen=True)
class NextOneParams:
    """
    Minimal history-seeded C3 branch-selection model.

    The relative rotor carries the already established dual-frame dynamics.
    A complex branch variable z lives in the two-dimensional transverse plane.

    Its equation is

        z_dot =
            (mu(E) + i * transport * phi_dot) z
            + anisotropy * conjugate(z)^2
            - saturation * |z|^2 z

    with

        mu(E) = growth_gain * (critical_energy - E).

    By default, critical_energy is the exact rotor barrier 2*kappa.

    This barrier-coupled growth law is a candidate closure, not a theorem of
    the original XNOR system.  What *is* structural is the C3-equivariant
    branch normal form and the fact that z=0 cannot select a branch by itself.
    """

    relative_inertia: float = 0.5
    kappa: float = 1.0
    damping: float = 0.05
    growth_gain: float = 0.5
    transport: float = 0.3
    anisotropy: float = 0.4
    saturation: float = 1.0
    critical_energy: Optional[float] = None

    def __post_init__(self) -> None:
        if self.relative_inertia <= 0.0:
            raise ValueError("relative_inertia must be positive")
        if self.kappa < 0.0:
            raise ValueError("kappa must be non-negative")
        if self.damping < 0.0:
            raise ValueError("damping must be non-negative")
        if self.growth_gain < 0.0:
            raise ValueError("growth_gain must be non-negative")
        if self.anisotropy < 0.0:
            raise ValueError("anisotropy must be non-negative")
        if self.saturation <= 0.0:
            raise ValueError("saturation must be positive")

    @property
    def barrier_energy(self) -> float:
        return 2.0 * self.kappa

    @property
    def branch_critical_energy(self) -> float:
        if self.critical_energy is None:
            return self.barrier_energy
        return float(self.critical_energy)


@dataclass(frozen=True)
class NextOneState:
    """
    Reduced relative-rotor state plus hidden branch residual.

    phi:
        unwrapped relative phase of the two tetrahedral frames
    ell:
        relative angular momentum
    z_re, z_im:
        hidden transverse branch residual z in the C3 representation
    """

    phi: float
    ell: float
    z_re: float
    z_im: float

    @property
    def z(self) -> complex:
        return complex(self.z_re, self.z_im)


def rotor_energy(state: NextOneState, params: NextOneParams) -> float:
    return (
        state.ell * state.ell / (2.0 * params.relative_inertia)
        + params.kappa * (1.0 - math.cos(3.0 * state.phi))
    )


def angular_velocity(state: NextOneState, params: NextOneParams) -> float:
    return state.ell / params.relative_inertia


def growth_rate(state: NextOneState, params: NextOneParams) -> float:
    return params.growth_gain * (
        params.branch_critical_energy - rotor_energy(state, params)
    )


def branch_rhs(
    z: complex,
    *,
    mu: float,
    anisotropy: float,
    saturation: float,
) -> complex:
    """
    Lowest-degree real-reflection-symmetric C3-equivariant branch field:

        z_dot = mu z + nu conjugate(z)^2 - beta |z|^2 z.

    Under z -> omega z, omega^3=1,

        F(omega z) = omega F(z).

    Consequently F(0)=0.  Exact C3 symmetry cannot select a branch
    deterministically from z=0.
    """
    return (
        float(mu) * z
        + float(anisotropy) * (z.conjugate() ** 2)
        - float(saturation) * (abs(z) ** 2) * z
    )


def derivatives(
    state: NextOneState,
    params: NextOneParams,
) -> Tuple[float, float, float, float]:
    """
    Coupled damped rotor + history-seeded branch dynamics.

    The rotor obeys

        phi_dot = ell / I_r
        ell_dot = -3 kappa sin(3 phi) - gamma phi_dot

    so

        dE/dt = -gamma * phi_dot^2 <= 0.

    The branch residual is transported by the signed angular velocity and then
    acted on by the minimal C3 branch normal form.
    """
    omega = angular_velocity(state, params)
    mu = growth_rate(state, params)
    z = state.z

    dz = (
        complex(mu, params.transport * omega) * z
        + params.anisotropy * (z.conjugate() ** 2)
        - params.saturation * (abs(z) ** 2) * z
    )

    return (
        omega,
        -3.0 * params.kappa * math.sin(3.0 * state.phi)
        - params.damping * omega,
        dz.real,
        dz.imag,
    )


def energy_dissipation_rate(
    state: NextOneState,
    params: NextOneParams,
) -> float:
    """Exact continuous-time rotor energy derivative."""
    omega = angular_velocity(state, params)
    return -params.damping * omega * omega


def rk4_step(
    state: NextOneState,
    params: NextOneParams,
    dt: float,
) -> NextOneState:
    dt = float(dt)
    if dt <= 0.0:
        raise ValueError("dt must be positive")

    y = (
        state.phi,
        state.ell,
        state.z_re,
        state.z_im,
    )

    def add_scaled(
        base: Tuple[float, float, float, float],
        delta: Tuple[float, float, float, float],
        scale: float,
    ) -> NextOneState:
        return NextOneState(
            phi=base[0] + scale * delta[0],
            ell=base[1] + scale * delta[1],
            z_re=base[2] + scale * delta[2],
            z_im=base[3] + scale * delta[3],
        )

    k1 = derivatives(state, params)
    k2 = derivatives(add_scaled(y, k1, 0.5 * dt), params)
    k3 = derivatives(add_scaled(y, k2, 0.5 * dt), params)
    k4 = derivatives(add_scaled(y, k3, dt), params)

    return NextOneState(
        phi=y[0] + dt * (k1[0] + 2.0 * k2[0] + 2.0 * k3[0] + k4[0]) / 6.0,
        ell=y[1] + dt * (k1[1] + 2.0 * k2[1] + 2.0 * k3[1] + k4[1]) / 6.0,
        z_re=y[2] + dt * (k1[2] + 2.0 * k2[2] + 2.0 * k3[2] + k4[2]) / 6.0,
        z_im=y[3] + dt * (k1[3] + 2.0 * k2[3] + 2.0 * k3[3] + k4[3]) / 6.0,
    )


def simulate_next_one(
    initial: NextOneState,
    params: NextOneParams,
    *,
    dt: float,
    steps: int,
    record_every: int = 1,
) -> Tuple[NextOneState, ...]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if record_every < 1:
        raise ValueError("record_every must be at least 1")

    state = initial
    out = [state]

    for step in range(1, steps + 1):
        state = rk4_step(state, params, dt)
        if step % record_every == 0 or step == steps:
            out.append(state)

    return tuple(out)


def branch_phase(branch: int) -> float:
    if branch not in (0, 1, 2):
        raise ValueError("branch must be 0, 1, or 2")
    return 2.0 * math.pi * branch / 3.0


def selected_branch(
    state: NextOneState,
    *,
    min_amplitude: float = 1e-6,
) -> Optional[int]:
    """
    Return the nearest stable C3 branch when the branch residual is resolved.

    The three stable rays for positive anisotropy are

        theta_k = 2*pi*k/3,  k=0,1,2.
    """
    z = state.z
    if abs(z) < float(min_amplitude):
        return None

    theta = math.atan2(z.imag, z.real)

    def angular_distance(a: float, b: float) -> float:
        return abs(math.atan2(math.sin(a - b), math.cos(a - b)))

    return min(
        (0, 1, 2),
        key=lambda k: angular_distance(theta, branch_phase(k)),
    )


def branch_lock_error(state: NextOneState) -> Optional[float]:
    branch = selected_branch(state)
    if branch is None:
        return None

    theta = math.atan2(state.z_im, state.z_re)
    target = branch_phase(branch)
    return abs(math.atan2(math.sin(theta - target), math.cos(theta - target)))


def c3_rotate(z: complex, turns: int = 1) -> complex:
    omega = cmath_exp(2.0 * math.pi * int(turns) / 3.0)
    return omega * z


def cmath_exp(angle: float) -> complex:
    return complex(math.cos(angle), math.sin(angle))
