"""RR46 second experiment: one flower's boundary comes from its own source.

Current response and later self-generated boundary are solved jointly.
All arithmetic is rational, including certified root bracketing. Execution
uses a fixed declared closure tolerance; no future context/family is input.
Public source law and root branch permit ordinary forward reproduction.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json

from intraflower_future_constraint import (
    fixtures, SolutionRule, context, generated_context, ContextPolicy,
    request_boundary, accept_context, resolve_open, execute_producer,
    publish_producer, event, AffineLetter, kernel, qmul, encode,
)
from single_flower_model import select_representative
from recursive_upper_decoder import (
    ExecutionState, UpperState, decode, step, promote_word, regular,
)


def head_at_source(t):
    return -729+162*t-8*t*t


def leaf_at_source(t):
    return 729-164*t+12*t*t


def boundary_mismatch(t):
    return head_at_source(t)*leaf_at_source(t)-1


def add_interval(a,b):
    return a[0]+b[0],a[1]+b[1]


def multiply_interval(a,b):
    v=[x*y for x in a for y in b]
    return min(v),max(v)


def derivative_interval(lo,hi):
    interval=(lo,hi)
    square=multiply_interval(interval,interval)
    a=add_interval(add_interval((-729,-729),multiply_interval((162,162),interval)),multiply_interval((-8,-8),square))
    b=add_interval(add_interval((729,729),multiply_interval((-164,-164),interval)),multiply_interval((12,12),square))
    da=add_interval((162,162),multiply_interval((-16,-16),interval))
    db=add_interval((-164,-164),multiply_interval((24,24),interval))
    return add_interval(multiply_interval(da,b),multiply_interval(a,db))


@dataclass(frozen=True)
class RootCertificate:
    branch: str
    initial_interval: tuple
    derivative_bounds: tuple
    final_interval: tuple
    representative: Q
    residual: Q
    closure_tolerance: Q
    steps: int


def isolate_boundary(branch='first',tolerance=Q(1,10**12)):
    tolerance=Q(tolerance)
    if not 0<tolerance<=Q(1,1000):
        raise ValueError('fixed positive closure tolerance at most 1/1000 required')
    if branch=='first':
        lo,hi=Q(27,4),Q(6751,1000)
    elif branch=='second':
        lo,hi=Q(13499,1000),Q(27,2)
    else:
        raise ValueError('an explicit root branch is required')
    initial=(lo,hi)
    slopes=derivative_interval(lo,hi)
    if boundary_mismatch(lo)*boundary_mismatch(hi)>=0 or slopes[0]<=0<=slopes[1]:
        raise AssertionError('a simple unique root must be bracketed')
    steps=0
    while True:
        mid=(lo+hi)/2
        value=boundary_mismatch(mid)
        if abs(value)<tolerance/2:
            return RootCertificate(branch,initial,slopes,(lo,hi),mid,value,tolerance,steps)
        if boundary_mismatch(lo)*value<0:
            hi=mid
        else:
            lo=mid
        steps+=1


@dataclass(frozen=True)
class EndogenousFlower:
    entry: object
    prepared_engine: object
    root: RootCertificate
    source: object
    emitted_context: tuple
    consumer_start: ExecutionState
    decoded: object
    fixed_result: tuple
    closure_error: Q
    prefix_error: Q
    events: tuple
    status: str='INTERNAL_BOUNDARY_COMPLETE_WITH_TOLERANCE'


def endogenous_flower(branch='first',tolerance=Q(1,10**12)):
    initial,y,_,_,_=fixtures()
    root=isolate_boundary(branch,tolerance)
    planned=resolve_open(accept_context(request_boundary(initial),y))
    selected=select_representative(planned,SolutionRule(root.representative))
    published=publish_producer(execute_producer(selected))
    source=published.pending.issue.operation
    # RR44 direct port, using the actually executed and published lower cell.
    emitted=generated_context(source,ContextPolicy('direct'))
    if emitted!=context([[14-2*root.representative,0,0],
                         [0,-13+root.representative,0],[0,0,root.representative]]):
        raise AssertionError('the actual source must match the joint boundary equation')
    if not regular(emitted,initial.library):
        raise ValueError('the generated boundary must lie inside the certified chart')
    # The old head was speculative, so changing the arrived context rewrites no
    # executed consumer tape. This is an internal source event before closure.
    staged=ExecutionState(UpperState(emitted,published.upper.live.accumulated),published.upper.executed_word)
    word=(published.pending.head,source)
    first=step(word[0],staged)
    endpoint=step(word[1],first)
    result=initial.result
    error=sum(abs(a-b) for a,b in zip(endpoint.live.accumulated,result))
    prefix_error=sum(abs(a-b) for a,b in zip(first.live.accumulated,result))
    if not error<root.closure_tolerance/2 or not prefix_error>root.closure_tolerance:
        raise ValueError('the fixed future result must close at the first tolerant nonempty boundary')
    # Exact subcertificate records the actual rational endpoint. The supplied
    # requirement remains fixed at -1, certified separately by the error bound.
    decoded=decode(staged,word,(endpoint.live.accumulated,))
    if len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries or decoded.state!=endpoint:
        raise AssertionError('one exact cell must witness the actual ordered path')
    if source.kernel(y)!=(Q(-9),0,0,0) or source.kernel(emitted)!=(leaf_at_source(root.representative),0,0,0):
        raise AssertionError('the same executed source must satisfy both evaluations')
    events=tuple(e.kind for e in published.events[len(initial.events):])+(
        'internal-future-context-emitted','internal-future-context-arrived',
        'consumer-first-boundary-certified-with-tolerance')
    return EndogenousFlower(initial,published,root,source,emitted,staged,decoded,result,error,prefix_error,events)


def summary(f):
    return dict(branch=f.root.branch,representative=f.root.representative,
                weights=f.source.cell.beta[0].weights,generated_future_context=f.emitted_context,
                current_correction=f.source.kernel(f.source.cell.start.live.context),
                current_producer_result=f.prepared_engine.lower.live.accumulated,
                future_head_action=head_at_source(f.root.representative),
                future_correction_action=leaf_at_source(f.root.representative),
                fixed_result=f.fixed_result,actual_endpoint=f.decoded.state.live.accumulated,
                closure_error=f.closure_error,tolerance=f.root.closure_tolerance,
                prefix_error=f.prefix_error,root_initial_interval=f.root.initial_interval,
                derivative_bounds=f.root.derivative_bounds,root_final_interval=f.root.final_interval,
                bisections=f.root.steps,events=f.events)


def forward_replay(f):
    """A chronological comparator uses only entry, public rule and branch."""
    initial=f.entry
    y=generated_context(initial.designated_head,ContextPolicy('direct'))
    computed=isolate_boundary(f.root.branch,f.root.closure_tolerance)
    planned=resolve_open(accept_context(request_boundary(initial),y))
    published=publish_producer(execute_producer(select_representative(
        planned,SolutionRule(computed.representative))))
    source=published.pending.issue.operation
    emitted=generated_context(source,ContextPolicy('direct'))
    staged=ExecutionState(UpperState(emitted,published.upper.live.accumulated),published.upper.executed_word)
    word=(published.pending.head,source)
    actual=tuple(qmul(kernel(word,emitted),staged.live.accumulated))
    decoded=decode(staged,word,(actual,))
    return published.lower,published.stock,emitted,decoded


def run():
    checks=[]
    def check(name,ok,**detail):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**detail))
    first=endogenous_flower()
    second=endogenous_flower('second')
    check('the joint boundary equation has a unique simple real root in each declared branch',
          first.root.derivative_bounds[0]>0 and second.root.derivative_bounds[1]<0
          and all(boundary_mismatch(f.root.initial_interval[0])*boundary_mismatch(f.root.initial_interval[1])<0
                  for f in (first,second)),
          equation='(-729+162t-8t^2)(729-164t+12t^2)=1',
          branches=[summary(first),summary(second)])
    check('current response is preserved exactly while future compatibility selects the null shift',
          all(f.source.kernel(f.source.cell.start.live.context)==(Q(-9),0,0,0)
                  and f.prepared_engine.lower.live.accumulated==(Q(9),0,0,0) for f in (first,second)))
    check('the actual future context is emitted by the executed RR44 direct source within this unit',
          all(f.source in f.prepared_engine.stock
                  and f.emitted_context==generated_context(f.source,ContextPolicy('direct')) for f in (first,second)),
          external_future_contexts=0,external_future_families=0,normalization=False)
    check('the speculative consumer head is not committed before the internal boundary arrives',
          all(f.prepared_engine.upper.executed_word==f.entry.upper.executed_word
                  and f.consumer_start.executed_word==f.entry.upper.executed_word
                  and f.source.cell.start.live.context!=f.emitted_context for f in (first,second)))
    check('one flower ends at its first nonempty boundary within the fixed declared tolerance',
          all(len(f.decoded.outputs)==1 and len(f.decoded.outputs[0].cell.beta)==2
                  and f.closure_error<f.root.closure_tolerance/2 and f.prefix_error>f.root.closure_tolerance
                  for f in (first,second)),
          tolerance=first.root.closure_tolerance,exact_fraction_errors=[first.closure_error,second.closure_error])
    check('the published source, actual endpoint and whole consumer word retain exact certificates',
          all(promote_word(f.source.cell)==f.source
                  and promote_word(f.decoded.outputs[0].cell)==f.decoded.outputs[0]
                  and f.decoded.state.executed_word[:5]==f.entry.upper.executed_word
                  and f.prepared_engine.lower.executed_word[:5]==f.entry.lower.executed_word
                  for f in (first,second)),
          lower_tape=6,consumer_tape=7,output_level=3)
    canonical_future=head_at_source(Q(0))*leaf_at_source(Q(0))
    check('the canonical clean current closure does not satisfy its own emitted future boundary',
          canonical_future==Q(-531441) and -canonical_future!=first.fixed_result[0],
          canonical_current_result=-1,canonical_future_result=-canonical_future)
    check('the boundary is an internally generated event with a forward-realizable public law',
          all(forward_replay(f)==(f.prepared_engine.lower,f.prepared_engine.stock,f.emitted_context,f.decoded)
                  for f in (first,second)),
          future_origin_derived=False,
          scope='a simultaneous internally sourced boundary condition; no independently unknown-family causal advantage')
    root=Path(__file__).resolve().parent
    previous=json.loads((root/'intraflower_future_constraint_result.json').read_text(encoding='utf-8'))
    paths=['endogenous_flower_boundary.py','test_endogenous_flower_boundary.py',*previous['source_sha256']]
    return dict(note='RR46-endogenous-boundary',passed=True,groups=len(checks),checks=checks,
                closure_tolerance=first.root.closure_tolerance,
                boundary_equation='(-729+162t-8t^2)(729-164t+12t^2)=1',
                external_future_context_input=False,external_future_family_input=False,
                source_law='RR44 direct boundary readout of the actual newly published lower source',
                branch_rule='unique simple root inside the declared rational interval',
                future_origin_derived=False,
                limits=['nonzero tolerance is explicit; executed endpoint is not claimed to equal -1 exactly',
                        'the actual rational endpoint has an exact nested WordCell subcertificate',
                        'public source law and branch selection have an ordinary forward realization',
                        'the source law itself is still a proposed model condition, not uniquely derived from v18'],
                source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths})


if __name__=='__main__':
    data=run()
    Path(__file__).with_name('endogenous_flower_boundary_result.json').write_text(
        json.dumps(data,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=data['groups'],external_future_family_input=False)))
