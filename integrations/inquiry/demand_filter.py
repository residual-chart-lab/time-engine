"""RR62: C and the requested observation determine residual inspection.

Archive authentication is exact and separate. Assessment reads an authenticated
envelope, never its retained scalar. No certificate authorizes deletion.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
import future_pullback as prior
from future_pullback import d,te

EXISTS='existence-of-certified-current-control'
ACTIONS='full-certified-current-action-set'
WORDS=('HHST','HHTS')

@dataclass
class Meter:
    exact_shift_reads: int=0

@dataclass(frozen=True)
class Entry:
    history_digest: str
    pair_digest: str
    reference: object
    head: object
    axis: tuple
    envelope: tuple

    @property
    def digest(self):
        return d.fingerprint((self.history_digest,self.pair_digest,
            self.reference.weights,d.library_key(self.reference.library),self.axis,self.envelope))

class Archive:
    """Owns the full retained objects. Entry validation never discards them."""
    def __init__(self):self._entries={};self._histories={}

    def register(self,history,envelope=(Q(-1,1024),Q(1,1024))):
        head,cert,axis,_=prior.data(history)
        lo,hi=map(Q,envelope)
        if lo>hi or not lo<=cert.shift<=hi:raise ValueError('the declared residual envelope is not certified')
        entry=Entry(history.digest,history.pair.digest,history.pair.representative,head,axis,(lo,hi))
        self._entries[entry.digest]=entry;self._histories[entry.digest]=history
        return entry

    def verify(self,entry):
        if type(entry) is not Entry or self._entries.get(entry.digest)!=entry:
            raise ValueError('the authenticated archive reference or envelope changed')
        return True

    def history(self,entry):
        self.verify(entry);return self._histories[entry.digest]

    def read_shift(self,entry,meter):
        self.verify(entry);meter.exact_shift_reads+=1
        return self._histories[entry.digest].pair.shift

@dataclass(frozen=True)
class Scope:
    entry_digest: str
    requirement: prior.Requirement
    domain: tuple=(Q(-64),Q(64))
    observation: str=ACTIONS
    words: tuple=WORDS

    def __post_init__(self):
        object.__setattr__(self,'domain',tuple(map(Q,self.domain)))
        if (type(self.requirement) is not prior.Requirement or len(self.domain)!=2 or self.domain[0]>self.domain[1]
                or self.observation not in (EXISTS,ACTIONS) or self.words!=WORDS):
            raise ValueError('the fixed C, ordered actuator interval, observation and word family are required')

    @property
    def digest(self):return d.fingerprint((self.entry_digest,self.requirement.digest,self.domain,self.observation,self.words))

@dataclass(frozen=True)
class Demand:
    scope_digest: str
    h: Q
    a: Q
    g: Q
    control_interval: object
    needs_exact_shift: bool
    verdict: object
    status: str

    @property
    def digest(self):return d.fingerprint(tuple(self.__dict__.values()))

def control_at(s,h,a,g):
    if not h or not g or not a+s*g:return None
    return (-1/(h*h*(a+s*g))-a)/g

def assess(archive,entry,scope):
    archive.verify(entry)
    if type(scope) is not Scope or scope.entry_digest!=entry.digest:raise ValueError('scope belongs to another retained entry')
    y=scope.requirement.context;library=entry.reference.library
    h=prior.scalar(entry.head.kernel(y));a=prior.scalar(entry.reference.kernel(y))
    g=prior.scalar(prior.direction_response(entry.axis,library,y))
    def out(interval,needs,verdict,status):return Demand(scope.digest,h,a,g,interval,needs,verdict,status)
    if not h:return out(None,False,False,'EMPTY_ZERO_HEAD')
    if not g:return out(None,False,False,'EMPTY_BLIND')  # -h**2*a**2 cannot equal +1
    if not te.port.regular(y,library):return out(None,False,None,'OUTSIDE_CERTIFIED_CHART')
    lo,hi=entry.envelope
    ends=tuple(sorted((a+lo*g,a+hi*g)))
    if ends[0]<=0<=ends[1]:return out(None,True,None,'ENVELOPE_CROSSES_ZERO_SOURCE')
    interval=(control_at(lo,h,a,g),control_at(hi,h,a,g))
    if interval[0]>interval[1]:raise ArithmeticError('the control law must be strictly increasing between poles')
    left,right=scope.domain
    if interval[1]<left or interval[0]>right:return out(interval,False,False,'EMPTY_DOMAIN_FOR_ENVELOPE')
    wholly_inside=left<=interval[0] and interval[1]<=right
    if scope.observation==EXISTS and wholly_inside:return out(interval,False,True,'EXISTENCE_CERTIFIED_WITHOUT_SHIFT')
    return out(interval,True,None,'ACTION_NEEDS_SHIFT' if scope.observation==ACTIONS else 'EXISTENCE_NEEDS_REFINEMENT')

def verify_demand(archive,entry,scope,demand):
    if type(demand) is not Demand or demand!=assess(archive,entry,scope):
        raise ValueError('entry, C, observation, domain or inspection proof changed')
    return True

@dataclass(frozen=True)
class Resolution:
    scope_digest: str
    demand_digest: str
    feasible: object
    control: object
    exact_shift_used: bool

def resolve(archive,entry,scope,demand,meter):
    verify_demand(archive,entry,scope,demand)
    if not demand.needs_exact_shift:
        return Resolution(scope.digest,demand.digest,demand.verdict,None,False)
    s=archive.read_shift(entry,meter)
    v=control_at(s,demand.h,demand.a,demand.g)
    feasible=v is not None and scope.domain[0]<=v<=scope.domain[1]
    # A boolean proof never grants a numerical actuator or an execution.
    return Resolution(scope.digest,demand.digest,feasible,v if feasible and scope.observation==ACTIONS else None,True)

def exact_oracle(archive,entry,scope):
    """Always read the retained future response; verification control only."""
    history=archive.history(entry);y=scope.requirement.context
    h=prior.scalar(entry.head.kernel(y));a=prior.scalar(entry.reference.kernel(y))
    g=prior.scalar(prior.direction_response(entry.axis,entry.reference.library,y))
    retained=prior.scalar(history.pair.original.kernel(y))
    if not h or not g:return False,None
    if not te.port.regular(y,entry.reference.library):return None,None
    if not retained:return False,None
    v=(-1/(h*h*retained)-a)/g
    feasible=scope.domain[0]<=v<=scope.domain[1]
    return feasible,v if feasible and scope.observation==ACTIONS else None
