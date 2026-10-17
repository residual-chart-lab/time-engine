"""RR54: three sequential flowers, and one shared upper terminal requirement.

The terminal frame is an explicitly constructed test requirement. The selector
receives a tensor/result/tolerance, never an external list of finished paths.
Its finite continuation family is computed from the original entry and stock.
Counterfactual previews never become the actual committed inventory or tape.
"""
from dataclasses import dataclass,replace
from fractions import Fraction as Q
from functools import lru_cache
from pathlib import Path
from itertools import product
import hashlib,json

import completed_single_flower as single
import two_flower_connection as pair
from two_flower_connection import (
    Configuration,Parameters,ConnectionSpec,RootCertificate,FlowerMachine,
    TOLERANCE,Interval,context,UpperState,ExecutionState,encode,prepare_connection,
    compatibility_polynomial,isolating_brackets,evaluate,derivative,add,mul,scale,
    ready_second,advance,close,event,select_representative,SolutionRule,
    execute_producer,publish_producer,
)
from recursive_upper_decoder import decode,promote_word,step


def decimal_integer(value):
    """Exact decimal chunks; do not loosen the process-wide integer limit."""
    if value<0:return '-'+decimal_integer(-value)
    base=10**1000;parts=[]
    while value>=base:
        value,remainder=divmod(value,base);parts.append(str(remainder).zfill(1000))
    return str(value)+''.join(reversed(parts))


def parse_integer(text):
    if not isinstance(text,str) or not text:raise ValueError('decimal integer text required')
    negative=text.startswith('-');digits=text[1:] if negative else text
    if not digits or any(c not in '0123456789' for c in digits):raise ValueError('invalid decimal integer')
    value=0
    for i in range(0,len(digits),1000):
        chunk=digits[i:i+1000];value=value*10**len(chunk)+int(chunk)
    return -value if negative else value


def encode(value):
    if isinstance(value,Q):
        numerator=decimal_integer(value.numerator)
        return numerator if value.denominator==1 else numerator+'/'+decimal_integer(value.denominator)
    raise TypeError(type(value))


@dataclass(frozen=True)
class Forecast:
    choices: tuple
    records: tuple
    source_certificates: tuple


@dataclass(frozen=True)
class TerminalRequirement:
    x: Q
    result: tuple=(Q(-1),Q(0),Q(0),Q(0))
    tolerance: Q=TOLERANCE

    def __post_init__(self):
        object.__setattr__(self,'x',Q(self.x))
        if not Q(1,4)<self.x<Q(2,5):raise ValueError('the declared terminal frame chart is required')
        if self.result!=(-1,0,0,0) or self.tolerance!=TOLERANCE:
            raise ValueError('the fixed upper requirement and tolerance cannot be replaced')

    @property
    def context(self):return context([[self.x,0,0],[0,1-self.x,0],[0,0,0]])


@dataclass(frozen=True)
class UpperFrameCertificate:
    polynomial: tuple
    bracket: tuple
    derivative_range: tuple
    requirement: TerminalRequirement


@dataclass(frozen=True)
class MacroCommitment:
    requirement: TerminalRequirement
    chosen: Forecast
    admissible_count: int
    free_choice: int


@dataclass(frozen=True)
class MacroOccurrence:
    commitment: MacroCommitment
    actual_records: tuple
    upper_start: ExecutionState
    upper_decoded: object


@lru_cache(maxsize=256)
def isolated(polynomial):return isolating_brackets(polynomial)


def source_witness(anchor,branch):
    p=compatibility_polynomial(anchor);total,inside,brackets=isolated(p)
    if total!=2 or inside!=2:raise ValueError('this experiment declares exactly two simple source branches')
    lo,hi,slope=brackets[branch];a,b=lo,hi;left=evaluate(p,a)
    for _ in range(512):
        t=(a+b)/2;v=evaluate(p,t)
        if abs(v)<TOLERANCE/64:return RootCertificate(p,(lo,hi),slope,t,branch,total,inside)
        if left*v<0:b=t
        else:a=t;left=v
    raise ValueError('source precision budget exceeded')


