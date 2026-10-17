"""RR44: a declared context readout of actually closed, published history.

No external context schedule or target-inverse lookup enters this source.
The readout is a channel, not a replacement for the full ordered residue.
Direct and normalized ports are explicit candidate rules, not derived v18 G.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

from persistent_correction_cycle import (
    fixtures, boot, request_boundary, accept_context, finish_current, event,
    PersistentEngine, context, promote_word, kernel, regular, encode,
)
from recursive_upper_decoder import AffineLetter, certify_word
from same_level_continuation import Experiment
from fixed_result_compatibility import generate_request
from future_existence_residual import residue, boundary, scale


class EmptyReadout(ValueError):
    pass


@dataclass(frozen=True)
class ContextPolicy:
    mode: str='direct'
    radius: Q=Q(1,8)

    def __post_init__(self):
        object.__setattr__(self,'radius',Q(self.radius))
        if self.mode not in ('direct','normalized') or not 0<self.radius<Q(1,3):
            raise ValueError('declared source mode and fixed radius in (0,1/3) required')


def boundary_readout(operation):
    if operation.level!=2 or promote_word(operation.cell)!=operation:
        raise ValueError('an actually certified level-two source is required')
    word=operation.cell.beta
    if not word or any(not isinstance(leaf,AffineLetter) for leaf in word):
        raise ValueError('this boundary port reads certified primitive-affine words')
    # Public order-sensitive weights, fixed before any future target is read.
    denominator=Q(len(word)*(len(word)+1),2)
    result=[[Q(0)]*3 for _ in range(3)]
    for position,leaf in enumerate(word,1):
        for i in range(3):
            for j in range(3):
                result[i][j]+=Q(position)/denominator*sum(
                    w*op.source.endpoint[i][j] for w,op in zip(leaf.weights,leaf.library))
    return context(result)


def generated_context(operation,policy):
    x=boundary_readout(operation)
    if policy.mode=='direct':
        return x
    s=residue([list(row) for row in x])
    size=sum(abs(v) for row in s for v in row)
    if not size:
        raise EmptyReadout('this port is isotropic; the full source may still be active')
    return context(boundary(scale(policy.radius/size,s)))


@dataclass(frozen=True)
class ContextMessage:
    source: object
    trigger: object
    target_round: int
    emitted_at: int
    context_value: tuple
    policy: ContextPolicy


@dataclass(frozen=True)
class NativeDriver:
    engine: PersistentEngine
    policy: ContextPolicy
    messages: tuple=()
    consumed: int=0
    stop: str='RUNNABLE'


def actual_source(engine):
    # Prefer the last actually executed and published lower production cell.
    for trace in reversed(engine.rounds):
        if trace.route=='produced':
            source=trace.pending.issue.operation
            if source not in engine.stock:
                raise ValueError('the actual source has not been published')
            return source
    # Bootstrap from a cell already in the committed initial history.
    if engine.designated_head not in engine.stock:
        raise ValueError('there is no published initial source')
    return engine.designated_head


def emit_next(driver):
    if driver.engine.phase!='IDLE' or driver.stop!='RUNNABLE':
        raise ValueError('the previous consumer boundary must have completed')
    waiting=request_boundary(driver.engine)
    source=actual_source(waiting)
    trigger=waiting.outputs[-1] if waiting.outputs else waiting.designated_head
    try:
        y=generated_context(source,driver.policy)
    except EmptyReadout:
        stopped=event(waiting,'stopped:empty-context-readout',phase='SOURCE_STOP')
        return NativeDriver(stopped,driver.policy,driver.messages,driver.consumed,'SOURCE_PORT_EMPTY')
    index=len(waiting.events)
    emitted=event(waiting,'context-source-emitted:'+driver.policy.mode)
    message=ContextMessage(source,trigger,waiting.pending.number,index,y,driver.policy)
    return NativeDriver(emitted,driver.policy,driver.messages+(message,),driver.consumed)


def start_native(engine,policy=ContextPolicy()):
    if engine.phase!='IDLE' or not engine.stock:
        raise ValueError('a committed initial history and published stock are required')
    return emit_next(NativeDriver(engine,policy))


def step_native(driver):
    if driver.stop!='RUNNABLE':
        return driver
    if driver.engine.phase!='WAIT_CONTEXT' or driver.consumed>=len(driver.messages):
        raise ValueError('one internally emitted message must await its fixed request')
    message=driver.messages[driver.consumed]
    if message.target_round!=driver.engine.pending.number or message.source not in driver.engine.stock:
        raise ValueError('message provenance or receiving boundary mismatch')
    engine=finish_current(accept_context(driver.engine,message.context_value))
    stop='RUNNABLE' if engine.phase=='IDLE' else engine.phase
    advanced=NativeDriver(engine,driver.policy,driver.messages,driver.consumed+1,stop)
    return emit_next(advanced) if stop=='RUNNABLE' else advanced


def advance_native(driver,steps):
    if not isinstance(steps,int) or steps<0:
        raise ValueError('nonnegative finite execution budget required')
    for _ in range(steps):
        if driver.stop!='RUNNABLE':
            break
        driver=step_native(driver)
    return driver


def empty_port_fixture():
    ab,_,_,_,_=fixtures()
    a=ab.prepared.operations[0].cell.beta[0]
    last=AffineLetter((0,Q(1,2),Q(1,2),0,0,0),a.library)
    source=promote_word(certify_word(ab.prepared.endpoint,(a,last),(-3,0,0,0)))
    return boot(Experiment(ab.prepared,generate_request(source)))


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    ab,changed,_,_,_=fixtures()
    initial=boot(ab)
    direct=advance_native(start_native(initial,ContextPolicy('direct')),4)
    normalized=advance_native(start_native(initial,ContextPolicy('normalized')),4)
    check('both source rules use the same committed bootstrap with no supplied context schedule',
          direct.stop==normalized.stop=='RUNNABLE' and len(direct.engine.rounds)==len(normalized.engine.rounds)==4
          and direct.consumed==normalized.consumed==4,
          external_context_values_after_initial_history=0,rounds=4)
    check('messages contain published source cells and are emitted after a fixed request before arrival',
          all(m.source in trace.pending.stock_before and m.context_value==trace.pending.arrived_context
              for d in (direct,normalized) for m,trace in zip(d.messages,d.engine.rounds))
          and all(d.engine.events[m.emitted_at].kind.startswith('context-source-emitted:')
                  and d.engine.events[m.emitted_at-1].kind=='boundary-requested'
                  and d.engine.events[m.emitted_at+1].kind=='context-arrived'
                  for d in (direct,normalized) for m in d.messages[:d.consumed]))
    check('old certificates and whole ordered residues survive the context readout',
          initial.designated_head.cell.endpoint==initial.upper
          and direct.messages[0].source==normalized.messages[0].source==initial.designated_head
          and direct.engine.stock[:4]==normalized.engine.stock[:4]==initial.stock,
          scope='the boundary matrix is a context channel, not the full-word residue extractor')
    check('the public order-sensitive port bootstraps a regular context from the old two-letter cell',
          direct.messages[0].context_value==context([[Q(1,3),0,0],[0,Q(2,3),0],[0,0,0]])
          and regular(direct.messages[0].context_value,initial.library),
          first_context=direct.messages[0].context_value)
    parameters=[2*m.context_value[0][0]-1 for m in direct.messages]
    for a,b in zip(parameters,parameters[1:]):
        assert b==-1/(a**3)
    stock_obstructions=[]
    for message,trace,a in zip(direct.messages,direct.engine.rounds,parameters):
        magnitudes=[abs(op.kernel(message.context_value)[0]) for op in trace.pending.stock_before]
        assert all(not any(op.kernel(message.context_value)[1:]) for op in trace.pending.stock_before)
        wanted=Q(1)/(a*a)
        assert (all(v<=1 for v in magnitudes) and wanted>1) or (all(v>=1 for v in magnitudes) and wanted<1)
        stock_obstructions.append(dict(a=a,existing_magnitudes=magnitudes,required_magnitude=wanted))
    check('direct feedback follows the exact inverse-cube branch and needs fresh production in every tested round',
          parameters==[Q(-1,3),Q(27),Q(-1,19683),Q(3**27),Q(-1,3**81)]
          and all(t.route=='produced' for t in direct.engine.rounds),
          a_parameters=parameters,formula='a_next=-a^-3; log absolute magnitude changes sign and grows by factor three',
          stock_obstructions=stock_obstructions)
    for m in normalized.messages:
        s=residue([list(row) for row in m.context_value])
        assert sum(abs(v) for row in s for v in row)==Q(1,8)
        assert all(abs(s[i][i])<=Q(1,16) for i in range(3))
    check('normalized context port has an exact bound without deleting the source amplitude',
          all(m.source in normalized.engine.stock for m in normalized.messages),
          residual_L1_norm=Q(1,8),diagonal_deviation_bound=Q(1,16),
          scope='readout only; no assertion that the whole producer state is bounded')
    coefficient_limit=Q(28423,225)
    coefficient_maxima=[]
    for trace in normalized.engine.rounds:
        weights=trace.pending.plan.leaf.weights
        assert all(x==0 for x in weights[2:]) and sum(weights[:2])==1
        assert -Q(28198,225)<=weights[0]<0
        coefficient_maxima.append(max(abs(x) for x in weights))
    check('the canonical normalized diagonal branch bounds fresh coefficients after the bootstrap',
          normalized.engine.rounds[0].pending.plan.leaf.weights[0]==Q(-1753,15)
          and all(x<=coefficient_limit for x in coefficient_maxima),
          coefficient_limit=coefficient_limit,coefficient_maxima=coefficient_maxima,
          scope='specified diagonal source, radius 1/8, zero-free-coordinate solver; not every chart or source')
    growth=[]
    for trace in normalized.engine.rounds:
        c=trace.pending.plan.wanted_action[0]
        assert trace.route=='produced' and Q(576,121)<=c<=Q(576,25)
        growth.append(trace.lower_after.live.accumulated[0])
    check('bounded contexts do not imply bounded producer accumulation',
          all(abs(b)>abs(a) for a,b in zip([initial.lower.live.accumulated[0]]+growth,growth)),
          producer_values=growth,per_fresh_cell_factor_lower_bound=Q(576,121),
          per_fresh_cell_factor_upper_bound=Q(576,25))
    check('the persistent controller preserves fixed result, designated head and actual lower history',
          all(len(d.engine.stock)==8 and len(d.engine.lower.executed_word)==9
              and len(d.engine.upper.executed_word)==13
              and all(t.pending.head==initial.designated_head and t.pending.result==initial.result
                      for t in d.engine.rounds) for d in (direct,normalized)),
          initial_stock=4,final_stock=8,lower_tape=9,consumer_tape=13)
    for policy in (ContextPolicy('direct'),ContextPolicy('normalized')):
        started=start_native(initial,policy)
        for cut in range(5):
            assert advance_native(advance_native(started,cut),4-cut)==advance_native(started,4)
    check('source messages and pending requests resume without duplicate emission',True,policies=2,all_splits=5,
          completed_rounds=4,pending_messages=1)
    # The last emission is ready for the next step; it has not been delivered.
    check('the source has one queued endogenous context beyond the finite execution budget',
          len(direct.messages)==len(normalized.messages)==5
          and direct.engine.phase==normalized.engine.phase=='WAIT_CONTEXT'
          and direct.engine.pending.arrived_context is None and normalized.engine.pending.arrived_context is None)
    empty=empty_port_fixture()
    direct_empty=start_native(empty,ContextPolicy('direct'))
    chart=step_native(direct_empty)
    normalized_empty=start_native(empty,ContextPolicy('normalized'))
    check('an isotropic readout does not mean the retained full word is inactive',
          boundary_readout(empty.designated_head)==context(boundary([[Q(0)]*3 for _ in range(3)]))
          and chart.stop=='CHART_STOP' and normalized_empty.stop=='SOURCE_PORT_EMPTY'
          and not normalized_empty.messages and normalized_empty.engine.outputs==()
          and empty.designated_head.kernel(context([[2,0,0],[0,Q(-1,4),0],[0,0,Q(-3,4)]]))
              !=empty.designated_head.kernel(initial.upper.live.context),
          scope='port degeneracy, not a zero full residual or a global impossibility')
    # The emitted sequence can be computed from its committed source record.
    replay=initial
    for message in direct.messages[:direct.consumed]:
        waiting=request_boundary(replay)
        # Preserve the same source-event chronology in the forward comparator.
        emitted=event(waiting,'context-source-emitted:'+message.policy.mode)
        replay=finish_current(accept_context(emitted,message.context_value))
    check('the source-driven course has an ordinary history-preserving forward realization',
          replay.rounds==direct.engine.rounds and replay.stock==direct.engine.stock
          and replay.upper==direct.engine.upper and replay.lower==direct.engine.lower,
          scope='no independent unknown future input or non-forward causal advantage is claimed')
    root=Path(__file__).resolve().parent
    paths=['closure_native_context_source.py','test_closure_native_context_source.py',
           'persistent_correction_cycle.py','test_persistent_correction_cycle.py',
           'certified_correction_release.py','test_certified_correction_release.py',
           'same_level_continuation.py','test_same_level_continuation.py',
           'fixed_result_compatibility.py','test_fixed_result_compatibility.py',
           'closed_boundary_loop.py','test_closed_boundary_loop.py',
           'recursive_upper_decoder.py','test_recursive_upper_decoder.py',
           'certified_cell_bridge.py','test_certified_cell_bridge.py',
           'residual_extraction_transport.py','future_existence_residual.py',
           'vendor/two_flower_kernel_certificate.py','vendor/internal_port_certificate.py']
    return dict(note='RR44',passed=True,groups=len(checks),checks=checks,
                source_base_commit='288a2bbf1e82d6fc9cc72f6587411f2664cd82a4',
                source_rule='read actual published lower closure; public ordered boundary average; optional fixed-radius observation port',
                policies=['direct','normalized with radius 1/8'],rounds_per_policy=4,
                no_external_context_schedule=True,
                supplied_resources=['committed initial history and frame','fixed result and designated head',
                                    'continued lower producer and private boundary construction',
                                    'publication rule and chosen context readout'],
                limits=['context source rule is proposed, not derived or uniquely selected by v18 G',
                        'direct inverse-cube branch is unstable; normalized port does not bound producer accumulation',
                        'the generated actual contexts do not replace the full admitted future family',
                        'future-boundary result selection and future-origin C remain unresolved'],
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('closure_native_context_source_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'],policies=data['policies'],rounds_each=4)))
