"""RR57: strengthen Time Engine with its completed 3+1 component embedded.

The input is the authenticated RR56 snapshot, not a new 3+1 model. All first
contacts close at the same local frame. Retained action differences then enter
the unchanged RR53 connector and the RR54 common upper requirement. Forecast
ledgers remain isolated; actual execution replays one frozen path only.
"""
from dataclasses import dataclass, replace, fields, is_dataclass
from functools import lru_cache
from pathlib import Path
from fractions import Fraction as Q
import hashlib
import json
import re
import time

import outbound as port
import three_flower_constraint as triple
import two_flower_connection as pair
from persistent_correction_cycle import request_boundary, accept_context, resolve_open

HERE = Path(__file__).resolve().parent
OUTPUT = port.ROOT / '.work/rr57-local'
SCHEMA = 'time-engine-embedded-3plus1-three-flower-v1'
_SUFFIXES = {}


@lru_cache(maxsize=3)
def published_record(name):
    """Authenticated frozen input; never regenerate SGD, J, K or source roots."""
    manifest = json.loads((HERE / 'records/manifest.json').read_bytes())
    entry = next(r for r in manifest['records'] if r['path'] == 'records/'+name+'.record.json')
    future = entry['requirement']
    requirement = port.FutureRequirement(tuple(tuple(Q(x) for x in row) for row in future['context']))
    return port.import_occurrence((HERE / entry['path']).read_bytes(), requirement,
        config=port.CourseConfig(**{**entry['config'], 'order': tuple(entry['config']['order'])}),
        mode=entry['mode'], spec=port.PortSpec(**entry['spec']), free_choice=entry['free_choice'],
        verification='transport', trusted_sha256=entry['sha256'])


@lru_cache(maxsize=8)
def prepare(mode='keep', gain=Q(1)):
    if mode not in ('keep', 'erase', 'restore'):
        raise ValueError('this experiment declares keep, erase and restore')
    source = published_record('erase-primary' if mode == 'erase' else 'keep-primary').commitment
    state = replace(source.state, mode=mode)
    spec = port.PortSpec(gain=gain)
    return port.Prepared(state, source.receiver, spec,
        tuple(port.contact_candidate(state, source.receiver, spec, i) for i in range(4)))


def local_requirement(prepared):
    # Deliberately a common local closure fixture at the current frame: the
    # port's null property makes all four sources indistinguishable here.
    return port.FutureRequirement(prepared.receiver.anchor.current_context)


@dataclass(frozen=True)
class FirstReceipt:
    prepared: port.Prepared
    contact_index: int
    petal_choice: int

    def __post_init__(self):
        if type(self.contact_index) is not int or self.contact_index not in range(4):
            raise ValueError('one of the four embedded contacts is required')
        if type(self.petal_choice) is not int or self.petal_choice not in (0, 1):
            raise ValueError('the declared short or detour word is required')


@dataclass(frozen=True)
class FirstResidue:
    source: object
    terminal_operation: object
    producer_after: object
    consumer_after: object
    internal_context: tuple


@dataclass(frozen=True)
class FirstClosure:
    receipt: FirstReceipt
    fixed_result: tuple
    tolerance: Q
    actual_endpoint: tuple
    closure_error: Q
    closed_engine: object
    residue: FirstResidue


def execute_first(receipt):
    """Exact TE execution from an already trusted frozen first receipt."""
    p = receipt.prepared
    candidate = p.candidates[receipt.contact_index]
    receiver = p.receiver
    requirement = local_requirement(p)
    if candidate.contact_index != receipt.contact_index:
        raise ValueError('the contact and its bound source differ')
    engine = receiver.anchor.producer_plan
    if (candidate.leaf.library != engine.library or
            candidate.leaf.kernel(receiver.anchor.current_context) != engine.pending.plan.wanted_action):
        raise ValueError('the frozen source changed the anchored current compensation')
    plan = replace(engine.pending.plan, leaf=candidate.leaf)
    engine = port.event(engine, 'rr57-embedded-contact-bound', pending=replace(engine.pending, plan=plan))
    published = port.publish_producer(port.execute_producer(engine))
    source = published.pending.issue.operation
    port.available(published, source)
    start = port.ExecutionState(port.UpperState(requirement.context, published.upper.live.accumulated),
                                published.upper.executed_word)
    if start.live.accumulated != receiver.anchor.original.upper.live.accumulated:
        raise ValueError('the consumer inheritance changed before context arrival')
    word = (published.pending.head, source) if receipt.petal_choice == 0 else (published.pending.head,)*2+(source,)*2
    engine = port.event(published, 'rr57-common-local-context-arrived', upper=start)
    errors = []
    for op in word:
        state = port.step(op, engine.upper)
        engine = port.event(engine, 'rr57-consumer-action-executed', upper=state)
        errors.append(sum(abs(a-b) for a,b in zip(state.live.accumulated, requirement.result)))
    endpoint = engine.upper.live.accumulated
    if not (errors[-1] < requirement.tolerance/2 and all(e > requirement.tolerance for e in errors[:-1])):
        raise ValueError('the frozen word must close first at its actual final boundary')
    decoded = port.decode(start, word, (endpoint,))
    if (len(decoded.outputs) != 1 or decoded.tail or decoded.boundaries or decoded.state != engine.upper
            or port.promote_word(decoded.outputs[0].cell) != decoded.outputs[0]):
        raise ValueError('one actual exact cell certificate is required')
    closed = port.close_round(engine, decoded, 'rr57-embedded-first-flower')
    residue = FirstResidue(source, decoded.outputs[0], closed.lower, closed.upper, requirement.context)
    return FirstClosure(receipt, requirement.result, requirement.tolerance, endpoint, errors[-1], closed, residue)


