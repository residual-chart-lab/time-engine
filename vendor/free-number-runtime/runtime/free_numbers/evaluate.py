"""Certified outward bounds, independently controlled from response depth."""
from dataclasses import dataclass
from fractions import Fraction as Q
from .algebra import ZERO, Polynomial, fingerprint
from .retention import Meter
from .demand import Policy, plan


def outward(lo, hi, bits):
    scale = 1 << bits
    a, b = lo * scale, hi * scale
    return Q(a.numerator // a.denominator,scale), Q(-((-b.numerator)//b.denominator),scale)


def add(x, y, bits):
    return outward(x[0]+y[0], x[1]+y[1], bits)


def mul(x, y, bits):
    xs = tuple(a*b for a in x for b in y)
    return outward(min(xs),max(xs),bits)


def absolute(x):
    lo, hi = x
    return (Q(0) if lo <= 0 <= hi else min(abs(lo),abs(hi)), max(abs(lo),abs(hi)))


def enclose(coefficients, values, bits):
    out = [(Q(0),Q(0))] * 4
    for monomial, coefficient in coefficients:
        scalar = (Q(1),Q(1))
        for key in monomial:
            scalar = mul(scalar,values[key],bits)
        for i, a in enumerate(coefficient):
            out[i] = add(out[i],mul(scalar,outward(a,a,bits),bits),bits)
    return tuple(out)


def verdict(query, bounds):
    if query.purpose == 'exact-value':
        return None
    errors = [absolute((lo-t,hi-t)) for (lo,hi),t in zip(bounds,query.target)]
    lo, hi = sum(e[0] for e in errors),sum(e[1] for e in errors)
    if hi < query.tolerance:
        return True
    if lo >= query.tolerance:
        return False
    return None


@dataclass(frozen=True)
class Stage:
    mode: str
    bits: int
    bounds: tuple
    keys: tuple


@dataclass(frozen=True)
class Certificate:
    query_digest: str
    plan_digest: str
    policy: Policy
    status: str
    decision: object
    value: object
    stages: tuple
    exact_keys: tuple

    @property
    def digest(self):
        return fingerprint((self.query_digest,self.plan_digest,tuple(self.policy.__dict__.values()),
            self.status,self.decision,self.value,tuple((s.mode,s.bits,s.bounds,s.keys) for s in self.stages),self.exact_keys))


def evaluate(query, vault, policy=Policy(), meter=None):
    meter = Meter() if meter is None else meter
    p = plan(query,vault,policy,meter)
    def result(status, decision=None, value=None, stages=(), keys=()):
        return Certificate(query.digest,p.digest,policy,status,decision,value,tuple(stages),keys)
    if p.status != 'AVAILABLE':
        return result('UNDETERMINED_'+p.status)
    poly = Polynomial(p.coefficients,policy.max_terms)
    if not p.dependencies:
        v = poly.exact({})
        accepted = None if query.purpose == 'exact-value' else sum(abs(a-b) for a,b in zip(v,query.target)) < query.tolerance
        return result('EXACT',accepted,v)
    values = {key:vault.coarse(key,meter) for key in p.dependencies}
    stages = []
    first = policy.precisions[0]
    bounds = enclose(p.coefficients,values,first)
    stages.append(Stage('authenticated-envelope',first,bounds,()))
    accepted = verdict(query,bounds)
    if accepted is not None:
        return result('BOUNDED',accepted,stages=stages)
    if query.purpose != 'exact-value':
        for bits in policy.precisions:
            values = {key:vault.refine(key,bits,meter) for key in p.dependencies}
            bounds = enclose(p.coefficients,values,bits)
            stages.append(Stage('refined-bounds',bits,bounds,p.dependencies))
            accepted = verdict(query,bounds)
            if accepted is not None:
                return result('BOUNDED',accepted,stages=stages)
    if not policy.exact_fallback:
        return result('UNDETERMINED_PRECISION',stages=stages)
    exact = {key:vault.exact(key,meter) for key in p.dependencies}
    value = poly.exact(exact)
    accepted = None if query.purpose == 'exact-value' else sum(abs(a-b) for a,b in zip(value,query.target)) < query.tolerance
    return result('EXACT',accepted,value,stages,p.dependencies)


def verify_certificate(query, vault, certificate, policy=None):
    if (type(certificate) is not Certificate or
            (policy is not None and certificate.policy != policy) or
            certificate != evaluate(query,vault,certificate.policy)):
        raise ValueError('the query, scope, precision/depth policy or bound witness changed')
    return True


def replacement_query(expression, representative, scope):
    """Exact observed difference; zero never authorizes erasing either input."""
    from .expression import constant
    from .algebra import ONE, qscale
    from .demand import Query
    return Query(expression + constant(qscale(Q(-1),ONE))*representative,scope)


@dataclass(frozen=True)
class ReplacementJudgement:
    status: str
    certificate: Certificate


def assess_replacement(expression, representative, scope, vault, policy=Policy(), meter=None):
    query = replacement_query(expression,representative,scope)
    proof = evaluate(query,vault,policy,meter)
    status = ('UNDETERMINED' if proof.value is None else
              'REPLACEABLE_IN_SCOPE' if proof.value == ZERO else 'NOT_REPLACEABLE_IN_SCOPE')
    return ReplacementJudgement(status,proof)
