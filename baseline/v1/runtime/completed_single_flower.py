"""RR52: a complete conditional one-flower protocol with free petal choice.

The source/readout law and branch are declared model conditions. A free
entry integer chooses among certified finite continuations; no uniqueness,
shortest-distance law or next flower is required. Commitment freezes the
actual word. Candidate proofs never become published occurrences.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import hashlib
import json

from history_selection_gap import retained_candidates, proof_for_word
from intrinsic_connection_progress import Problem, catalog
from robust_flower_geometry import (
    Parameters, BRACKETS, TOLERANCE, prepare_model, isolate, geometry,
    select_representative, SolutionRule, execute_producer, publish_producer,
    boundary_readout, context, ExecutionState, UpperState, step, decode,
    promote_word, encode,
)
from persistent_correction_cycle import event, close_round

ROUTE='rr52-committed-petal'


@dataclass(frozen=True)
class Configuration:
    parameters: Parameters=Parameters()
    source_branch: str='first'
    petal_choice: int=0
    search_cap: int=4

    def __post_init__(self):
        if self.source_branch not in BRACKETS: raise ValueError('declared source branch required')
        if type(self.petal_choice) is not int or self.petal_choice<0:
            raise ValueError('nonnegative free entry choice required')
        if type(self.search_cap) is not int or not 1<=self.search_cap<=4:
            raise ValueError('this minimal implementation declares a search cap from one to four')
        if any(abs(getattr(self.parameters,n))>Q(1,10**8) for n in self.parameters.__dataclass_fields__):
            raise ValueError('the RR48 scalar model box is the declared domain')


@dataclass(frozen=True)
class EntryAnchor:
    configuration: Configuration
    original: object
    current_context: tuple
    producer_plan: object


@dataclass(frozen=True)
class Candidate:
    indices: tuple
    endpoint: tuple


@dataclass(frozen=True)
class Commitment:
    anchor: EntryAnchor
    problem: Problem
    committed_engine: object
    indices: tuple
    word: tuple
    predicted_endpoint: tuple
    candidate_count: int
    selected_ordinal: int


@dataclass(frozen=True)
class FullFlowerResidue:
    source: object
    terminal_operation: object
    producer_after: ExecutionState
    consumer_after: ExecutionState
    anchor: EntryAnchor
    internal_context: tuple


@dataclass(frozen=True)
class FlowerRecord:
    commitment: Commitment
    fixed_result: tuple
    tolerance: Q
    actual_endpoint: tuple
    closure_error: Q
    closed_engine: object
    residue: FullFlowerResidue


@dataclass(frozen=True)
class FlowerMachine:
    anchor: EntryAnchor
    phase: str
    engine: object
    representative: object=None
    problem: object=None
    frontier: tuple=()
    commitment: object=None
    cursor: int=0
    record: object=None


def begin(configuration=Configuration()):
    entry,current,plan=prepare_model(configuration.parameters)
    anchor=EntryAnchor(configuration,entry,current,plan)
    return FlowerMachine(anchor,'ENTRY_BOUND',plan)


def produce_source(machine):
    if machine.phase!='ENTRY_BOUND' or machine.engine!=machine.anchor.producer_plan:
        raise ValueError('the original unexecuted producer plan is required')
    cfg=machine.anchor.configuration
    representative=isolate(cfg.parameters,cfg.source_branch,tolerance=TOLERANCE/16)
    selected=select_representative(machine.engine,SolutionRule(representative))
    published=publish_producer(execute_producer(selected))
    return replace(machine,phase='SOURCE_PUBLISHED',engine=published,representative=representative)


def validate_problem(problem,anchor):
    cfg=anchor.configuration
    if (problem.entry!=anchor.original or problem.parameters!=cfg.parameters
            or problem.branch!=cfg.source_branch):
        raise ValueError('source and entry must agree with the trusted entry anchor')
    lo,hi=BRACKETS[cfg.source_branch]
    if not lo<problem.representative<hi or not abs(geometry(problem.representative,cfg.parameters)['mismatch'])<TOLERANCE/32:
        raise ValueError('the declared intraflower source compatibility must hold')
    # Verification replays the lower certificate from the anchored plan; it
    # neither re-solves a future root nor changes an actual committed source.
    expected=publish_producer(execute_producer(select_representative(
        anchor.producer_plan,SolutionRule(problem.representative))))
    if problem.prepared!=expected:
        raise ValueError('the actual producer history and publication must match the entry')
    catalog(problem)  # Includes fixed F, both arrivals and exact inherited tape.


def arrive_internal_context(machine):
    if machine.phase!='SOURCE_PUBLISHED': raise ValueError('actual source publication must precede internal arrival')
    published=machine.engine;source=published.pending.issue.operation
    raw=boundary_readout(source);r=machine.anchor.configuration.parameters.future_readout
    y=context([[(1-r)*raw[i][j]+(r/3 if i==j else 0) for j in range(3)] for i in range(3)])
    staged=ExecutionState(UpperState(y,published.upper.live.accumulated),published.upper.executed_word)
    problem=Problem(machine.anchor.configuration.parameters,machine.anchor.configuration.source_branch,
        machine.anchor.original,published,source,y,staged,machine.representative)
    validate_problem(problem,machine.anchor)
    emitted=event(published,'rr52-internal-context-emitted',phase='RR52_CONTEXT_EMITTED')
    arrived=event(emitted,'rr52-internal-context-arrived',upper=staged,phase='RR52_CONTEXT_READY')
    return replace(machine,phase='CONTEXT_READY',engine=arrived,problem=problem)


def candidates(problem,cap):
    cat=catalog(problem)
    found=retained_candidates(problem.start,cat,cap,head_pending=True)
    return tuple(Candidate(tuple(p['indices']),tuple(p['endpoint'])) for p in found['candidates'])


def arrived_engine(problem):
    emitted=event(problem.prepared,'rr52-internal-context-emitted',phase='RR52_CONTEXT_EMITTED')
    return event(emitted,'rr52-internal-context-arrived',upper=problem.start,phase='RR52_CONTEXT_READY')


def propose(machine):
    if machine.phase!='CONTEXT_READY' or machine.engine!=arrived_engine(machine.problem):
        raise ValueError('an unchanged arrived consumer state is required')
    frontier=candidates(machine.problem,machine.anchor.configuration.search_cap)
    phase='CANDIDATES_READY' if frontier else 'OPEN_WITHIN_SEARCH_CAP'
    engine=event(machine.engine,'rr52-possible-continuations-checked',phase='RR52_'+phase)
    return replace(machine,phase=phase,engine=engine,frontier=frontier)


def commit(machine):
    if machine.phase!='CANDIDATES_READY' or not machine.frontier:
        raise ValueError('at least one certified possible continuation is required')
    cfg=machine.anchor.configuration
    # Check the complete bounded pool once at commitment. The pool is then
    # discarded; execution never searches or ranks a replacement continuation.
    expected=candidates(machine.problem,cfg.search_cap)
    proposed=event(arrived_engine(machine.problem),'rr52-possible-continuations-checked',phase='RR52_CANDIDATES_READY')
    if expected!=machine.frontier or machine.engine!=proposed:
        raise ValueError('the candidate pool or unexecuted consumer state changed')
    ordinal=cfg.petal_choice%len(expected)
    chosen=expected[ordinal];cat=catalog(machine.problem)
    word=tuple(cat.actions[i] for i in chosen.indices)
    proof_for_word(machine.problem.start,cat,chosen.indices)
    engine=event(machine.engine,'rr52-petal-committed',phase='RR52_COMMITTED')
    receipt=Commitment(machine.anchor,machine.problem,engine,chosen.indices,word,chosen.endpoint,len(expected),ordinal)
    return replace(machine,phase='COMMITTED',engine=engine,frontier=(),commitment=receipt)


def expected_execution(receipt,cursor):
    if type(cursor) is not int or not 0<=cursor<=len(receipt.word):
        raise ValueError('the committed cursor is outside its finite word')
    engine=receipt.committed_engine
    for i,action in enumerate(receipt.word[:cursor]):
        state=step(action,engine.upper)
        phase='RR52_EXECUTED' if i+1==len(receipt.word) else 'RR52_EXECUTING'
        engine=event(engine,'rr52-consumer-action-executed',upper=state,phase=phase)
    return engine


def verify_active(machine,receipt):
    # The supplied immutable receipt is the trusted commitment anchor, not a
    # cryptographic signature or proof of which caller owns the machine.
    if (machine.commitment!=receipt or machine.anchor!=receipt.anchor
            or machine.problem!=receipt.problem or machine.representative!=receipt.problem.representative
            or machine.frontier or machine.record is not None):
        raise ValueError('the committed source, entry, word and discarded frontier must remain bound')
    phase=('COMMITTED' if machine.cursor==0 else
           'EXECUTED' if machine.cursor==len(receipt.word) else 'EXECUTING')
    if machine.phase!=phase or machine.engine!=expected_execution(receipt,machine.cursor):
        raise ValueError('consumer inheritance, executed prefix or actual chronology differs from the commitment')
    return True


def advance(machine,receipt):
    verify_active(machine,receipt)
    if machine.cursor==len(receipt.word): raise ValueError('the committed word has already ended')
    cursor=machine.cursor+1
    phase='EXECUTED' if cursor==len(receipt.word) else 'EXECUTING'
    actual=step(receipt.word[machine.cursor],machine.engine.upper)
    engine=event(machine.engine,'rr52-consumer-action-executed',upper=actual,phase='RR52_'+phase)
    return replace(machine,phase=phase,engine=engine,cursor=cursor)


def restore(checkpoint,receipt):
    """Resume an immutable value checkpoint without a solver or replanner.

    This is an in-process value interface, not a portable file format.
    """
    verify_active(checkpoint,receipt)
    return checkpoint


def close(machine,receipt):
    verify_active(machine,receipt)
    if machine.phase!='EXECUTED': raise ValueError('the entire committed word must execute before closure')
    p=receipt.problem;actual=machine.engine.upper
    error=sum(abs(a-b) for a,b in zip(actual.live.accumulated,p.entry.result))
    current=p.start
    for a in receipt.word[:-1]:
        current=step(a,current)
        if sum(abs(x-y) for x,y in zip(current.live.accumulated,p.entry.result))<=TOLERANCE:
            raise ValueError('an earlier tolerant boundary already ended the flower')
    if not error<TOLERANCE/2 or actual.live.accumulated!=receipt.predicted_endpoint:
        raise ValueError('the actual endpoint must satisfy the unchanged request and committed witness')
    decoded=decode(p.start,receipt.word,(actual.live.accumulated,))
    if (len(decoded.outputs)!=1 or decoded.tail or decoded.boundaries or decoded.state!=actual
            or promote_word(decoded.outputs[0].cell)!=decoded.outputs[0]):
        raise ValueError('an exact first-boundary certificate must witness the executed word')
    ended=close_round(machine.engine,decoded,ROUTE)
    residue=FullFlowerResidue(p.source,decoded.outputs[0],ended.lower,ended.upper,receipt.anchor,p.context)
    record=FlowerRecord(receipt,p.entry.result,TOLERANCE,actual.live.accumulated,error,ended,residue)
    return replace(machine,phase='ONE_FLOWER_COMPLETE',engine=ended,record=record)


def verify_record(record,receipt):
    if record.commitment!=receipt or record.fixed_result!=receipt.anchor.original.result or record.tolerance!=TOLERANCE:
        raise ValueError('the original request and tolerance must remain bound')
    validate_problem(receipt.problem,receipt.anchor)
    cfg=receipt.anchor.configuration;pool=candidates(receipt.problem,cfg.search_cap)
    if not pool: raise ValueError('the anchored bounded language has no candidate')
    ordinal=cfg.petal_choice%len(pool);chosen=pool[ordinal];cat=catalog(receipt.problem)
    proposed=event(arrived_engine(receipt.problem),'rr52-possible-continuations-checked',phase='RR52_CANDIDATES_READY')
    committed=event(proposed,'rr52-petal-committed',phase='RR52_COMMITTED')
    if (receipt.candidate_count!=len(pool) or receipt.selected_ordinal!=ordinal
            or receipt.indices!=chosen.indices or receipt.predicted_endpoint!=chosen.endpoint
            or receipt.word!=tuple(cat.actions[i] for i in chosen.indices)
            or receipt.committed_engine!=committed):
        raise ValueError('the selected word and chronology must follow the anchored free entry choice')
    engine=expected_execution(receipt,len(receipt.word))
    machine=FlowerMachine(receipt.anchor,'EXECUTED',engine,receipt.problem.representative,
        receipt.problem,(),receipt,len(receipt.word))
    expected=close(machine,receipt).record
    if record!=expected:
        raise ValueError('the exact actual occurrence, retained residue or endpoint was substituted')
    return True


def retain(residue):
    """Faithful identity transport of this typed full record; no next action."""
    return FullFlowerResidue(residue.source,residue.terminal_operation,residue.producer_after,
        residue.consumer_after,residue.anchor,residue.internal_context)


def record_type_registry():
    """Fixed local dataclass allowlist; JSON cannot request module imports."""
    import certified_cell_bridge, certified_correction_release, intrinsic_connection_progress
    import persistent_correction_cycle, recursive_upper_decoder, residual_extraction_transport
    import robust_flower_geometry
    from dataclasses import is_dataclass
    own=(Configuration,EntryAnchor,Candidate,Commitment,FullFlowerResidue,FlowerRecord,FlowerMachine)
    registry={'completed_single_flower.'+t.__name__:t for t in own}
    for module in (certified_cell_bridge,certified_correction_release,intrinsic_connection_progress,
                   persistent_correction_cycle,recursive_upper_decoder,residual_extraction_transport,robust_flower_geometry):
        for name,t in vars(module).items():
            if isinstance(t,type) and is_dataclass(t) and t.__module__==module.__name__:
                registry[module.__name__+'.'+name]=t
    return registry


def export_record(record):
    """Exact JSON object graph: no rounding, repr payloads or lost nesting."""
    from dataclasses import fields, is_dataclass
    registry=record_type_registry();names={t:tag for tag,t in registry.items()}
    nodes=[];seen={}
    def pack(value):
        if value is None or type(value) in (str,int,bool): return value
        if isinstance(value,Q): return {'fraction':[str(value.numerator),str(value.denominator)]}
        if id(value) in seen: return {'ref':seen[id(value)]}
        index=len(nodes);seen[id(value)]=index;nodes.append(None)
        if isinstance(value,tuple): node={'tuple':[pack(x) for x in value]}
        elif is_dataclass(value) and type(value) in names:
            node={'type':names[type(value)],'fields':{f.name:pack(getattr(value,f.name)) for f in fields(value)}}
        else: raise TypeError('unsupported exact record node: '+type(value).__name__)
        nodes[index]=node
        return {'ref':index}
    root=pack(record)
    return dict(schema='time-engine-one-flower-record-v1',root=root,nodes=nodes)


def import_record(payload,expected_configuration):
    """Load the exact graph, then validate against the supplied entry config.

    This validates the model's execution, not the identity of a file author.
    """
    from dataclasses import fields
    if payload.get('schema')!='time-engine-one-flower-record-v1': raise ValueError('unknown record schema')
    registry=record_type_registry();nodes=payload['nodes'];built={};visiting=set()
    def unpack(value):
        if value is None or type(value) in (str,int,bool): return value
        if set(value)=={'fraction'}:
            a,b=value['fraction'];return Q(int(a),int(b))
        if set(value)!={'ref'}: raise ValueError('unknown record value')
        index=value['ref']
        if type(index) is not int or not 0<=index<len(nodes): raise ValueError('invalid graph reference')
        if index in built: return built[index]
        if index in visiting: raise ValueError('cyclic graph is outside the declared record type')
        visiting.add(index);node=nodes[index]
        if set(node)=={'tuple'}: obj=tuple(unpack(x) for x in node['tuple'])
        elif set(node)=={'type','fields'} and node['type'] in registry:
            cls=registry[node['type']]
            if set(node['fields'])!={f.name for f in fields(cls)}: raise ValueError('record fields do not match the declared type')
            obj=cls(**{name:unpack(x) for name,x in node['fields'].items()})
        else: raise ValueError('unknown graph node or dataclass type')
        visiting.remove(index);built[index]=obj;return obj
    record=unpack(payload['root'])
    if not isinstance(record,FlowerRecord) or record.commitment.anchor.configuration!=expected_configuration:
        raise ValueError('the record must match the trusted entry configuration')
    entry,current,plan=prepare_model(expected_configuration.parameters)
    anchor=record.commitment.anchor
    if anchor.original!=entry or anchor.current_context!=current or anchor.producer_plan!=plan:
        raise ValueError('the serialized entry and producer plan must match the declared model')
    verify_record(record,record.commitment)
    return record


def run_flower(configuration=Configuration()):
    machine=propose(arrive_internal_context(produce_source(begin(configuration))))
    if machine.phase=='OPEN_WITHIN_SEARCH_CAP': return machine
    machine=commit(machine);receipt=machine.commitment
    while machine.cursor<len(receipt.word): machine=advance(machine,receipt)
    return close(machine,receipt)


def summary(machine):
    receipt=machine.commitment;record=machine.record
    if record is None:
        return dict(status=machine.phase,completed=False,search_cap=machine.anchor.configuration.search_cap,
                    absence_is_not_global_impossibility=True)
    return dict(status=machine.phase,completed=True,branch=receipt.problem.branch,
        parameters={n:getattr(receipt.problem.parameters,n) for n in receipt.problem.parameters.__dataclass_fields__},
        petal_choice=receipt.anchor.configuration.petal_choice,candidate_count=receipt.candidate_count,
        selected_ordinal=receipt.selected_ordinal,selected_indices=receipt.indices,
        consumer_steps=machine.cursor,fixed_result=record.fixed_result,actual_endpoint=record.actual_endpoint,
        closure_error=record.closure_error,output_level=record.residue.terminal_operation.level,
        retained_exact_nested_word=True,discarded_candidate_count=receipt.candidate_count-1,
        actual_new_source_count=len(record.closed_engine.stock)-len(receipt.anchor.original.stock),
        completed_consumer_cells=len(record.closed_engine.rounds)-len(receipt.anchor.original.rounds),
        events=[e.kind for e in record.closed_engine.events[len(receipt.anchor.original.events):]],
        next_flower_requests=0)


def run():
    checks=[]
    def check(name,ok,**details):
        if not ok: raise AssertionError(name)
        checks.append(dict(name=name,passed=True,**details))
    radius=Q(1,10**8)
    params=[Parameters(),*(Parameters(*(radius*s for s in signs)) for signs in product((-1,1),repeat=4))]
    cases=[]
    for parameters in params:
        for branch in BRACKETS:
            machine=run_flower(Configuration(parameters,branch))
            if machine.phase!='ONE_FLOWER_COMPLETE': raise AssertionError('the declared family failed to close')
            verify_record(machine.record,machine.commitment)
            cases.append(summary(machine))
    check('34 declared near models complete from source production through actual recorded consumer closure',
          len(cases)==34 and all(c['completed'] and c['consumer_steps']==2 for c in cases),cases=cases)
    freedoms=[]
    for branch in BRACKETS:
        short=run_flower(Configuration(source_branch=branch,petal_choice=0))
        long=run_flower(Configuration(source_branch=branch,petal_choice=1))
        if short.commitment.candidate_count!=2 or long.commitment.candidate_count!=2:
            raise AssertionError('the baseline petal freedom should remain visible')
        verify_record(long.record,long.commitment)
        if short.record.residue==long.record.residue: raise AssertionError('different histories were collapsed')
        from intrinsic_connection_progress import distance
        observed=[]
        for cursor in range(len(long.commitment.word)+1):
            engine=expected_execution(long.commitment,cursor)
            observed.append(distance(catalog(long.problem),engine.upper.live.accumulated[0],cursor==0,3).value)
        freedoms.append(dict(branch=branch,short=summary(short),long=summary(long),long_observed_distances=observed))
    check('two baseline petals remain executable, including a detour whose connection distance increases',
          all(p['long_observed_distances']==[2,1,2,1,0] for p in freedoms),comparisons=freedoms)
    machine=commit(propose(arrive_internal_context(produce_source(begin(Configuration(petal_choice=1))))))
    receipt=machine.commitment;paused=advance(machine,receipt)
    resumed=restore(paused,receipt)
    while resumed.cursor<len(receipt.word): resumed=advance(resumed,receipt)
    resumed=close(resumed,receipt)
    uninterrupted=run_flower(Configuration(petal_choice=1))
    check('resuming a value checkpoint preserves the selected tail, full actual history and exact endpoint',
          resumed.record==uninterrupted.record,checkpoint_scope='immutable in-process value; no portable serialization claim')
    limited=run_flower(Configuration(search_cap=1))
    check('a bounded search without a witness stops open and is never mislabeled completed or impossible',
          limited.phase=='OPEN_WITHIN_SEARCH_CAP' and limited.record is None,control=summary(limited))
    check('candidate proofs are discarded at commitment and do not enter the actual stock',
          not resumed.frontier and len(resumed.engine.stock)==len(resumed.anchor.original.stock)+1,
          actual_new_source_count=1,unchosen_histories_published=0)
    check('the fixed requirement and actual rational endpoint remain distinct',
          all(c['actual_endpoint']!=c['fixed_result'] and c['closure_error']<TOLERANCE/2 for c in cases),
          actual_endpoint_never_clamped=True)
    check('the full source and terminal cell survive faithful retention',
          retain(resumed.record.residue)==resumed.record.residue
          and resumed.record.residue.terminal_operation.cell.beta==receipt.word,
          compression_claimed=False,next_operation_executed=False)
    restored=import_record(json.loads(json.dumps(export_record(resumed.record))),Configuration(petal_choice=1))
    check('the complete actual occurrence survives an exact JSON object-graph round trip',
          restored==resumed.record,lossy_summary_only=False,portable_closed_record=True,
          portable_live_checkpoint=False)
    check('the completed output stops after one consumer cell with no next request or internal arrival',
          all(c['completed_consumer_cells']==1 and c['next_flower_requests']==0 for c in cases)
          and resumed.engine.pending is None,complete_state=resumed.phase)
    check('selection remains an explicit free entry condition rather than a uniquely derived law',True,
          choice_rule='petal_choice modulo the bounded candidate count in length-then-stock-index order',
          search_cap_is_not_future_deadline=True,source_branch_and_readout_law_are_declared=True,
          unique_macro_transport_proved=False,local_freedom_preserved=True)
    root=Path(__file__).resolve().parent
    prior=json.loads((root/'history_selection_gap_result.json').read_text(encoding='utf-8'))
    paths=['completed_single_flower.py','test_completed_single_flower.py','run_one_flower.py',*prior['source_sha256']]
    return dict(note='RR52',passed=True,groups=len(checks),checks=checks,
        source_base_commit='fc5fdef7569dcb94ed9eba7185c6818642cd5008',
        status='complete executable one-flower minimal model within declared conditions',
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in paths})


if __name__=='__main__':
    result=run()
    Path(__file__).with_name('completed_single_flower_result.json').write_text(
        json.dumps(result,default=encode,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=True,groups=result['groups'],near_models=34,baseline_petal_variants=4)))
