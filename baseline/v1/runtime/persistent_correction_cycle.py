"""RR43: persistent level-one production and repeated level-two consumption.

Requests bind an available action to the current exact consumer state. Source
certificates stay immutable. Arrivals and producer resources remain supplied.
Level-three outputs use a separate port; they never enter level-two stock.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import hashlib
import json

from certified_correction_release import (
    fixtures, primitive_fixture, correction_leaf, CorrectionPlan, LowerIssue,
    ExecutionState, UpperState, NEG_ONE, decode, qmul, inverse, encode,
    regular, kernel, resume, promote_word,
)
from fixed_result_compatibility import context


@dataclass(frozen=True)
class CycleEvent:
    index: int
    round_number: int
    kind: str
    lower: ExecutionState
    upper: ExecutionState
    stock: tuple


@dataclass(frozen=True)
class PendingRound:
    number: int
    head: object
    result: tuple
    lower_before: ExecutionState
    upper_before: ExecutionState
    stock_before: tuple
    arrived_context: object=None
    consumer_start: object=None
    decoded: object=None
    trial_response: object=None
    plan: object=None
    issue: object=None


@dataclass(frozen=True)
class RoundTrace:
    pending: PendingRound
    decoded: object
    route: str
    lower_after: ExecutionState
    stock_after: tuple


@dataclass(frozen=True)
class PersistentEngine:
    lower: ExecutionState
    upper: ExecutionState
    stock: tuple
    outputs: tuple
    rounds: tuple
    events: tuple
    library: tuple
    designated_head: object
    result: tuple
    max_existing_suffix: int=2
    phase: str='IDLE'
    pending: object=None


def event(engine,kind,**changes):
    fresh=replace(engine,**changes)
    number=fresh.pending.number if fresh.pending else len(fresh.rounds)
    item=CycleEvent(len(engine.events),number,kind,fresh.lower,fresh.upper,fresh.stock)
    return replace(fresh,events=engine.events+(item,))


def boot(experiment,result=NEG_ONE,max_existing_suffix=2):
    f=tuple(Q(x) for x in result);inverse(f)
    if not isinstance(max_existing_suffix,int) or not 1<=max_existing_suffix<=2:
        raise ValueError('the declared stock search bound is one or two letters')
    inherited=experiment.request.inherited
    if any(a.level!=1 for a in inherited.executed_word):
        raise ValueError('the initial producer must have a committed level-one tape')
    if any(a.level!=2 or promote_word(a.cell)!=a for a in experiment.stock):
        raise ValueError('verified level-two initial stock required')
    initial=CycleEvent(0,0,'engine-started',inherited,inherited,experiment.stock)
    return PersistentEngine(inherited,inherited,experiment.stock,(),(),(initial,),
        experiment.request.operation.leaves()[0].library,experiment.request.operation,f,
        max_existing_suffix=max_existing_suffix)


def available(engine,operation):
    if operation.level!=2 or operation not in engine.stock:
        raise ValueError('the requested action must be a published level-two stock item')


def request_boundary(engine,head=None):
    if engine.phase!='IDLE':
        raise ValueError('the current request must close before a new one is issued')
    head=engine.designated_head if head is None else head
    available(engine,head)
    # Current state is bound here, without receiving a future-context value.
    pending=PendingRound(len(engine.rounds)+1,head,engine.result,
                         engine.lower,engine.upper,engine.stock)
    return event(engine,'boundary-requested',phase='WAIT_CONTEXT',pending=pending)


def close_round(engine,decoded,route):
    pending=engine.pending
    if len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries:
        raise ValueError('exactly one complete consumer cell must close')
    if decoded.outputs[0].level!=3 or decoded.outputs[0].cell.beta[0]!=pending.head:
        raise ValueError('the output must preserve the designated level-two head')
    trace=RoundTrace(pending,decoded,route,engine.lower,engine.stock)
    return event(engine,'upper-cell-closed:'+route,upper=decoded.state,
                 outputs=engine.outputs+decoded.outputs,rounds=engine.rounds+(trace,),
                 phase='IDLE',pending=None)


def accept_context(engine,later_context):
    if engine.phase!='WAIT_CONTEXT':
        raise ValueError('a fixed request must precede context arrival')
    y=context(later_context)
    lower=ExecutionState(UpperState(y,engine.lower.live.accumulated),engine.lower.executed_word)
    upper=ExecutionState(UpperState(y,engine.upper.live.accumulated),engine.upper.executed_word)
    pending=replace(engine.pending,arrived_context=y,consumer_start=upper)
    fresh=event(engine,'context-arrived',lower=lower,upper=upper,pending=pending)
    if not regular(y,engine.library):
        return event(fresh,'stopped:outside-certified-chart',phase='CHART_STOP')
    decoded=decode(upper,(pending.head,),(pending.result,))
    response=tuple(qmul(pending.head.kernel(y),upper.live.accumulated))
    pending=replace(pending,decoded=decoded,trial_response=response)
    fresh=replace(fresh,pending=pending)
    if decoded.outputs:
        return close_round(fresh,decoded,'head')
    if not any(response):
        return event(fresh,'stopped:zero-trial',phase='ZERO_STOP')
    return replace(fresh,phase='OPEN')


def resolve_open(engine):
    if engine.phase!='OPEN':
        raise ValueError('a regular nonzero open tail is required')
    pending=engine.pending;y=pending.arrived_context
    wanted=tuple(qmul(pending.result,inverse(pending.trial_response)))
    # Deterministic bounded search uses only already published stock and Y.
    # No absence result from this search is called a global impossibility.
    for length in range(1,engine.max_existing_suffix+1):
        for word in product(engine.stock,repeat=length):
            if kernel(word,y)==wanted:
                decoded=resume(pending.decoded,extra_word=word)
                return close_round(engine,decoded,'reused')
    leaf=correction_leaf(y,engine.library,wanted)
    target=tuple(qmul(wanted,engine.lower.live.accumulated))
    plan=CorrectionPlan(pending.decoded,engine.lower,pending.trial_response,wanted,leaf,target)
    return event(engine,'correction-planned',phase='PLANNED',pending=replace(pending,plan=plan))


def execute_producer(engine):
    if engine.phase!='PLANNED' or engine.pending.plan.lower_start!=engine.lower:
        raise ValueError('the actual persistent producer must match the planned source start')
    pending=engine.pending;plan=pending.plan
    decoded=decode(engine.lower,(plan.leaf,),(plan.lower_target,))
    if len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries:
        raise ValueError('the continued producer did not close one lower cell')
    operation=decoded.outputs[0]
    if operation.level!=2 or operation.kernel(pending.arrived_context)!=plan.wanted_action:
        raise ValueError('the produced operation has the wrong scale or response')
    issue=LowerIssue(plan,decoded,operation,len(engine.events))
    return event(engine,'lower-cell-closed',phase='LOWER_CLOSED',lower=decoded.state,
                 pending=replace(pending,issue=issue))


def publish_producer(engine):
    if engine.phase!='LOWER_CLOSED':
        raise ValueError('publication requires an already executed lower cell')
    pending=engine.pending;issue=pending.issue
    if (issue.closed_at>=len(engine.events) or issue.decoded.state!=engine.lower
            or issue.operation.cell.start!=issue.plan.lower_start
            or promote_word(issue.operation.cell)!=issue.operation):
        raise ValueError('the actual lower source and issue certificate do not agree')
    return event(engine,'same-level-operation-published',phase='AVAILABLE',
                 stock=engine.stock+(issue.operation,))


def consume_produced(engine):
    if engine.phase!='AVAILABLE' or engine.pending.decoded!=engine.pending.plan.upper_snapshot:
        raise ValueError('the original pending prefix must await the published correction')
    operation=engine.pending.issue.operation
    available(engine,operation)
    return close_round(engine,resume(engine.pending.decoded,extra_word=(operation,)),'produced')


def finish_current(engine):
    if engine.phase=='OPEN':
        engine=resolve_open(engine)
    if engine.phase=='PLANNED':
        engine=execute_producer(engine)
    if engine.phase=='LOWER_CLOSED':
        engine=publish_producer(engine)
    if engine.phase=='AVAILABLE':
        engine=consume_produced(engine)
    return engine


def run_round(engine,y,head=None):
    return finish_current(accept_context(request_boundary(engine,head),y))


@dataclass(frozen=True)
class ScheduleResult:
    engine: PersistentEngine
    unoffered_contexts: tuple
    stop: str


def run_schedule(engine,contexts):
    contexts=tuple(contexts)
    if engine.phase in ('ZERO_STOP','CHART_STOP'):
        return ScheduleResult(engine,contexts,engine.phase)
    if engine.phase in ('OPEN','PLANNED','LOWER_CLOSED','AVAILABLE'):
        engine=finish_current(engine)
    for i,y in enumerate(contexts):
        if engine.phase=='WAIT_CONTEXT':
            engine=finish_current(accept_context(engine,y))
        else:
            engine=run_round(engine,y)
        if engine.phase!='IDLE':
            return ScheduleResult(engine,contexts[i+1:],engine.phase)
    stop='ContextExhausted' if engine.phase=='WAIT_CONTEXT' else 'InputExhausted'
    return ScheduleResult(engine,(),stop)


@dataclass(frozen=True)
class HigherReceipt:
    anchor: ExecutionState
    staged: ExecutionState
    operation: object
    decoded: object


def receive_higher(engine,index=0,later_context=None):
    if engine.phase!='IDLE' or not engine.outputs:
        raise ValueError('a completed consumer history and its higher output are required')
    operation=engine.outputs[index]
    if operation.level!=3:
        raise ValueError('the separate receiver accepts level-three outputs')
    y=context(operation.cell.start.live.context if later_context is None else later_context)
    # A new typed receiver inherits the current checkpoint, including all logs.
    staged=ExecutionState(UpperState(y,engine.upper.live.accumulated),engine.upper.executed_word)
    decoded=decode(staged,(operation,),(engine.result,))
    return HigherReceipt(engine.upper,staged,operation,decoded)


def replay_trace(initial,engine):
    lower=initial.lower;upper=initial.upper;stock=initial.stock
    for trace in engine.rounds:
        p=trace.pending;y=p.arrived_context
        assert p.lower_before==lower and p.upper_before==upper and p.stock_before==stock
        lower=ExecutionState(UpperState(y,lower.live.accumulated),lower.executed_word)
        upper=ExecutionState(UpperState(y,upper.live.accumulated),upper.executed_word)
        assert upper==p.consumer_start
        if trace.route=='produced':
            issue=p.issue
            assert issue.operation.cell.start==lower
            producer=decode(lower,(p.plan.leaf,),(p.plan.lower_target,))
            assert producer==issue.decoded
            lower=producer.state;stock=stock+(issue.operation,)
        direct=decode(upper,trace.decoded.outputs[0].cell.beta,(p.result,))
        assert direct==trace.decoded
        upper=direct.state
        assert lower==trace.lower_after and stock==trace.stock_after
    return lower==engine.lower and upper==engine.upper and stock==engine.stock


def fixtures_sequence():
    ab,_,first,second,zero_context=fixtures()
    _,_,_,policy=primitive_fixture()
    initial=boot(ab)
    contexts=(second,second,policy.probe,policy.probe,first,ab.prepared.endpoint.live.context)
    return initial,contexts,zero_context


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    initial,contexts,zero_context=fixtures_sequence()
    full=run_schedule(initial,contexts);engine=full.engine
    routes=[trace.route for trace in engine.rounds]
    lengths=[len(trace.decoded.outputs[0].cell.beta) for trace in engine.rounds]
    check('one persistent engine closes six rounds with production, reuse and direct closure',
          full.stop=='InputExhausted' and routes==['produced','reused','produced','reused','head','reused']
          and lengths==[2,2,2,2,1,2] and len(engine.outputs)==6,
          routes=routes,terminal_lengths=lengths)
    check('consumer and producer keep different actual states instead of restarting per round',
          len(engine.lower.executed_word)==len(initial.lower.executed_word)+2
          and len(engine.upper.executed_word)==len(initial.upper.executed_word)+sum(lengths)
          and engine.rounds[2].pending.plan.lower_start.live.accumulated==(Q(1,6),0,0,0),
          initial_tape_length=len(initial.lower.executed_word),
          final_lower_length=len(engine.lower.executed_word),final_upper_length=len(engine.upper.executed_word),
          final_lower_value=engine.lower.live.accumulated)
    check('published corrections survive context changes and are reused without new lower execution',
          len(engine.stock)==6 and engine.stock[:4]==initial.stock
          and engine.rounds[1].decoded.outputs[0].cell.beta[1]==engine.stock[4]
          and engine.rounds[3].decoded.outputs[0].cell.beta[1]==engine.stock[5]
          and [len(t.stock_after) for t in engine.rounds]==[5,5,6,6,6,6],
          stock_sizes=[len(t.stock_after) for t in engine.rounds])
    check('same-scale outputs remain on a separate higher port and do not silently become next heads',
          all(a.level==2 for a in engine.stock) and all(a.level==3 for a in engine.outputs))
    check('the whole persistent trace independently replays through the original decoders',replay_trace(initial,engine))
    for cut in range(7):
        first_part=run_schedule(initial,contexts[:cut])
        second_part=run_schedule(first_part.engine,contexts[cut:])
        assert second_part==full
        assert engine.rounds[:cut]==first_part.engine.rounds
    check('pausing between rounds does not reset state, stock or prior certificates',True,all_splits=7)
    waiting=request_boundary(initial)
    arrived=accept_context(waiting,contexts[0])
    planned=resolve_open(arrived)
    issued=execute_producer(planned)
    rejected=False
    try:
        available(issued,issued.pending.issue.operation)
    except ValueError:
        rejected=True
    complete=finish_current(issued)
    check('request, arrival and publication preserve strict order during a paused round',
          waiting.lower==initial.lower and waiting.upper==initial.upper
          and waiting.pending.arrived_context is None and rejected
          and complete==run_round(initial,contexts[0]),
          first_round_events=[e.kind for e in complete.events])
    check('resuming a requested or planned round does not issue a duplicate boundary or lower cell',
          run_schedule(waiting,contexts)==full and run_schedule(planned,contexts[1:])==full
          and run_schedule(waiting,()).stop=='ContextExhausted')
    # Existing two-letter compensation is tried before asking the producer.
    old_word=run_round(initial,initial.upper.live.context,head=initial.stock[0])
    check('a short existing suffix can avoid production even when no single stock letter suffices',
          old_word.rounds[0].route=='reused' and len(old_word.outputs[0].cell.beta)==3
          and old_word.lower.executed_word==initial.lower.executed_word and len(old_word.stock)==4,
          search_bound=2,consumer_word_length=3)
    zero=run_schedule(initial,contexts[:2]+(zero_context,)+contexts[2:])
    check('zero trial stops after earlier real closures and preserves the remaining schedule',
          zero.stop=='ZERO_STOP' and len(zero.engine.rounds)==2 and len(zero.engine.stock)==5
          and zero.engine.pending.trial_response==(0,0,0,0)
          and zero.engine.upper.executed_word==engine.rounds[1].decoded.state.executed_word
          and zero.unoffered_contexts==contexts[2:]
          and run_schedule(zero.engine,zero.unoffered_contexts)==zero)
    singular=context([[0,0,0],[0,0,0],[0,0,1]])
    chart=run_schedule(initial,contexts[:1]+(singular,)+contexts[1:])
    check('chart exit preserves arrived context and earlier inventory without false promotion',
          chart.stop=='CHART_STOP' and len(chart.engine.rounds)==1 and len(chart.engine.stock)==5
          and chart.engine.upper.live.context==singular and chart.engine.pending.decoded is None
          and tuple(qmul(chart.engine.pending.head.kernel(singular),chart.engine.upper.live.accumulated))==engine.result
          and chart.engine.upper.executed_word==engine.rounds[0].decoded.state.executed_word
          and chart.unoffered_contexts==contexts[1:]
          and run_schedule(chart.engine,chart.unoffered_contexts)==chart)
    rejected_level=False
    try:
        request_boundary(engine,engine.outputs[0])
    except ValueError:
        rejected_level=True
    higher=receive_higher(engine)
    check('explicit higher reception can close at level four without resetting current history',
          rejected_level and len(higher.decoded.outputs)==1 and higher.decoded.outputs[0].level==4
          and higher.anchor==engine.upper and higher.staged.executed_word==engine.upper.executed_word
          and len(higher.decoded.state.executed_word)==len(engine.upper.executed_word)+1,
          higher_input_level=3,higher_output_level=4)
    publication_events=[e for e in engine.events if e.kind=='same-level-operation-published']
    check('global publication journal keeps both actual clocks and never rewrites sources',
          [e.index for e in engine.events]==list(range(len(engine.events)))
          and len(publication_events)==2
          and engine.stock[4].cell.start==engine.rounds[0].pending.plan.lower_start
          and engine.stock[5].cell.start==engine.rounds[2].pending.plan.lower_start
          and initial.designated_head.cell.endpoint==initial.upper,
          journal_events=len(engine.events),lower_cells_produced=2)
    root=Path(__file__).resolve().parent
    paths=['persistent_correction_cycle.py','test_persistent_correction_cycle.py',
           'certified_correction_release.py','test_certified_correction_release.py',
           'same_level_continuation.py','test_same_level_continuation.py',
           'fixed_result_compatibility.py','test_fixed_result_compatibility.py',
           'closed_boundary_loop.py','test_closed_boundary_loop.py',
           'recursive_upper_decoder.py','test_recursive_upper_decoder.py',
           'certified_cell_bridge.py','test_certified_cell_bridge.py',
           'residual_extraction_transport.py','future_existence_residual.py',
           'vendor/two_flower_kernel_certificate.py','vendor/internal_port_certificate.py']
    return dict(note='RR43',passed=True,groups=len(checks),checks=checks,
                source_base_commit='df6b5cc55a90a86289f04eebff7746d890d67f07',
                fixed_result=initial.result,routes=routes,terminal_lengths=lengths,
                producer_level=1,consumer_level=2,output_level=3,higher_demo_level=4,
                declared_policy='request -> actual context arrival -> bounded stock reuse -> lower production if needed',
                stock_search_bound=2,
                supplied_resources=['context arrival schedule','fixed result and designated head',
                                    'continued lower producer','private lower boundaries','publication gate'],
                limits=['no global minimal-suffix or minimal-stock claim from bounded search',
                        'higher receiver is a separate typed process, not a level-two stock item',
                        'no autonomous context generation, general Gamma or future-origin C derived'],
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('persistent_correction_cycle_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'],routes=data['routes'])))
