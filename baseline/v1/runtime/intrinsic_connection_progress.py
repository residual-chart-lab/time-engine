"""RR49: progress from certified same-level continuation reachability.

The distance queries use only the fixed request, arrived context, inherited
state and published stock. No completed endpoint or chosen future word is
input to the planner. The mandatory head and nonempty-boundary rule remain.
One unit ends at its first certified boundary, without a next context.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json

from robust_flower_geometry import (
    Parameters, Interval, BRACKETS, TOLERANCE, geometry, isolate, prepare_model,
    select_representative, SolutionRule, execute_producer, publish_producer,
    boundary_readout, context, ExecutionState, UpperState, step, decode,
    kernel, qmul, promote_word, encode,
)


@dataclass(frozen=True,order=True)
class OpenInterval:
    lo: Q
    hi: Q

    def __post_init__(self):
        object.__setattr__(self,'lo',Q(self.lo))
        object.__setattr__(self,'hi',Q(self.hi))
        if self.lo>=self.hi: raise ValueError('nonempty open interval required')

    def contains(self,value): return self.lo<value<self.hi


def normalize(intervals):
    result=[]
    for interval in sorted(intervals):
        if result and interval.lo<result[-1].hi:
            result[-1]=OpenInterval(result[-1].lo,max(result[-1].hi,interval.hi))
        else: result.append(interval)
    return tuple(result)


def preimage(intervals,multiplier):
    a=Q(multiplier)
    if not a: return ()  # Our target and all its finite preimages exclude zero.
    return normalize(OpenInterval(*sorted((i.lo/a,i.hi/a))) for i in intervals)


def contains(intervals,value): return any(i.contains(value) for i in intervals)
def measure(intervals): return sum((i.hi-i.lo for i in intervals),Q(0))
def subset(left,right):
    return all(any(j.lo<=i.lo and i.hi<=j.hi for j in right) for i in left)


def outside_boundary_band(intervals,result,epsilon):
    pieces=[]
    for i in intervals:
        if i.lo<result-epsilon: pieces.append(OpenInterval(i.lo,min(i.hi,result-epsilon)))
        if i.hi>result+epsilon: pieces.append(OpenInterval(max(i.lo,result+epsilon),i.hi))
    return normalize(pieces)


@dataclass(frozen=True)
class Problem:
    parameters: Parameters
    branch: str
    entry: object
    prepared: object
    source: object
    context: tuple
    start: ExecutionState
    representative: Q


@lru_cache(maxsize=64)
def make_problem(parameters=Parameters(),branch='first'):
    entry,current,plan=prepare_model(parameters)
    # More accurate root calculation BEFORE execution, not a tighter goal or
    # an edit of the RR48 occurrence. This leaves margin for detour controls.
    t=isolate(parameters,branch,tolerance=TOLERANCE/16)
    return problem_at_representative(parameters,branch,t)


def problem_at_representative(parameters,branch,t):
    entry,current,plan=prepare_model(parameters)
    pub=publish_producer(execute_producer(select_representative(plan,SolutionRule(t))))
    source=pub.pending.issue.operation
    raw=boundary_readout(source);r=parameters.future_readout
    y=context([[(1-r)*raw[i][j]+(r/3 if i==j else 0) for j in range(3)] for i in range(3)])
    start=ExecutionState(UpperState(y,pub.upper.live.accumulated),pub.upper.executed_word)
    if not (entry.result==pub.result==pub.pending.result==(-1,0,0,0)
            and pub.pending.upper_before==entry.upper
            and pub.upper==pub.pending.consumer_start
            and start.live.accumulated==entry.upper.live.accumulated
            and start.executed_word==entry.upper.executed_word):
        raise AssertionError('the original fixed request and consumer inheritance must remain bound')
    return Problem(parameters,branch,entry,pub,source,y,start,t)


@dataclass(frozen=True)
class Catalog:
    actions: tuple
    multipliers: tuple
    head: int
    result: Q
    epsilon: Q
    context: tuple

    @property
    def margin(self): return self.epsilon/2


def catalog(problem):
    stock=problem.prepared.stock
    if not (problem.prepared.phase=='AVAILABLE' and problem.source in stock
            and problem.source==problem.prepared.pending.issue.operation):
        raise ValueError('actual source publication must precede continuation queries')
    pending=problem.prepared.pending
    raw=boundary_readout(problem.source);r=problem.parameters.future_readout
    emitted=context([[(1-r)*raw[i][j]+(r/3 if i==j else 0) for j in range(3)] for i in range(3)])
    inherited=ExecutionState(UpperState(pending.arrived_context,problem.entry.upper.live.accumulated),
                             problem.entry.upper.executed_word)
    staged=ExecutionState(UpperState(emitted,problem.prepared.upper.live.accumulated),
                         problem.prepared.upper.executed_word)
    if not (problem.entry.result==problem.prepared.result==pending.result==(-1,0,0,0)
            and pending.head==problem.entry.designated_head
            and pending.upper_before==problem.entry.upper
            and pending.consumer_start==inherited==problem.prepared.upper
            and problem.context==emitted and problem.start==staged
            and problem.prepared.lower==problem.source.cell.endpoint):
        raise ValueError('fixed request, source readout and consumer inheritance must match the entry')
    if not all(a.level==2 and promote_word(a.cell)==a for a in stock):
        raise ValueError('all actions must be certified, published and at the same level')
    values=tuple(a.kernel(problem.context) for a in stock)
    if any(any(q[1:]) for q in values) or any(problem.start.live.accumulated[1:]):
        raise ValueError('this interval implementation uses the declared real-response class')
    return Catalog(stock,tuple(q[0] for q in values),stock.index(problem.prepared.pending.head),
                   problem.entry.result[0],TOLERANCE,problem.context)


@lru_cache(maxsize=256)
def backward_sets(multipliers,result,epsilon,horizon):
    if not isinstance(horizon,int) or horizon<0: raise ValueError('nonnegative finite horizon required')
    if not 0<epsilon<abs(result): raise ValueError('nonzero target separated from zero required')
    margin=epsilon/2
    levels=[(OpenInterval(result-margin,result+margin),)]
    for _ in range(horizon):
        previous=levels[-1]
        expanded=normalize((*previous,*(i for a in multipliers for i in preimage(previous,a))))
        # Preserve RR46's separated first boundary: intermediate errors >eps,
        # final error <eps/2. The unresolved band is never silently traversed.
        levels.append(normalize((*levels[0],*outside_boundary_band(expanded,result,epsilon))))
    return tuple(levels)


def requirements(cat,horizon,head_pending=False):
    """Sections of ONE augmented state space (head pending, accumulated z)."""
    if head_pending:
        if horizon==0: return ()
        previous=backward_sets(cat.multipliers,cat.result,cat.epsilon,horizon-1)[-1]
        return preimage(previous,cat.multipliers[cat.head])
    return backward_sets(cat.multipliers,cat.result,cat.epsilon,horizon)[-1]


def augmented_measure(cat,horizon):
    return measure(requirements(cat,horizon))+measure(requirements(cat,horizon,True))


@dataclass(frozen=True)
class Distance:
    value: object
    status: str
    lower_bound: object=None


def distance(cat,value,head_pending=False,horizon=3):
    if not isinstance(horizon,int) or horizon<0: raise ValueError('finite nonnegative search limit required')
    value=Q(value)
    if value==0 or (head_pending and cat.multipliers[cat.head]==0):
        return Distance(None,'PROVED_UNREACHABLE_ZERO')
    if not head_pending and cat.margin<=abs(value-cat.result)<=cat.epsilon:
        return Distance(None,'OUTSIDE_BOUNDARY_SEPARATION')
    for n in range(horizon+1):
        if contains(requirements(cat,n,head_pending),value): return Distance(n,'EXACT_MINIMUM')
    return Distance(None,'NOT_FOUND_WITHIN_LIMIT',horizon+1)


def plan_shortest(cat,start,horizon=3):
    """A declared selection rule, using existing actions only; then stop."""
    value=Q(start);pending=True;indices=[];distances=[]
    initial=distance(cat,value,pending,horizon)
    if initial.value is None: return (),(),initial
    remaining=initial.value
    while True:
        distances.append(remaining)
        if remaining==0: return tuple(indices),tuple(distances),initial
        options=(cat.head,) if pending else range(len(cat.actions))
        chosen=None
        for index in options:
            nxt=value*cat.multipliers[index]
            d=distance(cat,nxt,False,remaining-1)
            if d.value==remaining-1: chosen=index;break
        if chosen is None: raise AssertionError('a finite exact distance must have a descending edge')
        indices.append(chosen);value*=cat.multipliers[chosen];pending=False;remaining-=1


def certify_trace(problem,indices):
    cat=catalog(problem)
    word=tuple(cat.actions[i] for i in indices)
    if not word or word[0]!=cat.actions[cat.head]: raise ValueError('the entry-bound head must remain first')
    states=[problem.start]
    for a in word: states.append(step(a,states[-1]))
    errors=[abs(s.live.accumulated[0]-cat.result) for s in states]
    if not errors[-1]<cat.margin or any(e<=cat.epsilon for e in errors[1:-1]):
        raise ValueError('one first nonempty boundary must close inside the unchanged safety margin')
    decoded=decode(problem.start,word,(states[-1].live.accumulated,))
    if (len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries
            or decoded.state!=states[-1] or promote_word(decoded.outputs[0].cell)!=decoded.outputs[0]):
        raise AssertionError('the actual whole word needs its own exact nested certificate')
    values=[s.live.accumulated[0] for s in states]
    ds=[distance(cat,z,k==0,horizon=3) for k,z in enumerate(values)]
    # Pulling the fixed tail's terminal defect through the ordered motion is
    # exactly invariant; it cannot be a decreasing progress variable.
    propagated=[tuple(qmul(kernel(word[k:],problem.context),state.live.accumulated))[0]-cat.result
                for k,state in enumerate(states)]
    if len(set(propagated))!=1: raise AssertionError('fixed-tail defect must telescope exactly')
    return dict(indices=indices,states=values,connection_distances=[d.value for d in ds],
        distance_statuses=[d.status for d in ds],raw_remaining_word_lengths=list(range(len(word),-1,-1)),
        live_result_distances=errors,propagated_terminal_defect=propagated[0],
        actual_endpoint=states[-1].live.accumulated,closure_error=errors[-1],
        exact_word_certified=True,consumer_level=word[0].level,
        output_level=decoded.outputs[0].level,new_contexts_after_closure=0)


def strict_layer_witnesses(cat,depth=3):
    """A residue-based sufficient condition proves strictness for ALL n.

    If a positive stock multiplier M is largest in absolute value, M>1,
    and epsilon<|F|(1-1/M), then z_n=F/M^(n+1) reaches F using n+1
    copies of M, while every word of <=n actions stays too small in norm.
    This concerns requirement sets, not a claim that all witness states
    occur on the original prescribed two-letter trajectory.
    """
    m=max(cat.multipliers)
    if not (m>1 and m==max(abs(a) for a in cat.multipliers)
            and cat.epsilon<abs(cat.result)*(1-1/m)):
        raise ValueError('the strict-layer sufficient condition is not satisfied')
    witness=[]
    for n in range(depth):
        value=cat.result/m**(n+1)
        if contains(requirements(cat,n),value) or not contains(requirements(cat,n+1),value):
            raise AssertionError('strict-layer witness failed')
        witness.append(dict(inside=n+1,outside=n,state=value,
                            forbidden_short_word_error_lower=abs(cat.result)*(1-1/m)))
    return dict(largest_positive_multiplier=m,witnesses=witness,
                general_quantifier='every integer n>=0, not only the displayed finite levels')


def uniform_layer_certificate(radius=Q(1,10**8)):
    box=Parameters(*(Interval(-radius,radius) for _ in range(4)))
    cert=[]
    for branch,(lo,hi) in BRACKETS.items():
        g=geometry(Interval(lo,hi),box)
        # The inherited stock's first three actions are the three axis
        # letters, followed by the perturbed head and the new source.
        others=[2*y-1 for y in g['future']]+[g['head']]
        source=g['source']
        bound=max(a.max_abs() for a in others)
        if not (source.lo>max(Q(1),bound) and TOLERANCE<1-1/source.lo):
            raise AssertionError('dominant expanding source is not uniformly certified')
        cert.append(dict(branch=branch,source_range=source.as_pair(),
                         other_actions_abs_upper=bound,strict_layer_gap_lower=1-1/source.lo))
    return dict(radius=radius,branches=cert,
                conclusion='strict nested requirement sets exist at every finite horizon for the entire declared model box')


def visible_only_control(problem):
    cat=catalog(problem)
    after_head=step(cat.actions[cat.head],problem.start).live.accumulated[0]
    proxy=tuple(a.visible[0] for a in cat.actions)
    true=distance(cat,after_head,False,3)
    levels=backward_sets(proxy,cat.result,cat.epsilon,3)
    found=next((n for n,v in enumerate(levels) if contains(v,after_head)),None)
    return dict(true_distance=true.value,proxy_distance=found,
                proxy_status='NOT_FOUND_WITHIN_LIMIT' if found is None else 'EXACT_MINIMUM',
                proxy_limit=3,meaning='diagnostic graph discarding active residue; no proxy action is executed or certified')


def run():
    checks=[]
    def check(name,ok,**details):
        if not ok: raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**details))
    uniform=uniform_layer_certificate()
    check('residue kernels imply strictly nested backward requirement sets at every finite connection horizon',True,
          uniform_certificate=uniform,clock_input=False)
    radius=uniform['radius']
    params=[Parameters(),*(Parameters(*(radius*s for s in signs)) for signs in product((-1,1),repeat=4))]
    cases=[]
    for p in params:
        for branch in BRACKETS:
            problem=make_problem(p,branch);cat=catalog(problem)
            indices,ds,initial=plan_shortest(cat,problem.start.live.accumulated[0],3)
            trace=certify_trace(problem,indices)
            sets=[(requirements(cat,n),requirements(cat,n,True)) for n in range(4)]
            if not all(subset(a[0],b[0]) and subset(a[1],b[1]) for a,b in zip(sets,sets[1:])):
                raise AssertionError('all horizons must use one fixed augmented state space')
            volumes=[augmented_measure(cat,n) for n in range(4)]
            if not all(a<b for a,b in zip(volumes,volumes[1:])):
                raise AssertionError('the shrinking requirements must be strict in this stock')
            cases.append(dict(parameters={n:getattr(p,n) for n in p.__dataclass_fields__},branch=branch,
                representative=problem.representative,stock_size=len(cat.actions),connection_distances=ds,
                selected_indices=indices,closure_error=trace['closure_error'],
                first_nonempty_closure=True,augmented_requirement_measures=volumes,
                strict_layers=strict_layer_witnesses(cat,2)))
    check('all 34 nearby models follow a computed 2-to-1-to-0 connection path using only published actions',
          len(cases)==34 and all(c['connection_distances']==(2,1,0) for c in cases),cases=cases)
    first=make_problem();second=make_problem(branch='second')
    baselines=[]
    for p in (first,second):
        cat=catalog(p)
        short,_,_=plan_shortest(cat,p.start.live.accumulated[0])
        detour=(cat.head,cat.head,cat.actions.index(p.source),cat.actions.index(p.source))
        normal=certify_trace(p,short);long=certify_trace(p,detour)
        baselines.append(dict(branch=p.branch,shortest=normal,detour=long))
    check('connection distance is not the unconsumed length of a selected future word',
          all(b['detour']['connection_distances']==[2,1,2,1,0]
              and b['detour']['raw_remaining_word_lengths']==[4,3,2,1,0] for b in baselines),
          controls=baselines,selection_rule='choose a published action reducing the exact connection distance')
    check('current target displacement and fully propagated terminal defect do not define the new progress',
          all(b['shortest']['live_result_distances'][0]==0
              and b['shortest']['live_result_distances'][1]>Q(1,2) for b in baselines),
          propagated_defect='exactly invariant along each certified word; not decreasing')
    ablations=[visible_only_control(p) for p in (first,second)]
    check('active residuals change connectability although the same actual current state is queried',
          all(a['true_distance']==1 and a['proxy_distance'] is None for a in ablations),
          controls=ablations,absence_beyond_search_limit_not_claimed=True)
    c=catalog(first)
    zero=distance(c,0,False,3)
    unresolved=distance(c,Q(1,10**9),False,0)
    check('proved zero obstruction and finite search exhaustion remain distinct',
          zero.status=='PROVED_UNREACHABLE_ZERO' and unresolved.status=='NOT_FOUND_WITHIN_LIMIT'
          and unresolved.lower_bound==1)
    check('head-pending entry cannot finish merely because its live value already equals minus one',
          distance(c,-1,True).value==2 and distance(c,-1,False).value==0,
          protocol_origin='the existing first-nonempty boundary rule and entry-bound designated head')
    check('requirements shrink strictly as the computed connection distance decreases, at fixed target and tolerance',
          all(c['augmented_requirement_measures'][2]>c['augmented_requirement_measures'][1]
              >c['augmented_requirement_measures'][0] for c in cases),
          strength='strict inclusion of admissible augmented current-state sets; not a growth claim for kernel derivatives')
    zero_ports=[]
    for branch in BRACKETS:
        g=geometry(Q(0));factor='first' if branch=='first' else 'second'
        t0=-g[factor+'_head_action']/g[factor+'_head_slope']
        p=problem_at_representative(Parameters(),branch,t0);cat=catalog(p)
        state=distance(cat,p.start.live.accumulated[0],True)
        zero_ports.append(dict(branch=branch,head_kernel=cat.multipliers[cat.head],status=state.status))
    check('the RR48 departure point has no permitted continuation, even when all published tails are considered',
          all(z['head_kernel']==0 and z['status']=='PROVED_UNREACHABLE_ZERO' for z in zero_ports),
          controls=zero_ports)
    check('no new primitive, new correction issue, target change or next-flower event is used by the planner',
          all(b['shortest']['new_contexts_after_closure']==0 for b in baselines),
          new_selection_rule=True,
          language='fixed mandatory head then any finite tail from the already published level-two stock',
          change_from_rr48='continuation family explicitly enlarged beyond its prescribed two-letter word, using the RR41 stock language')
    root=Path(__file__).resolve().parent
    previous=json.loads((root/'robust_flower_geometry_result.json').read_text(encoding='utf-8'))
    paths=['intrinsic_connection_progress.py','test_intrinsic_connection_progress.py',*previous['source_sha256']]
    return dict(note='RR49',passed=True,groups=len(checks),checks=checks,
        source_base_commit='0575c9a8b1323b1bcd2faa8c276344b947eb20d4',
        progress='minimum admissible same-level connections to the first nonempty terminal boundary',
        goal=dict(fixed_result=-1,epsilon=TOLERANCE,unchanged_operational_margin=TOLERANCE/2),
        scope='a fixed arrived internal context, fixed published stock and fixed head within one flower',
        target_status='operational candidate: graph-derived progress and strictly nested finite-horizon requirements; the distance-reducing selection rule is declared, not uniquely derived',
        limitations=['not a decreasing quantity along arbitrary legal detours',
                     'not residual erasure, physical duration, chronological gain or a proof of independent backward force',
                     'the prescribed RR48 word and RR41-style inventory continuation language are distinct classes',
                     'finite search failure is not a global impossibility certificate'],
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in paths})


if __name__=='__main__':
    result=run()
    Path(__file__).with_name('intrinsic_connection_progress_result.json').write_text(
        json.dumps(result,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=result['groups'],models=34)))
