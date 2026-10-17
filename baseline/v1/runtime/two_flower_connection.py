"""RR53: connect two same-scale flowers without resetting their actual state.

A declared port reads the first completed level-three operation into the next
level-two flower's context. It does not put that higher operation in the lower
stock. The second flower retains RR46-style internal future compatibility.
"""
from dataclasses import dataclass, replace, fields, is_dataclass
from fractions import Fraction as Q
from pathlib import Path
from itertools import product
from math import gcd,lcm
import hashlib
import json

import completed_single_flower as single
from completed_single_flower import (
    Configuration,EntryAnchor,FlowerMachine,Problem,FullFlowerResidue,FlowerRecord,
    TOLERANCE,context,UpperState,ExecutionState,encode,arrived_engine,propose,commit,
    advance,close,expected_execution,record_type_registry,export_record,import_record,
)
from retrospective_residue_readout import load_published,verify_completed_against_receipt
from persistent_correction_cycle import request_boundary,accept_context,resolve_open,event
from single_flower_model import null_direction,SolutionRule,select_representative
from robust_flower_geometry import Interval,Parameters,execute_producer,publish_producer
from closure_native_context_source import boundary_readout
from recursive_upper_decoder import promote_word,regular


@dataclass(frozen=True)
class ConnectionSpec:
    mode: str='anchored'
    strength: Q=Q(1,1024)
    source_branch: int=0
    petal_choice: int=0
    search_cap: int=4

    def __post_init__(self):
        object.__setattr__(self,'strength',Q(self.strength))
        if self.mode not in ('anchored','direct') or not 0<=self.strength<=Q(1,16):
            raise ValueError('a declared port and strength in [0,1/16] are required')
        if type(self.source_branch) is not int or self.source_branch not in (0,1):
            raise ValueError('choose one of the first two isolated source branches')
        Configuration(petal_choice=self.petal_choice,search_cap=self.search_cap)


@dataclass(frozen=True)
class RootCertificate:
    polynomial: tuple
    bracket: tuple
    derivative_range: tuple
    representative: Q
    selected_branch: int
    real_roots: int
    roots_in_search_domain: int


@dataclass(frozen=True)
class ConnectedRecord:
    first: FlowerRecord
    spec: ConnectionSpec
    raw_port: tuple
    arrived_port: tuple
    source_certificate: RootCertificate
    second: FlowerRecord


def ordered_terminal_readout(operation):
    if operation.level!=3 or promote_word(operation.cell)!=operation:
        raise ValueError('the connection source must be an actually certified level-three output')
    leaves=operation.leaves();den=Q(len(leaves)*(len(leaves)+1),2)
    return context([[sum(Q(pos)/den*sum(w*source.source.endpoint[i][j]
        for w,source in zip(leaf.weights,leaf.library)) for pos,leaf in enumerate(leaves,1))
        for j in range(3)] for i in range(3)])


def connection_context(first,spec):
    raw=ordered_terminal_readout(first.residue.terminal_operation)
    if spec.mode=='direct': return raw,raw
    anchor=boundary_readout(first.closed_engine.designated_head)
    y=context([[anchor[i][j]+spec.strength*(raw[i][j]-(Q(1,3) if i==j else 0))
                for j in range(3)] for i in range(3)])
    return raw,y


def prepare_connection(first,spec):
    # The input was already validated as a completed occurrence. Never change
    # its past to make the second request succeed.
    verify_completed_against_receipt(first,first.commitment)
    if first.closed_engine.phase!='IDLE' or first.closed_engine.pending is not None:
        raise ValueError('one completed first flower must precede the next request')
    raw,y=connection_context(first,spec)
    waiting=request_boundary(first.closed_engine)
    emitted=event(waiting,'rr53-terminal-residue-port-emitted')
    plan=resolve_open(accept_context(emitted,y))
    if plan.phase!='PLANNED':
        raise ValueError('this experiment requires a fresh nonzero certified source plan')
    cfg=Configuration(Parameters(),'first' if spec.source_branch==0 else 'second',spec.petal_choice,spec.search_cap)
    return raw,y,EntryAnchor(cfg,first.closed_engine,y,plan)


