"""RR58: scoped replacement certificates, retained residues, bounded previews.

Only the B2 chart of frozen Free Numbers Core v1 is used. Higher TE operations
stay ordered expressions. Certificates authorize specified observations;
they never replace a source, mutate a ledger, or authorize residue deletion.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'integrations/three_plus_one'))
import three_flower as embedded
from recursive_upper_decoder import AffineLetter, qmul, regular
from two_flower_kernel_certificate import qstate,probe,join,eye

SAFE='REPLACEABLE_IN_SCOPE'
DIFFERENT='NOT_REPLACEABLE_IN_SCOPE'
UNKNOWN='UNDETERMINED'


def fingerprint(value):
    raw=json.dumps(value,default=embedded.triple.encode,separators=(',',':'),sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def sigma2(q):
    """Frozen Core 04, section 5; m2(e_a|e_b)=e_b e_a."""
    a,x,y,z=map(Q,q)
    return ((-a/3,-z/2,y/2),(z/2,-a/3,-x/2),(-y/2,x/2,-a/3))


def split_tensor(x):
    value=tuple(qstate(x));base=sigma2(value)
    residual=tuple(tuple(Q(x[i][j])-base[i][j] for j in range(3)) for i in range(3))
    return value,residual


def tensor(leaf):
    return tuple(tuple(sum(w*op.source.endpoint[i][j] for w,op in zip(leaf.weights,leaf.library))
                       for j in range(3)) for i in range(3))


def library_key(library):
    return tuple(op.source.endpoint for op in library)


@lru_cache(maxsize=128)
def base_responses(library,context):
    # Coefficients of this linear readout depend on the small library and
    # frame, not on the potentially huge retained affine coefficients.
    return tuple(tuple(op.apply(context)) for op in library)


@dataclass
class Meter:
    exact_retained_responses: int=0
    exact_tensor_expansions: int=0
    bounded_leaf_responses: int=0
    bounded_operations: int=0
    coefficient_bound_reads: int=0
    largest_integer_bits: int=0


@dataclass(frozen=True)
class RetainedPair:
    original: AffineLetter
    representative: AffineLetter
    shift: Q
    direction: tuple
    origin: str

    def __post_init__(self):
        object.__setattr__(self,'shift',Q(self.shift))
        object.__setattr__(self,'direction',tuple(map(Q,self.direction)))
        if (type(self.original) is not AffineLetter or type(self.representative) is not AffineLetter
                or self.original.library!=self.representative.library
                or len(self.direction)!=len(self.original.weights) or sum(self.direction)!=0
                or self.original.weights!=tuple(w+self.shift*d for w,d in
                    zip(self.representative.weights,self.direction)) or type(self.origin) is not str or not self.origin):
            raise ValueError('the immutable original, representative and exact residual recipe must agree')
        for op in self.original.library:
            x=op.source.endpoint
            if (sum(x[i][i] for i in range(3))!=1 or
                    any(x[i][j]!=x[j][i] for i in range(3) for j in range(3))):
                raise ValueError('this adapter requires the declared symmetric trace-one B2 library')

    @property
    def value(self):
        # This m2 value is NOT the visible action of the promoted TE source.
        return (Q(-1),Q(0),Q(0),Q(0))

    @property
    def digest(self):
        return fingerprint((self.origin,self.original.weights,self.representative.weights,
                            self.direction,self.shift,library_key(self.original.library)))

    def residual_tensor(self,meter):
        meter.exact_tensor_expansions+=2
        x,y=tensor(self.original),tensor(self.representative)
        return tuple(tuple(a-b for a,b in zip(r,s)) for r,s in zip(x,y))


@dataclass(frozen=True)
class Scope:
    contexts: tuple
    observation: str='kernel'
    entry: str='fixed-response-query'

    def __post_init__(self):
        contexts=tuple(embedded.port.single.context(y) for y in self.contexts)
        object.__setattr__(self,'contexts',contexts)
        if (not contexts or self.observation not in ('kernel','compression','boundary_tensor')
                or type(self.entry) is not str or not self.entry):
            raise ValueError('a nonempty finite observation scope and entry are required')


@dataclass(frozen=True)
class ReplacementCertificate:
    pair_digest: str
    scope: Scope
    budget: int
    status: str
    factors: tuple


def assess(pair,scope,budget=None):
    """Factor the difference as shift * small response; keep the shift latent."""
    if type(scope) is not Scope: raise ValueError('an explicit observation scope is required')
    if budget is None: budget=len(scope.contexts)
    if type(budget) is not int or budget<0: raise ValueError('a nonnegative probe budget is required')
    factors=[]
    for y in scope.contexts[:budget]:
        if scope.observation=='compression':
            factor=(Q(0),)*4
        elif scope.observation=='boundary_tensor':
            library=pair.original.library
            factor=tuple(sum(d*op.source.endpoint[i][j] for d,op in zip(pair.direction,library))
                         for i in range(3) for j in range(3))
        else:
            if not regular(y,pair.original.library):
                raise ValueError('kernel queries must remain in the declared regular chart')
            values=base_responses(pair.original.library,y)
            factor=tuple(sum(d*v[j] for d,v in zip(pair.direction,values)) for j in range(4))
        factors.append(factor)
        if pair.shift and any(factor):
            return ReplacementCertificate(pair.digest,scope,budget,DIFFERENT,tuple(factors))
    status=SAFE if len(factors)==len(scope.contexts) else UNKNOWN
    return ReplacementCertificate(pair.digest,scope,budget,status,tuple(factors))


def verify_certificate(pair,scope,certificate):
    if (type(certificate) is not ReplacementCertificate or certificate.scope!=scope
            or certificate.pair_digest!=pair.digest or certificate!=assess(pair,scope,certificate.budget)):
        raise ValueError('the original pair, entry, observation, scope or proof changed')
    return True


def read(pair,scope,meter,certificate=None):
    if scope.observation!='kernel' or len(scope.contexts)!=1:
        raise ValueError('read requires one kernel query, not a different observation certificate')
    if certificate is None: certificate=assess(pair,scope)
    verify_certificate(pair,scope,certificate)
    if certificate.status==UNKNOWN: raise ValueError('the unresolved difference remains retained')
    if certificate.status==SAFE:
        return pair.representative.kernel(scope.contexts[0])
    meter.exact_retained_responses+=1
    return pair.original.kernel(scope.contexts[0])


@dataclass(frozen=True)
class DeferredWord:
    pair: RetainedPair
    tail: tuple=()

    def __post_init__(self):
        object.__setattr__(self,'tail',tuple(self.tail))
        if any(type(a) is not AffineLetter or a.level!=self.pair.original.level for a in self.tail):
            raise ValueError('retain an ordered same-level primitive tail')

    def append(self,letter):
        if type(letter) is not AffineLetter or letter.level!=self.pair.original.level:
            raise ValueError('append a declared primitive of the same level')
        return DeferredWord(self.pair,self.tail+(letter,))

    def read(self,scope,meter,certificate=None):
        current=read(self.pair,scope,meter,certificate)
        for letter in self.tail:
            current=tuple(qmul(letter.kernel(scope.contexts[0]),current))
        return current


@dataclass(frozen=True)
class Grid:
    """Outward integer intervals on a fixed dyadic grid; no float bounds."""
    lo: int
    hi: int
    bits: int

    def __post_init__(self):
        if self.lo>self.hi or not 1<=self.bits<=4096: raise ValueError('invalid bounded grid interval')

    @staticmethod
    def enclose(q,bits,meter=None):
        q=Q(q);n=q.numerator<<bits;d=q.denominator
        if meter is not None: meter.coefficient_bound_reads+=1
        return Grid(n//d,-((-n)//d),bits)

    def _same(self,other):
        if self.bits!=other.bits: raise ValueError('grid precision changed inside an expression')

    def add(self,other,meter):
        self._same(other);meter.bounded_operations+=1
        return self._record(Grid(self.lo+other.lo,self.hi+other.hi,self.bits),meter)

    def neg(self): return Grid(-self.hi,-self.lo,self.bits)

    def mul(self,other,meter):
        self._same(other);meter.bounded_operations+=1
        terms=(self.lo*other.lo,self.lo*other.hi,self.hi*other.lo,self.hi*other.hi)
        d=1<<self.bits
        return self._record(Grid(min(terms)//d,-((-max(terms))//d),self.bits),meter)

    def absolute(self):
        return Grid(0 if self.lo<=0<=self.hi else min(abs(self.lo),abs(self.hi)),
                    max(abs(self.lo),abs(self.hi)),self.bits)

    @staticmethod
    def _record(result,meter):
        meter.largest_integer_bits=max(meter.largest_integer_bits,abs(result.lo).bit_length(),abs(result.hi).bit_length())
        return result

    def fractions(self): return Q(self.lo,1<<self.bits),Q(self.hi,1<<self.bits)
    def contains(self,q):
        q=Q(q);return self.lo*q.denominator<=q.numerator*(1<<self.bits)<=self.hi*q.denominator


def grid_qmul(a,b,meter):
    # Basis table is the original TE quaternion multiplication convention.
    from internal_port_certificate import mul
    result=[Grid(0,0,a[0].bits) for _ in range(4)]
    for i in range(4):
        for j in range(4):
            code=mul(i+1,j+1);term=a[i].mul(b[j],meter)
            if code<0: term=term.neg()
            result[abs(code)-1]=result[abs(code)-1].add(term,meter)
    return tuple(result)


@dataclass(frozen=True)
class WordQuery:
    groups: tuple
    context: tuple
    inherited: tuple
    target: tuple
    tolerance: Q
    origin: str

    def __post_init__(self):
        object.__setattr__(self,'groups',tuple(tuple(g) for g in self.groups))
        object.__setattr__(self,'context',embedded.port.single.context(self.context))
        object.__setattr__(self,'inherited',tuple(map(Q,self.inherited)))
        object.__setattr__(self,'target',tuple(map(Q,self.target)))
        object.__setattr__(self,'tolerance',Q(self.tolerance))
        if (not self.groups or any(not g for g in self.groups) or len(self.inherited)!=4
                or len(self.target)!=4 or self.tolerance<=0 or type(self.origin) is not str or not self.origin
                or any(type(a) is not AffineLetter for g in self.groups for a in g)):
            raise ValueError('an immutable ordered word, entry and unchanged observation policy are required')
        library=self.groups[0][0].library
        if any(a.library!=library for g in self.groups for a in g) or not regular(self.context,library):
            raise ValueError('one regular library chart is required')

    @property
    def digest(self):
        return fingerprint((self.origin,self.context,self.inherited,self.target,self.tolerance,
            tuple(tuple(a.weights for a in g) for g in self.groups),library_key(self.groups[0][0].library)))


@dataclass(frozen=True)
class PreviewCertificate:
    query_digest: str
    bits: int
    verdict: object
    error_bounds: tuple


def preview(query,bits,meter):
    base=base_responses(query.groups[0][0].library,query.context)
    base=tuple(tuple(Grid.enclose(x,bits) for x in response) for response in base)
    current=tuple(Grid.enclose(x,bits,meter) for x in query.inherited)
    target=tuple(Grid.enclose(x,bits) for x in query.target)
    errors=[]
    for group in query.groups:
        for leaf in group:
            meter.bounded_leaf_responses+=1
            weights=tuple(Grid.enclose(w,bits,meter) for w in leaf.weights)
            value=[]
            for j in range(4):
                total=Grid(0,0,bits)
                for w,v in zip(weights,base): total=total.add(w.mul(v[j],meter),meter)
                value.append(total)
            current=grid_qmul(tuple(value),current,meter)
        error=Grid(0,0,bits)
        for x,y in zip(current,target): error=error.add(x.add(y.neg(),meter).absolute(),meter)
        errors.append(error.fractions())
    verdict=None
    if errors[-1][0]>=query.tolerance/2 or any(hi<=query.tolerance for lo,hi in errors[:-1]):
        verdict=False
    elif errors[-1][1]<query.tolerance/2 and all(lo>query.tolerance for lo,hi in errors[:-1]):
        verdict=True
    return PreviewCertificate(query.digest,bits,verdict,tuple(errors))


def adaptive_preview(query,meter,precisions=(24,48,80,112)):
    if not precisions or any(type(b) is not int or not 1<=b<=4096 for b in precisions):
        raise ValueError('an explicit finite precision policy is required')
    certificate=None
    for bits in precisions:
        certificate=preview(query,bits,meter)
        if certificate.verdict is not None: return certificate
    return certificate  # UNDETERMINED stays unresolved; no silent rounding.


def verify_preview(query,certificate,meter):
    if (type(certificate) is not PreviewCertificate or certificate.query_digest!=query.digest
            or certificate!=preview(query,certificate.bits,meter)):
        raise ValueError('the original word, boundary, inheritance, policy or interval proof changed')
    return True


def exact_preview(query,meter):
    """Independent original TE arithmetic: the oracle, not the fast filter."""
    current=query.inherited;errors=[]
    for group in query.groups:
        for leaf in group:
            meter.exact_retained_responses+=1
            current=tuple(qmul(leaf.kernel(query.context),current))
        errors.append(sum(abs(x-y) for x,y in zip(current,query.target)))
    verdict=errors[-1]<query.tolerance/2 and all(e>query.tolerance for e in errors[:-1])
    return verdict,tuple(errors),current


def query_from_first(first,context,origin):
    word=first.residue.terminal_operation.cell.beta
    return WordQuery(tuple(a.leaves() for a in word),context,
        first.residue.terminal_operation.cell.start.live.accumulated,
        first.fixed_result,first.tolerance,origin)


def query_from_macro(actual,context,origin):
    return WordQuery(tuple(r.residue.terminal_operation.leaves() for r in actual.actual_records),context,
        actual.actual_records[-1].actual_endpoint,embedded.port.FIXED_RESULT,embedded.port.EPSILON,origin)