def commit_from_pool(ready,pool):
    """Same public ordinal rule as RR52; reuse a previously computed pool."""
    cfg=ready.anchor.configuration;ordinal=cfg.petal_choice%len(pool);chosen=pool[ordinal]
    cat=single.catalog(ready.problem);word=tuple(cat.actions[i] for i in chosen.indices)
    proposed=event(ready.engine,'rr52-possible-continuations-checked',phase='RR52_CANDIDATES_READY')
    engine=event(proposed,'rr52-petal-committed',phase='RR52_COMMITTED')
    receipt=single.Commitment(ready.anchor,ready.problem,engine,chosen.indices,word,chosen.endpoint,len(pool),ordinal)
    return replace(ready,phase='COMMITTED',engine=engine,frontier=(),commitment=receipt)


def preview_next(previous):
    _,_,anchor=prepare_connection(previous,ConnectionSpec())
    options=[]
    for branch in (0,1):
        certificate=source_witness(anchor,branch)
        ready=ready_second(replace(anchor,configuration=Configuration(Parameters(),
            'first' if branch==0 else 'second',0,4)),certificate)
        pool=single.candidates(ready.problem,4)
        if len(pool)!=2:raise ValueError('the stated binary-petal comparison needs exactly two candidates')
        for choice in range(len(pool)):
            adjusted=replace(ready,anchor=replace(ready.anchor,configuration=replace(ready.anchor.configuration,petal_choice=choice)))
            machine=commit_from_pool(adjusted,pool);receipt=machine.commitment
            while machine.cursor<len(receipt.word):machine=advance(machine,receipt)
            options.append((branch,choice,close(machine,receipt).record,certificate))
    return tuple(options)


@lru_cache(maxsize=1)
def finite_family():
    """64 isolated previews, not 64 actual histories in one engine."""
    paths=[]
    for source,choice in product(('first','second'),(0,1)):
        first=single.run_flower(Configuration(source_branch=source,petal_choice=choice)).record
        for b2,c2,second,s2 in preview_next(first):
            for b3,c3,third,s3 in preview_next(second):
                paths.append(Forecast((source,choice,b2,c2,b3,c3),(first,second,third),(s2,s3)))
    if len(paths)!=64:raise AssertionError('the declared finite family has changed')
    return tuple(paths)


def kernel_polynomial(record):
    p=(Q(1),)
    for leaf in record.residue.terminal_operation.leaves():
        if any(leaf.weights[3:]):raise ValueError('the declared scalar terminal frame class is required')
        a,b,_=leaf.weights[:3]
        p=mul(p,(2*b-1,2*(a-b)))
    return p


def terminal_polynomial(records):
    p=(Q(1),)
    for r in records:p=mul(p,kernel_polynomial(r))
    z=records[-1].actual_endpoint[0]
    return add(scale(p,z),(Q(1),))


def construct_test_requirement(reference_index=0):
    """An explicit solvable fixture, separate from the actual path selector.

    Construct the common future frame from the declared all-short reference
    using the same original entry and connector. Do not hide this construction
    as a universally derived future-generation law or supply its path to search.
    """
    if type(reference_index) is not int or not 0<=reference_index<64:
        raise ValueError('a declared solvable-fixture index in [0,64) is required')
    reference=finite_family()[reference_index];p=terminal_polynomial(reference.records)
    a,b=Q(1,4),Q(2,5);left=evaluate(p,a)
    if left*evaluate(p,b)>=0:raise ValueError('the reference terminal frame is not bracketed')
    for _ in range(512):
        x=(a+b)/2;value=evaluate(p,x)
        if abs(value)<TOLERANCE/64:
            # A compact local interval proves this is a simple terminal root.
            radius=Q(1,10**9);lo,hi=x-radius,x+radius
            slope=evaluate(derivative(p),Interval(lo,hi))
            if not (slope.excludes_zero() and evaluate(p,lo)*evaluate(p,hi)<0):
                raise AssertionError('the terminal root must have an independent interval certificate')
            return UpperFrameCertificate(p,(lo,hi),slope.as_pair(),TerminalRequirement(x))
        if left*value<0:b=x
        else:a=x;left=value
    raise ValueError('terminal fixture precision budget exceeded')


