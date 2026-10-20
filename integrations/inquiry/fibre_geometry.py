"""RR61: the entire regular current-invisible source fibre, not a chosen ray.

Symmetric trace-one frames, the frozen six-generator affine basis, exact
rationals. The geometric axis is computed from the frame's trace invariants.
The existing action-matrix null routine is used only as an independent check
in the study, never as an input to the geometric construction.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from functools import lru_cache

import internal_port as previous
from internal_port import d,te
from internal_port_certificate import rref,solve

IDENTITY=tuple(tuple(Q(i==j) for j in range(3)) for i in range(3))
COORDS=((0,0),(1,1),(2,2),(0,1),(0,2),(1,2))


def add(x,y):return tuple(tuple(a+b for a,b in zip(r,s)) for r,s in zip(x,y))
def scale(a,x):return tuple(tuple(Q(a)*v for v in row) for row in x)
def mm(x,y):return tuple(tuple(sum(x[i][k]*y[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def tr(x):return sum(x[i][i] for i in range(3))
def norm2(x):return sum(v*v for row in x for v in row)
def transpose(x):return tuple(zip(*x))
def conjugate(rotation,x):return mm(mm(rotation,x),transpose(rotation))


def stf_basis():
    return (scale(1,((1,0,0),(0,-1,0),(0,0,0))),
            scale(1,((1,0,0),(0,0,0),(0,0,-1))),
            scale(1,((0,1,0),(1,0,0),(0,0,0))),
            scale(1,((0,0,1),(0,0,0),(1,0,0))),
            scale(1,((0,0,0),(0,0,1),(0,1,0))))


def nullspace(matrix):
    reduced,pivots=rref(matrix);n=len(matrix[0]);vectors=[]
    for free in (i for i in range(n) if i not in pivots):
        v=[Q(0)]*n;v[free]=Q(1)
        for row,pivot in zip(reduced,pivots):v[pivot]=-row[free]
        vectors.append(tuple(v))
    return tuple(vectors),len(pivots)


def boundary_matrix(library):
    return tuple(tuple(op.source.endpoint[i][j] for op in library) for i,j in COORDS)


@dataclass(frozen=True)
class Geometry:
    context: tuple
    variance: Q
    cubic: Q
    discriminant: Q
    response_rank: int
    invisible_dimension: int
    intrinsic_axis: object
    coefficient_axis: object
    boundary_basis_rank: int


@lru_cache(maxsize=192)
def geometry(context,library):
    y=te.port.single.context(context)
    if len(library)!=6:raise ValueError('the six-generator chart is required')
    b=boundary_matrix(library);boundary_rank=len(rref(b)[1])
    if boundary_rank!=6:raise ValueError('the six boundary tensors must be a complete affine basis')
    if any(tr(op.source.endpoint)!=1 or transpose(op.source.endpoint)!=op.source.endpoint for op in library):
        raise ValueError('the boundary basis must be symmetric and trace one')
    a=add(y,scale(Q(-1,3),IDENTITY));a2=mm(a,a)
    v=tr(a2);cubic=tr(mm(a2,a));discriminant=v**3/2-3*cubic**2
    columns=tuple(tuple(d.join(s,y)) for s in stf_basis())
    _,rank=nullspace(tuple(zip(*columns)))
    intrinsic=axis=None
    if v and discriminant>0:
        intrinsic=add(add(a2,scale(-v/3,IDENTITY)),scale(-cubic/v,a))
        if norm2(intrinsic)!=discriminant/(3*v):raise ArithmeticError('trace invariant identity failed')
        delta=tuple(solve([list(row) for row in b],tuple(intrinsic[i][j] for i,j in COORDS)))
        last=max(i for i,x in enumerate(delta) if x)
        axis=tuple(x/delta[last] for x in delta)
        if rank!=4:raise ArithmeticError('the distinct-spectrum current fibre must have dimension one')
    elif discriminant<0:
        raise ArithmeticError('a real symmetric frame cannot have negative spectral discriminant')
    return Geometry(y,v,cubic,discriminant,rank,5-rank,intrinsic,axis,boundary_rank)


def tensor_axis(axis,library):
    return tuple(tuple(sum(c*op.source.endpoint[i][j] for c,op in zip(axis,library))
                       for j in range(3)) for i in range(3))


@dataclass(frozen=True)
class FibreCertificate:
    context: tuple
    source_digest: str
    representative_digest: str
    coefficient_axis: tuple
    shift: Q
    direction: tuple


def source_digest(source):return d.fingerprint((source.weights,d.library_key(source.library)))


def certify_pair(context,source,representative):
    if (type(source) is not d.AffineLetter or type(representative) is not d.AffineLetter
            or source.library!=representative.library):
        raise ValueError('two normalized affine sources in the same fixed library are required')
    g=geometry(context,source.library)
    if g.coefficient_axis is None:
        raise ValueError('the frame is not regular: no one-axis completeness certificate is issued')
    delta=g.coefficient_axis
    differences=tuple(a-b for a,b in zip(source.weights,representative.weights))
    last=max(i for i,x in enumerate(delta) if x)
    shift=differences[last]/delta[last]
    if differences!=tuple(shift*x for x in delta):
        raise ValueError('the pair is outside the complete current-invisible fibre')
    return FibreCertificate(g.context,source_digest(source),source_digest(representative),
        delta,shift,tensor_axis(delta,source.library))


def verify_pair(context,source,representative,certificate):
    if type(certificate) is not FibreCertificate or certificate!=certify_pair(context,source,representative):
        raise ValueError('the source pair, current frame or geometric proof changed')
    return True

