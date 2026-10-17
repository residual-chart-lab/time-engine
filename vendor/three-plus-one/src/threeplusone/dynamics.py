from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Tuple


@dataclass(frozen=True)
class DualRotorParams:
    """
    Conservative two-frame rotor parameters.

    theta_plus and theta_minus are the independent rotations of the two
    tetrahedral frames around their shared axis.  The lowest non-trivial
    interaction compatible with the unlabeled threefold symmetry is

        V(phi) = kappa * (1 - cos(3 phi))

    with phi = theta_plus - theta_minus.
    """

    inertia_plus: float = 1.0
    inertia_minus: float = 1.0
    kappa: float = 1.0

    def __post_init__(self) -> None:
        if self.inertia_plus <= 0.0 or self.inertia_minus <= 0.0:
            raise ValueError("rotor inertias must be positive")
        if self.kappa < 0.0:
            raise ValueError("kappa must be non-negative")


@dataclass(frozen=True)
class DualRotorState:
    theta_plus: float
    theta_minus: float
    p_plus: float
    p_minus: float


def relative_phase(state: DualRotorState) -> float:
    return state.theta_plus - state.theta_minus


def total_momentum(state: DualRotorState) -> float:
    return state.p_plus + state.p_minus


def relative_inertia(params: DualRotorParams) -> float:
    return (
        params.inertia_plus
        * params.inertia_minus
        / (params.inertia_plus + params.inertia_minus)
    )


def relative_angular_velocity(
    state: DualRotorState,
    params: DualRotorParams,
) -> float:
    return (
        state.p_plus / params.inertia_plus
        - state.p_minus / params.inertia_minus
    )


def relative_momentum(
    state: DualRotorState,
    params: DualRotorParams,
) -> float:
    return relative_inertia(params) * relative_angular_velocity(state, params)


def potential(phi: float, params: DualRotorParams) -> float:
    return params.kappa * (1.0 - math.cos(3.0 * float(phi)))


def total_energy(state: DualRotorState, params: DualRotorParams) -> float:
    kinetic = (
        state.p_plus * state.p_plus / (2.0 * params.inertia_plus)
        + state.p_minus * state.p_minus / (2.0 * params.inertia_minus)
    )
    return kinetic + potential(relative_phase(state), params)


def relative_energy(state: DualRotorState, params: DualRotorParams) -> float:
    ell = relative_momentum(state, params)
    inertia = relative_inertia(params)
    return ell * ell / (2.0 * inertia) + potential(relative_phase(state), params)


def relative_regime(
    state: DualRotorState,
    params: DualRotorParams,
    *,
    tolerance: float = 1e-12,
) -> str:
    """
    Classify the conservative relative motion.

    The threefold potential has barrier height 2*kappa.

    - E_rel > 2*kappa: continuous relative rotation
    - E_rel < 2*kappa: libration inside one well
    - E_rel = 2*kappa: separatrix

    When kappa == 0, nonzero relative momentum is free rotation.
    """
    energy = relative_energy(state, params)
    barrier = 2.0 * params.kappa

    if abs(energy - barrier) <= tolerance:
        return "separatrix"
    if energy > barrier:
        return "rotation"
    return "libration"


def tetrahedral_alignment(state: DualRotorState) -> float:
    """Even part of the unlabeled relative order parameter."""
    return math.cos(3.0 * relative_phase(state))


def tetrahedral_parity(state: DualRotorState) -> float:
    """Odd part of the unlabeled relative order parameter."""
    return math.sin(3.0 * relative_phase(state))


def _forces(
    state: DualRotorState,
    params: DualRotorParams,
) -> tuple[float, float]:
    """
    Hamiltonian forces on p_plus and p_minus.

    For V(phi)=kappa(1-cos(3 phi)):

        dV/dphi = 3*kappa*sin(3 phi)
        p_plus_dot  = -dV/dphi
        p_minus_dot = +dV/dphi
    """
    d_v = 3.0 * params.kappa * math.sin(3.0 * relative_phase(state))
    return -d_v, d_v


def velocity_verlet_step(
    state: DualRotorState,
    params: DualRotorParams,
    dt: float,
) -> DualRotorState:
    """
    One symplectic velocity-Verlet step.

    This preserves the total angular momentum exactly up to floating-point
    arithmetic and keeps the conservative energy bounded over long runs.
    """
    dt = float(dt)
    if dt <= 0.0:
        raise ValueError("dt must be positive")

    f_plus, f_minus = _forces(state, params)

    p_plus_half = state.p_plus + 0.5 * dt * f_plus
    p_minus_half = state.p_minus + 0.5 * dt * f_minus

    theta_plus = (
        state.theta_plus
        + dt * p_plus_half / params.inertia_plus
    )
    theta_minus = (
        state.theta_minus
        + dt * p_minus_half / params.inertia_minus
    )

    provisional = DualRotorState(
        theta_plus=theta_plus,
        theta_minus=theta_minus,
        p_plus=p_plus_half,
        p_minus=p_minus_half,
    )
    f_plus_new, f_minus_new = _forces(provisional, params)

    return DualRotorState(
        theta_plus=theta_plus,
        theta_minus=theta_minus,
        p_plus=p_plus_half + 0.5 * dt * f_plus_new,
        p_minus=p_minus_half + 0.5 * dt * f_minus_new,
    )


def simulate_dual_rotor(
    initial: DualRotorState,
    params: DualRotorParams,
    *,
    dt: float,
    steps: int,
    record_every: int = 1,
) -> Tuple[DualRotorState, ...]:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    if record_every < 1:
        raise ValueError("record_every must be at least 1")

    state = initial
    out = [state]

    for step in range(1, steps + 1):
        state = velocity_verlet_step(state, params, dt)
        if step % record_every == 0 or step == steps:
            out.append(state)

    return tuple(out)


def relative_winding(states: Iterable[DualRotorState]) -> float:
    """
    Net unwrapped relative rotation in turns.

    The stored theta values are intentionally not reduced modulo 2*pi.
    """
    data = list(states)
    if len(data) < 2:
        return 0.0
    phi0 = relative_phase(data[0])
    phi1 = relative_phase(data[-1])
    return (phi1 - phi0) / (2.0 * math.pi)