def upper_preview(records,requirement):
    start=ExecutionState(UpperState(requirement.context,records[-1].actual_endpoint),
                         records[-1].closed_engine.upper.executed_word)
    word=tuple(r.residue.terminal_operation for r in records)
    states=[];current=start
    for op in word:
        current=step(op,current);states.append(current)
    errors=tuple(sum(abs(x-y) for x,y in zip(s.live.accumulated,requirement.result)) for s in states)
    return start,word,states,errors


def admissible(forecast,requirement):
    _,_,_,errors=upper_preview(forecast.records,requirement)
    return errors[-1]<requirement.tolerance/2 and all(e>requirement.tolerance for e in errors[:-1])


def select_macro(requirement,free_choice=0):
    if type(free_choice) is not int or free_choice<0:raise ValueError('a nonnegative free selection value is required')
    allowed=tuple(p for p in finite_family() if admissible(p,requirement))
    if not allowed:raise ValueError('no witness in this finite continuation family; not global impossibility')
    return MacroCommitment(requirement,allowed[free_choice%len(allowed)],len(allowed),free_choice)


def replay_frozen(record,previous=None):
    """Actually execute one frozen producer and consumer without searching."""
    receipt=record.commitment;anchor=receipt.anchor
    if previous is None:
        # The original entry and the unexecuted producer plan were bound and
        # validated at commitment, before any actual new source was executed.
        if anchor.original!=receipt.problem.entry:raise ValueError('the original first entry changed')
    else:
        if previous.closed_engine!=anchor.original:
            raise ValueError('the actual previous exit does not match the next entry')
        _,y=pair.connection_context(previous,ConnectionSpec())
        waiting=pair.request_boundary(previous.closed_engine)
        arrived=pair.accept_context(event(waiting,'rr53-terminal-residue-port-emitted'),y)
        plan=anchor.producer_plan.pending.plan
        from recursive_upper_decoder import qmul,inverse
        wanted=tuple(qmul(arrived.pending.result,inverse(arrived.pending.trial_response)))
        if (anchor.current_context!=y or plan.lower_start!=arrived.lower
                or plan.upper_snapshot!=arrived.pending.decoded
                or plan.speculative_response!=arrived.pending.trial_response or plan.wanted_action!=wanted
                or plan.leaf.kernel(y)!=wanted
                or plan.lower_target!=tuple(qmul(wanted,arrived.lower.live.accumulated))):
            raise ValueError('the frozen source plan changed its actual entry')
        actual_plan=event(arrived,'correction-planned',phase='PLANNED',
                          pending=replace(arrived.pending,plan=plan))
        if actual_plan!=anchor.producer_plan:raise ValueError('the bound producer chronology changed')
    pub=publish_producer(execute_producer(select_representative(anchor.producer_plan,
                           SolutionRule(receipt.problem.representative))))
    if pub!=receipt.problem.prepared:raise ValueError('the frozen source was not actually produced and published')
    ready=single.arrived_engine(receipt.problem)
    proposed=event(ready,'rr52-possible-continuations-checked',phase='RR52_CANDIDATES_READY')
    committed=event(proposed,'rr52-petal-committed',phase='RR52_COMMITTED')
    if committed!=receipt.committed_engine:raise ValueError('the frozen consumer entry changed')
    machine=FlowerMachine(anchor,'COMMITTED',committed,receipt.problem.representative,receipt.problem,(),receipt,0)
    while machine.cursor<len(receipt.word):machine=advance(machine,receipt)
    actual=close(machine,receipt).record
    if actual!=record:raise ValueError('actual execution differed from the committed witness')
    return actual


def execute_macro(commitment):
    records=[]
    for forecast in commitment.chosen.records:
        records.append(replay_frozen(forecast,records[-1] if records else None))
    records=tuple(records);start,word,states,errors=upper_preview(records,commitment.requirement)
    if not (errors[-1]<TOLERANCE/2 and all(e>TOLERANCE for e in errors[:-1])):
        raise ValueError('the actual upper terminal requirement failed')
    decoded=decode(start,word,(states[-1].live.accumulated,))
    if len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries or decoded.state!=states[-1]:
        raise ValueError('the three outputs did not close one first-boundary upper cell')
    if promote_word(decoded.outputs[0].cell)!=decoded.outputs[0]:raise ValueError('upper certificate failed')
    return MacroOccurrence(commitment,records,start,decoded)


