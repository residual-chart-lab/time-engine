"""Ordered tensor-expression DAGs and finite, explicit response observations."""
from dataclasses import dataclass, field
from fractions import Fraction as Q
from .algebra import (ZERO, ONE, BASIS, primitive, rational, quat, vector, fingerprint, qscale)
from .retention import Reference


@dataclass(frozen=True)
class Tensor:
    kind: str
    grade: int
    data: tuple
    children: tuple = ()
    digest: str = field(init=False)

    def __post_init__(self):
        if type(self.grade) is not int or self.grade < 1:
            raise ValueError('this runtime handles positive finite grades')
        if type(self.data) is not tuple or type(self.children) is not tuple:
            raise TypeError('immutable node data and children are required')
        if any(type(c) is not Tensor for c in self.children):
            raise TypeError('tensor children are required')
        if self.kind == 'block':
            if self.children:
                raise ValueError('blocks have no children')
            last = None
            for word, coefficient in self.data:
                if (type(word) is not tuple or len(word) != self.grade or
                        any(type(a) is not int or a not in (0,1,2) for a in word) or
                        type(coefficient) is not Q or not coefficient or
                        (last is not None and word <= last)):
                    raise ValueError('a canonical sparse rational tensor block is required')
                last = word
        elif self.kind == 'concat':
            if (self.data or len(self.children) != 2 or
                    self.grade != sum(c.grade for c in self.children)):
                raise ValueError('concatenation preserves ordered factors and additive grade')
        elif self.kind == 'sum':
            if self.data or len(self.children) != 2 or any(c.grade != self.grade for c in self.children):
                raise ValueError('sum operands must have the same grade')
        elif self.kind == 'scale':
            if len(self.data) != 1 or type(self.data[0]) is not Q or len(self.children) != 1 or self.children[0].grade != self.grade:
                raise ValueError('invalid scalar node')
        elif self.kind == 'retained':
            if (len(self.data) != 1 or type(self.data[0]) is not Reference or len(self.children) != 2 or
                    any(c.kind != 'block' or c.grade != self.grade for c in self.children)):
                raise ValueError('a retained block is representative + scalar * residual block')
            if self.children[1].compressed() != ZERO:
                raise ValueError('a declared residual direction must have zero compression')
        else:
            raise ValueError('unknown tensor operation')
        data = tuple((x.key, x.origin, x.envelope, x.commitment) if type(x) is Reference else x for x in self.data)
        object.__setattr__(self, 'digest', fingerprint((self.kind, self.grade, data,
                                                      tuple(c.digest for c in self.children))))

    def compressed(self):
        if self.kind != 'block':
            raise ValueError('only small constant blocks are compressed at construction')
        out = [Q(0)] * 4
        for w, a in self.data:
            v = primitive(w, (None,) * (self.grade-1))
            for i in range(4):
                out[i] += a * v[i]
        return tuple(out)

    def then(self, other):
        return Tensor('concat', self.grade + other.grade, (), (self, other))

    def __add__(self, other):
        return Tensor('sum', self.grade, (), (self, other))

    def scaled(self, coefficient):
        return Tensor('scale', self.grade, (rational(coefficient),), (self,))


def block(grade, terms):
    d = {}
    for word, a in terms:
        w = tuple(word)
        d[w] = d.get(w, Q(0)) + rational(a)
    return Tensor('block', grade, tuple(sorted((w,a) for w,a in d.items() if a)))


def matrix_block(matrix):
    rows = tuple(tuple(map(rational, r)) for r in matrix)
    if len(rows) != 3 or any(len(r) != 3 for r in rows):
        raise ValueError('a 3x3 rational boundary tensor is required')
    return block(2, (((i,j), rows[i][j]) for i in range(3) for j in range(3)))


def retained(vault, key, value, envelope, origin, representative, direction):
    ref = vault.register(key, value, envelope, origin)
    return Tensor('retained', representative.grade, (ref,), (representative, direction))


@dataclass(frozen=True)
class Channel:
    gaps: tuple
    weight: Q = Q(1)
    left: tuple = ONE
    right: tuple = ONE

    def __post_init__(self):
        object.__setattr__(self, 'gaps', tuple(None if p is None else vector(p) for p in self.gaps))
        object.__setattr__(self, 'weight', rational(self.weight))
        object.__setattr__(self, 'left', quat(self.left))
        object.__setattr__(self, 'right', quat(self.right))

    @property
    def depth(self):
        return sum(p is not None for p in self.gaps)


@dataclass(frozen=True)
class Observation:
    grade: int
    channels: tuple

    def __post_init__(self):
        if (type(self.grade) is not int or self.grade < 1 or type(self.channels) is not tuple or
                not self.channels or any(type(c) is not Channel or len(c.gaps) != self.grade-1 for c in self.channels)):
            raise ValueError('a finite explicit family of grade-matched channels is required')

    @property
    def depth(self):
        return max(c.depth for c in self.channels)

    @property
    def digest(self):
        return fingerprint((self.grade, tuple((c.gaps,c.weight,c.left,c.right) for c in self.channels)))


def compression(grade):
    return Observation(grade, (Channel((None,) * (grade-1)),))


@dataclass(frozen=True)
class Circuit:
    kind: str
    data: tuple
    children: tuple = ()
    digest: str = field(init=False)

    def __post_init__(self):
        if type(self.data) is not tuple or type(self.children) is not tuple:
            raise TypeError('immutable circuit data are required')
        if any(type(c) is not Circuit for c in self.children):
            raise TypeError('circuit children are required')
        if self.kind == 'read':
            if (len(self.data) != 2 or type(self.data[0]) is not Tensor or
                    type(self.data[1]) is not Observation or self.children or
                    self.data[0].grade != self.data[1].grade):
                raise ValueError('bind a tensor and an explicit matching observation')
            data = (self.data[0].digest, self.data[1].digest)
        elif self.kind == 'constant':
            if len(self.data) != 1 or self.children or quat(self.data[0]) != self.data[0]:
                raise ValueError('a constant quaternion is required')
            data = self.data
        elif self.kind in ('add', 'mul'):
            if self.data or len(self.children) != 2:
                raise ValueError('a binary ordered arithmetic operation is required')
            data = self.data
        else:
            raise ValueError('unknown circuit operation')
        object.__setattr__(self, 'digest', fingerprint((self.kind, data, tuple(c.digest for c in self.children))))

    def __add__(self, other):
        return Circuit('add', (), (self, other))

    def __mul__(self, other):
        return Circuit('mul', (), (self, other))


def read(tensor, observation=None):
    return Circuit('read', (tensor, compression(tensor.grade) if observation is None else observation))


def constant(value):
    return Circuit('constant', (quat(value),))


def component(expression, index):
    """A registered real-linear component readout, built from ordered products."""
    if type(index) is not int or not 0 <= index < 4:
        raise ValueError('a quaternion component in [0,3] is required')
    conjugate = BASIS[index] if index == 0 else qscale(Q(-1),BASIS[index])
    x = constant(conjugate)*expression
    total = x
    for axis in BASIS[1:]:
        total = total + constant(qscale(Q(-1),axis))*x*constant(axis)
    return constant((Q(1,4),Q(0),Q(0),Q(0)))*total
