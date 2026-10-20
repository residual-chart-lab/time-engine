"""RR62: reuse actual retained S and produce a distinct current T.

Words HHST / HHTS close locally at -1. Their actual level-three outputs
are subsequently tested at the independently specified C, target +1.
"""
from dataclasses import dataclass,replace
from fractions import Fraction as Q
import demand_filter as f
from demand_filter import prior,d,te
from future_pullback import cycle,NEG

@dataclass(frozen=True)
class Execution:
    scope_digest: str
    resolution: f.Resolution
    word: str
    retained_source: object
    new_source: object
    closed_engine: object
    terminal: object
    prefix_errors: tuple

def execute(archive,entry,scope,demand,resolution,word,control_test=None):
    f.verify_demand(archive,entry,scope,demand)
    if scope.observation!=f.ACTIONS:raise ValueError('a feasibility-only certificate cannot authorize execution')
    checked=f.resolve(archive,entry,scope,demand,f.Meter())
    if resolution!=checked or not resolution.feasible or resolution.control is None:
        raise ValueError('a bound feasible actuator resolution is required')
    if word not in scope.words:raise ValueError('current must choose one of the two declared free words')
    v=resolution.control if control_test is None else Q(control_test)
    if not scope.domain[0]<=v<=scope.domain[1]:raise ValueError('current actuator range exceeded')
    history=archive.history(entry);prior.previous.verify_flight(history)
    before=history.first.closed_engine;retained=history.first.residue.source
    te.port.available(before,retained)
    arrived=te.accept_context(te.request_boundary(before),history.first.residue.internal_context)
    if arrived.phase!='OPEN':raise ValueError('the unchanged current flower must remain open after its head')
    p=arrived.pending
    leaf=d.AffineLetter(tuple(a+v*b for a,b in zip(entry.reference.weights,entry.axis)),entry.reference.library)
    wanted=tuple(cycle.qmul(p.result,cycle.inverse(p.trial_response)))
    if leaf.kernel(p.arrived_context)!=wanted:raise ValueError('new T must keep the local source response')
    plan=cycle.CorrectionPlan(p.decoded,arrived.lower,p.trial_response,wanted,leaf,
        tuple(cycle.qmul(wanted,arrived.lower.live.accumulated)))
    planned=te.port.event(arrived,'rr62-demand-bound-source-planned',phase='PLANNED',pending=replace(p,plan=plan))
    ready=te.port.publish_producer(te.port.execute_producer(planned));new=ready.pending.issue.operation
    start=ready.pending.consumer_start
    engine=te.port.event(ready,'rr62-current-word-chosen',upper=start)
    ops=tuple({'H':p.head,'S':retained,'T':new}[c] for c in word);errors=[]
    for op in ops:
        te.port.available(engine,op)
        engine=te.port.event(engine,'rr62-current-action-executed',upper=te.port.step(op,engine.upper))
        errors.append(sum(abs(a-b) for a,b in zip(engine.upper.live.accumulated,NEG)))
    decoded=te.port.decode(start,ops,(NEG,))
    if (engine.upper.live.accumulated!=NEG or any(x<=te.port.EPSILON for x in errors[:-1])
            or len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries or decoded.state!=engine.upper):
        raise ValueError('the current flower must close exactly at the first nonempty terminal boundary')
    terminal=decoded.outputs[0];closed=te.port.close_round(engine,decoded,'rr62-retained-plus-new')
    if (closed.events[:len(before.events)]!=before.events or closed.stock!=before.stock+(new,)
            or closed.rounds[:-1]!=before.rounds or closed.outputs!=before.outputs+(terminal,)):
        raise ValueError('the actual earlier history and stock must survive unchanged')
    record=Execution(scope.digest,resolution,word,retained,new,closed,terminal,tuple(errors))
    return record

def verify_execution(archive,entry,scope,demand,record,control_test=None):
    if type(record) is not Execution or record!=execute(archive,entry,scope,demand,record.resolution,record.word,control_test):
        raise ValueError('the actual word, inherited entry or retained/new source changed')
    return True

def future(archive,entry,scope,demand,record,control_test=None):
    verify_execution(archive,entry,scope,demand,record,control_test)
    c=scope.requirement
    if record.closed_engine.upper.live.accumulated!=c.inherited or record.terminal not in record.closed_engine.outputs:
        raise ValueError('future inherits the actual current endpoint and output')
    if record.terminal.level!=3:raise ValueError('future reads one certified level-three output')
    start=te.port.ExecutionState(te.port.UpperState(c.context,c.inherited),())
    trial=te.port.step(record.terminal,start);decoded=te.port.decode(start,(record.terminal,),(c.target,))
    ok=bool(len(decoded.outputs)==1 and not decoded.tail and not decoded.boundaries)
    if ok and (trial.live.accumulated!=c.target or decoded.state!=trial or decoded.outputs[0].level!=4
               or te.port.promote_word(decoded.outputs[0].cell)!=decoded.outputs[0]):
        raise ValueError('the exact upper occurrence does not match its C and actual inheritance')
    return trial,decoded,ok