def first_options(prepared):
    return tuple(execute_first(FirstReceipt(prepared, i, j)) for i in range(4) for j in range(2))


def preview_second(first):
    # The RR53 entry validator expects an RR52-specific source-generated frame.
    # Here the first entry is RR57's explicitly different, authenticated fixed
    # frame. Recheck it with its own receipt, then apply the SAME RR53 port,
    # request/arrival/planning operations and original RR54 suffix machinery.
    if first != execute_first(first.receipt):
        raise ValueError('the completed integrated first occurrence changed')
    spec = pair.ConnectionSpec()
    _, y = pair.connection_context(first, spec)
    waiting = request_boundary(first.closed_engine)
    plan = resolve_open(accept_context(port.event(waiting, 'rr53-terminal-residue-port-emitted'), y))
    if plan.phase != 'PLANNED':
        raise ValueError('a new nonzero source plan is required')
    anchor = pair.EntryAnchor(pair.Configuration(), first.closed_engine, y, plan)
    options = []
    for branch in (0, 1):
        certificate = triple.source_witness(anchor, branch)
        ready = pair.ready_second(replace(anchor, configuration=pair.Configuration(
            source_branch='first' if branch == 0 else 'second')), certificate)
        pool = port.single.candidates(ready.problem, 4)
        if len(pool) != 2:
            raise ValueError('the declared suffix family requires two locally admissible words')
        for choice in range(2):
            adjusted = replace(ready, anchor=replace(ready.anchor,
                configuration=replace(ready.anchor.configuration, petal_choice=choice)))
            machine = triple.commit_from_pool(adjusted, pool)
            receipt = machine.commitment
            while machine.cursor < len(receipt.word):
                machine = pair.advance(machine, receipt)
            options.append((branch, choice, pair.close(machine, receipt).record, certificate))
    return tuple(options)


@dataclass(frozen=True)
class Forecast:
    choices: tuple
    records: tuple
    source_certificates: tuple


@lru_cache(maxsize=8)
def finite_family(prepared):
    paths = []
    for first in first_options(prepared):
        key = (first.closed_engine, first.residue.terminal_operation)
        if key not in _SUFFIXES:
            rows = []
            for b2,c2,second,s2 in preview_second(first):
                for b3,c3,third,s3 in triple.preview_next(second):
                    rows.append((b2,c2,b3,c3,second,third,s2,s3))
            _SUFFIXES[key] = tuple(rows)
        for b2,c2,b3,c3,second,third,s2,s3 in _SUFFIXES[key]:
            r = first.receipt
            paths.append(Forecast((r.contact_index,r.petal_choice,b2,c2,b3,c3),
                (first,second,third), (s2,s3)))
        print('RR57 forecast prefix',prepared.state.mode,first.receipt.contact_index,
              first.receipt.petal_choice,'paths',len(paths),flush=True)
    if len(paths) != 128:
        raise AssertionError('eight first choices times sixteen suffixes must remain available')
    return tuple(paths)


