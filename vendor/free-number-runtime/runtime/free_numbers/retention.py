"""Immutable exact scalar retention with scoped, instrumented read requests.

Registration authenticates an exact value and its envelope once. Bounds are
certified by this trusted in-process vault, not by an unauthenticated hash.
Finite-precision bound reads and full exact reads are counted separately.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from .algebra import rational, fingerprint


@dataclass(frozen=True)
class Reference:
    key: str
    origin: str
    envelope: tuple
    commitment: str

    @property
    def digest(self):
        return fingerprint((self.key, self.origin, self.envelope, self.commitment))


@dataclass
class Meter:
    coarse_reads: int = 0
    refinement_reads: int = 0
    exact_reads: int = 0
    compiled_tensor_slices: int = 0
    compile_cache_hits: int = 0


class Vault:
    def __init__(self):
        self._entries = {}

    def register(self, key, value, envelope, origin):
        if not isinstance(key, str) or not key or not isinstance(origin, str) or not origin:
            raise ValueError('a nonempty key and provenance are required')
        value = rational(value)
        bounds = tuple(map(rational, envelope))
        if len(bounds) != 2 or not bounds[0] <= value <= bounds[1]:
            raise ValueError('the exact retained value must lie in its envelope')
        ref = Reference(key, origin, bounds, fingerprint((key, origin, value, bounds)))
        if key in self._entries and self._entries[key] != (ref, value):
            raise ValueError('a retained key cannot be rebound')
        self._entries[key] = (ref, value)
        return ref

    def verify(self, ref):
        if type(ref) is not Reference or self._entries.get(ref.key, (None,))[0] != ref:
            raise ValueError('unknown or substituted retained reference')

    def reference(self, key):
        return self._entries[key][0]

    def coarse(self, key, meter):
        meter.coarse_reads += 1
        return self.reference(key).envelope

    def refine(self, key, bits, meter):
        if type(bits) is not int or not 1 <= bits <= 4096:
            raise ValueError('a finite dyadic precision in [1,4096] is required')
        meter.refinement_reads += 1
        q = self._entries[key][1]
        n, d = q.numerator << bits, q.denominator
        lo, hi = Q(n // d, 1 << bits), Q(-((-n) // d), 1 << bits)
        a, b = self.reference(key).envelope
        return max(a, lo), min(b, hi)

    def exact(self, key, meter):
        meter.exact_reads += 1
        return self._entries[key][1]

    def _records(self):
        # Checkpointing deliberately carries every retained exact value. It is
        # not counted as a demand read or a claim of zero-cost serialization.
        return tuple((ref, value) for ref, value in sorted(self._entries.values(),
                                                         key=lambda p: p[0].key))
