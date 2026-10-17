"""RR45: one local flower ends at its first certified consumer boundary.

The chosen level-two consumer cell is the motion unit. Lower preparation
closures are internal resources. No next request or context is emitted here.
The affine representative rule is an explicit input, bound before arrival.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

from persistent_correction_cycle import (
    fixtures_sequence, request_boundary, accept_context, resolve_open,
    execute_producer, publish_producer, consume_produced, event, available,
    ExecutionState, UpperState, context, qmul, decode, encode, replay_trace,
)
from certified_correction_release import active_leaf
from recursive_upper_decoder import (
    action_matrix, rref, AffineLetter, promote_word, regular,
)
from closure_native_context_source import boundary_readout, generated_context, ContextPolicy


@dataclass(frozen=True)
class SolutionRule:
    null_shift: Q=Q(0)

    def __post_init__(self):
        object.__setattr__(self, 'null_shift', Q(self.null_shift))


def null_direction(y, library):
    """Public pivot order fixes the one remaining normalized action-null axis."""
    matrix=action_matrix(y, library)
    reduced,pivots=rref(matrix)
    if len(library)!=6 or len(pivots)!=5:
        raise ValueError('the declared regular six-generator chart is required')
    free=next(j for j in range(6) if j not in pivots)
    delta=[Q(0)]*6
    delta[free]=Q(1)
    for row,pivot in zip(reduced,pivots):
        delta[pivot]=-row[free]
    assert all(sum(a*b for a,b in zip(row,delta))==0 for row in matrix)
    return tuple(delta)


def select_representative(engine, rule):
    if engine.phase!='PLANNED':
        raise ValueError('only a planned unexecuted correction can be selected')
    p=engine.pending
    leaf=p.plan.leaf
    delta=null_direction(p.arrived_context,engine.library)
    chosen=AffineLetter(tuple(w+rule.null_shift*d for w,d in zip(leaf.weights,delta)),leaf.library)
    if not active_leaf(chosen) or chosen.kernel(p.arrived_context)!=p.plan.wanted_action:
        raise ValueError('the declared representative must remain active with the same current response')
    plan=replace(p.plan,leaf=chosen)
    return event(engine,'correction-representative-selected',pending=replace(p,plan=plan))


@dataclass(frozen=True)
class FlowerEntry:
    checkpoint: object
    head: object
    result: tuple
    solution_rule: SolutionRule
    consumer_level: int=2


@dataclass(frozen=True)
class FlowerExit:
    entry: FlowerEntry
    consumer_cell: object
    higher_operation: object
    consumer_after: ExecutionState
    lower_after: ExecutionState
    stock_after: tuple
    events: tuple
    route: str
    produced_operation: object=None


@dataclass(frozen=True)
class Flower:
    entry: FlowerEntry
    engine: object
    status: str
    exit: object=None


def capture(entry,engine):
    base=entry.checkpoint
    if len(engine.rounds)==len(base.rounds)+1:
        if (engine.phase!='IDLE' or engine.pending is not None
                or len(engine.outputs)!=len(base.outputs)+1):
            raise ValueError('one complete consumer closure must end the unit')
        trace=engine.rounds[-1]
        operation=engine.outputs[-1]
        cell=operation.cell
        if (trace.pending.head!=entry.head or cell.beta[0]!=entry.head
                or cell.target!=entry.result or operation.level!=entry.consumer_level+1
                or promote_word(cell)!=operation or cell.endpoint!=engine.upper
                or cell.start!=trace.pending.consumer_start):
            raise ValueError('flower exit does not match its fixed entry and certificate')
        issue=trace.pending.issue
        receipt=FlowerExit(entry,cell,operation,engine.upper,engine.lower,engine.stock,
                          engine.events[len(base.events):],trace.route,
                          issue.operation if issue is not None else None)
        return Flower(entry,engine,'COMPLETE',receipt)
    if len(engine.rounds)!=len(base.rounds) or len(engine.outputs)!=len(base.outputs):
        raise ValueError('this wrapper accepts exactly one new consumer unit')
    states={'WAIT_CONTEXT':'WAIT_CONTEXT','OPEN':'OPEN','PLANNED':'PLANNED',
            'LOWER_CLOSED':'LOWER_CLOSED','AVAILABLE':'AVAILABLE',
            'ZERO_STOP':'HEAD_ZERO','CHART_STOP':'OUTSIDE_CERTIFIED_CHART'}
    if engine.phase not in states:
        raise ValueError('unrecognized incomplete flower phase')
    return Flower(entry,engine,states[engine.phase])


def begin_flower(checkpoint,head=None,solution_rule=SolutionRule()):
    if not isinstance(solution_rule,SolutionRule):
        raise TypeError('a declared solution rule is required')
    waiting=request_boundary(checkpoint,head)
    entry=FlowerEntry(checkpoint,waiting.pending.head,waiting.pending.result,solution_rule)
    return capture(entry,waiting)


def arrive(flower,y):
    if flower.status!='WAIT_CONTEXT':
        raise ValueError('one context arrival belongs to the waiting unit only')
    return capture(flower.entry,accept_context(flower.engine,y))


def advance(flower):
    # Completion is absorbing at this API: there is no automatic next request.
    if flower.status in ('COMPLETE','WAIT_CONTEXT','HEAD_ZERO','OUTSIDE_CERTIFIED_CHART'):
        return flower
    engine=flower.engine
    if flower.status=='OPEN':
        engine=resolve_open(engine)
        if engine.phase=='PLANNED':
            engine=select_representative(engine,flower.entry.solution_rule)
    elif flower.status=='PLANNED':
        engine=execute_producer(engine)
    elif flower.status=='LOWER_CLOSED':
        engine=publish_producer(engine)
    elif flower.status=='AVAILABLE':
        engine=consume_produced(engine)
    else:
        raise ValueError('unrecognized flower status')
    return capture(flower.entry,engine)


def finish(flower):
    while flower.status in ('OPEN','PLANNED','LOWER_CLOSED','AVAILABLE'):
        flower=advance(flower)
    return flower


def one_flower(checkpoint,y,head=None,solution_rule=SolutionRule()):
    return finish(arrive(begin_flower(checkpoint,head,solution_rule),y))


@dataclass(frozen=True)
class ConnectionProbe:
    source_exit: FlowerExit
    staged: ExecutionState
    response: tuple
    status: str
    decoded: object=None


def probe_higher_connection(receipt,y):
    """Second problem, read-only: a new receiver attempts the exported action."""
    y=context(y)
    staged=ExecutionState(UpperState(y,receipt.consumer_after.live.accumulated),
                          receipt.consumer_after.executed_word)
    response=tuple(qmul(receipt.higher_operation.kernel(y),staged.live.accumulated))
    if not regular(y,receipt.entry.checkpoint.library):
        return ConnectionProbe(receipt,staged,response,'OUTSIDE_CERTIFIED_CHART')
    decoded=decode(staged,(receipt.higher_operation,),(receipt.entry.result,))
    return ConnectionProbe(receipt,staged,response,
                           'CONNECTED' if decoded.outputs else 'NO_TERMINAL_PREFIX',decoded)


def solution_pair():
    initial,ys,_=fixtures_sequence()
    return initial,ys[0],one_flower(initial,ys[0]),one_flower(initial,ys[0],solution_rule=SolutionRule(1))


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    initial,y,left,right=solution_pair()
    waiting=begin_flower(initial)
    check('entry binds current states, available head, result and selection rule before arrival',
          waiting.status=='WAIT_CONTEXT' and waiting.engine.pending.arrived_context is None
          and waiting.entry.checkpoint==initial and waiting.engine.upper==initial.upper
          and waiting.engine.lower==initial.lower and advance(waiting)==waiting)
    opened=arrive(waiting,y)
    planned=advance(opened)
    issued=advance(planned)
    published=advance(issued)
    complete=advance(published)
    check('the lower helper closure does not complete the consumer flower',
          issued.status=='LOWER_CLOSED' and issued.exit is None
          and issued.engine.outputs==initial.outputs and issued.engine.upper==opened.engine.upper
          and len(issued.engine.lower.executed_word)==len(initial.lower.executed_word)+1)
    unavailable=False
    try:
        available(issued.engine,issued.engine.pending.issue.operation)
    except ValueError:
        unavailable=True
    check('actual lower certification must precede publication and same-level consumption',
          unavailable and published.status=='AVAILABLE' and complete==left,
          events=[e.kind for e in left.exit.events])
    cells=(left.exit.consumer_cell,right.exit.consumer_cell)
    check('one flower closes at the first nonempty certified consumer boundary',
          all(len(c.beta)==2 and c.target==initial.result for c in cells)
          and opened.engine.pending.trial_response==(Q(6),0,0,0)
          and all(c.endpoint.live.accumulated==initial.result for c in cells),
          head_trial=opened.engine.pending.trial_response,terminal_length=2,result=initial.result)
    check('closure stops without creating a request or context for another flower',
          left.status==right.status=='COMPLETE' and left.engine.pending is None
          and len(left.engine.rounds)==len(initial.rounds)+1
          and left.exit.events[-1].kind=='upper-cell-closed:produced'
          and advance(left) is left and finish(left) is left,
          next_requests=0,next_context_messages=0)
    check('the completed exit keeps exact source words, certificates, stock and both histories',
          left.exit.consumer_after.executed_word[:len(initial.upper.executed_word)]==initial.upper.executed_word
          and left.exit.lower_after.executed_word[:len(initial.lower.executed_word)]==initial.lower.executed_word
          and left.exit.stock_after[:len(initial.stock)]==initial.stock
          and left.exit.produced_operation.cell.endpoint==left.exit.lower_after
          and left.exit.consumer_cell.beta[1]==left.exit.produced_operation
          and replay_trace(initial,left.engine) and replay_trace(initial,right.engine),
          lower_tape=len(left.exit.lower_after.executed_word),consumer_tape=len(left.exit.consumer_after.executed_word),
          stock=len(left.exit.stock_after),higher_operation_level=left.exit.higher_operation.level)
    lp=left.engine.rounds[-1].pending.plan;rp=right.engine.rounds[-1].pending.plan
    check('different explicit representative rules have equal current correction and closure',
          lp.wanted_action==rp.wanted_action==(Q(-1,6),0,0,0)
          and lp.leaf.kernel(y)==rp.leaf.kernel(y)==lp.wanted_action
          and lp.lower_target==rp.lower_target and left.exit.consumer_after.live==right.exit.consumer_after.live
          and left.exit.lower_after.live==right.exit.lower_after.live,
          null_direction=null_direction(y,initial.library),canonical_weights=lp.leaf.weights,
          shifted_weights=rp.leaf.weights,current_correction=lp.wanted_action,producer_target=lp.lower_target)
    ports=[boundary_readout(f.exit.produced_operation) for f in (left,right)]
    later=[generated_context(f.exit.produced_operation,ContextPolicy('direct')) for f in (left,right)]
    normalized=[generated_context(f.exit.produced_operation,ContextPolicy('normalized')) for f in (left,right)]
    check('the same visible result retains different exact residues and optional next-context readouts',
          left.exit.consumer_cell!=right.exit.consumer_cell
          and left.exit.higher_operation!=right.exit.higher_operation
          and left.exit.stock_after!=right.exit.stock_after
          and ports[0]!=ports[1] and later[0]!=later[1] and normalized[0]!=normalized[1],
          boundary_readouts=ports,optional_direct_contexts=later,optional_normalized_contexts=normalized,
          scope='read-only connection diagnostics; no next motion or emission inside the flower')
    probe=context([[Q(3,2),0,0],[0,Q(3,4),0],[0,0,Q(-5,4)]])
    values=[f.exit.higher_operation.kernel(probe) for f in (left,right)]
    check('the retained difference also changes actual exported action at one common later context',
          values[0]!=values[1],common_context=probe,exported_action_values=values)
    probes=[probe_higher_connection(left.exit,v) for v in (y,initial.upper.live.context)]
    check('a separate successful or unsuccessful connection cannot revoke completed closure',
          {p.status for p in probes}=={'CONNECTED','NO_TERMINAL_PREFIX'}
          and all(p.source_exit is left.exit for p in probes) and advance(left) is left,
          connection_statuses=[p.status for p in probes])
    _,ys,zero=fixtures_sequence()
    blocked=one_flower(initial,zero)
    singular=context([[0,0,0],[0,0,0],[0,0,1]])
    outside=one_flower(initial,singular)
    check('logical head obstruction and chart exclusion are incomplete units, not completed stops',
          blocked.status=='HEAD_ZERO' and outside.status=='OUTSIDE_CERTIFIED_CHART'
          and blocked.exit is None and outside.exit is None
          and blocked.engine.upper.executed_word==outside.engine.upper.executed_word==initial.upper.executed_word
          and outside.engine.pending.decoded is None
          and tuple(qmul(initial.designated_head.kernel(singular),initial.upper.live.accumulated))==initial.result,
          statuses=[blocked.status,outside.status],chart_case_response_matches_result=True)
    # These are separate explicit units; the first immutable receipt remains complete.
    following=one_flower(left.engine,zero)
    check('failure of a separately requested next flower preserves the prior completed unit',
          following.status=='HEAD_ZERO' and following.engine.rounds[:1]==left.engine.rounds
          and following.engine.outputs==left.engine.outputs
          and following.engine.stock==left.engine.stock and left.status=='COMPLETE')
    direct=one_flower(initial,ys[4])
    reused=one_flower(initial,initial.upper.live.context)
    check('direct closure and existing compensation end the same unit protocol without production',
          direct.status==reused.status=='COMPLETE' and direct.exit.route=='head' and reused.exit.route=='reused'
          and direct.exit.produced_operation is None and reused.exit.produced_operation is None
          and direct.engine.lower.executed_word==reused.engine.lower.executed_word==initial.lower.executed_word,
          routes=[direct.exit.route,reused.exit.route],terminal_lengths=[len(direct.exit.consumer_cell.beta),len(reused.exit.consumer_cell.beta)])
    for phase in (waiting,opened,planned,issued,published,complete):
        if phase.status!='WAIT_CONTEXT':
            assert finish(phase)==left
    check('pauses inside a flower preserve one entry, first closure and full exit',True,phase_checkpoints=6)
    root=Path(__file__).resolve().parent
    previous=json.loads((root/'closure_native_context_source_result.json').read_text(encoding='utf-8'))
    paths=['single_flower_model.py','test_single_flower_model.py',*previous['source_sha256']]
    return dict(note='RR45',passed=True,groups=len(checks),checks=checks,
                source_base_commit='fe024d7d65cd89b7baf4bded06d8990a2d506eda',
                unit='one first-certified level-two consumer cell; lower closure is internal preparation',
                completed_status='COMPLETE',next_connection='separate second problem; no automatic request or emission',
                rules_compared=[0,1],fixed_result=initial.result,
                supplied_conditions=['committed initial exact histories and six-generator frame',
                                     'published same-level stock and designated head','fixed nonzero result and arrived context',
                                     'continued lower producer, private target and publication gate',
                                     'bounded existing suffix search and explicit affine representative rule'],
                limits=['local operational minimum, not a proof of globally fewest components',
                        'local closure certification is not long-term stability of a connection rule',
                        'context/readout generation belongs to composition; full residue is retained independently',
                        'general future-result selection and future-origin C are not derived'],
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('single_flower_model_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'],unit=data['unit'])))
