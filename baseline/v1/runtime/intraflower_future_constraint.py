"""RR46: future compatibility constrains a representative inside one unit.

The actual future context is absent. A declared finite boundary family is
available as a model condition. Selection solves the present response and
the whole word's future result simultaneously, before actual production.
This is a conditional two-boundary candidate, also realizable forward when
the family is known. It is not a derivation of an independently unknown family.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

from single_flower_model import (
    begin_flower, arrive, advance, null_direction, SolutionRule,
    AffineLetter, context, regular, encode, qmul,
)
from persistent_correction_cycle import (
    fixtures_sequence, request_boundary, accept_context, resolve_open,
    execute_producer, publish_producer, consume_produced, event, replay_trace,
)
from certified_correction_release import active_leaf
from closure_native_context_source import (
    boundary_readout, ContextPolicy, generated_context, start_native, advance_native,
)
from recursive_upper_decoder import kernel


@dataclass(frozen=True)
class FutureFamily:
    label: str
    contexts: tuple

    def __post_init__(self):
        values=tuple(context(y) for y in self.contexts)
        if not values or len(set(values))!=len(values):
            raise ValueError('a nonempty family of distinct contexts is required')
        object.__setattr__(self,'contexts',values)


@dataclass(frozen=True)
class SelectionProof:
    family: FutureFamily
    null_shift: Q
    base_weights: tuple
    direction: tuple
    chosen_weights: tuple
    result: tuple
    inherited_value: tuple
    equations: tuple


def solve_future_selection(engine,family):
    """Return one affine witness, or None for an exact inconsistent system."""
    if engine.phase!='PLANNED':
        raise ValueError('an unexecuted correction plan is required')
    p=engine.pending
    if any(not regular(y,engine.library) for y in family.contexts):
        raise ValueError('future certification uses the declared regular chart')
    base=p.plan.leaf
    delta=null_direction(p.arrived_context,engine.library)
    equations=[]
    inherited=p.consumer_start.live.accumulated
    for y in family.contexts:
        after_head=tuple(qmul(p.head.kernel(y),inherited))
        baseline=tuple(qmul(base.kernel(y),after_head))
        gain_action=tuple(sum(d*op.apply(y)[j] for d,op in zip(delta,engine.library)) for j in range(4))
        gain=tuple(qmul(gain_action,after_head))
        equations.append((y,baseline,gain))
    solution=None
    for _,baseline,gain in equations:
        for required,actual,coefficient in zip(p.result,baseline,gain):
            rhs=required-actual
            if not coefficient:
                if rhs:
                    return None
                continue
            proposed=rhs/coefficient
            if solution is not None and proposed!=solution:
                return None
            solution=proposed
    t=Q(0) if solution is None else solution
    chosen=AffineLetter(tuple(w+t*d for w,d in zip(base.weights,delta)),base.library)
    if not active_leaf(chosen) or chosen.kernel(p.arrived_context)!=p.plan.wanted_action:
        raise ValueError('the selected source must preserve present response and remain active')
    for y,_,_ in equations:
        response=tuple(qmul(chosen.kernel(y),qmul(p.head.kernel(y),inherited)))
        assert response==p.result
    proof=SelectionProof(family,t,base.weights,delta,chosen.weights,p.result,inherited,tuple(equations))
    return chosen,proof


@dataclass(frozen=True)
class FutureWitness:
    family: FutureFamily
    word: tuple
    actual_source: object
    result: tuple
    inherited_value: tuple
    responses: tuple


def certify_future_compatibility(engine,family):
    # This evaluates a candidate continuation; it does not execute an
    # unpublished action or assert that an actual future event has occurred.
    if engine.phase!='AVAILABLE':
        raise ValueError('future verification requires actual lower execution and publication')
    p=engine.pending
    source=p.issue.operation
    if source not in engine.stock or source.level!=p.head.level:
        raise ValueError('a published same-level source is required')
    word=(p.head,source)
    responses=tuple(tuple(qmul(kernel(word,y),p.consumer_start.live.accumulated)) for y in family.contexts)
    if any(response!=p.result for response in responses):
        return None
    return FutureWitness(family,word,source,p.result,p.consumer_start.live.accumulated,responses)


@dataclass(frozen=True)
class TwoBoundaryFlower:
    checkpoint: object
    family: object
    engine: object
    status: str
    selection: object=None
    witness: object=None


def prepare(checkpoint,y,family):
    # Request and known family are bound before the actual context arrives.
    if family is not None and not isinstance(family,FutureFamily):
        raise TypeError('an explicit boundary-family condition is required')
    waiting=request_boundary(checkpoint)
    if family is not None:
        waiting=event(waiting,'future-family-condition-bound')
    opened=accept_context(waiting,y)
    if family is None:
        return TwoBoundaryFlower(checkpoint,None,opened,'FUTURE_FAMILY_UNRESOLVED')
    if opened.phase!='OPEN':
        raise ValueError('this prototype examines an open nonzero production branch')
    planned=resolve_open(opened)
    if planned.phase!='PLANNED':
        raise ValueError('this prototype requires fresh production, not a silently substituted stock route')
    selected=solve_future_selection(planned,family)
    if selected is None:
        return TwoBoundaryFlower(checkpoint,family,planned,'INCOMPATIBLE_BOUNDARIES')
    chosen,proof=selected
    p=planned.pending
    planned=event(planned,'future-compatibility-selected-representative',
                  pending=replace(p,plan=replace(p.plan,leaf=chosen)))
    issued=execute_producer(planned)
    published=publish_producer(issued)
    witness=certify_future_compatibility(published,family)
    if witness is None:
        raise AssertionError('an actual source violated its pre-execution compatibility proof')
    checked=event(published,'intraflower-future-family-certified')
    return TwoBoundaryFlower(checkpoint,family,checked,'READY_FOR_JOINT_CLOSURE',proof,witness)


def close(flower):
    if flower.status=='BOUNDARY_COMPATIBLE_COMPLETE':
        return flower
    if flower.status!='READY_FOR_JOINT_CLOSURE' or flower.witness is None:
        raise ValueError('present result alone is not the completion condition')
    if certify_future_compatibility(flower.engine,flower.family)!=flower.witness:
        raise ValueError('the actual published source must still satisfy the same future condition')
    engine=consume_produced(flower.engine)
    output=engine.outputs[-1]
    if output.cell.beta!=flower.witness.word:
        raise ValueError('the committed history must be the jointly verified history')
    return replace(flower,engine=engine,status='BOUNDARY_COMPATIBLE_COMPLETE')


def future_responses(operation,initial_value,family):
    return tuple(tuple(qmul(operation.kernel(y),initial_value)) for y in family.contexts)


def fixtures():
    initial,ys,_=fixtures_sequence()
    native_y=generated_context(initial.designated_head,ContextPolicy('direct'))
    first=ys[4]
    old=initial.upper.live.context
    plus=FutureFamily('native-or-Y1',(native_y,first))
    minus=FutureFamily('native-or-Y0',(native_y,old))
    union=FutureFamily('native-or-Y1-or-Y0',(native_y,first,old))
    return initial,native_y,plus,minus,union


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    initial,y,plus,minus,union=fixtures()
    p=prepare(initial,y,plus)
    m=prepare(initial,y,minus)
    left=close(p);right=close(m)
    canonical=arrive(begin_flower(initial),y)
    while canonical.status!='COMPLETE':
        canonical=advance(canonical)
    check('the current context comes from RR44 direct readout, with no normalization',
          y==context([[Q(1,3),0,0],[0,Q(2,3),0],[0,0,0]])
          and p.engine.pending.trial_response==(Q(1,9),0,0,0),
          current_context=y,present_head_trial=p.engine.pending.trial_response)
    check('future family changes the selected residue while current correction and result stay fixed',
          p.selection.null_shift==Q(41,14) and m.selection.null_shift==Q(71,14)
          and p.engine.pending.plan.wanted_action==m.engine.pending.plan.wanted_action==(Q(-9),0,0,0)
          and left.engine.upper.live==right.engine.upper.live==canonical.engine.upper.live
          and left.engine.lower.live==right.engine.lower.live==canonical.engine.lower.live,
          future_family_shifts=[p.selection.null_shift,m.selection.null_shift],
          weights=[p.selection.chosen_weights,m.selection.chosen_weights],
          current_correction=p.engine.pending.plan.wanted_action,
          current_result=left.engine.result)
    check('joint closure is guarded by future compatibility before the consumer commits',
          p.status==m.status=='READY_FOR_JOINT_CLOSURE'
          and p.engine.outputs==m.engine.outputs==initial.outputs
          and p.engine.upper.executed_word==m.engine.upper.executed_word==initial.upper.executed_word
          and left.status==right.status=='BOUNDARY_COMPATIBLE_COMPLETE',
          events=[e.kind for e in left.engine.events[len(initial.events):]])
    check('one selected actual history succeeds at every context of its declared future family',
          future_responses(left.engine.outputs[-1],initial.upper.live.accumulated,plus)==(initial.result,)*2
          and future_responses(right.engine.outputs[-1],initial.upper.live.accumulated,minus)==(initial.result,)*2,
          families=[plus.contexts,minus.contexts],future_result=initial.result,
          actual_future_context_input=None)
    old_future=future_responses(canonical.engine.outputs[-1],initial.upper.live.accumulated,union)
    check('clean current closure alone fails the added future condition',
          old_future==(initial.result,(Q(-43,2),0,0,0),(Q(69,2),0,0,0)),
          canonical_future_responses=old_future,scope='RR45 COMPLETE is only current closure, not completed future causality')
    cross=[future_responses(left.engine.outputs[-1],initial.upper.live.accumulated,minus)[1],
           future_responses(right.engine.outputs[-1],initial.upper.live.accumulated,plus)[1]]
    check('the same fixed future result induces incompatible requirements for two future families',
          cross==[(Q(14),0,0,0)]*2,wrong_family_responses=cross,
          scope='the actual family is a model condition; the concrete future context is absent')
    empty=prepare(initial,y,union)
    check('no representative in this current one-parameter class meets the union family',
          empty.status=='INCOMPATIBLE_BOUNDARIES'
          and len(empty.engine.lower.executed_word)==len(initial.lower.executed_word)
          and empty.engine.outputs==initial.outputs and empty.engine.stock==initial.stock,
          scope='all real shifts of the declared affine null line; not every possible operation')
    unresolved=prepare(initial,y,None)
    check('an unknown family is left unresolved instead of inserted through a hidden current input',
          unresolved.status=='FUTURE_FAMILY_UNRESOLVED' and unresolved.selection is None
          and unresolved.engine.outputs==initial.outputs and unresolved.engine.stock==initial.stock)
    check('different selected sources remain actual committed sources with complete history',
          left.engine.outputs[-1]!=right.engine.outputs[-1]
          and left.engine.stock[:4]==right.engine.stock[:4]==initial.stock
          and replay_trace(initial,left.engine) and replay_trace(initial,right.engine),
          lower_tape=len(left.engine.lower.executed_word),consumer_tape=len(left.engine.upper.executed_word),
          stocks=[len(left.engine.stock),len(right.engine.stock)])
    # A maximally informed forward solver with the same family chooses the same
    # null shift and reproduces both clocks and exact output. Do not claim a
    # backward causal advantage over it.
    forward=[]
    for selected in (left,right):
        f=arrive(begin_flower(initial,solution_rule=SolutionRule(selected.selection.null_shift)),y)
        while f.status!='COMPLETE':
            f=advance(f)
        assert (f.engine.upper,f.engine.lower,f.engine.stock,f.engine.outputs)==(
            selected.engine.upper,selected.engine.lower,selected.engine.stock,selected.engine.outputs)
        forward.append(True)
    check('known-family selection has an ordinary full-history forward realization',all(forward),
          future_origin_derived=False,scope='no independent unknown-family causal effect has been established')
    direct=advance_native(start_native(initial,ContextPolicy('direct')),4)
    parameters=[2*x.context_value[0][0]-1 for x in direct.messages]
    check('RR44 inverse-cube motion remains intact as a reference, without imposing stable operation',
          parameters==[Q(-1,3),Q(27),Q(-1,19683),Q(3**27),Q(-1,3**81)]
          and all(b==-1/a**3 for a,b in zip(parameters,parameters[1:])),
          direct_parameters=parameters,scope='the chosen canonical source rule; fluctuation itself does not certify future causality')
    check('the new guard ends one unit without emitting another request or future event',
          left.engine.pending is None and len(left.engine.rounds)==1
          and left.engine.events[-1].kind=='upper-cell-closed:produced' and close(left) is left,
          new_requests_after_closure=0,actual_future_events_generated=0)
    root=Path(__file__).resolve().parent
    previous=json.loads((root/'single_flower_model_result.json').read_text(encoding='utf-8'))
    paths=['intraflower_future_constraint.py','test_intraflower_future_constraint.py',*previous['source_sha256']]
    return dict(note='RR46',passed=True,groups=len(checks),checks=checks,
                source_base_commit='a77dd2533783ce7fc51738478051ae62012fb4a6',
                scope='future-family compatibility guards residue selection within one operational unit',
                future_condition='whole committed word returns the same fixed result for every context in the supplied finite family',
                actual_future_context_supplied=False,future_family_supplied=True,future_origin_derived=False,
                unfinished_core='derivation of the actual admissible future family and its role in a strong causal comparison',
                limits=['boundary families and the joint completion guard are declared model conditions',
                        'the known-family procedure is exactly forward-realizable',
                        'union-family impossibility applies to this current one-parameter affine class',
                        'one clean result closure is not a completed Time Engine with future causality'],
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('intraflower_future_constraint_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'],future_origin_derived=False)))
