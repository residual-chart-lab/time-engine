from __future__ import annotations

import math
from typing import Sequence, Tuple


Vec3 = Tuple[float, float, float]
Vec4 = Tuple[float, float, float, float]
Tetrahedron = Tuple[Vec3, Vec3, Vec3, Vec3]


def _as_vec3(v: Sequence[float]) -> Vec3:
    if len(v) != 3:
        raise ValueError("expected a 3-vector")
    return (float(v[0]), float(v[1]), float(v[2]))


def add(u: Sequence[float], v: Sequence[float]) -> Vec3:
    u3, v3 = _as_vec3(u), _as_vec3(v)
    return (u3[0] + v3[0], u3[1] + v3[1], u3[2] + v3[2])


def sub(u: Sequence[float], v: Sequence[float]) -> Vec3:
    u3, v3 = _as_vec3(u), _as_vec3(v)
    return (u3[0] - v3[0], u3[1] - v3[1], u3[2] - v3[2])


def scale(c: float, v: Sequence[float]) -> Vec3:
    v3 = _as_vec3(v)
    c = float(c)
    return (c * v3[0], c * v3[1], c * v3[2])


def dot(u: Sequence[float], v: Sequence[float]) -> float:
    u3, v3 = _as_vec3(u), _as_vec3(v)
    return u3[0] * v3[0] + u3[1] * v3[1] + u3[2] * v3[2]


def cross(u: Sequence[float], v: Sequence[float]) -> Vec3:
    u3, v3 = _as_vec3(u), _as_vec3(v)
    return (
        u3[1] * v3[2] - u3[2] * v3[1],
        u3[2] * v3[0] - u3[0] * v3[2],
        u3[0] * v3[1] - u3[1] * v3[0],
    )


def norm(v: Sequence[float]) -> float:
    return math.sqrt(dot(v, v))


def normalize(v: Sequence[float]) -> Vec3:
    v3 = _as_vec3(v)
    n = norm(v3)
    if n == 0.0:
        raise ValueError("cannot normalize the zero vector")
    return scale(1.0 / n, v3)


def orthonormal_transverse_basis(axis: Sequence[float]) -> tuple[Vec3, Vec3]:
    """
    Return e1, e2 spanning the plane perpendicular to axis.

    The orientation is chosen so that e1 x e2 = axis.
    """
    a = normalize(axis)
    candidates = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    ref = min(candidates, key=lambda e: abs(dot(a, e)))
    e1 = normalize(cross(a, ref))
    e2 = normalize(cross(a, e1))
    return e1, e2


def rotate_about_axis(
    v: Sequence[float],
    axis: Sequence[float],
    angle: float,
) -> Vec3:
    """Rotate v around axis by angle radians using Rodrigues' formula."""
    v3 = _as_vec3(v)
    a = normalize(axis)
    c = math.cos(float(angle))
    s = math.sin(float(angle))
    return add(
        add(scale(c, v3), scale(s, cross(a, v3))),
        scale((1.0 - c) * dot(a, v3), a),
    )


def centered_contrast_vertices() -> tuple[Vec4, Vec4, Vec4, Vec4]:
    """
    The four normalized centered singleton directions in the zero-sum
    contrast space of R^4.

        v_i = (4 e_i - 1) / sqrt(12)

    They form a regular tetrahedron: ||v_i|| = 1 and
    <v_i, v_j> = -1/3 for i != j.
    """
    denom = math.sqrt(12.0)
    vertices = []
    for i in range(4):
        row = tuple((3.0 if j == i else -1.0) / denom for j in range(4))
        vertices.append(row)
    return tuple(vertices)  # type: ignore[return-value]


def transverse_rays(
    axis: Sequence[float] = (0.0, 0.0, 1.0),
    *,
    phase: float = 0.0,
) -> tuple[Vec3, Vec3, Vec3]:
    """Three unit rays at 120 degrees in the plane perpendicular to axis."""
    a = normalize(axis)
    e1, _ = orthonormal_transverse_basis(a)
    return tuple(
        rotate_about_axis(e1, a, float(phase) + 2.0 * math.pi * k / 3.0)
        for k in range(3)
    )  # type: ignore[return-value]


def tetrahedron_vertices(
    axis: Sequence[float] = (0.0, 0.0, 1.0),
    *,
    phase: float = 0.0,
    inverted: bool = False,
) -> Tetrahedron:
    """
    A unit regular tetrahedron with one distinguished vertex on axis.

    For the non-inverted tetrahedron, the apex is +axis and the other three
    vertices are

        -axis/3 + (2 sqrt(2)/3) b_k,

    where b_k are three transverse rays at 120 degrees.

    The inverted tetrahedron is the central inversion of the same construction.
    """
    a = normalize(axis)
    rays = transverse_rays(a, phase=phase)
    radial = 2.0 * math.sqrt(2.0) / 3.0

    if not inverted:
        apex = a
        base = tuple(add(scale(-1.0 / 3.0, a), scale(radial, b)) for b in rays)
    else:
        apex = scale(-1.0, a)
        base = tuple(add(scale(1.0 / 3.0, a), scale(-radial, b)) for b in rays)

    return (apex, base[0], base[1], base[2])


def dual_tetrahedra(
    axis: Sequence[float] = (0.0, 0.0, 1.0),
    *,
    theta_plus: float = 0.0,
    theta_minus: float = 0.0,
) -> tuple[Tetrahedron, Tetrahedron]:
    """
    Two oppositely oriented regular tetrahedra with independent rotations
    around the same axis.
    """
    return (
        tetrahedron_vertices(axis, phase=theta_plus, inverted=False),
        tetrahedron_vertices(axis, phase=theta_minus, inverted=True),
    )


def oriented_area(
    axis: Sequence[float],
    u: Sequence[float],
    v: Sequence[float],
) -> float:
    """
    Oriented area form in the transverse plane:

        omega_axis(u, v) = axis . (u x v)

    For transverse u and v this is their signed parallelogram area.
    """
    a = normalize(axis)
    return dot(a, cross(u, v))


def tetrahedral_relative_order(
    theta_plus: float,
    theta_minus: float,
) -> tuple[float, float]:
    """
    Return the unlabeled relative alignment and parity of two 3-fold frames.

    A base triangle is unchanged by relabeling after a 2*pi/3 rotation, so the
    gauge-invariant relative order parameter is

        q = exp(3 i (theta_plus - theta_minus)).

    This function returns (Re q, Im q) = (alignment, parity).
    """
    phi = float(theta_plus) - float(theta_minus)
    return math.cos(3.0 * phi), math.sin(3.0 * phi)


def child_axes(
    axis: Sequence[float] = (0.0, 0.0, 1.0),
    *,
    phase: float = 0.0,
) -> tuple[Vec3, Vec3, Vec3]:
    """
    The three candidate child axes supplied by the base vertices of a regular
    tetrahedron whose distinguished parent axis is axis.
    """
    tetra = tetrahedron_vertices(axis, phase=phase, inverted=False)
    return tetra[1], tetra[2], tetra[3]


TETRAHEDRAL_BRANCH_ANGLE = math.acos(-1.0 / 3.0)