def construct_requirement(reference):
    """Declared solvable fixture, constructed once and shared across modes."""
    polynomial = triple.terminal_polynomial(reference.records)
    a,b = Q(1,4),Q(2,5)
    left = triple.evaluate(polynomial,a)
    if left*triple.evaluate(polynomial,b) >= 0:
        raise ValueError('the declared future-frame interval has no sign bracket')
    for _ in range(512):
        x = (a+b)/2
        value = triple.evaluate(polynomial,x)
        if abs(value) < port.EPSILON/64:
            lo,hi = x-Q(1,10**9),x+Q(1,10**9)
            slope = triple.evaluate(triple.derivative(polynomial),triple.Interval(lo,hi))
            if not (slope.excludes_zero() and triple.evaluate(polynomial,lo)*triple.evaluate(polynomial,hi)<0):
                raise ValueError('a simple upper-frame root certificate is required')
            return triple.UpperFrameCertificate(polynomial,(lo,hi),slope.as_pair(),triple.TerminalRequirement(x))
        if left*value < 0:
            b=x
        else:
            a=x
            left=value
    raise ValueError('upper-frame precision budget exceeded')


def allowed(paths, requirement):
    return tuple(p for p in paths if triple.admissible(p,requirement))


@dataclass(frozen=True)
class Commitment:
    prepared: port.Prepared
    requirement: triple.TerminalRequirement
    chosen: Forecast
    admissible_count: int
    free_choice: int


def select(prepared, requirement, free_choice=0):
    if type(free_choice) is not int or free_choice < 0:
        raise ValueError('a nonnegative current free choice is required')
    if prepared != prepare(prepared.state.mode,prepared.spec.gain):
        raise ValueError('the authenticated completed 3+1 input and unchanged port must remain bound')
    choices = allowed(finite_family(prepared),requirement)
    if not choices:
        raise ValueError('no witness among the declared 128 continuations; not global impossibility')
    return Commitment(prepared,requirement,choices[free_choice%len(choices)],len(choices),free_choice)


@dataclass(frozen=True)
class Occurrence:
    commitment: Commitment
    neural_contact: port.NeuralContact
    actual_records: tuple
    upper_start: object
    upper_decoded: object


def execute(receipt, frozen_contact=None):
    """Replay one committed history; no search, root solver or 3+1 redesign."""
    if (type(receipt) is not Commitment or len(receipt.chosen.records)!=3
            or len(receipt.chosen.source_certificates)!=2 or receipt.admissible_count<1
            or type(receipt.free_choice) is not int or receipt.free_choice<0):
        raise ValueError('a complete frozen three-flower commitment is required')
    first = receipt.chosen.records[0]
    if first.receipt.prepared != receipt.prepared:
        raise ValueError('the committed first entry differs from the embedded input')
    suffix_choices=[]
    for record,certificate in zip(receipt.chosen.records[1:],receipt.chosen.source_certificates):
        r=record.commitment
        branch=0 if r.anchor.configuration.source_branch=='first' else 1
        if (certificate.selected_branch!=branch or certificate.representative!=r.problem.representative
                or certificate.polynomial!=pair.compatibility_polynomial(r.anchor)
                or not certificate.bracket[0]<certificate.representative<certificate.bracket[1]
                or abs(triple.evaluate(certificate.polynomial,certificate.representative))>=port.EPSILON/64):
            raise ValueError('the frozen suffix source certificate changed')
        suffix_choices.extend((branch,r.anchor.configuration.petal_choice))
    if receipt.chosen.choices!=(first.receipt.contact_index,first.receipt.petal_choice,*suffix_choices):
        raise ValueError('the path descriptor differs from the executed choices')
    contact = frozen_contact if frozen_contact is not None else port.execute_contact(
        receipt.prepared.state,first.receipt.contact_index)
    state = receipt.prepared.state
    expected_before = port.NeuralState(state.course.checkpoints[-1].network,state.vector)
    x,target = port.CONTACTS[first.receipt.contact_index]
    if (contact.contact_index != first.receipt.contact_index or contact.sample != x or contact.target != target
            or contact.before != expected_before or len(contact.after.network) != 17 or len(contact.after.tangent) != 4
            or contact.fixed_readout_response != port.dot(state.radial,
                port.subtract(contact.after.tangent,state.vector))/port.dot(state.radial,state.radial)):
        raise ValueError('the actual neural contact changed its trusted entry')
    actual_first = execute_first(first.receipt)
    if actual_first != first:
        raise ValueError('the first actual flower differs from its frozen forecast')
    records = [actual_first]
    for forecast in receipt.chosen.records[1:]:
        records.append(triple.replay_frozen(forecast,records[-1]))
    records = tuple(records)
    start,word,states,errors = triple.upper_preview(records,receipt.requirement)
    if not (errors[-1] < port.EPSILON/2 and all(e > port.EPSILON for e in errors[:-1])):
        raise ValueError('the actual upper word failed its unchanged requirement')
    decoded = port.decode(start,word,(states[-1].live.accumulated,))
    if (len(decoded.outputs) != 1 or decoded.tail or decoded.boundaries or decoded.state != states[-1]
            or port.promote_word(decoded.outputs[0].cell) != decoded.outputs[0]):
        raise ValueError('the actual three outputs must certify one first upper boundary')
    return Occurrence(receipt,contact,records,start,decoded)


