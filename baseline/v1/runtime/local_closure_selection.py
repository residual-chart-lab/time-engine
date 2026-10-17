"""RR50: a distance-free local closure protocol, and its missing priority.

Only an already arrived context, live state, fixed request and published
certified stock enter the matcher. This is an explicit operational protocol,
not a derivation that all admissible dynamics must choose immediate closure.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import product, permutations
from pathlib import Path
import hashlib
import json

from intrinsic_connection_progress import (
    Parameters, Interval, BRACKETS, TOLERANCE, geometry, make_problem,
    catalog, certify_trace, ExecutionState, UpperState, step, decode,
    promote_word, encode,
)
from recursive_upper_decoder import regular


@dataclass(frozen=True)
class LocalMatch:
    status: str
    actions: tuple
    required_multiplier: object
    multiplier_radius: object
    trials: tuple


def match_stock(state, stock, result=Q(-1), epsilon=TOLERANCE):
    """Return ALL immediate closers; never rank by distance, cost or order.

    The first nonempty step and bound head are the driver's responsibility.
    This low-level diagnostic also accepts other regular real-response ports.
    A lack of immediate matches says nothing about longer continuations.
    """
    result=Q(result);epsilon=Q(epsilon)
    if not 0<epsilon<abs(result): raise ValueError('separated nonzero request required')
    if any(state.live.accumulated[1:]): raise ValueError('declared real-response port required')
    actions=tuple(dict.fromkeys(stock))  # Identical repeated handles are not different histories.
    for a in actions:
        if a.level!=2 or promote_word(a.cell)!=a:
            raise ValueError('certified level-two stock required')
        if not regular(state.live.context,a.leaves()[0].library):
            raise ValueError('regular certified context required')
    z=state.live.accumulated[0]
    if not z: return LocalMatch('ZERO_OBSTRUCTION',(),None,None,())
    trials=[];matches=[]
    for a in actions:
        k=a.kernel(state.live.context)
        if any(k[1:]): raise ValueError('declared real-response stock required')
        error=abs(z*k[0]-result)
        trials.append((a,k[0],error))
        if error<epsilon/2: matches.append(a)
    status=('NO_IMMEDIATE_CLOSURE' if not matches else
            'UNIQUE_IMMEDIATE_CLOSURE' if len(matches)==1 else 'MULTIPLE_IMMEDIATE_CLOSURES')
    return LocalMatch(status,tuple(matches),result/z,epsilon/(2*abs(z)),tuple(trials))


@dataclass(frozen=True)
class LocalRun:
    status: str
    states: tuple
    actions: tuple
    match: object
    output: object=None


def run_local(problem, stock_order=None):
    """Apply the given head, then commit a unique immediate closing action.

    Closing now is an explicit priority inherited in form from RR43 stock
    reuse. No fallback search, manufactured correction or stock-order tie is
    used. The choice is left unresolved if it is not unique.
    """
    cat=catalog(problem)  # Binds request, source publication, context and inheritance.
    offered=cat.actions if stock_order is None else tuple(stock_order)
    if set(offered)!=set(cat.actions):
        raise ValueError('the frozen published stock must be preserved')
    head=cat.actions[cat.head]
    after=step(head,problem.start)
    if abs(after.live.accumulated[0]-cat.result)<=cat.epsilon:
        raise ValueError('this protocol requires the established nonclosing head prefix')
    matched=match_stock(after,offered,cat.result,cat.epsilon)
    if matched.status!='UNIQUE_IMMEDIATE_CLOSURE':
        return LocalRun(matched.status,(problem.start,after),(head,),matched)
    selected=matched.actions[0]
    end=step(selected,after)
    # The exact achieved rational endpoint, not the requested -1, is certified.
    decoded=decode(problem.start,(head,selected),(end.live.accumulated,))
    if (len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries
            or decoded.state!=end or promote_word(decoded.outputs[0].cell)!=decoded.outputs[0]):
        raise AssertionError('the committed word needs its own original Decoder certificate')
    return LocalRun('CLOSED',(problem.start,after,end),(head,selected),matched,decoded.outputs[0])


def choose_one_step(state, stock, result=Q(-1), epsilon=TOLERANCE):
    """A NEW local interpretation of v18 result-mismatch selection.

    Its scope is one offered action, not all possible complete histories.
    The chooser receives neither a designated-head label nor a source label.
    """
    match=match_stock(state,stock,result,epsilon)
    if not match.trials: return LocalMatch('NO_RANKABLE_ACTION',(),None,None,())
    minimum=min(error for a,k,error in match.trials)
    actions=tuple(a for a,k,error in match.trials if error==minimum)
    return LocalMatch('UNIQUE_LOCAL_MINIMUM' if len(actions)==1 else 'MULTIPLE_LOCAL_MINIMA',
                      actions,match.required_multiplier,match.multiplier_radius,match.trials)


def run_greedy(problem, max_steps=8):
    """Try local mismatch minimization without a distance or prescribed word.

    Nonempty closure is inherited. The entry-bound head is checked AFTER
    independent selection; a disagreement stops rather than changes the entry.
    The iteration cap is a computational safeguard, not a future deadline.
    """
    if not isinstance(max_steps,int) or max_steps<1: raise ValueError('positive iteration cap required')
    cat=catalog(problem);states=[problem.start];word=[];last=None
    for _ in range(max_steps):
        last=choose_one_step(states[-1],cat.actions,cat.result,cat.epsilon)
        if last.status!='UNIQUE_LOCAL_MINIMUM':
            return LocalRun(last.status,tuple(states),tuple(word),last)
        action=last.actions[0]
        if not word and action!=cat.actions[cat.head]:
            return LocalRun('DISAGREES_WITH_BOUND_HEAD',tuple(states),(),last)
        word.append(action);states.append(step(action,states[-1]))
        error=abs(states[-1].live.accumulated[0]-cat.result)
        if error<cat.margin:
            d=decode(problem.start,tuple(word),(states[-1].live.accumulated,))
            if (len(d.outputs)!=1 or d.tail or d.boundaries or d.state!=states[-1]
                    or promote_word(d.outputs[0].cell)!=d.outputs[0]):
                raise AssertionError('greedy trace needs an actual first-boundary certificate')
            return LocalRun('CLOSED',tuple(states),tuple(word),last,d.outputs[0])
        if error<=cat.epsilon:
            return LocalRun('OUTSIDE_BOUNDARY_SEPARATION',tuple(states),tuple(word),last)
    return LocalRun('ITERATION_LIMIT',tuple(states),tuple(word),last)


def uniform_match_certificate(radius=Q(1,10**8)):
    """At each RR48 exact local root, only the published source closes now.

    At a root z H S=F, the error of competitor a is |1-k_a/S|.
    The interval proof is conditional on those preconstructed source branches.
    It does not generate them or select between the two branches.
    """
    box=Parameters(*(Interval(-radius,radius) for _ in range(4)))
    branches=[]
    for branch,(lo,hi) in BRACKETS.items():
        g=geometry(Interval(lo,hi),box)
        competitors=[2*y-1 for y in g['future']]+[g['head']]
        errors=[1-k/g['source'] for k in competitors]
        bounds=[e.min_abs() for e in errors]
        if not min(bounds)>TOLERANCE: raise AssertionError('a competitor can enter the boundary band')
        # At the entry, no empty word is offered. The head need not be named
        # to the one-action mismatch selector: at a root z H=-1/S.
        head_error=1-1/g['source']
        entry_others=[2*y-1 for y in g['future']]+[g['source']]
        entry_bounds=[(1+g['z']*k).min_abs() for k in entry_others]
        if not head_error.hi<min(entry_bounds): raise AssertionError('local head preference is not uniform')
        branches.append(dict(branch=branch,competitor_error_lower_bounds=bounds,
            source_response=g['source'].as_pair(),source_error_at_exact_root=0,
            entry_head_error_upper=head_error.hi,entry_other_error_lower_bounds=entry_bounds))
    return dict(radius=radius,branches=branches,
        scope='every exact RR48 branch root in the four-parameter scalar box; executed rational representatives are checked separately')


def bounded_next_actions(problem, prefix, total_tail_limit):
    """UNRANKED feasibility diagnostic, separate from the local controller.

    The cap includes the next action. Earlier terminal prefixes stop a word.
    A larger cap can reveal alternatives; it is not a generated deadline.
    """
    if total_tail_limit<1: raise ValueError('positive finite cap required')
    cat=catalog(problem);prefix=tuple(prefix)
    if not prefix or prefix[0]!=cat.head: raise ValueError('the bound head must remain first')
    state=problem.start
    for i in prefix:
        state=step(cat.actions[i],state)
        if abs(state.live.accumulated[0]-cat.result)<=cat.epsilon:
            raise ValueError('a continuation diagnostic requires a separated open prefix')
    found={}
    for length in range(1,total_tail_limit+1):
        for indices in product(range(len(cat.actions)),repeat=length):
            value=state.live.accumulated[0];valid=True
            for k,i in enumerate(indices):
                value*=cat.multipliers[i]
                if k<length-1 and abs(value-cat.result)<=cat.epsilon:
                    valid=False;break
            if valid and abs(value-cat.result)<cat.margin:
                found.setdefault(indices[0],prefix+indices)
    return found


def ambiguous_port(problem):
    """A separate exact regular port with distinct certified matching actions.

    This is not a modified RR49 entry or an extra action in its frozen stock.
    The inherited scalar here is explicitly supplied as a diagnostic input.
    """
    cat=catalog(problem)
    y=((Q(2),Q(0),Q(0)),(Q(0),Q(1),Q(0)),(Q(0),Q(0),Q(-2)))
    state=ExecutionState(UpperState(y,(Q(-1,3),Q(0),Q(0),Q(0))))
    match=match_stock(state,cat.actions)
    outputs=[]
    for a in match.actions:
        d=decode(state,(a,),((-1,0,0,0),))
        if len(d.outputs)!=1 or d.tail or promote_word(d.outputs[0].cell)!=d.outputs[0]:
            raise AssertionError('both diagnostic candidates need genuine certificates')
        outputs.append(d.outputs[0])
    return state,match,tuple(outputs)


def run():
    checks=[]
    def check(name,ok,**details):
        if not ok: raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**details))
    uniform=uniform_match_certificate()
    check('the exact source is the unique immediately closing stock action throughout the declared branch box',True,
          certificate=uniform)
    radius=uniform['radius']
    params=[Parameters(),*(Parameters(*(radius*s for s in signs)) for signs in product((-1,1),repeat=4))]
    cases=[]
    # Distance is used only by this AFTER-RUN observer, never by run_local/match_stock.
    from intrinsic_connection_progress import distance
    for parameters in params:
        for branch in BRACKETS:
            p=make_problem(parameters,branch);cat=catalog(p);ran=run_local(p)
            ds=[distance(cat,s.live.accumulated[0],i==0,3).value for i,s in enumerate(ran.states)]
            case=dict(parameters={n:getattr(parameters,n) for n in parameters.__dataclass_fields__},branch=branch,
                status=ran.status,source_chosen=ran.actions[-1]==p.source,observed_distances=ds,
                closure_error=abs(ran.states[-1].live.accumulated[0]-cat.result),
                required_multiplier=ran.match.required_multiplier,
                multiplier_radius=ran.match.multiplier_radius,
                competing_error_min=min(error for a,k,error in ran.match.trials if a!=p.source))
            greedy=run_greedy(p)
            case.update(greedy_status=greedy.status,greedy_same_word=greedy.actions==ran.actions,
                        first_action_chosen_without_head_label=choose_one_step(p.start,cat.actions).actions==(cat.actions[cat.head],))
            cases.append(case)
    check('34 actual one-flower runs close without inputting or evaluating a connection distance in the controller',
          len(cases)==34 and all(c['status']=='CLOSED' and c['source_chosen']
            and c['observed_distances']==[2,1,0] and c['closure_error']<TOLERANCE/2 for c in cases),cases=cases)
    check('a declared one-action mismatch policy independently picks the head then source in all 34 models',
          all(c['greedy_status']=='CLOSED' and c['greedy_same_word']
              and c['first_action_chosen_without_head_label'] for c in cases),
          policy_is_new_local_realization=True,full_history_argmin_equivalence_proved=False,
          no_stop_at_empty_word=True,no_distance_input=True)
    baseline=[make_problem(branch=b) for b in BRACKETS]
    permutations_checked=0
    for p in baseline:
        cat=catalog(p)
        after=step(cat.actions[cat.head],p.start)
        for order in permutations(cat.actions):
            matched=match_stock(after,order)
            first=choose_one_step(p.start,order)
            if (matched.actions!=(p.source,) or first.actions!=(cat.actions[cat.head],)):
                raise AssertionError('stock order selected an answer')
            permutations_checked+=1
    check('all 240 permutations of the two baseline stocks choose the same unique operation',
          permutations_checked==240,permutations=permutations_checked)
    comparisons=[]
    for p in baseline:
        cat=catalog(p);h=cat.head;s=cat.actions.index(p.source)
        short=certify_trace(p,(h,s));detour=certify_trace(p,(h,h,s,s))
        one=bounded_next_actions(p,(h,),1);three=bounded_next_actions(p,(h,),3)
        if not (set(one)=={s} and h in three and s in three):
            raise AssertionError('unranked continuation alternatives were not preserved')
        for witness in three.values(): certify_trace(p,witness)
        comparisons.append(dict(branch=p.branch,short=short,detour=detour,
            next_actions_with_one_step_cap=list(one),next_actions_with_three_step_cap=list(three),
            certified_three_step_witnesses=list(three.values())))
    check('the same fixed entry admits both immediate closure and a distance-increasing certified detour',True,
          comparisons=comparisons,logical_conclusion='legality and future compatibility alone do not force the local closure priority')
    p=baseline[0];cat=catalog(p);h=cat.actions[cat.head]
    after=step(h,p.start)
    no_source=match_stock(after,tuple(a for a in cat.actions if a!=p.source))
    later=match_stock(step(h,after),cat.actions)
    check('absence of an immediate match remains unresolved rather than unreachable or forcibly corrected',
          no_source.status=='NO_IMMEDIATE_CLOSURE' and later.status=='NO_IMMEDIATE_CLOSURE',
          source_withheld=no_source.status,after_detour_head=later.status,
          longer_detour_certified=True)
    state,match,outputs=ambiguous_port(p)
    check('a separate regular port has two genuinely distinct certified immediate closers',
          match.status=='MULTIPLE_IMMEDIATE_CLOSURES' and len(outputs)==2,
          candidates=len(match.actions),caller_supplied_diagnostic_inheritance=state.live.accumulated,
          rule='retain ambiguity; do not pick the first stock entry')
    proxy=[]
    for p in baseline:
        cat=catalog(p);z=step(cat.actions[cat.head],p.start).live.accumulated[0]
        proxy.append([i for i,a in enumerate(cat.actions) if abs(z*a.visible[0]-cat.result)<cat.margin])
    check('discarding residual kernels removes the immediate closing match in both baseline controls',
          proxy==[[],[]],visible_only_matches=proxy,proxy_actions_executed=False)
    check('source generation, requested head, branch and context law remain preconditions rather than derived choices',True,
          head_is_given=True,source_branch_preconstructed=True,source_law_derived=False,
          new_priority='commit a unique immediate closer after the mandatory head; otherwise leave selection unresolved',
          equivalent_exact_rr43_code=False,original_decoder_unchanged=True,
          chronology='RR43 bounded exact reuse motivates the priority; RR50 uses the already declared approximate boundary and refuses ties')
    root=Path(__file__).resolve().parent
    prior=json.loads((root/'intrinsic_connection_progress_result.json').read_text(encoding='utf-8'))
    paths=['local_closure_selection.py','test_local_closure_selection.py',*prior['source_sha256']]
    return dict(note='RR50',passed=True,groups=len(checks),checks=checks,
        source_base_commit='55d0be2bbd5014476fa40b6bdba48f018a11c4e1',
        result='distance-free operational selection succeeds conditionally; automatic priority from existing admissibility is not established',
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in paths})


if __name__=='__main__':
    result=run()
    Path(__file__).with_name('local_closure_selection_result.json').write_text(
        json.dumps(result,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=result['groups'],models=34)))