def verify_occurrence(occurrence,receipt):
    if type(occurrence) is not MacroOccurrence or occurrence.commitment!=receipt:
        raise ValueError('the common future condition and chosen history must stay bound')
    if occurrence!=execute_macro(receipt):raise ValueError('the actual three-flower occurrence was substituted')
    return True


def macro_registry():
    return {**pair.registry(),**{'three_flower_constraint.'+cls.__name__:cls for cls in
        (Forecast,TerminalRequirement,UpperFrameCertificate,MacroCommitment,MacroOccurrence)}}


def export_macro(record):
    from dataclasses import fields,is_dataclass
    names={cls:tag for tag,cls in macro_registry().items()};nodes=[];seen={}
    def pack(value):
        if value is None or type(value) in (str,int,bool):return value
        if isinstance(value,Q):return {'fraction':[decimal_integer(value.numerator),decimal_integer(value.denominator)]}
        if id(value) in seen:return {'ref':seen[id(value)]}
        index=len(nodes);seen[id(value)]=index;nodes.append(None)
        if isinstance(value,tuple):node={'tuple':[pack(v) for v in value]}
        elif is_dataclass(value) and type(value) in names:
            node={'type':names[type(value)],'fields':{f.name:pack(getattr(value,f.name)) for f in fields(value)}}
        else:raise ValueError('unsupported macro record node')
        nodes[index]=node;return {'ref':index}
    root=pack(record)
    return dict(schema='time-engine-three-flower-upper-occurrence-v1',root=root,nodes=nodes)


def import_macro(payload,expected_requirement,free_choice=0):
    from dataclasses import fields
    if payload.get('schema')!='time-engine-three-flower-upper-occurrence-v1':raise ValueError('unknown macro schema')
    types=macro_registry();nodes=payload['nodes'];built={};visiting=set()
    def unpack(value):
        if value is None or type(value) in (str,int,bool):return value
        if set(value)=={'fraction'}:return Q(*(parse_integer(x) for x in value['fraction']))
        if set(value)!={'ref'}:raise ValueError('invalid graph reference')
        i=value['ref']
        if type(i) is not int or not 0<=i<len(nodes):raise ValueError('invalid node index')
        if i in built:return built[i]
        if i in visiting:raise ValueError('cyclic macro history is outside this model')
        visiting.add(i);node=nodes[i]
        if set(node)=={'tuple'}:obj=tuple(unpack(v) for v in node['tuple'])
        elif set(node)=={'type','fields'} and node['type'] in types:
            cls=types[node['type']]
            if set(node['fields'])!={f.name for f in fields(cls)}:raise ValueError('unknown record fields')
            obj=cls(**{k:unpack(v) for k,v in node['fields'].items()})
        else:raise ValueError('unknown macro node type')
        visiting.remove(i);built[i]=obj;return obj
    occurrence=unpack(payload['root'])
    receipt=select_macro(expected_requirement,free_choice)
    verify_occurrence(occurrence,receipt)
    return occurrence