def verify_occurrence(record, receipt, *, frozen_contact=False):
    if type(record) is not Occurrence or record.commitment != receipt:
        raise ValueError('the original requirement, entry and free selection must remain bound')
    expected = execute(receipt,record.neural_contact if frozen_contact else None)
    if record != expected:
        raise ValueError('the actual first history, inheritance, source publication or upper endpoint changed')
    return True


def registry():
    own = (FirstReceipt,FirstResidue,FirstClosure,Forecast,Commitment,Occurrence)
    return {**port.registry(),**{'three_flower.'+cls.__name__:cls for cls in own}}


def export_record(record):
    types = {cls:tag for tag,cls in registry().items()}
    nodes,seen = [],{}
    def pack(value):
        if value is None or type(value) in (str,int,bool): return value
        if isinstance(value,Q): return {'fraction':[triple.decimal_integer(value.numerator),triple.decimal_integer(value.denominator)]}
        if id(value) in seen: return {'ref':seen[id(value)]}
        index=len(nodes);seen[id(value)]=index;nodes.append(None)
        if isinstance(value,tuple): node={'tuple':[pack(v) for v in value]}
        elif is_dataclass(value) and type(value) in types:
            node={'type':types[type(value)],'fields':{f.name:pack(getattr(value,f.name)) for f in fields(value)}}
        else: raise ValueError('unsupported exact integrated record node')
        nodes[index]=node
        return {'ref':index}
    root=pack(record)
    return dict(schema=SCHEMA,root=root,nodes=nodes)


def import_record(raw, requirement, mode='keep', gain=Q(1), free_choice=0, *, trusted_sha256):
    """Authenticated transport, then exact replay; upstream snapshots stay inputs.

    The external hash authenticates the selected proof and binary64 contact.
    Full 128-family enumeration is an independent experiment, not repeated by
    this transport path. The external receipt binds C, mode, gain and choice.
    """
    if not isinstance(raw,bytes) or not isinstance(trusted_sha256,str) or not re.fullmatch('[0-9a-f]{64}',trusted_sha256):
        raise ValueError('original bytes and an external trusted SHA-256 are required')
    if hashlib.sha256(raw).hexdigest() != trusted_sha256:
        raise ValueError('the original integrated record bytes changed')
    payload=json.loads(raw)
    if payload.get('schema') != SCHEMA: raise ValueError('unknown integrated record schema')
    types,nodes,built,visiting=registry(),payload['nodes'],{},set()
    def unpack(value):
        if value is None or type(value) in (str,int,bool): return value
        if set(value)=={'fraction'}: return Q(*(triple.parse_integer(v) for v in value['fraction']))
        if set(value)!={'ref'}: raise ValueError('unknown graph value')
        index=value['ref']
        if type(index) is not int or not 0<=index<len(nodes) or index in visiting:
            raise ValueError('invalid or cyclic graph reference')
        if index in built: return built[index]
        visiting.add(index);node=nodes[index]
        if set(node)=={'tuple'}: obj=tuple(unpack(v) for v in node['tuple'])
        elif set(node)=={'type','fields'} and node['type'] in types:
            cls=types[node['type']]
            if set(node['fields'])!={f.name for f in fields(cls)}: raise ValueError('unknown fields')
            data={name:unpack(v) for name,v in node['fields'].items()}
            obj=cls(**data)
            for name,value in data.items():
                if type(getattr(obj,name)) is not type(value) or getattr(obj,name)!=value:
                    raise ValueError('serialized fields must already be canonical')
                object.__setattr__(obj,name,value)
        else: raise ValueError('unknown graph node type')
        visiting.remove(index);built[index]=obj
        return obj
    record=unpack(payload['root'])
    if type(record) is not Occurrence: raise ValueError('a complete actual occurrence is required')
    receipt=record.commitment
    prepared=prepare(mode,gain)
    if (type(free_choice) is not int or free_choice<0 or receipt.prepared!=prepared
            or receipt.requirement!=requirement or receipt.free_choice!=free_choice
            or receipt.admissible_count<1 or receipt.chosen.records[0].receipt.prepared!=prepared):
        raise ValueError('the external entry, requirement or choice changed')
    verify_occurrence(record,receipt,frozen_contact=True)
    return record