# Small exact polynomial routines (ascending coefficients). Positive primitive
# rescaling controls integer growth without changing Sturm signs.
def trim(p):
    p=list(map(Q,p))
    while len(p)>1 and p[-1]==0: p.pop()
    return tuple(p)

def add(p,q):
    return trim(tuple((p[i] if i<len(p) else 0)+(q[i] if i<len(q) else 0)
                      for i in range(max(len(p),len(q)))))

def scale(p,a): return trim(tuple(a*x for x in p))

def mul(p,q):
    out=[Q(0)]*(len(p)+len(q)-1)
    for i,a in enumerate(p):
        for j,b in enumerate(q): out[i+j]+=a*b
    return trim(out)

def evaluate(p,t):
    value=0
    for a in reversed(p): value=value*t+a
    return value

def derivative(p): return trim(tuple(i*a for i,a in enumerate(p) if i) or (0,))

def remainder(p,q):
    p=trim(p);q=trim(q)
    if q==(0,): raise ValueError('nonzero divisor required')
    while p!=(0,) and len(p)>=len(q):
        shift=len(p)-len(q);factor=p[-1]/q[-1]
        p=add(p,scale((0,)*shift+q,-factor))
    return p

def primitive(p):
    p=trim(p);den=lcm(*(a.denominator for a in p))
    ints=tuple(int(a*den) for a in p);common=gcd(*ints)
    return tuple(Q(a//common) for a in ints) if common else (Q(0),)

def sturm(p):
    sequence=[primitive(p),primitive(derivative(p))]
    if sequence[0]==(0,): raise ValueError('a nonzero compatibility polynomial is required')
    while sequence[-1]!=(0,):
        r=primitive(scale(remainder(sequence[-2],sequence[-1]),-1))
        if r==(0,):break
        sequence.append(r)
    return tuple(sequence)

def variations(signs):
    signs=[v for v in signs if v]
    return sum(a!=b for a,b in zip(signs,signs[1:]))

def sign(value): return (value>0)-(value<0)

def count_roots(sequence,lo=None,hi=None):
    def at(x,positive):
        if x is not None:return variations([sign(evaluate(p,x)) for p in sequence])
        return variations([sign(p[-1])*(1 if positive or (len(p)-1)%2==0 else -1) for p in sequence])
    return at(lo,False)-at(hi,True)


def compatibility_polynomial(anchor):
    plan=anchor.producer_plan;leaf=plan.pending.plan.leaf
    if any(plan.upper.live.accumulated[1:]): raise ValueError('the connected scalar class is required')
    base=leaf.weights;delta=null_direction(anchor.current_context,plan.library)
    if any(base[3:]) or any(delta[3:]): raise ValueError('the diagonal affine source line is required')
    weights=[(a,b) for a,b in zip(base[:3],delta[:3])]
    head=(Q(1),)
    for h in plan.pending.head.leaves():
        if any(h.weights[3:]): raise ValueError('the diagonal affine head class is required')
        factor=(-Q(1),)
        for a,w in zip(h.weights[:3],weights): factor=add(factor,scale(w,2*a))
        head=mul(head,factor)
    source=(-Q(1),)
    for w in weights:source=add(source,scale(mul(w,w),2))
    return add(scale(mul(head,source),plan.upper.live.accumulated[0]),(1,))


def isolating_brackets(polynomial):
    sequence=sturm(polynomial);lo,hi=Q(-64),Q(64)
    if not evaluate(polynomial,lo) or not evaluate(polynomial,hi):
        raise ValueError('a root at the declared search-domain boundary requires a separate case')
    total=count_roots(sequence);inside=count_roots(sequence,lo,hi)
    pending=[(lo,hi,inside,0)];found=[];d=derivative(polynomial)
    while pending:
        a,b,n,depth=pending.pop()
        if not n:continue
        slope=evaluate(d,Interval(a,b))
        if n==1 and b-a<=Q(1,16) and slope.excludes_zero():
            found.append((a,b,slope.as_pair()));continue
        if depth>=256:raise ValueError('root isolation budget exceeded; not a global impossibility')
        midpoint=next((a+(b-a)/k for k in range(2,8) if evaluate(polynomial,a+(b-a)/k)!=0),None)
        if midpoint is None:raise AssertionError('a quartic cannot vanish at six distinct split points')
        left=count_roots(sequence,a,midpoint)
        pending.extend(((midpoint,b,n-left,depth+1),(a,midpoint,left,depth+1)))
    return total,inside,tuple(sorted(found))


def source_certificate(anchor,branch):
    polynomial=compatibility_polynomial(anchor)
    total,inside,brackets=isolating_brackets(polynomial)
    if len(brackets)<=branch:
        raise ValueError('no requested source branch within the declared connection domain')
    lo,hi,slope=brackets[branch];a,b=lo,hi;left=evaluate(polynomial,a)
    if left*evaluate(polynomial,b)>=0:raise AssertionError('a simple sign-changing source root is required')
    for _ in range(512):
        t=(a+b)/2;value=evaluate(polynomial,t)
        if abs(value)<TOLERANCE/64:
            return RootCertificate(polynomial,(lo,hi),slope,t,branch,total,inside)
        if left*value<0:b=t
        else:a=t;left=value
    raise ValueError('source precision budget exhausted')


def ready_second(anchor,certificate):
    pub=publish_producer(execute_producer(select_representative(
        anchor.producer_plan,SolutionRule(certificate.representative))))
    source=pub.pending.issue.operation;y=boundary_readout(source)
    start=ExecutionState(UpperState(y,pub.upper.live.accumulated),pub.upper.executed_word)
    problem=Problem(Parameters(),anchor.configuration.source_branch,anchor.original,pub,source,y,start,
                    certificate.representative)
    single.catalog(problem)
    return FlowerMachine(anchor,'CONTEXT_READY',arrived_engine(problem),certificate.representative,problem)


def connect_two(first,spec=ConnectionSpec()):
    single.verify_record(first,first.commitment)
    raw,y,anchor=prepare_connection(first,spec)
    certificate=source_certificate(anchor,spec.source_branch)
    machine=propose(ready_second(anchor,certificate))
    if machine.phase=='OPEN_WITHIN_SEARCH_CAP':
        raise ValueError('no witnessed second flower within its declared word cap')
    machine=commit(machine);receipt=machine.commitment
    while machine.cursor<len(receipt.word): machine=advance(machine,receipt)
    second=close(machine,receipt).record
    return ConnectedRecord(first,spec,raw,y,certificate,second)


def verify_connection(record,expected_first,expected_spec):
    if type(record) is not ConnectedRecord or record.first!=expected_first or record.spec!=expected_spec:
        raise ValueError('the original first occurrence and connection conditions must remain bound')
    single.verify_record(expected_first,expected_first.commitment)
    raw,y,anchor=prepare_connection(expected_first,expected_spec)
    c=record.source_certificate;p=compatibility_polynomial(anchor)
    total,inside,brackets=isolating_brackets(p)
    if (c.polynomial!=p or c.selected_branch!=expected_spec.source_branch
            or c.real_roots!=total or c.roots_in_search_domain!=inside
            or len(brackets)<=c.selected_branch
            or (c.bracket[0],c.bracket[1],c.derivative_range)!=brackets[c.selected_branch]
            or not c.bracket[0]<c.representative<c.bracket[1]
            or abs(evaluate(p,c.representative))>=TOLERANCE/64):
        raise ValueError('the second source must satisfy its bound internal future-compatibility branch')
    ready=ready_second(anchor,c)
    committed=commit(propose(ready))
    if (record.raw_port!=raw or record.arrived_port!=y
            or record.second.commitment!=committed.commitment):
        raise ValueError('the connection port, inheritance, stock or chosen second history was substituted')
    verify_completed_against_receipt(record.second,committed.commitment)
    first=record.first.closed_engine;second=record.second.closed_engine
    if (second.rounds[:len(first.rounds)]!=first.rounds
            or second.outputs[:len(first.outputs)]!=first.outputs
            or second.events[:len(first.events)]!=first.events
            or second.stock[:len(first.stock)]!=first.stock):
        raise ValueError('the first completed occurrence must remain an immutable prefix')
    return True


def registry():
    return {**record_type_registry(),**{'two_flower_connection.'+c.__name__:c
        for c in (ConnectionSpec,RootCertificate,ConnectedRecord)}}


def export_connected(record):
    names={t:tag for tag,t in registry().items()};nodes=[];seen={}
    def pack(value):
        if value is None or type(value) in (str,int,bool):return value
        if isinstance(value,Q):return {'fraction':[str(value.numerator),str(value.denominator)]}
        if id(value) in seen:return {'ref':seen[id(value)]}
        index=len(nodes);seen[id(value)]=index;nodes.append(None)
        if isinstance(value,tuple):node={'tuple':[pack(x) for x in value]}
        elif is_dataclass(value) and type(value) in names:
            node={'type':names[type(value)],'fields':{f.name:pack(getattr(value,f.name)) for f in fields(value)}}
        else:raise TypeError('unsupported connection record node')
        nodes[index]=node;return {'ref':index}
    root=pack(record)
    return dict(schema='time-engine-two-flower-record-v1',root=root,nodes=nodes)


def import_connected(payload,expected_first,expected_spec):
    if payload.get('schema')!='time-engine-two-flower-record-v1':raise ValueError('unknown connection schema')
    types=registry();nodes=payload['nodes'];built={};visiting=set()
    def unpack(value):
        if value is None or type(value) in (str,int,bool):return value
        if set(value)=={'fraction'}:return Q(*(int(x) for x in value['fraction']))
        if set(value)!={'ref'}:raise ValueError('unknown graph reference')
        index=value['ref']
        if type(index) is not int or not 0<=index<len(nodes):raise ValueError('invalid graph reference')
        if index in built:return built[index]
        if index in visiting:raise ValueError('cyclic histories are outside this record type')
        visiting.add(index);node=nodes[index]
        if set(node)=={'tuple'}:obj=tuple(unpack(x) for x in node['tuple'])
        elif set(node)=={'type','fields'} and node['type'] in types:
            cls=types[node['type']]
            if set(node['fields'])!={f.name for f in fields(cls)}:raise ValueError('invalid record fields')
            obj=cls(**{k:unpack(v) for k,v in node['fields'].items()})
        else:raise ValueError('unknown typed node')
        visiting.remove(index);built[index]=obj;return obj
    record=unpack(payload['root']);verify_connection(record,expected_first,expected_spec)
    return record


def brief(record):
    first=record.first;second=record.second;c=record.source_certificate
    return dict(first_branch=first.commitment.problem.branch,
        first_choice=first.commitment.anchor.configuration.petal_choice,
        second_source_branch=record.spec.source_branch,second_choice=record.spec.petal_choice,
        connection_mode=record.spec.mode,strength=record.spec.strength,
        port_diagonal=tuple(record.arrived_port[i][i] for i in range(3)),
        representative=c.representative,source_bracket=c.bracket,real_source_roots=c.real_roots,
        second_indices=second.commitment.indices,second_candidates=second.commitment.candidate_count,
        inherited_consumer=second.commitment.anchor.original.upper.live.accumulated,
        first_endpoint=first.actual_endpoint,second_endpoint=second.actual_endpoint,
        fixed_result=second.fixed_result,second_closure_error=second.closure_error,
        total_consumer_cells=len(second.closed_engine.rounds),total_level_three_outputs=len(second.closed_engine.outputs),
        added_level_two_sources=len(second.closed_engine.stock)-len(first.closed_engine.stock),
        first_history_unchanged=True,second_stops_idle=second.closed_engine.phase=='IDLE' and second.closed_engine.pending is None,
        third_request_issued=False)


def run():
    checks=[];records=[];direct=[];ports=[]
    def check(name,ok,**details):
        if not ok:raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**details))
    for first_branch in ('first','second'):
        pair=[]
        for first_choice in (0,1):
            first=load_published(first_branch,first_choice)
            _,_,anchor=prepare_connection(first,ConnectionSpec(mode='direct'))
            p=compatibility_polynomial(anchor);real=count_roots(sturm(p))
            direct.append(dict(first_branch=first_branch,first_choice=first_choice,real_roots=real,
                               polynomial=p,method='exact Sturm variations at negative and positive infinity'))
            pair.append(connection_context(first,ConnectionSpec())[1])
            for second_branch,second_choice in product((0,1),repeat=2):
                spec=ConnectionSpec(source_branch=second_branch,petal_choice=second_choice)
                record=connect_two(first,spec);verify_connection(record,first,spec)
                records.append(brief(record))
        ports.append(dict(first_branch=first_branch,short_context=pair[0],long_context=pair[1],different=pair[0]!=pair[1]))
    check('four direct residue ports have no real second-source solution in the declared affine line',
          len(direct)==4 and all(d['real_roots']==0 for d in direct),certificates=direct)
    check('sixteen anchored connections actually close a second certified flower',
          len(records)==16 and all(r['total_consumer_cells']==2 and r['total_level_three_outputs']==2 for r in records),cases=records)
    check('the first actual endpoint is the exact second inherited consumer value',
          all(r['inherited_consumer']==r['first_endpoint'] and r['first_endpoint']!=r['fixed_result'] for r in records))
    check('both first histories change the actual port into the second flower',all(p['different'] for p in ports),ports=ports)
    check('each connection preserves the first history and adds one published same-level source',
          all(r['first_history_unchanged'] and r['added_level_two_sources']==1 for r in records))
    check('the second target is fixed and the actual endpoint remains unclamped',
          all(r['second_endpoint']!=r['fixed_result'] and r['second_closure_error']<TOLERANCE/2 for r in records))
    check('second flowers retain local petal freedom without putting level-three outputs in level-two stock',
          all(r['second_candidates']>=2 for r in records)
          and {len(r['second_indices']) for r in records}=={2,4})
    check('every second flower stops before a third request',all(r['second_stops_idle'] and not r['third_request_issued'] for r in records))
    controls=[]
    first=load_published('first',0)
    for strength in (Q(0),Q(1,2048),Q(1,512)):
        record=connect_two(first,ConnectionSpec(strength=strength));verify_connection(record,first,record.spec)
        controls.append(brief(record))
    check('declared zero and two nearby nonzero port strengths also execute without a target or state reset',
          len(controls)==3,controls=controls,
          strength_is_an_explicit_connection_condition=True,uniquely_derived_port=False)
    example=connect_two(first);restored=import_connected(json.loads(json.dumps(export_connected(example))),first,ConnectionSpec())
    check('the complete two-flower occurrence survives exact JSON export and validated import',
          restored==example,third_flower_generated=False,
          macro_uniqueness_proved=False,first_petal_freedom_removed=False)
    root=Path(__file__).resolve().parent
    prior=json.loads((root/'retrospective_residue_readout_result.json').read_text(encoding='utf-8'))
    paths=['two_flower_connection.py','test_two_flower_connection.py',*prior['source_sha256']]
    return dict(note='RR53',passed=True,groups=len(checks),checks=checks,
        base_commit='0b3b27b35ce53a70bf20c29129464bbe8b679e0e',
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in paths})


if __name__=='__main__':
    result=run()
    Path(__file__).with_name('two_flower_connection_result.json').write_text(
        json.dumps(result,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=result['groups'],baseline_connections=16,strength_controls=3)))
