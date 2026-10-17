"""RR47: extract an operational causal pullback from an actual closure.

A required result is not an occurrence. The pullback uses the verified
actual source, boundary and endpoint, not RR46's quartic or root preview.
Counterfactual source replays are separate runs; actual history is immutable.
Fixed-boundary substitution and regenerated-boundary substitution differ.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

from endogenous_flower_boundary import endogenous_flower, EndogenousFlower
from single_flower_model import null_direction
from closure_native_context_source import generated_context, ContextPolicy
from recursive_upper_decoder import (
    AffineLetter, ExecutionState, UpperState, action_matrix, rref, solve,
    kernel, qmul, decode, step, promote_word, regular,
)
from fixed_result_compatibility import context, encode


@dataclass(frozen=True)
class BoundaryRequirement:
    result: tuple
    tolerance: Q


@dataclass(frozen=True)
class ClosureOccurrence:
    label: str
    requirement: BoundaryRequirement
    head: object
    source: object
    lower_before: ExecutionState
    lower_after: ExecutionState
    consumer_before: ExecutionState
    consumer_after: ExecutionState
    terminal_operation: object
    events: tuple


def record_occurrence(f,label):
    if not isinstance(f,EndogenousFlower) or f.status!='INTERNAL_BOUNDARY_COMPLETE_WITH_TOLERANCE':
        raise ValueError('an executed and completed flower, not a requirement or preview, is required')
    prepared=f.prepared_engine
    pending=prepared.pending
    if pending is None or prepared.phase!='AVAILABLE':
        raise ValueError('the published source must retain its entry-bound pending request')
    if not (f.fixed_result==f.entry.result==pending.result==prepared.result):
        raise ValueError('the fixed requirement must agree with the entry and bound request')
    # A context arrival changes the context only. The consumer head remains
    # speculative until the internal boundary arrives, so neither its exact
    # inherited value nor its committed word may change between checkpoints.
    # The supplied entry is the trust anchor; this is not a signature scheme.
    arrived_start=ExecutionState(UpperState(pending.arrived_context,
        pending.upper_before.live.accumulated),pending.upper_before.executed_word)
    internal_start=ExecutionState(UpperState(f.emitted_context,
        prepared.upper.live.accumulated),prepared.upper.executed_word)
    if (pending.upper_before!=f.entry.upper
            or pending.consumer_start!=arrived_start
            or prepared.upper!=pending.consumer_start
            or f.consumer_start!=internal_start):
        raise ValueError('consumer inheritance must remain bound across both context arrivals')
    if (len(f.decoded.outputs)!=1 or f.decoded.tail or f.decoded.boundaries
            or f.source not in f.prepared_engine.stock
            or f.prepared_engine.lower!=f.source.cell.endpoint):
        raise ValueError('actual publication and one complete consumer cell are required')
    operation=f.decoded.outputs[0]
    cell=operation.cell
    if (promote_word(cell)!=operation or promote_word(f.source.cell)!=f.source
            or cell.start!=f.consumer_start or cell.endpoint!=f.decoded.state
            or cell.beta!=(f.prepared_engine.pending.head,f.source)
            or f.emitted_context!=generated_context(f.source,ContextPolicy('direct'))
            or cell.start.live.context!=f.emitted_context
            or f.consumer_start.executed_word!=f.prepared_engine.upper.executed_word):
        raise ValueError('the source, boundary and ordered occurrence do not agree')
    first=step(cell.beta[0],cell.start)
    actual=step(cell.beta[1],first)
    error=sum(abs(a-b) for a,b in zip(actual.live.accumulated,f.fixed_result))
    prefix_error=sum(abs(a-b) for a,b in zip(first.live.accumulated,f.fixed_result))
    if (actual!=cell.endpoint or error!=f.closure_error or prefix_error!=f.prefix_error
            or not error<f.root.closure_tolerance/2 or not prefix_error>f.root.closure_tolerance):
        raise ValueError('the fixed requirement and first tolerant boundary must be verified')
    expected=['same-level-operation-published','internal-future-context-emitted',
              'internal-future-context-arrived','consumer-first-boundary-certified-with-tolerance']
    if [f.events.index(k) for k in expected]!=sorted(f.events.index(k) for k in expected):
        raise ValueError('publication, emission, arrival and closure must occur in order')
    return ClosureOccurrence(label,BoundaryRequirement(f.fixed_result,f.root.closure_tolerance),
        cell.beta[0],f.source,f.source.cell.start,f.source.cell.endpoint,
        cell.start,cell.endpoint,operation,f.events)


def source_leaf(occurrence):
    if not isinstance(occurrence,ClosureOccurrence):
        raise TypeError('causal extraction requires a recorded occurrence')
    word=occurrence.source.cell.beta
    if len(word)!=1 or not isinstance(word[0],AffineLetter):
        raise ValueError('this extractor applies to the declared one-leaf affine source class')
    return word[0]


@dataclass(frozen=True)
class CausalPullback:
    occurrence: ClosureOccurrence
    null_direction: tuple
    current_matrix: tuple
    terminal_matrix: tuple
    current_rhs: tuple
    current_rank: int
    joint_rank: int
    current_gain: tuple
    terminal_gain: tuple
    reconstructed_weights: tuple
    allowed_requirement_shift: tuple


def extract_pullback(occurrence):
    leaf=source_leaf(occurrence)
    past_y=occurrence.lower_before.live.context
    future_y=occurrence.consumer_before.live.context
    current=action_matrix(past_y,leaf.library)
    delta=null_direction(past_y,leaf.library)
    before=tuple(qmul(occurrence.head.kernel(future_y),occurrence.consumer_before.live.accumulated))
    columns=[tuple(qmul(op.apply(future_y),before)) for op in leaf.library]
    terminal=[list(row) for row in zip(*columns)]
    current_rhs=(Q(1),*leaf.kernel(past_y))
    joint=current+terminal
    rhs=(*current_rhs,*occurrence.consumer_after.live.accumulated)
    ranks=(len(rref(current)[1]),len(rref(joint)[1]))
    current_gain=tuple(sum(d*row[j] for d,row in zip(delta,[op.apply(past_y) for op in leaf.library]))
                       for j in range(4))
    terminal_gain=tuple(sum(d*row[j] for d,row in zip(delta,columns)) for j in range(4))
    if ranks!=(5,6) or any(current_gain) or not any(terminal_gain):
        raise ValueError('the actual future readout must resolve the current affine null direction')
    reconstructed=tuple(solve(joint,list(rhs)))
    if reconstructed!=leaf.weights:
        raise AssertionError('terminal record and current constraint must recover the actual source')
    # The two RR46 diagonal occurrences have one real terminal component.
    if any(terminal_gain[1:]) or any(occurrence.consumer_after.live.accumulated[1:]):
        raise ValueError('this tolerance interval currently uses the diagonal real-response chart')
    g=terminal_gain[0]
    target=occurrence.requirement.result[0]
    actual=occurrence.consumer_after.live.accumulated[0]
    eps=occurrence.requirement.tolerance
    bounds=sorted(((target-eps-actual)/g,(target+eps-actual)/g))
    return CausalPullback(occurrence,delta,tuple(tuple(r) for r in current),
        tuple(tuple(r) for r in terminal),tuple(current_rhs),*ranks,current_gain,
        terminal_gain,reconstructed,tuple(bounds))


def preserves_actual_record(pullback,shift):
    return all(g*Q(shift)==0 for g in pullback.terminal_gain)


def meets_fixed_requirement(pullback,shift):
    lo,hi=pullback.allowed_requirement_shift
    return lo<=Q(shift)<=hi


@dataclass(frozen=True)
class CounterfactualReplay:
    original_occurrence: ClosureOccurrence
    shift: Q
    mode: str
    source: object
    boundary: tuple
    response: tuple
    error: Q
    requirement_met: bool
    generated_boundary: tuple
    generation_rule_preserved: bool


def counterfactual_replay(occurrence,shift,mode='fixed-boundary'):
    leaf=source_leaf(occurrence)
    delta=null_direction(occurrence.lower_before.live.context,leaf.library)
    h=Q(shift)
    new_leaf=AffineLetter(tuple(w+h*d for w,d in zip(leaf.weights,delta)),leaf.library)
    # Separate producer replay from the same immutable past, not a revision of
    # the original occurrence and not an extra item pooled into its inventory.
    lower=decode(occurrence.lower_before,(new_leaf,),(occurrence.source.cell.target,))
    if len(lower.outputs)!=1 or lower.tail or lower.boundaries:
        raise ValueError('the counterfactual source must independently close its lower cell')
    replacement=lower.outputs[0]
    generated=generated_context(replacement,ContextPolicy('direct'))
    if mode=='fixed-boundary':
        y=occurrence.consumer_before.live.context
    elif mode=='regenerated-boundary':
        y=generated
    else:
        raise ValueError('an explicit fixed or regenerated boundary intervention is required')
    response=tuple(qmul(kernel((occurrence.head,replacement),y),occurrence.consumer_before.live.accumulated))
    error=sum(abs(a-b) for a,b in zip(response,occurrence.requirement.result))
    return CounterfactualReplay(occurrence,h,mode,replacement,y,response,error,
                                error<=occurrence.requirement.tolerance,generated,y==generated)


def boundary_direction(occurrence):
    actual=occurrence.consumer_before.live.context
    varied=counterfactual_replay(occurrence,1,'regenerated-boundary').boundary
    return tuple(tuple(a-b for a,b in zip(ar,br)) for ar,br in zip(varied,actual))


def diagnostic_response(occurrence,source_shift,context_shift):
    leaf=source_leaf(occurrence)
    delta=null_direction(occurrence.lower_before.live.context,leaf.library)
    replacement=AffineLetter(tuple(w+Q(source_shift)*d for w,d in zip(leaf.weights,delta)),leaf.library)
    change=boundary_direction(occurrence)
    y=context([[a+Q(context_shift)*d for a,d in zip(row,drow)]
               for row,drow in zip(occurrence.consumer_before.live.context,change)])
    return tuple(qmul(replacement.kernel(y),qmul(occurrence.head.kernel(y),
                                                occurrence.consumer_before.live.accumulated)))


def polynomial_derivative(values,points):
    matrix=[[Q(x)**power for power in range(len(points))] for x in points]
    return tuple(solve(matrix,[v[j] for v in values])[1] for j in range(4))


def causal_path_gains(occurrence):
    baseline=diagnostic_response(occurrence,0,0)
    direct=tuple(a-b for a,b in zip(diagnostic_response(occurrence,1,0),baseline))
    context_points=(0,1,-1,2)
    context_gain=polynomial_derivative([diagnostic_response(occurrence,0,k) for k in context_points],context_points)
    total_points=(0,1,-1,2,-2)
    total_gain=polynomial_derivative([diagnostic_response(occurrence,k,k) for k in total_points],total_points)
    if total_gain!=tuple(a+b for a,b in zip(direct,context_gain)):
        raise AssertionError('the direct residue path and source/context path must compose exactly')
    return dict(direct_residue=direct,through_generated_context=context_gain,total=total_gain)


def blind_readout_control(occurrence):
    leaf=source_leaf(occurrence)
    delta=null_direction(occurrence.lower_before.live.context,leaf.library)
    # A separately supplied regular boundary, not a new RR46 source rule.
    # At this boundary the same fixed result is attained while the current
    # null coordinate is genuinely invisible to the tested whole-word action.
    blind=context([[Q(1,3),0,0],[0,Q(2,13),0],[0,0,Q(20,39)]])
    before=tuple(qmul(occurrence.head.kernel(blind),occurrence.consumer_before.live.accumulated))
    values=[]
    certificates=[]
    for h in (0,1,-1,Q(1,100)):
        replay=counterfactual_replay(occurrence,h)
        values.append(tuple(qmul(replay.source.kernel(blind),before)))
        staged=ExecutionState(UpperState(blind,occurrence.consumer_before.live.accumulated),
                              occurrence.consumer_before.executed_word)
        decoded=decode(staged,(occurrence.head,replay.source),(occurrence.requirement.result,))
        certificates.append(len(decoded.outputs)==1 and not decoded.tail and not decoded.boundaries
                            and promote_word(decoded.outputs[0].cell)==decoded.outputs[0])
    columns=[tuple(qmul(op.apply(blind),before)) for op in leaf.library]
    terminal=[list(row) for row in zip(*columns)]
    joint_rank=len(rref(action_matrix(occurrence.lower_before.live.context,leaf.library)+terminal)[1])
    gain=tuple(sum(d*v[j] for d,v in zip(delta,columns)) for j in range(4))
    return dict(boundary=blind,regular=regular(blind,leaf.library),joint_rank=joint_rank,
                null_response=gain,responses=tuple(values),
                diagnostic_closure_certified=all(certificates),actual_rr46_occurrence=False,
                generation_rule_preserved=False)


def necessary_visibility_lemma(occurrence):
    """Certificate for the entire declared current affine solution line.

    A successful nonzero result excludes a zero head. The remaining direct
    gain is affine in the generated context shift, with one zero. At that
    zero the self-generated outcome is outside the fixed result tolerance.
    Hence every successful self-generated closure on this line exposes the
    current null direction. This is conditional on the existing source law.
    """
    leaf=source_leaf(occurrence)
    current=action_matrix(occurrence.lower_before.live.context,leaf.library)
    base=tuple(solve(current,[Q(1),*leaf.kernel(occurrence.lower_before.live.context)]))
    delta=null_direction(occurrence.lower_before.live.context,leaf.library)
    if (base!=(Q(14),Q(-13),0,0,0,0) or delta!=(-2,1,1,0,0,0)
            or occurrence.requirement.result!=(-1,0,0,0)
            or not 0<occurrence.requirement.tolerance<=Q(1,1000)):
        raise ValueError('the RR46 current line and declared nonzero requirement are required')
    def gain(y):
        return tuple(sum(d*op.apply(y)[j] for d,op in zip(delta,leaf.library)) for j in range(4))
    y=occurrence.consumer_before.live.context
    varied=counterfactual_replay(occurrence,1,'regenerated-boundary').boundary
    g0=gain(y)
    slope=tuple(a-b for a,b in zip(gain(varied),g0))
    if any(g0[1:]) or slope!=(12,0,0,0):
        raise ValueError('the affine diagonal direct source law is required')
    blind_shift=-g0[0]/slope[0]
    blind=counterfactual_replay(occurrence,blind_shift,'regenerated-boundary')
    if any(gain(blind.boundary)) or blind.requirement_met:
        raise AssertionError('the sole blind generated boundary cannot be a successful closure')
    return dict(current_canonical_weights=base,current_null_direction=delta,
                generated_leaf_gain_slope=slope,unique_blind_source=source_leaf_from_operation(blind.source).weights,
                unique_blind_boundary=blind.boundary,blind_response=blind.response,
                blind_fixed_result_error=blind.error,
                zero_head_cannot_meet_nonzero_result=True,
                conclusion='every successful closure on this self-generated affine line has nonzero terminal null-direction gain',
                quantifier='all real shifts of this declared line; not a finite-sample extrapolation')


def source_leaf_from_operation(operation):
    word=operation.cell.beta
    if len(word)!=1 or not isinstance(word[0],AffineLetter):
        raise ValueError('a one-leaf affine source operation is required')
    return word[0]


def receipt_summary(pullback):
    occ=pullback.occurrence
    return dict(label=occ.label,current_rank=pullback.current_rank,joint_rank=pullback.joint_rank,
                current_null_direction=pullback.null_direction,current_gain=pullback.current_gain,
                terminal_gain=pullback.terminal_gain,actual_endpoint=occ.consumer_after.live.accumulated,
                fixed_requirement=occ.requirement.result,tolerance=occ.requirement.tolerance,
                current_source_weights=source_leaf(occ).weights,
                reconstructed_source_weights=pullback.reconstructed_weights,
                allowed_nominal_result_shift=pullback.allowed_requirement_shift,
                allowed_half_width=(pullback.allowed_requirement_shift[1]-pullback.allowed_requirement_shift[0])/2,
                causal_paths=causal_path_gains(occ))


def fixtures():
    first=record_occurrence(endogenous_flower(),'RR46-first-occurrence')
    second=record_occurrence(endogenous_flower('second'),'RR46-second-occurrence')
    return first,second,extract_pullback(first),extract_pullback(second)


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    first,second,p1,p2=fixtures()
    rejected=False
    try:
        extract_pullback(first.requirement)
    except TypeError:
        rejected=True
    check('a required result is not promoted into an actual closure occurrence',rejected,
          scope='verified occurrence is required; algebraic relations may still be predicted earlier')
    check('actual source, boundary, endpoint and ordered histories carry exact certificates',
          all(promote_word(o.terminal_operation.cell)==o.terminal_operation
                  and promote_word(o.source.cell)==o.source for o in (first,second)),
          root_formula_used_by_pullback=False)
    check('a current invisible direction becomes operationally distinguishable at each achieved boundary',
          all(p.current_rank==5 and p.joint_rank==6 and not any(p.current_gain)
                  and any(p.terminal_gain) for p in (p1,p2)),
          receipts=[receipt_summary(p1),receipt_summary(p2)])
    check('the achieved terminal readout reconstructs the selected source from current constraints',
          all(tuple(solve([list(row) for row in p.current_matrix],list(p.current_rhs)))!=p.reconstructed_weights
                  and p.reconstructed_weights==source_leaf(p.occurrence).weights for p in (p1,p2)))
    zeroed=[counterfactual_replay(o,-source_leaf(o).weights[2]) for o in (first,second)]
    check('erasing the actual null coordinate preserves current correction but loses the achieved closure',
          all(r.source.kernel(r.source.cell.start.live.context)==(-9,0,0,0)
                  and not r.requirement_met for r in zeroed),
          fixed_boundary_responses=[r.response for r in zeroed])
    cross=[counterfactual_replay(first,source_leaf(second).weights[2]-source_leaf(first).weights[2]),
           counterfactual_replay(second,source_leaf(first).weights[2]-source_leaf(second).weights[2])]
    regenerated=[counterfactual_replay(r.original_occurrence,r.shift,'regenerated-boundary') for r in cross]
    check('two completed branches cannot replace each other at the same achieved boundary',
          all(not r.requirement_met and not r.generation_rule_preserved for r in cross),
          fixed_boundary_cross_responses=[r.response for r in cross],
          scope='controlled fixed-boundary intervention; the source-to-context arrow is held, not regenerated')
    check('regenerating the context closes the other branch but changes the occurrence being compared',
          all(r.requirement_met and r.generation_rule_preserved
                  and r.boundary!=r.original_occurrence.consumer_before.live.context
                  for r in regenerated)
          and regenerated[0].source==second.source and regenerated[1].source==first.source,
          scope='a separate counterfactual event, not preservation of the original future boundary')
    for p in (p1,p2):
        for h in (Q(-1,100),Q(1,100),Q(1)):
            replay=counterfactual_replay(p.occurrence,h)
            predicted=tuple(a+h*g for a,g in zip(p.occurrence.consumer_after.live.accumulated,p.terminal_gain))
            assert replay.response==predicted
    check('the backwards allowed-shift interval follows exactly from the forward kernel',True,
          actual_record_preserved_only_at_zero=all(preserves_actual_record(p,0)
              and not preserves_actual_record(p,Q(1,100)) for p in (p1,p2)))
    for p in (p1,p2):
        lo,hi=p.allowed_requirement_shift
        assert meets_fixed_requirement(p,0)
        assert counterfactual_replay(p.occurrence,lo).error==p.occurrence.requirement.tolerance
        assert counterfactual_replay(p.occurrence,hi).error==p.occurrence.requirement.tolerance
        assert not counterfactual_replay(p.occurrence,hi+(hi-lo)).requirement_met
    check('actual endpoint equality and nominal result tolerance remain separate requirements',True,
          fixed_result=-1,actual_endpoints=[o.consumer_after.live.accumulated for o in (first,second)])
    paths=[causal_path_gains(o) for o in (first,second)]
    check('direct retained-source and generated-context effects compose without conflating interventions',
          all(v['total']==tuple(a+b for a,b in zip(v['direct_residue'],v['through_generated_context']))
                  for v in paths),causal_paths=paths)
    blind=blind_readout_control(first)
    check('retained memory alone does not imply relevance to every future readout',
          blind['regular'] and not any(blind['null_response'])
          and blind['joint_rank']==5 and len(set(blind['responses']))==1
          and blind['responses'][0]==(Q(-1),0,0,0) and blind['diagnostic_closure_certified'],
          blind_readout=blind,
          scope='same fixed result at a separately supplied control boundary; not another RR46 endogenous source branch')
    lemmas=[necessary_visibility_lemma(o) for o in (first,second)]
    check('successful self-generated closure necessarily exposes the current null direction on the whole declared line',
          all(v['unique_blind_source']==(Q(1,3),Q(-37,6),Q(41,6),0,0,0)
                  and v['blind_response']==(Q(-20240,27),0,0,0)
                  and v['blind_fixed_result_error']>Q(1,1000) for v in lemmas),
          necessity_certificates=lemmas,
          scope='a conditional necessity consequence of the source rule and actual nonzero result, not a new imposed future predicate')
    check('causal extraction and all counterfactuals preserve the actual committed occurrences',
          first==record_occurrence(endogenous_flower(),'RR46-first-occurrence')
          and second==record_occurrence(endogenous_flower('second'),'RR46-second-occurrence'),
          new_future_generation_rules=0,new_actual_history_rewrites=0)
    root=Path(__file__).resolve().parent
    previous=json.loads((root/'endogenous_flower_boundary_result.json').read_text(encoding='utf-8'))
    paths=['closure_causal_pullback.py','test_closure_causal_pullback.py',*previous['source_sha256']]
    return dict(note='RR47',passed=True,groups=len(checks),checks=checks,
                certificate_revision='RR47-v002',
                certificate_scope='fixed requirement and consumer inheritance bound to the supplied original entry and pending request',
                source_base_commit='7f74c095eac7fda6c9b4de385f97f2b63e833cb5',
                scope='operational causal pullback from achieved boundary to current affine null direction',
                extracted_from_actual_record=True,uses_rr46_quartic=False,
                direction='time and execution forward; completed-boundary admissibility pulled back to past residue',
                limitations=['the fixed-boundary attribution is conditional on RR46 source law and operation class',
                             'fixed-boundary source substitution is a controlled intervention, not a whole-law alternative history',
                             'new regenerated contexts are separate counterfactual occurrences',
                             'availability of an actual witness is not unpredictability of its algebraic relation',
                             'no general minimal-residue, physical-force or independent unknown-future claim'],
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('closure_causal_pullback_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'],current_rank=5,terminal_joint_rank=6)))