def summary(paths,requirement):
    successes=allowed(paths,requirement)
    errors=[triple.upper_preview(p.records,requirement)[-1][-1] for p in paths if p not in successes]
    return dict(paths=len(paths),allowed_paths=len(successes),
        first_choices=[list(v) for v in sorted({p.choices[:2] for p in successes})],
        allowed_choices=[list(p.choices) for p in successes],
        minimum_excluded_error=triple.encode(min(errors)) if errors else None)


def run():
    begun=time.monotonic()
    prepared={mode:prepare(mode) for mode in ('keep','erase','restore')}
    families={mode:finite_family(value) for mode,value in prepared.items()}
    fixture=construct_requirement(families['keep'][0])
    primary=fixture.requirement
    alternate=construct_requirement(families['keep'][32]).requirement
    reports={mode:summary(paths,primary) for mode,paths in families.items()}
    zero=prepare('keep',Q(0))
    zero_report=summary(finite_family(zero),primary)
    actuals={
        'keep-primary':execute(select(prepared['keep'],primary,1)),
        'erase-primary':execute(select(prepared['erase'],primary,1)),
        'keep-alternate':execute(select(prepared['keep'],alternate,1)),
    }
    groups=[]
    def check(name,ok,**details):
        groups.append(dict(name=name,passed=bool(ok),**details))
        if not ok: raise AssertionError(name)
    check('same_current_phase_and_current_source_response',
        len({p.state.phase for p in prepared.values()})==1 and
        all(c.leaf.kernel(p.receiver.anchor.current_context)==(-9,0,0,0) for p in prepared.values() for c in p.candidates))
    check('all_eight_local_first_choices_close_exactly',
        all(r.actual_endpoint==port.FIXED_RESULT and r.closure_error==0 for p in prepared.values() for r in first_options(p)))
    check('shared_upper_constraint_reaches_embedded_first_contact',
        reports['keep']['first_choices']==[[0,0]] and reports['erase']['first_choices']==[[i,0] for i in range(4)],reports=reports)
    check('restoration_and_zero_coupling_controls',reports['restore']==reports['keep'] and zero_report==reports['erase'])
    other=summary(families['keep'],alternate)
    check('alternate_shared_future_changes_first_contact',other['first_choices']==[[1,0]] and not allowed(families['erase'],alternate),report=other)
    check('all_sixteen_suffixes_checked_for_each_first_choice',
        all(sum(p.choices[:2]==(i,j) for p in paths)==16 for paths in families.values() for i in range(4) for j in range(2)))
    check('actual_three_flowers_plus_one_upper_close',all(len(r.actual_records)==3 and
        len(r.upper_decoded.outputs)==1 and r.upper_decoded.outputs[0].level==4 for r in actuals.values()))
    check('actual_history_and_stock_are_inherited',all(
        all(b.closed_engine.stock[:len(a.closed_engine.stock)]==a.closed_engine.stock and
            b.closed_engine.events[:len(a.closed_engine.events)]==a.closed_engine.events and
            b.closed_engine.outputs[:len(a.closed_engine.outputs)]==a.closed_engine.outputs
            for a,b in zip(r.actual_records,r.actual_records[1:])) and
        len(r.actual_records[-1].closed_engine.stock)==7 for r in actuals.values()))
    hashes={}
    OUTPUT.mkdir(parents=True,exist_ok=True)
    for name,record in actuals.items():
        raw=(json.dumps(export_record(record),ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
        sha=hashlib.sha256(raw).hexdigest();receipt=record.commitment
        restored=import_record(raw,receipt.requirement,receipt.prepared.state.mode,receipt.prepared.spec.gain,
            receipt.free_choice,trusted_sha256=sha)
        check('exact_transport_'+name,restored==record and
            (json.dumps(export_record(restored),ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')==raw)
        (OUTPUT/(name+'.record.json')).write_bytes(raw)
        hashes[name]=dict(sha256=sha,bytes=len(raw))
    result=dict(experiment='RR57 embedded 3+1 / three-flower strengthening',groups=groups,
        primary_upper_x=triple.encode(primary.x),alternate_upper_x=triple.encode(alternate.x),
        records=hashes,upstream_floating_point_regenerated_for_forecasts=False,
        full_baseline_252_rerun=False)
    (OUTPUT/'result.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(passed=True,groups=len(groups),seconds=time.monotonic()-begun,reports=reports,
        alternate=other,records=hashes),ensure_ascii=False),flush=True)
    return result


if __name__=='__main__':
    run()
