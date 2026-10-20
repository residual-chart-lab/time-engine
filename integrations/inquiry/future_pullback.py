"""RR61: independent C, present control law, equal-information forward control.

Exact diagonal scalar subclass; original histories are never rewritten.
Neither decision procedure searches completed future paths.
"""
from dataclasses import dataclass,replace
from fractions import Fraction as Q
import fibre_geometry as geom
from fibre_geometry import previous,d,te
import persistent_correction_cycle as cycle
from word_fibre import first_return,accepts_future_parity

ONE=(Q(1),Q(0),Q(0),Q(0))
NEG=tuple(-x for x in ONE)

def scalar(q):
    if len(q)!=4 or any(q[1:]):raise ValueError('the declared scalar diagonal subclass is required')
    return q[0]

def diagonal(x):
    x=Q(x)
    return te.port.single.context(((x,0,0),(0,1-x,0),(0,0,0)))

@dataclass(frozen=True)
class Requirement:
    context: tuple
    target: tuple=ONE
    inherited: tuple=NEG

    def __post_init__(self):
        y=te.port.single.context(self.context)
        if y!=diagonal(y[0][0]) or self.target!=ONE or self.inherited!=NEG:
            raise ValueError('RR61 declares diagonal(x,1-x,0), target +1 and inherited -1')
        object.__setattr__(self,'context',y)

    @property
    def digest(self):return d.fingerprint((self.context,self.target,self.inherited))

def data(history):
    previous.verify_flight(history)
    f=history.first;y=f.residue.internal_context
    if f.actual_endpoint!=NEG or f.closed_engine.upper.live.accumulated!=NEG:
        raise ValueError('the actual closed history must retain endpoint -1')
    head=f.closed_engine.designated_head
    cert=geom.certify_pair(y,history.pair.original,history.pair.representative)
    axis=cert.coefficient_axis;library=history.pair.original.library
    if (scalar(head.kernel(y))!=Q(-1,9) or scalar(history.pair.original.kernel(y))!=-9
            or any(sum(c*op.apply(y)[j] for c,op in zip(axis,library)) for j in range(4))):
        raise ValueError('the declared current H/S chart is required')
    return head,cert,axis,library

def direction_response(axis,library,y):
    return tuple(sum(c*op.apply(y)[j] for c,op in zip(axis,library)) for j in range(4))

@dataclass(frozen=True)
class Decision:
    history_digest: str
    requirement: Requirement
    domain: tuple
    axis: tuple
    retained_shift: Q
    h: Q
    a: Q
    g: Q
    control: object
    all_controls: bool
    algebraically_feasible: bool
    chart_regular: bool
    status: str
    future_path_enumerations: int=0

    @property
    def digest(self):return d.fingerprint(tuple(v.digest if type(v) is Requirement else v for v in self.__dict__.values()))

def derive(history,requirement,domain=(Q(-64),Q(64))):
    """Pull C back before production: q_future=-b**n=+1 iff n odd, b=-1.

    This decides all primitive first-return H/S words, without constructing
    a completed path or selecting a particular word.
    """
    if type(requirement) is not Requirement:raise ValueError('an explicit independent requirement is required')
    lo,hi=map(Q,domain)
    if lo>hi:raise ValueError('ordered closed actuator domain required')
    head,cert,axis,library=data(history);y=requirement.context
    h=scalar(head.kernel(y));a=scalar(history.pair.representative.kernel(y))
    g=scalar(direction_response(axis,library,y));s=cert.shift
    chart=te.port.regular(y,library)
    control=None;all_controls=False;feasible=False
    if not h:status='EMPTY_ZERO_HEAD'
    elif not g:
        all_controls=h*a==-1;feasible=all_controls
        status='ALL_CONTROLS' if feasible else 'EMPTY_BLIND'
    else:
        control=(-1/h-a)/g-s
        feasible=lo<=control<=hi
        status='ADMISSIBLE' if feasible else 'EMPTY_DOMAIN'
    if feasible and not chart:status='ALGEBRAIC_ONLY'
    return Decision(history.digest,requirement,(lo,hi),axis,s,h,a,g,control,
                    all_controls,feasible,chart,status)

def verify_decision(history,decision):
    if type(decision) is not Decision or decision!=derive(history,decision.requirement,decision.domain):
        raise ValueError('the history, C, actuator domain or pullback evidence changed')
    return True

@dataclass(frozen=True)
class ForwardResult:
    reachable_base_interval: tuple
    intercept: Q
    slope: Q
    control: object
    all_controls: bool
    algebraically_feasible: bool
    chart_regular: bool
    future_path_enumerations: int=0

def forward_reachability(history,requirement,domain=(Q(-64),Q(64))):
    """Ordinary exact forward affine interval reachability, same information.

    Does not call derive. Uses actual retained source directly, rather than
    the reference-source decomposition. Both solvers share the same plant.
    """
    if type(requirement) is not Requirement:raise ValueError('explicit requirement required')
    head,_,axis,library=data(history);y=requirement.context
    lo,hi=map(Q,domain)
    if lo>hi:raise ValueError('ordered closed actuator domain required')
    hv=head.kernel(y)
    b0=scalar(cycle.qmul(hv,history.pair.original.kernel(y)))
    b1=scalar(cycle.qmul(hv,direction_response(axis,library,y)))
    interval=tuple(sorted((b0+b1*lo,b0+b1*hi)))
    all_controls=not b1 and b0==-1
    feasible=interval[0]<=-1<=interval[1]
    control=(-1-b0)/b1 if b1 else None
    return ForwardResult(interval,b0,b1,control,all_controls,feasible,
                         te.port.regular(y,library))

