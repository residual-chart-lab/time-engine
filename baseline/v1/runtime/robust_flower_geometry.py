"""RR48: an open scalar model family, and limits of terminal strengthening.

Uniform rational interval certificates, not a grid-to-theorem extrapolation.
Each executed instance has its own certified entry, head and published source.
The real diagonal response class is explicit; arbitrary quaternion changes
are not covered by the scalar branch-persistence statement.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json

from intraflower_future_constraint import fixtures
from recursive_upper_decoder import (
    AffineLetter, ExecutionState, UpperState, certify_word, promote_word,
    kernel, qmul, step, decode, regular, action_matrix, rref, solve,
)
from persistent_correction_cycle import (
    request_boundary, accept_context, resolve_open, execute_producer, publish_producer,
    CycleEvent,
)
from single_flower_model import SolutionRule, select_representative
from closure_native_context_source import boundary_readout
from fixed_result_compatibility import context, encode
from endogenous_flower_boundary import endogenous_flower
from closure_causal_pullback import record_occurrence
from certified_cell_bridge import CellWitness, certify, promotion


@dataclass(frozen=True)
class Interval:
    lo: Q
    hi: Q

    def __post_init__(self):
        object.__setattr__(self,'lo',Q(self.lo))
        object.__setattr__(self,'hi',Q(self.hi))
        if self.lo>self.hi: raise ValueError('ordered interval required')

    @staticmethod
    def cast(value):
        return value if isinstance(value,Interval) else Interval(value,value)

    def __add__(self,other):
        other=self.cast(other)
        return Interval(self.lo+other.lo,self.hi+other.hi)
    __radd__=__add__

    def __neg__(self): return Interval(-self.hi,-self.lo)
    def __sub__(self,other): return self+-self.cast(other)
    def __rsub__(self,other): return self.cast(other)+-self

    def __mul__(self,other):
        other=self.cast(other)
        endpoints=[a*b for a in (self.lo,self.hi) for b in (other.lo,other.hi)]
        return Interval(min(endpoints),max(endpoints))
    __rmul__=__mul__

    def reciprocal(self):
        if self.lo<=0<=self.hi: raise ValueError('interval division crosses zero')
        return Interval(1/self.hi,1/self.lo)
    def __truediv__(self,other): return self*self.cast(other).reciprocal()
    def __rtruediv__(self,other): return self.cast(other)*self.reciprocal()

    def excludes_zero(self): return self.hi<0 or self.lo>0
    def min_abs(self): return min(abs(self.lo),abs(self.hi)) if self.excludes_zero() else Q(0)
    def max_abs(self): return max(abs(self.lo),abs(self.hi))
    def contains(self,value): return self.lo<=value<=self.hi
    def as_pair(self): return self.lo,self.hi


@dataclass(frozen=True)
class Parameters:
    head_first: Q=Q(0)
    head_second: Q=Q(0)
    current_readout: Q=Q(0)
    future_readout: Q=Q(0)

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value=getattr(self,name)
            if not isinstance(value,Interval): object.__setattr__(self,name,Q(value))


BRACKETS={'first':(Q(27,4),Q(6751,1000)),
          'second':(Q(13499,1000),Q(27,2))}
TOLERANCE=Q(1,10**12)


def diagonal(values):
    return context([[values[i] if i==j else 0 for j in range(3)] for i in range(3)])


def geometry(t,parameters=Parameters()):
    """Scalar formulas derived from the unchanged quaternion action kernel.

    h,b change the two head leaves. c changes the current arrival readout.
    r changes the future readout toward I/3. All may vary independently.
    The source current affine line changes with the perturbed current chart.
    """
    h,b,c,r=(getattr(parameters,name) for name in parameters.__dataclass_fields__)
    # The inherited value is the actually reconstructed head source endpoint,
    # with fixed old source context diag(3/2,1/4,-3/4) and start value 1.
    z=(2*((1-h)*Q(3,2)+h*Q(1,4))-1)*(2*((1-b)*Q(1,4)+b*Q(-3,4))-1)
    current=((1-h)/3+c,(h+2*(1-b))/3-c,2*b/3)
    ah=2*((1-h)*current[0]+h*current[1])-1
    bh=2*((1-b)*current[1]+b*current[2])-1
    wanted=-1/(z*ah*bh)
    base=(((wanted+1)/2)-current[1])/(current[0]-current[1])
    d1=(current[1]-current[2])/(current[0]-current[1])
    delta=(d1,-1-d1,Q(1))
    weights=(base+d1*t,1-base+delta[1]*t,t)
    future=tuple((1-r)*w+r/3 for w in weights)
    future_d=tuple((1-r)*d for d in delta)
    a=2*((1-h)*future[0]+h*future[1])-1
    bvalue=2*((1-b)*future[1]+b*future[2])-1
    ad=2*((1-h)*future_d[0]+h*future_d[1])
    bd=2*((1-b)*future_d[1]+b*future_d[2])
    head=a*bvalue
    head_d=ad*bvalue+a*bd
    head_dd=2*ad*bd
    source=2*sum(w*y for w,y in zip(weights,future))-1
    source_d=2*sum(d*y+w*yd for d,y,w,yd in zip(delta,future,weights,future_d))
    source_dd=4*sum(d*yd for d,yd in zip(delta,future_d))
    source_null=2*sum(d*y for d,y in zip(delta,future))
    source_null_d=2*sum(d*yd for d,yd in zip(delta,future_d))
    mismatch=z*head*source+1
    derivative=z*(head_d*source+head*source_d)
    second_derivative=z*(head_dd*source+2*head_d*source_d+head*source_dd)
    return dict(z=z,current=current,wanted=wanted,weights=weights,delta=delta,future=future,
                head=head,source=source,mismatch=mismatch,derivative=derivative,
                source_null=source_null,fixed_boundary_gain=z*head*source_null,
                fixed_gain_derivative=z*(head_d*source_null+head*source_null_d),
                first_head_action=a,second_head_action=bvalue,
                first_head_slope=ad,second_head_slope=bd,second_derivative=second_derivative)


def uniform_certificate(radius=Q(1,10**8)):
    """Certifies EVERY real parameter in the box, with rational bounds."""
    radius=Q(radius)
    if not radius>0: raise ValueError('positive radius required')
    box=Parameters(*(Interval(-radius,radius) for _ in range(4)))
    branches=[]
    for name,(lo,hi) in BRACKETS.items():
        left=geometry(lo,box);right=geometry(hi,box)
        whole=geometry(Interval(lo,hi),box)
        opposite=(left['mismatch'].hi<0<right['mismatch'].lo or
                  right['mismatch'].hi<0<left['mismatch'].lo)
        chart=[]
        for label in ('current','future'):
            y=whole[label]
            for i,j in ((0,1),(0,2),(1,2)):
                difference=y[i]-y[j]
                if not difference.excludes_zero(): raise AssertionError('regular chart is not uniformly separated')
                chart.append((label,i,j,difference.as_pair()))
        if not (opposite and whole['derivative'].excludes_zero()
                and whole['source_null'].excludes_zero() and whole['source'].excludes_zero()
                and whole['z'].excludes_zero()):
            raise AssertionError('the box does not certify both transverse, visible branches')
        # At an exact root: z H S=-1, so fixed-boundary gain = -null/S.
        gain=-whole['source_null']/whole['source']
        prefix=1-1/whole['source']
        if not (gain.excludes_zero() and prefix.min_abs()>TOLERANCE):
            raise AssertionError('terminal visibility or first-boundary separation failed')
        branches.append(dict(branch=name,bracket=(lo,hi),left_mismatch=left['mismatch'].as_pair(),
            right_mismatch=right['mismatch'].as_pair(),derivative=whole['derivative'].as_pair(),
            derivative_abs_lower=whole['derivative'].min_abs(),
            root_fixed_boundary_gain=gain.as_pair(),source_null=whole['source_null'].as_pair(),
            source_response=whole['source'].as_pair(),first_prefix_error_lower=prefix.min_abs(),
            chart_separations=chart))
    return dict(parameter_box_radius=radius,independent_parameters=4,branches=branches,
                covers='every real parameter tuple in this closed box; not only sampled rational points',
                class_condition='diagonal real-response, unchanged six-generator affine chart')


def isolate(parameters=Parameters(),branch='first',tolerance=TOLERANCE):
    lo,hi=BRACKETS[branch]
    gl=geometry(lo,parameters)['mismatch']
    gr=geometry(hi,parameters)['mismatch']
    if gl*gr>=0: raise ValueError('branch not bracketed')
    for _ in range(256):
        t=(lo+hi)/2
        value=geometry(t,parameters)['mismatch']
        if abs(value)<tolerance/2: return t
        if gl*value<0: hi=t
        else: lo=t;gl=value
    raise AssertionError('finite rational isolation budget exceeded')


@lru_cache(maxsize=64)
def prepare_model(parameters=Parameters()):
    original,_,*_=fixtures()
    h,b,c,_=(getattr(parameters,name) for name in parameters.__dataclass_fields__)
    library=original.library
    leaves=(AffineLetter((1-h,h,0,0,0,0),library),
            AffineLetter((0,1-b,b,0,0,0),library))
    old=original.designated_head
    target=tuple(qmul(kernel(leaves,old.cell.start.live.context),old.cell.start.live.accumulated))
    head=promote_word(certify_word(old.cell.start,leaves,target))
    # Separate model instances have their own actually certified prefix and
    # inherited endpoint; no old occurrence is edited or pooled with another.
    if original.rounds or original.outputs or len(original.events)!=1:
        raise ValueError('each parameter instance starts from its own fresh entry')
    stock=tuple(head if op==old else op for op in original.stock)
    started=CycleEvent(0,0,'engine-started',head.cell.endpoint,head.cell.endpoint,stock)
    entry=replace(original,lower=head.cell.endpoint,upper=head.cell.endpoint,
                  stock=stock,designated_head=head,events=(started,))
    raw=boundary_readout(head)
    current=context([[raw[i][j]+(c if i==j==0 else -c if i==j==1 else 0)
                      for j in range(3)] for i in range(3)])
    plan=resolve_open(accept_context(request_boundary(entry),current))
    if plan.phase!='PLANNED': raise ValueError('the fixed fresh-source route is required')
    return entry,current,plan


@dataclass(frozen=True)
class ModelOccurrence:
    parameters: Parameters
    branch: str
    representative: Q
    entry: object
    prepared: object
    source: object
    emitted: tuple
    consumer_start: ExecutionState
    decoded: object
    closure_error: Q
    prefix_error: Q
    current_rank: int
    joint_rank: int
    fixed_gain: tuple
    reconstructed: tuple


def execute_model(parameters=Parameters(),branch='first'):
    entry,current,plan=prepare_model(parameters)
    t=isolate(parameters,branch)
    # On this pivot chart the canonical solver's free third weight is zero.
    selected=select_representative(plan,SolutionRule(t))
    published=publish_producer(execute_producer(selected))
    source=published.pending.issue.operation
    analytic=geometry(t,parameters)
    raw=boundary_readout(source);r=parameters.future_readout
    emitted=context([[(1-r)*raw[i][j]+(r/3 if i==j else 0) for j in range(3)] for i in range(3)])
    if (current!=diagonal(analytic['current']) or emitted!=diagonal(analytic['future'])
            or source.cell.beta[0].weights!=(*analytic['weights'],0,0,0)
            or entry.upper.live.accumulated!=(analytic['z'],0,0,0)):
        raise AssertionError('scalar geometry must agree with the unchanged executed kernel')
    staged=ExecutionState(UpperState(emitted,published.upper.live.accumulated),published.upper.executed_word)
    word=(published.pending.head,source)
    first=step(word[0],staged);endpoint=step(word[1],first)
    error=sum(abs(a-b) for a,b in zip(endpoint.live.accumulated,entry.result))
    prefix_error=sum(abs(a-b) for a,b in zip(first.live.accumulated,entry.result))
    if (not error<TOLERANCE/2 or not prefix_error>TOLERANCE
            or endpoint.live.accumulated!=(analytic['mismatch']-1,0,0,0)):
        raise AssertionError('the original fixed result must close at the first tolerant boundary')
    decoded=decode(staged,word,(endpoint.live.accumulated,))
    if (len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries
            or promote_word(source.cell)!=source or promote_word(decoded.outputs[0].cell)!=decoded.outputs[0]):
        raise AssertionError('actual source and actual consumer need exact nested certificates')
    if not (entry.result==published.result==published.pending.result==(-1,0,0,0)
            and published.pending.upper_before==entry.upper
            and published.upper==published.pending.consumer_start
            and published.upper.live.accumulated==staged.live.accumulated==entry.upper.live.accumulated
            and staged.executed_word==entry.upper.executed_word):
        raise AssertionError('entry-bound fixed requirement and consumer inheritance must persist')
    leaf=source.cell.beta[0]
    matrix=action_matrix(current,leaf.library)
    before=first.live.accumulated
    terminal=[list(row) for row in zip(*(tuple(qmul(op.apply(emitted),before)) for op in leaf.library))]
    joint=matrix+terminal
    ranks=len(rref(matrix)[1]),len(rref(joint)[1])
    delta=(*analytic['delta'],0,0,0)
    gain=tuple(sum(row[j]*delta[j] for j in range(6)) for row in terminal)
    reconstructed=tuple(solve(joint,[1,*leaf.kernel(current),*endpoint.live.accumulated]))
    if ranks!=(5,6) or gain!=(analytic['fixed_boundary_gain'],0,0,0) or reconstructed!=leaf.weights:
        raise AssertionError('terminal visibility and source recovery must survive perturbation')
    return ModelOccurrence(parameters,branch,t,entry,published,source,emitted,staged,decoded,
                           error,prefix_error,*ranks,gain,reconstructed)


def ordered_cut_requirements(occurrence,tolerance=TOLERANCE):
    """Exact pullback widths at the actual chronological cuts, same norm/eps."""
    word=occurrence.decoded.outputs[0].cell.beta
    states=[occurrence.consumer_start]
    for operation in word: states.append(step(operation,states[-1]))
    required=[]
    for k,state in enumerate(states):
        suffix=kernel(word[k:],occurrence.emitted)
        if any(suffix[1:]) or not suffix[0]: raise ValueError('nonzero real suffix required')
        center=occurrence.entry.result[0]/suffix[0]
        half_width=tolerance/abs(suffix[0])
        # Retrospective remaining path length: a necessary metric bound,
        # distinct from the exact preimage above and not a new hidden input.
        budget=sum(abs(b.live.accumulated[0]-a.live.accumulated[0])
                   for a,b in zip(states[k:],states[k+1:]))
        distance=abs(state.live.accumulated[0]-occurrence.entry.result[0])
        if distance>budget+tolerance: raise AssertionError('terminal reachability bound failed')
        required.append(dict(cut=k,actual_state=state.live.accumulated,
            required_center=center,exact_half_width=half_width,
            remaining_actual_path_budget=budget,necessary_terminal_radius=budget+tolerance))
    return required


def terminal_tube_width(occurrence,eta):
    """Width in source coordinate of a fixed-boundary endpoint tube.

    Eta is a geometric endpoint neighborhood, not a time or a replaced
    execution tolerance. Centers use the exact attained endpoint.
    """
    eta=Q(eta)
    if eta<0: raise ValueError('nonnegative endpoint radius required')
    return 2*eta/abs(occurrence.fixed_gain[0])


def transverse_readout_obstruction(epsilon=Q(1,10**8)):
    """A genuine small out-of-class readout change obstructs both branches.

    Add epsilon to the xy/yx entries of the generated context, retaining
    trace and symmetry. The unchanged source line has only one free t.
    For the original axis head, the terminal imaginary z component is
    2 z epsilon (lambda1-lambda2) (H+4 epsilon^2-2 S).
    Its nonzero coefficient is interval-certified over both old brackets.
    """
    epsilon=Q(epsilon)
    if not 0<abs(epsilon)<=Q(1,10**8): raise ValueError('small nonzero transverse readout required')
    bounds=[]
    for branch,(lo,hi) in BRACKETS.items():
        g=geometry(Interval(lo,hi))
        coefficient=2*g['z']*(g['weights'][0]-g['weights'][1])*(
            g['head']+4*epsilon*epsilon-2*g['source'])
        if not coefficient.excludes_zero(): raise AssertionError('transverse obstruction not separated')
        bounds.append(dict(branch=branch,imaginary_coefficient=coefficient.as_pair(),
                           imaginary_error_abs_lower=abs(epsilon)*coefficient.min_abs()))
    return dict(epsilon=epsilon,branches=bounds,
        conclusion='for every t in either old bracket, the imaginary terminal component is nonzero',
        scope='no exact fixed real result for this perturbed readout on the unchanged one-parameter source line')


APPROACH_WINDOWS={'first':(Q(6749,1000),Q(6752,1000)),
                  'second':(Q(13498,1000),Q(13501,1000))}


def approach_certificate(radius=Q(1,10**8)):
    """A fixed-F, fixed-epsilon strengthening theorem on geometric curves.

    From the nearby zero of one head factor to the designated exact closure,
    E runs from 0 to -1. On that curve d=|E-F| decreases and |G delta| rises.
    Therefore the HALF WIDTH epsilon/|G delta| of the held-boundary admissible
    source interval strictly contracts. Its center moves: no set-inclusion or
    automatic chronological movement claim is implied.
    """
    box=Parameters(*(Interval(-Q(radius),Q(radius)) for _ in range(4)))
    proof=[]
    for branch,(lo,hi) in APPROACH_WINDOWS.items():
        at_zero=geometry(Q(0),box)
        factor='first' if branch=='first' else 'second'
        head_zero=-at_zero[factor+'_head_action']/at_zero[factor+'_head_slope']
        whole=geometry(Interval(lo,hi),box)
        if not lo<head_zero.lo<=head_zero.hi<hi:
            raise AssertionError('head zero must remain inside the approach window')
        if not (whole['fixed_gain_derivative'].lo>0
                and whole['derivative'].excludes_zero()
                and (whole['derivative'].hi<0 if branch=='first' else whole['derivative'].lo>0)):
            raise AssertionError('endpoint distance and held-boundary strength are not uniformly monotone')
        if not all((whole['future'][i]-whole['future'][j]).excludes_zero()
                   for i,j in ((0,1),(0,2),(1,2))):
            raise AssertionError('the approach curve must remain in the certified chart')
        proof.append(dict(branch=branch,window=(lo,hi),head_zero_interval=head_zero.as_pair(),
            endpoint_derivative=whole['derivative'].as_pair(),
            whole_law_second_derivative=whole['second_derivative'].as_pair(),
            fixed_gain_derivative=whole['fixed_gain_derivative'].as_pair(),
            orientation='increasing t' if branch=='first' else 'decreasing t',
            target_result=-1,execution_tolerance=TOLERANCE,
            conclusion='as endpoint distance to -1 falls from 1 to 0, the held-boundary allowable source interval half-width strictly decreases'))
    return dict(parameter_box_radius=Q(radius),branches=proof,
        metric='absolute width in the fixed normalized current-null source coordinate; same F and epsilon',
        excludes=['automatic time evolution along the curve','nested admissible intervals with moving centers',
                  'a source substitution preserving the whole source-to-context law'])


def approach_probes(occurrence):
    p=occurrence.parameters
    entry,current,plan=prepare_model(p)
    g0=geometry(Q(0),p)
    factor='first' if occurrence.branch=='first' else 'second'
    start=-g0[factor+'_head_action']/g0[factor+'_head_slope']
    trials=[]
    for fraction in (Q(1,4),Q(1,2),Q(3,4),Q(7,8),Q(1)):
        t=start+fraction*(occurrence.representative-start)
        g=geometry(t,p)
        pub=publish_producer(execute_producer(select_representative(plan,SolutionRule(t))))
        source=pub.pending.issue.operation
        raw=boundary_readout(source);r=p.future_readout
        y=context([[(1-r)*raw[i][j]+(r/3 if i==j else 0) for j in range(3)] for i in range(3)])
        staged=ExecutionState(UpperState(y,pub.upper.live.accumulated),pub.upper.executed_word)
        actual=step(source,step(pub.pending.head,staged))
        if actual.live.accumulated!=(g['mismatch']-1,0,0,0):
            raise AssertionError('approach probe must agree with the executed quaternion kernel')
        center=-g['mismatch']/g['fixed_boundary_gain']
        half_width=TOLERANCE/abs(g['fixed_boundary_gain'])
        if source.kernel(current)!=pub.pending.plan.wanted_action:
            raise AssertionError('the whole approach curve must preserve the current correction')
        trials.append(dict(fraction=fraction,representative=t,endpoint=actual.live.accumulated,
            distance_to_fixed_result=abs(g['mismatch']),fixed_boundary_gain=g['fixed_boundary_gain'],
            whole_law_derivative=g['derivative'],
            allowable_source_shift_center=center,allowable_source_half_width=half_width,
            source_executed_and_published=True,completed_flower=abs(g['mismatch'])<TOLERANCE/2))
    if not all(a['distance_to_fixed_result']>b['distance_to_fixed_result']
               and a['allowable_source_half_width']>b['allowable_source_half_width']
               for a,b in zip(trials,trials[1:])):
        raise AssertionError('the actual approach probes must strengthen at fixed F and epsilon')
    return dict(branch=occurrence.branch,head_zero=start,probes=trials,
        meaning='separate candidate-source experiments; not successive edits to a published source or one automatic temporal trajectory')


def rotated_model_control(occurrence):
    """Rotate the entire certified construction, not just its future port."""
    r=((Q(3,5),Q(-12,25),Q(16,25)),(Q(4,5),Q(9,25),Q(-12,25)),(0,Q(4,5),Q(3,5)))
    def vector(v): return tuple(sum(r[i][j]*v[j] for j in range(3)) for i in range(3))
    def quaternion(q): return (q[0],*vector(q[1:]))
    def tensor(y):
        return context([[sum(r[i][a]*y[a][b]*r[j][b] for a in range(3) for b in range(3))
                         for j in range(3)] for i in range(3)])
    library=[]
    for op in occurrence.entry.library:
        witness=op.source.witness
        library.append(promotion(certify(CellWitness(tuple(vector(u) for u in witness.committed_past),
                                                     tuple(vector(u) for u in witness.beta)))))
    library=tuple(library)
    def leaf(a):
        if not isinstance(a,AffineLetter): raise ValueError('this control rotates the primitive committed prefix')
        return AffineLetter(a.weights,library)
    def state(s):
        return ExecutionState(UpperState(tensor(s.live.context),quaternion(s.live.accumulated)),
                              tuple(leaf(a) for a in s.executed_word))
    def operation(a):
        c=a.cell
        return promote_word(certify_word(state(c.start),tuple(leaf(x) for x in c.beta),quaternion(c.target)))
    head=operation(occurrence.entry.designated_head);source=operation(occurrence.source)
    start=state(occurrence.consumer_start)
    result=decode(start,(head,source),(quaternion(occurrence.decoded.state.live.accumulated),))
    if len(result.outputs)!=1 or result.tail or result.boundaries:
        raise AssertionError('the rotated consumer must have its own genuine certificate')
    if result.state.live.accumulated!=occurrence.decoded.state.live.accumulated:
        raise AssertionError('the real actual endpoint must be rotation invariant')
    for original,new in ((occurrence.source,source),(occurrence.entry.designated_head,head)):
        if new.kernel(tensor(occurrence.emitted))!=quaternion(original.kernel(occurrence.emitted)):
            raise AssertionError('quaternion kernel must transform covariantly')
    if tensor(boundary_readout(occurrence.source))!=boundary_readout(source):
        raise AssertionError('the source readout law must transform with the whole model')
    return dict(rotation=r,rotated_context=tensor(occurrence.emitted),
                genuinely_nondiagonal=any(start.live.context[i][j] for i in range(3) for j in range(3) if i!=j),
                source_and_consumer_certified=True,endpoint=result.state.live.accumulated,
                scope='simultaneous proper rotation of the full model; not an independent transverse readout perturbation')


def occurrence_summary(o):
    cuts=ordered_cut_requirements(o)
    return dict(parameters={n:getattr(o.parameters,n) for n in o.parameters.__dataclass_fields__},
        branch=o.branch,representative=o.representative,current_rank=o.current_rank,joint_rank=o.joint_rank,
        actual_source=o.source.cell.beta[0].weights,actual_context=o.emitted,
        fixed_result=o.entry.result,actual_endpoint=o.decoded.state.live.accumulated,
        closure_error=o.closure_error,prefix_error=o.prefix_error,fixed_boundary_gain=o.fixed_gain,
        reconstruction_exact=o.reconstructed==o.source.cell.beta[0].weights,
        ordered_cuts=cuts,terminal_tube_widths=[(eta,terminal_tube_width(o,eta))
                                              for eta in (Q(1,10**6),Q(1,10**9),TOLERANCE)],
        exact_cut_width_monotone=all(a['exact_half_width']>=b['exact_half_width'] for a,b in zip(cuts,cuts[1:])))


def run():
    checks=[]
    def check(name,ok,**details):
        if not ok: raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**details))
    cert=uniform_certificate()
    check('two unique simple branches persist uniformly over a four-parameter continuum',True,certificate=cert)
    check('regular charts and first-prefix separation persist throughout the certified box',
          all(b['first_prefix_error_lower']>TOLERANCE and b['derivative_abs_lower']>0 for b in cert['branches']))
    check('fixed-boundary visibility persists independently of total branch transversality',
          all(Interval(*b['root_fixed_boundary_gain']).excludes_zero() for b in cert['branches']),
          distinction='partial source change at held boundary is not total source-plus-readout change')
    radius=cert['parameter_box_radius']
    parameter_cases=[Parameters(),*(Parameters(*(radius*s for s in signs)) for signs in product((-1,1),repeat=4))]
    cases=[execute_model(p,branch) for p in parameter_cases for branch in BRACKETS]
    check('all 32 box corners and both center branches execute and certify with unchanged decoder',
          len(cases)==34 and all(o.closure_error<TOLERANCE/2 for o in cases),
          executions=len(cases),uniform_theorem_based_on_sampling=False)
    check('current-null terminal visibility and full source reconstruction survive each executed perturbation',
          all(o.current_rank==5 and o.joint_rank==6 and any(o.fixed_gain)
              and o.reconstructed==o.source.cell.beta[0].weights for o in cases))
    for branch in BRACKETS:
        old=record_occurrence(endogenous_flower(branch),'RR46-reference')
        new=next(o for o in cases if o.parameters==Parameters() and o.branch==branch)
        assert (new.source,new.emitted,new.decoded.state)==(old.source,old.consumer_before.live.context,old.consumer_after)
    check('the unperturbed model reproduces RR46 and repaired RR47 exactly',True)
    summaries=[occurrence_summary(o) for o in cases]
    check('the unchanged future result becomes a narrower geometric source tube as the endpoint neighborhood contracts',
          all(all(a[1]>b[1] for a,b in zip(s['terminal_tube_widths'],s['terminal_tube_widths'][1:])) for s in summaries),
          interpretation='endpoint tube radius eta decreases; no stronger execution tolerance is secretly substituted')
    check('smaller remaining motion budgets impose nested necessary terminal neighborhoods',
          all(all(a['necessary_terminal_radius']>=b['necessary_terminal_radius'] for a,b in zip(s['ordered_cuts'],s['ordered_cuts'][1:])) for s in summaries),
          limitation='a necessary metric bound, not the full exact feasible set or an endogenous clock law')
    check('chronological closeness alone does not monotonically strengthen the exact state requirement',
          all(not s['exact_cut_width_monotone'] for s in summaries),
          counterexamples=summaries[:2],same_tolerance_and_norm_at_all_cuts=True)
    obstruction=transverse_readout_obstruction()
    for o in cases[:2]:
        e=obstruction['epsilon'];y=[list(row) for row in o.emitted]
        y[0][1]=y[1][0]=e;y=context(y)
        actual=tuple(qmul(kernel(o.decoded.outputs[0].cell.beta,y),o.entry.upper.live.accumulated))
        g=geometry(o.representative)
        predicted=2*g['z']*e*(g['weights'][0]-g['weights'][1])*(g['head']+4*e*e-2*g['source'])
        assert actual[3]==predicted and abs(actual[3])>TOLERANCE
    check('an arbitrarily small transverse readout need not preserve a scalar exact branch',
          all(b['imaginary_error_abs_lower']>TOLERANCE for b in obstruction['branches']),
          obstruction=obstruction,original_kernel_verified=True)
    approach=approach_certificate(radius)
    probes=[approach_probes(o) for o in cases[:2]]
    check('approaching the future fixed result strengthens the held-boundary source requirement throughout the model box',
          True,certificate=approach,executed_candidate_probes=probes,
          fixed_target_and_tolerance=True,automatic_temporal_progression=False)
    rotations=[rotated_model_control(o) for o in cases[:2]]
    check('the model geometry also survives a genuine change of coordinate frame with full recertification',
          all(item['genuinely_nondiagonal'] and item['source_and_consumer_certified'] for item in rotations),
          exact_rotated_controls=rotations,
          general_basis='proper rotation covariance of tensor readout and quaternion multiplication')
    check('held-boundary strengthening does not imply strengthening of the whole source-to-context law',
          all(Interval(*b['whole_law_second_derivative']).lo>0 for b in approach['branches'])
          and all(all(abs(a['whole_law_derivative'])>abs(b['whole_law_derivative'])
                      for a,b in zip(path['probes'],path['probes'][1:])) for path in probes),
          conclusion='along these approach curves the held-boundary gain rises but the total response sensitivity falls',
          fixed_F_compatibility_set='for a fixed parameter tuple, {t: abs(Phi(t,p))<=epsilon} is one fixed set, not a sequence of automatically nested constraints')
    root=Path(__file__).resolve().parent
    previous=json.loads((root/'closure_causal_pullback_result.json').read_text(encoding='utf-8'))
    paths=['robust_flower_geometry.py','test_robust_flower_geometry.py',*previous['source_sha256']]
    return dict(note='RR48',passed=True,groups=len(checks),checks=checks,occurrences=summaries,
        source_base_commit='529e119da4525a9235138c29862e2ea2c2d1f2ed',
        scope='local structural persistence in a real diagonal model family; quantitative boundary pullbacks',
        final_target_status='structural persistence and local held-boundary strengthening established; whole-law or temporal automatic strengthening not established and natural stronger versions have counterexamples',
        limitations=['all real parameters in the certified scalar-response box, not arbitrary quaternion perturbations',
                     'the source/head/readout family remains a declared model class',
                     'remaining actual path budget is retrospective; a prospective budget needs a law of admissible continuations',
                     'no next-flower connection or independently unknown future force claim'],
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('robust_flower_geometry_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'],executions=len(data['occurrences']))))