def run():
    paths=finite_family();fixture=construct_test_requirement();requirement=fixture.requirement
    commitment=select_macro(requirement);actual=execute_macro(commitment);verify_occurrence(actual,commitment)
    allowed=[p for p in paths if admissible(p,requirement)];firsts=sorted({p.choices[:2] for p in allowed})
    all_firsts=sorted({p.choices[:2] for p in paths})
    failures=[]
    for first in all_firsts:
        alternatives=[p for p in paths if p.choices[:2]==first]
        errors=[upper_preview(p.records,requirement)[-1][-1] for p in alternatives]
        failures.append(dict(first=first,continuations_checked=len(alternatives),best_terminal_error=min(errors),
                             has_admissible_continuation=any(admissible(p,requirement) for p in alternatives)))
    checks=[]
    def check(name,ok,**details):
        if not ok:raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**details))
    check('three same-level flowers close on all 64 isolated allowed previews',len(paths)==64,
          first_choices=all_firsts,second_prefixes=16,three_flower_previews=64)
    check('a shared future upper requirement excludes first choices even after all later allowed choices are retried',
          0<len(firsts)<len(all_firsts),admissible_paths=[p.choices for p in allowed],
          first_choices_before=all_firsts,first_choices_after=firsts,per_first=failures)
    rejected=[f['best_terminal_error'] for f in failures if not f['has_admissible_continuation']]
    check('the rejected first choices miss by more than one million times the unchanged tolerance',
          bool(rejected) and min(rejected)>TOLERANCE*10**6,
          minimum_error_among_excluded_first_choices=min(rejected),
          minimum_error_to_tolerance_ratio=min(rejected)/TOLERANCE)
    _,_,_,errors=upper_preview(actual.actual_records,requirement)
    check('three actual outputs close one certified upper cell at its first nonempty boundary',
          len(actual.upper_decoded.outputs)==1 and len(actual.upper_decoded.outputs[0].cell.beta)==3,
          errors=errors,actual_upper_endpoint=actual.upper_decoded.state.live.accumulated,
          fixed_result=requirement.result,tolerance=requirement.tolerance,output_level=actual.upper_decoded.outputs[0].level)
    alternate=construct_test_requirement(63).requirement
    alternate_allowed=[p for p in paths if admissible(p,alternate)]
    alternate_firsts=sorted({p.choices[:2] for p in alternate_allowed})
    alternate_actual=execute_macro(select_macro(alternate))
    check('changing only the shared future frame changes which first choices can start the actual motion',
          bool(alternate_firsts) and alternate_firsts!=firsts,
          first_requirement=requirement.context,first_allowed=firsts,
          alternate_requirement=alternate.context,alternate_allowed=alternate_firsts,
          result_and_tolerance_unchanged=True,terminal_frames_are_declared_test_conditions=True,
          alternate_actual_upper_endpoint=alternate_actual.upper_decoded.state.live.accumulated)
    relaxed=[]
    for index in range(0,64,16):
        own=construct_test_requirement(index).requirement
        if not admissible(paths[index],own):raise AssertionError('the declared solvable control must close')
        relaxed.append(paths[index].choices[:2])
    check('allowing each path its own terminal frame restores all four first choices',
          sorted(set(relaxed))==all_firsts,first_choices_with_unbound_terminal_frame=relaxed,
          constraint_is_from_the_common_future_condition=True)
    final=actual.actual_records[-1].closed_engine
    check('only the chosen history reaches the actual ledger and all three stocks remain at the correct scale',
          len(final.rounds)==3 and len(final.outputs)==3 and len(final.stock)==7
          and all(op.level==2 for op in final.stock) and all(op.level==3 for op in final.outputs),
          actual_source_productions=3,actual_same_scale_flowers=3,additional_upper_enclosure=1,
          candidate_previews_are_not_actual_occurrences=True)
    check('the macro future frame is a declared constructed fixture rather than a secretly supplied path list',True,
          construction='all-short reference continuation; joint terminal-frame root in x in (1/4,2/5)',
          context=requirement.context,frame_root_bracket=fixture.bracket,frame_derivative_range=fixture.derivative_range,
          terminal_frame_independently_generated=False,arbitrary_future_uniqueness_proved=False)
    root=Path(__file__).resolve().parent
    prior=json.loads((root/'two_flower_connection_result.json').read_text(encoding='utf-8'))
    sources=['three_flower_constraint.py','test_three_flower_constraint.py',*prior['source_sha256']]
    return dict(note='RR54',passed=True,groups=len(checks),checks=checks,
        base_commit='5d8f222a595996919842caf47807225f4669533a',
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in sources})


if __name__=='__main__':
    result=run()
    Path(__file__).with_name('three_flower_constraint_result.json').write_text(
        json.dumps(result,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=result['groups'],local_paths=64,
        first_choices_before=len(result['checks'][1]['first_choices_before']),
        first_choices_after=len(result['checks'][1]['first_choices_after']))))