@dataclass(frozen=True)
class CurrentExecution:
    history_digest: str
    decision_digest: str
    control: Q
    word: str
    source: object
    head: object
    closed_engine: object
    terminal: object
    prefix_errors: tuple

def execute_current(history,decision,word,control=None,allow_control_test=False):
    """Current chooses a word; lower production precedes publication/use.

    Explicit test mode permits wrong-control/parity counterfactuals; never
    declares them successful for C. Local certification remains exact.
    """
    verify_decision(history,decision)
    if not first_return(word):raise ValueError('current input must be a primitive first-return word')
    if not allow_control_test and (not accepts_future_parity(word) or not decision.algebraically_feasible
                                  or not decision.chart_regular):
        raise ValueError('current choice outside the certified admissible set')
    if control is None:
        if decision.all_controls:raise ValueError('current must freely choose a control in the interval')
        control=decision.control
    if control is None:raise ValueError('no control available')
    control=Q(control)
    if not decision.domain[0]<=control<=decision.domain[1]:raise ValueError('actuator range exceeded')
    if not allow_control_test and not decision.all_controls and control!=decision.control:
        raise ValueError('a control for another retained history cannot be silently reused')
    before=history.first.closed_engine
    waiting=te.request_boundary(before)
    arrived=te.accept_context(waiting,history.first.residue.internal_context)
    if arrived.phase!='OPEN':raise ValueError('next current flower must be open in the same current chart')
    leaf=d.AffineLetter(tuple(w+control*v for w,v in zip(history.pair.original.weights,decision.axis)),
                        history.pair.original.library)
    p=arrived.pending
    wanted=tuple(cycle.qmul(p.result,cycle.inverse(p.trial_response)))
    if leaf.kernel(p.arrived_context)!=wanted:raise ValueError('current response changed')
    target=tuple(cycle.qmul(wanted,arrived.lower.live.accumulated))
    plan=cycle.CorrectionPlan(p.decoded,arrived.lower,p.trial_response,wanted,leaf,target)
    planned=te.port.event(arrived,'rr61-independent-C-control-planned',phase='PLANNED',
                          pending=replace(p,plan=plan))
    ready=te.port.publish_producer(te.port.execute_producer(planned))
    source=ready.pending.issue.operation;head=ready.pending.head
    start=ready.pending.consumer_start
    engine=te.port.event(ready,'rr61-current-word-chosen',upper=start)
    ops=tuple(head if symbol=='H' else source for symbol in word);errors=[]
    for op in ops:
        te.port.available(engine,op)
        engine=te.port.event(engine,'rr61-current-word-executed',upper=te.port.step(op,engine.upper))
        errors.append(sum(abs(x-y) for x,y in zip(engine.upper.live.accumulated,engine.pending.result)))
    decoded=te.port.decode(start,ops,(engine.pending.result,))
    if (engine.upper.live.accumulated!=NEG or any(e<=te.port.EPSILON for e in errors[:-1])
            or len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries or decoded.state!=engine.upper):
        raise ValueError('current word must close exactly once at its first boundary')
    terminal=decoded.outputs[0]
    if terminal.level!=3 or te.port.promote_word(terminal.cell)!=terminal:
        raise ValueError('actual level-three current output required')
    closed=te.port.close_round(engine,decoded,'rr61-current-control')
    if (closed.events[:len(before.events)]!=before.events or closed.stock!=before.stock+(source,)
            or closed.outputs!=before.outputs+(terminal,) or closed.rounds[:-1]!=before.rounds):
        raise ValueError('original completed history must be retained exactly')
    return CurrentExecution(history.digest,decision.digest,control,word,source,head,closed,terminal,tuple(errors))

def verify_current(history,decision,record,allow_control_test=False):
    if type(record) is not CurrentExecution or record!=execute_current(history,decision,record.word,
            record.control,allow_control_test):raise ValueError('actual current execution changed')
    return True

def read_future(history,decision,record,allow_control_test=False):
    """Separate higher-level reader, after actual current control execution."""
    verify_current(history,decision,record,allow_control_test)
    c=decision.requirement
    if record.closed_engine.upper.live.accumulated!=c.inherited:
        raise ValueError('future inheritance must equal the actual current endpoint')
    start=te.port.ExecutionState(te.port.UpperState(c.context,c.inherited),())
    if record.terminal not in record.closed_engine.outputs or record.terminal.level!=3:
        raise ValueError('future may use only the actually certified level-three current output')
    trial=te.port.step(record.terminal,start)
    decoded=te.port.decode(start,(record.terminal,),(c.target,))
    closed=bool(len(decoded.outputs)==1 and not decoded.tail and not decoded.boundaries)
    if closed and (trial.live.accumulated!=c.target or decoded.state!=trial
                   or decoded.outputs[0].level!=4 or te.port.promote_word(decoded.outputs[0].cell)!=decoded.outputs[0]):
        raise ValueError('exact future certificate does not match its actual entry')
    return trial,decoded,closed
