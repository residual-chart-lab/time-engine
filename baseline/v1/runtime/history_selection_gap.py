"""RR51: distinguish local greed, whole-history compatibility and isolation.

No new primitive, target, source law or automatic winner is introduced.
Diagnostic open ports are separate inputs, never edits of the RR49 entry.
Candidate continuation proofs are not newly published actual occurrences.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import hashlib
import json

from local_closure_selection import (
    BRACKETS, Parameters, Interval, TOLERANCE, geometry, make_problem,
    catalog, certify_trace, choose_one_step, match_stock, run_greedy,
    ExecutionState, UpperState, step, decode, promote_word, encode,
)
from recursive_upper_decoder import kernel, regular


def as_interval(x): return Interval.cast(x)


def root_bracket(branch, width=Q(1,10**18)):
    lo,hi=BRACKETS[branch]
    gl=geometry(lo)['mismatch']
    for _ in range(256):
        if hi-lo<width: return lo,hi
        middle=(lo+hi)/2;gm=geometry(middle)['mismatch']
        if gm==0: raise AssertionError('the selected baseline root is not expected rational')
        if gm*gl<0: hi=middle
        else: lo=middle;gl=gm
    raise AssertionError('root bracket budget exhausted')


def exact_greedy_cycle_certificate(branch):
    """Uniform interval inequalities at the BASELINE exact root, not a grid.

    Let a be the tiny negative axis response, b the other head axis, h=ab,
    s=1/h. Starting at -1/h^2, local greed chooses a,a,s,h,s,h,... .
    The two cycle states are -1/b^2 and -1/(h*b^2), both away from F.
    Rational representatives only approximately repeat; their finite traces
    are a separate control and are never called exact infinite cycles.
    """
    lo,hi=root_bracket(branch);g=geometry(Interval(lo,hi))
    axes=[2*y-1 for y in g['future']]
    h=g['head'];s=1/h
    small=0 if branch=='first' else 1
    big=1-small
    a=axes[small];b=axes[big]
    if not (a.hi<0 and b.hi<0 and h.lo>0 and h.hi<1):
        raise AssertionError('the scalar cycle chart failed')
    values=(-1/(h*h),-a/(h*h),-1/(b*b),-1/(h*b*b))
    multipliers=(*axes,h,s)
    winners=(small,small,4,3)
    comparisons=[]
    for z,winner in zip(values,winners):
        errors=[as_interval(1+z*k) for k in multipliers]
        best_upper=errors[winner].max_abs()
        others_lower=min(e.min_abs() for i,e in enumerate(errors) if i!=winner)
        if not best_upper<others_lower: raise AssertionError('local cycle winner is not uniquely certified')
        comparisons.append(dict(state_range=z.as_pair(),winner=winner,
            best_error_upper=best_upper,other_errors_lower=others_lower))
    if not all(as_interval(1+z).min_abs()>TOLERANCE for z in values):
        raise AssertionError('cycle crossed the terminal boundary')
    return dict(branch=branch,exact_root_bracket=(lo,hi),comparisons=comparisons,
        unique_winners=winners,cycle_indices=(4,3),head_response=h.as_pair(),
        conclusion='at the exact baseline root, the live scalar response repeats two nonterminal values while the ordered history keeps growing',
        full_exact_state_is_periodic=False,
        feasible_exact_closing_word=(3,3),
        scope='two baseline branch roots and deliberately supplied diagnostic open states; not all RR48 parameter perturbations')


def diagnostic_port(problem):
    cat=catalog(problem);h=cat.multipliers[cat.head]
    # Independent input to the already-head-released section. No original
    # consumer checkpoint, entry request or committed tape is rewritten.
    return ExecutionState(UpperState(cat.context,(-1/(h*h),Q(0),Q(0),Q(0))))


def proof_for_word(start,cat,indices):
    """Check a hypothetical continuation with the original exact Decoder."""
    word=tuple(cat.actions[i] for i in indices)
    if not word: raise ValueError('a nonempty continuation is required')
    states=[start]
    for action in word: states.append(step(action,states[-1]))
    errors=[abs(s.live.accumulated[0]-cat.result) for s in states]
    if errors[-1]>=cat.margin or any(e<=cat.epsilon for e in errors[1:-1]):
        raise ValueError('not a separated first boundary')
    d=decode(start,word,(states[-1].live.accumulated,))
    if (len(d.outputs)!=1 or d.tail or d.boundaries or d.state!=states[-1]
            or promote_word(d.outputs[0].cell)!=d.outputs[0]):
        raise AssertionError('hypothetical continuation lacks its original certificate')
    return dict(indices=tuple(indices),states=[s.live.accumulated[0] for s in states],
        endpoint=d.state.live.accumulated,closure_error=errors[-1],output_level=d.outputs[0].level,
        certified_possible_continuation=True,published_actual_occurrence=False)


def retained_candidates(start,cat,cap,head_pending=False):
    """Keep every witnessed first-boundary word within the explicit cap.

    The cap is a computational limit, not an internally generated deadline.
    No local mismatch or shortest-distance ranking discards a branch. All
    words up to the cap are checked, including longer completed candidates.
    Absence/uniqueness is asserted ONLY within this finite search language.
    """
    if not isinstance(cap,int) or cap<1: raise ValueError('positive finite cap required')
    z=start.live.accumulated[0]
    if any(start.live.accumulated[1:]) or start.live.context!=cat.context:
        raise ValueError('the fixed real-response catalog context is required')
    if not head_pending and abs(z-cat.result)<=cat.epsilon:
        raise ValueError('an open already-head-released state is required')
    result=[]
    for length in range(1,cap+1):
        for indices in product(range(len(cat.actions)),repeat=length):
            if head_pending and indices[0]!=cat.head: continue
            value=z;valid=True
            for k,i in enumerate(indices):
                value*=cat.multipliers[i]
                if k<length-1 and abs(value-cat.result)<=cat.epsilon:
                    valid=False;break
            if valid and abs(value-cat.result)<cat.margin:
                result.append(proof_for_word(start,cat,indices))
    return dict(status='WITNESSES_WITHIN_CAP' if result else 'NO_WITNESS_WITHIN_CAP',cap=cap,
        candidates=result,next_actions=sorted({p['indices'][0] for p in result}),
        global_exhaustiveness_proved=False,winner_selected=False,new_stock_items_published=0)


def finite_greedy_control(problem,steps=8):
    cat=catalog(problem);state=diagnostic_port(problem);states=[state];indices=[]
    for _ in range(steps):
        m=choose_one_step(state,cat.actions,cat.result,cat.epsilon)
        if len(m.actions)!=1: raise AssertionError('diagnostic local choice became ambiguous')
        a=m.actions[0];indices.append(cat.actions.index(a));state=step(a,state);states.append(state)
        if abs(state.live.accumulated[0]-cat.result)<cat.margin: break
    # RR49's distance is AFTER-TRACE diagnostics only.
    from intrinsic_connection_progress import distance
    distances=[distance(cat,s.live.accumulated[0],False,3).value for s in states]
    return dict(branch=problem.branch,steps=steps,indices=indices,
        states=[s.live.accumulated[0] for s in states],observed_distances=distances,
        closed_within_cap=abs(state.live.accumulated[0]-cat.result)<cat.margin,
        feasible_exact_word=proof_for_word(states[0],cat,(cat.head,cat.head)),
        original_entry_modified=False,rational_trace_claim='finite nonclosure; not an exact infinite-cycle claim')


def response_profiles(problem):
    cat=catalog(problem);h=cat.head;s=cat.actions.index(problem.source)
    words=((h,s),(h,h,s,s))
    ports={'present_correction':problem.prepared.pending.arrived_context,
           'internal_arrival':problem.context,
           'head_origin':cat.actions[h].cell.start.live.context}
    profiles=[]
    for indices in words:
        certified=certify_trace(problem,indices)
        values={name:kernel(tuple(cat.actions[i] for i in indices),y) for name,y in ports.items()}
        if any(any(value[1:]) for value in values.values()): raise AssertionError('declared scalar probe class failed')
        profiles.append(dict(indices=indices,actual_word_certificate=certified['exact_word_certified'],
            kernel_by_port=values,full_ordered_record=indices))
    return dict(branch=problem.branch,profiles=profiles,
        diagnostic_only=True,neighbor_coupling_inferred=False,external_residue_measure_inferred=False)


@dataclass(frozen=True)
class IsolationAssessment:
    status: str
    external_state_unchanged: object
    scope: str
    sealed: object=None
    changes: tuple=()


@dataclass(frozen=True)
class PeerPort:
    context: tuple
    accumulated: Q=Q(-1)
    required: Q=Q(-1)


def assess_isolation(word=(),coupling=None,peers=None):
    """Do not turn absent neighbor data into proof of v18 §29 sealing.

    The isolated case is an explicitly added product-system completion. It
    shows the base premises can coexist with equal external costs for both
    histories. It is not inferred from immutable software records.
    """
    if coupling is None or not peers:
        return IsolationAssessment('UNDEFINED_EXTERNAL_COUPLING',None,
            'v18 neighbor set, action coupling, residue measure and before/after baseline are not concretized')
    if coupling not in ('declared-isolated-product','declared-shared-response-product'):
        return IsolationAssessment('UNSUPPORTED_COUPLING',None,'a concrete action and residue measure are required')
    if not word or any(a.level!=2 or promote_word(a.cell)!=a for a in word):
        raise ValueError('a certified nonempty level-two local word is required')
    changes=[]
    for peer in peers:
        if not regular(peer.context,word[0].leaves()[0].library):
            raise ValueError('regular external diagnostic context required')
        response=kernel(word,peer.context)
        if any(response[1:]): raise ValueError('declared scalar external diagnostic ports required')
        multiplier=Q(1) if coupling=='declared-isolated-product' else response[0]
        after=peer.accumulated*multiplier
        delta=abs(after-peer.required)-abs(peer.accumulated-peer.required)
        changes.append(dict(before=peer.accumulated,after=after,multiplier=multiplier,external_delta=delta))
    return IsolationAssessment('ASSESSED_DECLARED_PRODUCT_MODEL',
        all(c['before']==c['after'] for c in changes),
        'explicit product coupling and scalar external valuation; not a derived Time Engine neighbor model',
        all(c['external_delta']<=0 for c in changes),tuple(changes))


def run():
    checks=[]
    def check(name,ok,**details):
        if not ok: raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**details))
    problems=[make_problem(branch=b) for b in BRACKETS]
    check('the original two RR50 baseline flowers still close under their declared local policy',
          all(run_greedy(p).status=='CLOSED' for p in problems),scope='no change to prior sources, entries or policies')
    certificates=[exact_greedy_cycle_certificate(b) for b in BRACKETS]
    check('exact root interval inequalities prove two nonterminal local-greedy cycles at diagnostic open states',True,
          certificates=certificates)
    controls=[finite_greedy_control(p) for p in problems]
    check('the rational diagnostic ports have an exact two-action closure while eight local choices do not close',
          all(not c['closed_within_cap'] and c['feasible_exact_word']['closure_error']==0 for c in controls),
          controls=controls)
    check('the locally smallest result mismatch need not decrease connection distance',
          all(c['observed_distances'][0]==2 and c['observed_distances'][1]==2
              and 3 in c['observed_distances'] for c in controls),
          distance_input_to_chooser=False)
    retained=[]
    for p in problems:
        cat=catalog(p);start=diagnostic_port(p)
        short=retained_candidates(start,cat,1);full=retained_candidates(start,cat,3)
        if short['candidates'] or not any(w['indices']==(cat.head,cat.head) for w in full['candidates']):
            raise AssertionError('the viable two-action branch was lost')
        retained.append(dict(branch=p.branch,cap_one=short,cap_three=full))
    check('retaining complete compatible continuations recovers the exact closing branch without local ranking',True,
          diagnostics=retained)
    original=[]
    for p in problems:
        cat=catalog(p);found=retained_candidates(p.start,cat,4,head_pending=True)
        h=cat.head;s=cat.actions.index(p.source)
        wordset={w['indices'] for w in found['candidates']}
        if not {(h,s),(h,h,s,s)}<=wordset: raise AssertionError('compatible history ambiguity disappeared')
        original.append(dict(branch=p.branch,candidates=found))
    check('the original entry retains both short and detour histories rather than manufacturing a winner',True,
          diagnostics=original)
    profiles=[response_profiles(p) for p in problems]
    for record in profiles:
        short,long=record['profiles']
        if short['kernel_by_port']['present_correction']!=(1,0,0,0) or long['kernel_by_port']['present_correction']!=(1,0,0,0):
            raise AssertionError('the current correction port should exactly tie')
        if short['kernel_by_port']['head_origin']==long['kernel_by_port']['head_origin']:
            raise AssertionError('full-residue differences were not visible at the old origin probe')
    check('equal terminal success and present-port action coexist with distinct full response profiles',True,
          profiles=profiles,profiles_are_not_actual_neighbor_damage=True)
    undefined=assess_isolation()
    check('missing external couplings never pass the hard no-scattering test vacuously',
          undefined.status=='UNDEFINED_EXTERNAL_COUPLING' and undefined.external_state_unchanged is None,
          assessment=undefined.__dict__)
    coupling_controls=[]
    for p in problems:
        cat=catalog(p);head=cat.actions[cat.head]
        words=((head,p.source),(head,head,p.source,p.source))
        current=PeerPort(p.prepared.pending.arrived_context)
        origin=PeerPort(head.cell.start.live.context)
        isolated=[assess_isolation(w,'declared-isolated-product',(origin,)) for w in words]
        current_shared=[assess_isolation(w,'declared-shared-response-product',(current,)) for w in words]
        origin_shared=[assess_isolation(w,'declared-shared-response-product',(origin,)) for w in words]
        if not (all(a.sealed for a in isolated+current_shared) and not any(a.sealed for a in origin_shared)):
            raise AssertionError('conditional external effects were not distinguished')
        coupling_controls.append(dict(branch=p.branch,isolated=[a.__dict__ for a in isolated],
            current_shared=[a.__dict__ for a in current_shared],origin_shared=[a.__dict__ for a in origin_shared]))
    check('explicit diagnostic couplings can leave both histories sealed or reject both, without deriving a unique winner',True,
          controls=coupling_controls,couplings_and_external_scalar_valuation_are_added_assumptions=True,
          actual_time_engine_coupling_derived=False)
    check('candidate proof generation neither publishes speculative histories nor applies a new selection law',
          all(not x['cap_three']['winner_selected'] and x['cap_three']['new_stock_items_published']==0 for x in retained),
          new_primitive_actions=0,new_future_contexts=0,path_loss_valuation_defined=False,
          conclusion='whole-history compatibility constrains candidates; deterministic commitment still needs a concrete path-selection mechanism')
    root=Path(__file__).resolve().parent
    prior=json.loads((root/'local_closure_selection_result.json').read_text(encoding='utf-8'))
    paths=['history_selection_gap.py','test_history_selection_gap.py',*prior['source_sha256']]
    return dict(note='RR51',passed=True,groups=len(checks),checks=checks,
        source_base_commit='e45fc81598c5921c3537cd590216383659e206cf',
        original_rr50_result_preserved=True,source_generation_law_derived=False,
        internal_selection_fully_derived=False,
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in paths})


if __name__=='__main__':
    result=run()
    Path(__file__).with_name('history_selection_gap_result.json').write_text(
        json.dumps(result,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=result['groups'],baseline_branches=2)))
